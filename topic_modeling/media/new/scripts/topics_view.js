/*
 * Displays all topics in a table format that can be sorted.
 */
var AllTopicSubView = DefaultView.extend({
    
    baseTemplate:
"<div id=\"form-container\" class=\"row\"></div>"+
"<div id=\"table-container\" class=\"row\"></div>",
    
    formTemplate:
"<form role=\"form\">"+
"    <div class=\"form-group col-xs-6\">"+
"        <label for=\"words-input\">Filter Topics by Words</label>"+
"        <input id=\"words-input\" class=\"form-control\" type=\"text\" placeholder=\"Enter words...\"></input>"+
"    </div>"+
"    <div class=\"form-group col-xs-2\">"+
"        <label for=\"top-words-input\">Top Words</label>"+
"        <input id=\"top-words-input\" class=\"form-control\" type=\"number\" placeholder=\"Enter a #.\"></input>"+
"    </div>"+
"    <div class=\"form-group col-xs-2\">"+
"        <label for=\"display-words-input\">Display Words</label>"+
"        <input id=\"display-words-input\" class=\"form-control\" type=\"number\" placeholder=\"Enter a #.\"></input>"+
"    </div>"+
"    <div class=\"form-group col-xs-2\">"+
"        <button id=\"submit-button\" class=\"btn btn-default\" type=\"submit\">Submit</button>"+
"    </div>"+
"</form>",
    
    initialize: function() {
        this.model = new Backbone.Model();
        this.model.set({ "words": "*", "topicTopNWords": 10, "topicDisplayNWords": 10 });
        this.model.on("multichange", this.renderTopicsTable, this);
    },
    
    cleanup: function(topics) {
        // Not bound to external models.
    },
    
    render: function() {
        this.$el.html(this.baseTemplate);
        this.renderForm();
        this.renderTopicsTable();
    },
    
    renderForm: function() {
        var settings = this.model.attributes;
        var words = settings["words"].split(/[\s,]+/).join(" ");
        var topNWords = settings["topicTopNWords"];
        var displayNWords = settings["topicDisplayNWords"];
        
        // Create the form
        var el = d3.select(this.el).select("#form-container");
        el.html(this.formTemplate);
        el.select("#words-input").property("value", words);
        el.select("#top-words-input").property("value", topNWords);
        el.select("#display-words-input").property("value", displayNWords);
        el.select("form").on("submit", this.formSubmit.bind(this));
    },
    
    formSubmit: function() {
        var words = d3.select("#words-input").property("value").split(/[\s,]+/);
        words = _.map(words, function(word) { return word.trim().toLowerCase(); });
        words = _.filter(words, function(word) { return word !== ""; });
        words.sort();
        words = _.uniq(words, true);
        words = words.join(",");
        var topNWords = parseInt(d3.select("#top-words-input").property("value"));
        var displayNWords = parseInt(d3.select("#display-words-input").property("value"));
        this.model.set({ words: words });
        if($.isNumeric(topNWords) && topNWords > 0) {
            this.model.set({ topicTopNWords: topNWords });
        }
        if($.isNumeric(displayNWords) && topNWords > 0) {
            this.model.set({ topicDisplayNWords: displayNWords });
        }
        this.model.trigger("multichange");
    },
    
    renderTopicsTable: function() {
        d3.select("#table-container").html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        var settings = this.model.attributes;
        // Make a request
        globalDataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "topics": "*",
            "words": settings["words"],
            "top_n_words": settings["topicTopNWords"],
            "topic_attr": "metrics,names",
            "dataset_attr": "metrics",
            "word_metrics": "token_count",
        }, function(data) {
            d3.select("#table-container").html("");
            
            // Create table.
            var table = d3.select("#table-container").append("table")
                .attr("id", "topics-table")
                .classed("table table-hover table-condensed", true);
            // Table header.
            var header = ["", "#", "% of Corpus", "Name", "Top Words", "% of Topic"];
            // Format data.
            var datasetTokens = data.datasets[globalSelectionModel.get("dataset")].metrics["Token Count"];
            var displayNWords = settings['topicDisplayNWords'];
            var topics = extractTopics(data);
            topics = d3.entries(topics).map(function(d) {
                var wordObjects = d.value["words"];
                var wordTypes = [];
                for(key in wordObjects) wordTypes.push(key);
                wordTypes.sort(function(a, b) { return wordObjects[b]["token_count"]-wordObjects[a]["token_count"]; });
                var words = wordTypes.slice(0, displayNWords).join(" ");
                var wordsTokenCount = _.reduce(wordTypes, function(sum, word) { return sum + wordObjects[word]["token_count"]; }, 0);
                var topicTokenCount = parseFloat(d.value.metrics["Number of tokens"]);
                return [parseFloat(d.key), parseFloat(d.key), (topicTokenCount*100)/datasetTokens, d.value.names["Top3"], words, (wordsTokenCount*100)/topicTokenCount];
            });
            topics = topics.filter(function(item) { return item[3] != ""; });
            // Function performed on row click.
            var onClick = function(d, i) { 
                this.selectionModel.set({ "topic": d[0] }); 
            }.bind(this);
            // Make the table.
            var toCleanup = createSortableTable(table, {
                header: header,
                data: topics,
                onClick: {  
                        "1": onClick,
                        "3": onClick,
                        "4": onClick,
                    },
                bars: [2,5],
                percentages: [2,5],
                favicon: [0, "topics", this],
            });
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return "<h4>FilterTopics by Words</h4>"+
        "<p>To filter the topics enter words separated by commas or spaces, use the splat ('*') symbol to indicate all words.</p>"+
        "<h4>Top Words</h4>"+
        "<p>This field is to limit the results returned by the server. The results are used to determine the % of the topic they make up.</p>"+
        "<h4>Display Words</h4>"+
        "<p>This will determine the maximum number of words displayed on the screen.</p>"+
        "<h4>Submit</h4>"+
        "<p>Click submit to view the changes made.</p>"+
        "<h4>The Topics Table</h4>"+
        "<p><ul>"+
        "<li>The '% of Corpus' column is the amount of the corpus the topic makes up by word count. "+
        "Due to stopwords (i.e. the, a, this, etc.) the percentages may not add up to 100.</li>"+
        "<li>The '% of Topic' column is the amount of the words the topic is composed of.</li>"+
        "<li>Click on the column headings to sort the data by that column; click again to reverse the sort.</li>"+
        "<li>Click on a row to select a topic and toggle to a different view.</li>"+
        "</ul></p>";
    },
});

var SingleTopicView = DefaultView.extend({
    
    mainTemplate: 
"<div id=\"single-topic-title\" class=\"row\"></div>"+
"<div id=\"single-topic-info\" class=\"row\"></div>",
    
    initialize: function() {
        this.selectionModel.on("change:topic", this.render, this);
    },
    
    cleanup: function() {
        this.selectionModel.off(null, null, this);
    },
    
    render: function() {
        this.$el.html(this.mainTemplate);
        this.renderTopicTitle();
        createTabbedContent(d3.select(this.el).select("#single-topic-info"), {
            "Similar Topics": this.renderSimilarTopics.bind(this) ,
            "Top Documents": this.renderTopDocuments.bind(this) ,
            "Metadata/Metrics": this.renderMetadataAndMetrics.bind(this),
        });
    },

    renderTopicTitle: function() {
        if(!this.selectionModel.nonEmpty(["topic"])) {
            this.$el.html("<p>Select a topic to display its information.</p>");
            return;
        }
        
        var selections = globalSelectionModel.attributes;
        var container = d3.select(this.el).select("#single-topic-title");
        container.html(this.loadingTemplate);
        // Make a request
        globalDataModel.submitQueryByHash({
            "datasets": selections["dataset"],
            "analyses": selections["analysis"],
            "topics": selections["topic"],
            "word_metrics": "token_count",
            "words": "*",
            "top_n_words": "10",
        }, function(data) {
            container.html("");
            var topic = extractTopics(data)[selections["topic"]];
            var words = [];
            for(key in topic["words"]) words.push({ key: key, value: topic["words"][key]});
            words.sort(function(a, b) { return b.value.token_count - a.value.token_count; });
            words = _.map(words, function(entry) { return entry.key; });
            
            container.append("h2")
                .text("Topic Number: "+selections["topic"]);
            container.append("h3")
                .text(words.join(" "));
        }, this.renderError.bind(this));
    },
    
    renderTopDocuments: function(content) {
        content.html(this.loadingTemplate);
        var selections = globalSelectionModel.attributes;
        globalDataModel.submitQueryByHash({
            "datasets": selections["dataset"],
            "analyses": selections["analysis"],
            "topics": selections["topic"],
            "topic_attr": "metrics",
            "top_n_documents": 10,
        }, function(data) {
            content.html("");
            var topicNumber = this.selectionModel.get("topic");
            var topic = extractTopics(data)[topicNumber];
            var topDocs = topic["top_n_documents"];
            var tokenCount = parseFloat(topic.metrics["Number of tokens"]);
            var documents = d3.entries(topDocs).map(function(entry) {
                return [entry.key, entry.key, entry.value.token_count, (entry.value.token_count/tokenCount)*100];
            });
            var table = content.append("table")
                .classed("table table-hover table-condensed", true);
            var onClick = function(d, i) {
                this.selectionModel.set({ "document": d[0] });
            }.bind(this);
            createSortableTable(table, {
                header: ["", "Document", "Token Count", "%"], 
                data: documents, 
                onClick: { "1": onClick }, 
                bars: [3], 
                percentages: [3],
                favicon: [0, "documents", this],
            });
        }.bind(this), this.renderError.bind(this));
    },
    
    renderSimilarTopics: function(content) {
        var that = this;
        content.html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        globalDataModel.submitQueryByHash({
                "datasets": selections["dataset"],
                "analyses": selections["analysis"],
                "topics": selections["topic"],
                "topic_attr": "metrics,names,pairwise",
        }, function(data) {
            globalDataModel.submitQueryByHash({
                "datasets": selections["dataset"],
                "analyses": selections["analysis"],
                "topics": "*",
                "topic_attr": "names",
            },function(allTopicsData) {
                content.html("");
                var allTopics = extractTopics(allTopicsData);
                var currentTopic = that.selectionModel.get("topic");
                var topic = extractTopics(data)[currentTopic];
                var header = ["", "#", "Topic Name"];
                var updateHeader = true;
                var percentageColumns = [];
                var finalData = d3.entries(allTopics)
                    .filter(function(entry) {
                        return entry.key != currentTopic;
                    })
                    .map(function(entry) {
                        var result = [entry.key, entry.key, entry.value.names.Top3];
                        var index = parseFloat(entry.key);
                        var pairwise = topic["pairwise"];
                        for(key in pairwise) {
                            result.push(pairwise[key][index]*100);
                            if(updateHeader) {
                                header.push(key);
                                percentageColumns.push(header.length-1);
                            }
                        }
                        updateHeader = false;
                        return result;
                    });
                
                var table = content.append("table")
                    .classed("table table-hover table-condensed", true);
                var onClick = function(d, i) {
                    this.selectionModel.set({ "topic": d[0] });
                }.bind(this);
                
                createSortableTable(table, {
                    header: header, 
                    data: finalData, 
                    onClick: { "1": onClick, "2": onClick }, 
                    bars: percentageColumns, 
                    percentages: percentageColumns,
                    favicon: [0, "topics", this],
                });
            }.bind(this), this.renderError.bind(this));
        }.bind(this), this.renderError.bind(this));
    },
    
    renderMetadataAndMetrics: function(content) {
        var that = this;
        content.html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        globalDataModel.submitQueryByHash({
                "datasets": selections["dataset"],
                "analyses": selections["analysis"],
                "topics": selections["topic"],
                "topic_attr": "metrics,metadata",
        }, function(data) {
            content.html("<div id=\"single-topic-metadata\" class=\"row container-fluid\"></div><div id=\"single-topic-metrics\" class=\"row container-fluid\"></div>");
            var topic = extractTopics(data)[selections["topic"]];
            createTableFromHash(content.select("#single-topic-metadata"), topic.metadata, ["Key", "Value"], "metadata");
            createTableFromHash(content.select("#single-topic-metrics"), topic.metrics, ["Metric", "Value"]), "metrics";
        }, this.renderError.bind(this));
    },
});

var SingleTopicSubView = DefaultView.extend({
    
    mainTemplate: "<div id=\"all-topic-container\" class=\"col-xs-4\"></div>"+
                  "<div id=\"topic-info\" class=\"col-xs-8\"></div>",
    
    dropdownTemplate: "<div class=\"btn-group\">"+
                          "<button type=\"button\" class=\"btn btn-primary\">Sort By</button>"+
                          "<button type=\"button\" class=\"btn btn-primary dropdown-toggle\" data-toggle=\"dropdown\">"+
                            "<span class=\"caret\"></span>"+
                            "<span class=\"sr-only\">Toggle Dropdown</span>"+
                          "</button>"+
                          "<ul id=\"sort-by\" class=\"dropdown-menu\" role=\"menu\"></ul>"+
                      "</div>",
    
    initialize: function() {},
    
    cleanup: function() {
        if(this.info !== undefined) {
            this.info.cleanup();
        }
    },
    
    render: function() {
        this.$el.html(this.mainTemplate);
        this.renderAllTopicsSideBar();
        this.renderTopicInfo();
    },
    
    renderTopicInfo: function() {
        if(this.info !== undefined) {
            this.info.cleanup();
        }
        this.info = new SingleTopicView({ el: $("#topic-info") });
        this.info.render();
    },
    
    renderAllTopicsSideBar: function() {
        var selections = globalSelectionModel.attributes;
        var container = d3.select("#all-topic-container");
        container.append("button")
            .classed("btn btn-default", true)
            .attr("type", "button")
            .html("<span class=\"glyphicon glyphicon-chevron-left pewter\"></span> Back to All Topics")
            .on("click", function() {
                this.selectionModel.set({ "topic": "" });
            });
        container.append("hr");
        container = container.append("div");
        container.html(this.loadingTemplate);
        
        // Make a request
        globalDataModel.submitQueryByHash({
            "datasets": selections["dataset"],
            "analyses": selections["analysis"],
            "topics": '*',
            "topic_attr": "metrics,names",
            "dataset_attr": "metrics",
            "word_metrics": "token_count",
        }, function(data) { // Render the content
            container.html(this.dropdownTemplate);
            
            var sortList = [];
            var topics = extractTopics(data);
            topics = d3.entries(topics).map(function(d) {
                
                var items = {};
                for(key in d.value.names) {
                    items[key] = d.value.names[key];
                }
                for(key in d.value.metrics) {
                    items[key] = d.value.metrics[key];
                }
                items["Number"] = d.key;
                if(d.key === "0") {
                    for(key in items) sortList.push(key);
                }
                return [d.key, d.value.names.Top3, items];
            });
            var tableHeader = ['Topics'];
            var ascending = true;
            var sortBy = 'Number';
            
            
            var list = d3.select("#all-topic-container").append("ul")
                .classed("list-unstyled", true);
            var items = list.selectAll("li")
                .data(topics)
                .enter()
                .append("li")
                .classed("list-group-item", true)
                .text(function(d) {
                    return d[0] + ": " +d[1];
                })
                .on("click", function(d) {
                    globalSelectionModel.set({ "topic": d[0] });
                });
            
            var sort = d3.select("#sort-by").selectAll("li")
                .data(sortList)
                .enter()
                .append("li")
                .append("a")
                .text(function(d) { return d; })
                .on("click", function(d) {
                    var ascendingSort = function(a, b) {
                        if($.isNumeric(a[2][d]) && $.isNumeric(b[2][d])) return parseFloat(a[2][d]) - parseFloat(b[2][d]);
                        else return a[2][d].localeCompare(b[2][d]);
                    };
                    var descendingSort = function(a, b) {
                        return ascendingSort(b,a);
                    };
                    
                    if(d !== sortBy) ascending = true;
                    sortBy = d;
                    if(ascending) {
                        items.sort(ascendingSort);
                        ascending = false;
                    } else {
                        items.sort(descendingSort);
                        ascending = true;
                    }
                });
        }.bind(this), this.renderError.bind(this));
    },
});

var TopicView = DefaultView.extend({
    
    readableName: "Topics",
    
    initialize: function() {
        globalSelectionModel.on("change:topic", this.render, this);
    },
    
    render: function() {
        if(globalSelectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<div id=\"topics-over-time\"></div><div id=\"info\"></div>");
            this.cleanupViews();
            if(globalSelectionModel.nonEmpty(["topic"])) {
                this.subview = new SingleTopicSubView({ el: "#info" });
            } else {
                this.subview = new AllTopicSubView({ el: "#info" });
            }
            this.subview.render();
        } else {
            this.$el.html("<p>You should select a <a href=\"#\">dataset and analysis</a> before proceeding.</p>");
        }
    },
    
    renderHelpAsHtml: function() {
        if(this.subview !== undefined) {
            return this.subview.renderHelpAsHtml();
        }
        return DefaultView.prototype.renderHelpAsHtml();
    },
    
    cleanupViews: function() {
        if(this.subview !== undefined) {
            this.subview.cleanup();
        }
    },
    
    cleanup: function() {
        this.cleanupViews();
        globalSelectionModel.off(null, this.render, this);
    }
    
});

// Add the Topic View to the top level menu
globalViewModel.addViewClass([], TopicView);
