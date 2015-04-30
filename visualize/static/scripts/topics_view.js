
/*
 * Displays all topics in a table format that can be sorted.
 */
var AllTopicSubView = DefaultView.extend({
    
    baseTemplate:
"<div id=\"form-container\" class=\"row container-fluid\"></div>"+
"<div id=\"table-container\" class=\"row container-fluid\"></div>",
    
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
"        <label for=\"submit-button\"></label>"+
"        <input id=\"submit-button\" class=\"btn btn-default\" type=\"submit\"></input>"+
"    </div>"+
"</form>",
    
    initialize: function() {
        var settings = _.extend({ "words": "*", "topicTopNWords": 10, "topicDisplayNWords": 10, "sortBy": 1, "sortAscending": true }, this.settingsModel.attributes)
        this.settingsModel.set(settings);
        this.listenTo(this.settingsModel, "multichange", this.renderTopicsTable);
    },
    
    cleanup: function(topics) {},
    
    render: function() {
        this.$el.html(this.baseTemplate);
        this.renderForm();
        this.renderTopicsTable();
    },
    
    renderForm: function() {
        var that = this;
        var settings = this.settingsModel.attributes;
        var words = settings["words"].split(/[\s,]+/).join(" ");
        var topNWords = settings["topicTopNWords"];
        var displayNWords = settings["topicDisplayNWords"];
        
        // Create the form
        var el = d3.select(this.el).select("#form-container");
        el.html(this.formTemplate);
        el.select("#words-input").property("value", words);
        el.select("#top-words-input").property("value", topNWords);
        el.select("#display-words-input").property("value", displayNWords);
        el.select("form").on("submit", function() {
            d3.event.preventDefault();
            that.formSubmit();
        });
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
        this.settingsModel.set({ words: words });
        if($.isNumeric(topNWords) && topNWords > 0) {
            this.settingsModel.set({ topicTopNWords: topNWords });
        }
        if($.isNumeric(displayNWords) && topNWords > 0) {
            this.settingsModel.set({ topicDisplayNWords: displayNWords });
        }
        this.settingsModel.trigger("multichange");
    },
    
    renderTopicsTable: function() {
        var container = d3.select("#table-container").html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        var settings = this.settingsModel.attributes;
        // Make a request
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "topics": "*",
            "words": settings["words"],
            "top_n_words": settings["topicTopNWords"],
            "topic_attr": ["metrics", "names", "top_n_words"],
            "analysis_attr": "metrics",
        }, function(data) {
            container.html("");
            
            // Create HTML table element.
            var table = container.append("table")
                .attr("id", "topics-table")
                .classed("table table-hover table-condensed", true);
            // Table header.
            var header = ["", "#", "% of Corpus", "Name", "Top Words", "% of Topic"];
            // Format data.
            var totalTokens = data.datasets[this.selectionModel.get("dataset")].analyses[this.selectionModel.get("analysis")].metrics["Token Count"];
            var displayNWords = settings['topicDisplayNWords'];
            var topics = extractTopics(data);
            topics = d3.entries(topics).map(function(d) {
                var wordObjects = d.value["words"];
                var wordTypes = [];
                for(key in wordObjects) wordTypes.push(key);
                wordTypes.sort(function(a, b) { return wordObjects[b]["token_count"]-wordObjects[a]["token_count"]; });
                var words = wordTypes.slice(0, displayNWords).join(" ");
                var wordsTokenCount = _.reduce(wordTypes, function(sum, word) { return sum + wordObjects[word]["token_count"]; }, 0);
                var topicTokenCount = parseFloat(d.value.metrics["Token Count"]);
                return [parseFloat(d.key), parseFloat(d.key), (topicTokenCount*100)/totalTokens, d.value.names["Top3"], words, (wordsTokenCount*100)/topicTokenCount];
            });
            topics = topics.filter(function(item) { return item[3] != ""; });
            var wordPercentage = _.reduce(topics, function(total, innerArray) {
                return total + ((innerArray[2] * innerArray[5])/10000);
            }, 0);
            // Function performed on row click.
            var onClick = function(d, i) {
                this.selectionModel.set({ "topic": d[0] }); 
            }.bind(this);
            // Function to record current column and how it is sorted.
            var onSort = function(column, ascending) {
                this.settingsModel.set({ sortBy: column, sortAscending: ascending });
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
                sortBy: this.settingsModel.get("sortBy"),
                sortAscending: this.settingsModel.get("sortAscending"),
                onSort: onSort
            });
            // Add the word as percentage of corpus total at the bottom.
            var wordPercentageContainer = container.append("div");
            wordPercentageContainer.append("span")
                .append("b")
                .text("All filtered topic words as % of corpus: " + (wordPercentage*100).toFixed(2) + "%");
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return "<h4>FilterTopics by Words</h4>"+
        "<p>To filter the topics enter words separated by commas or spaces, use the asterisk (*) to indicate all words.</p>"+
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
        this.listenTo(this.selectionModel, "change:topic", this.render);
    },
    
    render: function() {
        this.$el.html(this.mainTemplate);
        this.renderTopicTitle();
        var tabs = {
            "Similar Topics": this.renderSimilarTopics.bind(this) ,
            "Top Documents": this.renderTopDocuments.bind(this) ,
            "Metadata and Metrics": this.renderMetadataAndMetrics.bind(this),
            "Words and Words in Context": this.renderWords.bind(this),
        };
        
        var tabOnClick = function(tab) {
            this.settingsModel.set({ selected: tab });
        }.bind(this);
        
        createTabbedContent(d3.select(this.el).select("#single-topic-info"), {
            tabs: tabs,
            selected: this.settingsModel.get("selected"),
            tabOnClick: tabOnClick,
        });
    },

    renderTopicTitle: function() {
        if(!this.selectionModel.nonEmpty(["topic"])) {
            this.$el.html("<p>Select a topic to display its information.</p>");
            return;
        }
        
        var selections = this.selectionModel.attributes;
        var container = d3.select(this.el).select("#single-topic-title");
        container.html(this.loadingTemplate);
        // Make a request
        this.dataModel.submitQueryByHash({
            "datasets": selections["dataset"],
            "analyses": selections["analysis"],
            "topics": selections["topic"],
            "topic_attr": "top_n_words",
            "words": "*",
            "top_n_words": "10",
        }, function(data) {
            container.html("");
            var topic = extractTopics(data, this.selectionModel)[selections["topic"]];
            var words = [];
            for(key in topic["words"]) words.push({ key: key, value: topic["words"][key]});
            words.sort(function(a, b) { return b.value.token_count - a.value.token_count; });
            words = _.map(words, function(entry) { return entry.key; });
            
            container.append("h2")
                .text("Topic Number: "+selections["topic"]);
            container.append("h3")
                .text(words.join(" "));
        }.bind(this), this.renderError.bind(this));
    },
    
    renderTopDocuments: function(tab, content) {
        content.html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
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
            var tokenCount = parseFloat(topic.metrics["Token Count"]);
            var documents = d3.entries(topDocs).map(function(entry) {
                return [entry.key, entry.key, entry.value.token_count, (entry.value.token_count/tokenCount)*100];
            });
            var table = content.append("table")
                .classed("table table-hover table-condensed", true);
            var onClick = function(d, i) {
                this.selectionModel.set({ "document": d[0] });
                window.location.href = "#documents";
            }.bind(this);
            createSortableTable(table, {
                header: ["", "Document", "Token Count", "% of Topic"], 
                data: documents, 
                onClick: { "1": onClick }, 
                bars: [3], 
                percentages: [3],
                favicon: [0, "documents", this],
                sortBy: 3,
                sortAscending: false,
            });
        }.bind(this), this.renderError.bind(this));
    },
    
    renderSimilarTopics: function(tab, content) {
        var that = this;
        content.html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selections["dataset"],
                "analyses": selections["analysis"],
                "topics": selections["topic"],
                "topic_attr": "metrics,names,pairwise",
        }, function(data) {
            this.dataModel.submitQueryByHash({
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
                    sortBy: header.length-1,
                    sortAscending: false,
                });
            }.bind(this), this.renderError.bind(this));
        }.bind(this), this.renderError.bind(this));
    },
    
    renderMetadataAndMetrics: function(tab, content) {
        var that = this;
        content.html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
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
    
    renderWords: function(tab, content) {
        var that = this;
        content.html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "topics": selection["topic"],
            "topic_attr": "top_n_words",
            "words": "*",
            "top_n_words": 100,
        }, function(data) {
            // Containers.
            content.html("");
            content.append("h3")
                .text("Word Cloud");
            var cloud = content.append("div")
                .classed("word-cloud container-fluid", true);
            content.append("h3")
                .text("Words in Context");
            var context = content.append("div")
                .classed("word-in-context container-fluid", true);
            
            
            // Data extraction.
            var topic = extractTopics(data, this.selectionModel)[selection.topic];
            var words = _.reduce(topic.words, function(result, value, key) {
                result[key] = value["token_count"];
                return result;
            }, {});
            
            // Select top 5 words.
            var top5 = d3.entries(words).sort(function sortWords(a, b) {
                return parseInt(b.value) - parseInt(a.value);
            }).slice(0, 5);
            
            // Set up words in context.
            this.wordsInContext = {};
            for(var i = 0; i < top5.length; i++) {
                var w = top5[i].key;
                this.wordsInContext[w] = true;
                this.renderWordInContext(context.append("div"), w);
            }
            
            // Allow more words in context.
            var wordOnClick = function wordOnClick(word) { 
                this.selectionModel.set({ word: word });
                if(!(word in this.wordsInContext)) {
                    this.wordsInContext[word] = true;
                    this.renderWordInContext(context.append("div"), word);
                }
            }.bind(this);
            
            // Render word cloud.
            createWordCloud(cloud, {
                words: words,
                wordOnClick: wordOnClick,
            });
        }.bind(this), this.renderError.bind(this));
    },
    
    /*
     * Helper function to renderWords.
     * container - The container to render the words document context in.
     * word - The word to find all contexts of.
     * Return nothing.
     */
    renderWordInContext: function(container, word) {
        container.text("Loading...");
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "topics": selection["topic"],
            "topic_attr": "word_tokens",
            "words": [word],
        }, function(data) {
            var tokens = extractTopics(data, this.selectionModel)[selection["topic"]].word_tokens[word];
            var index = 0;
            container.html(icons.document+"<span> </span>"+icons.previous+"<span> </span>"+icons.next+"<span class=\"document-text\"></span>");
            container.select(".document")
                .style("cursor", "pointer")
                .attr("title", tokens[index][0])
                .on("click", function onDocumentClick() {
                    this.selectionModel.set({ document: tokens[index][0] });
                    window.location.href = "#documents";
                }.bind(this));
            container.select(".previous")
                .style("cursor", "pointer")
                .attr("title", "Previous Context")
                .on("click", function onLeftClick() {
                    index = (index - 1 + tokens.length)%tokens.length;
                    this.renderContextText(container.select(".document-text"), tokens[index]);
                }.bind(this));
            container.select(".next")
                .style("cursor", "pointer")
                .attr("title", "Next Context")
                .on("click", function onRightClick() {
                    index = (index + 1)%tokens.length;
                    this.renderContextText(container.select(".document-text"), tokens[index]);
                }.bind(this));
            this.renderContextText(container.select(".document-text"), tokens[index]);
        }.bind(this), this.renderError.bind(this));
    },
    
    /*
     * Helper function to renderWordInContext.
     * container - D3 text container to put the text into.
     * tokenInfo - The document and the token index as a 2-tuple e.g. [doc, index].
     * Return nothing.
     */
    renderContextText: function(container, tokenInfo) {
        container.text("Loading...");
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "documents": tokenInfo[0],
            "document_attr": "kwic",
            "token_indices": tokenInfo[1],
        }, function(data) {
            var textInfo = extractDocuments(data, this.selectionModel)[tokenInfo[0]].kwic[tokenInfo[1]];
            container.html("");
            container.append("span")
                .text(textInfo[0]);
            container.append("span")
                .style("cursor", "pointer")
                .style("background-color", "yellow")
                .text(textInfo[1])
                .on("click", function onWordClick() {
                    this.selectionModel.set({ word: textInfo[3] });
                }.bind(this))
                .on("mouseenter", function() {
                    d3.select(this).style("color", "blue");
                })
                .on("mouseleave", function() {
                    d3.select(this).style("color", "black");
                });
            container.append("span")
                .text(textInfo[2]);
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return "";
    },
});

var SingleTopicSubView = DefaultView.extend({
    
    mainTemplate: "<div id=\"all-topic-container\" class=\"col-xs-3\"></div>"+
                  "<div id=\"topic-info\" class=\"col-xs-9\"></div>",
    
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
            this.info.dispose();
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
        this.info = new SingleTopicView({ el: $("#topic-info"), settingsModel: this.settingsModel });
        this.info.render();
    },
    
    renderAllTopicsSideBar: function() {
        var selections = this.selectionModel.attributes;
        var container = d3.select("#all-topic-container");
        container.append("button")
            .classed("btn btn-default", true)
            .attr("type", "button")
            .html("<span class=\"glyphicon glyphicon-chevron-left pewter\"></span> Back to All Topics")
            .on("click", function() {
                this.selectionModel.set({ "topic": "" });
            }.bind(this));
        container.append("hr");
        container = container.append("div");
        container.html(this.loadingTemplate);
        
        // Make a request
        this.dataModel.submitQueryByHash({
            "datasets": selections["dataset"],
            "analyses": selections["analysis"],
            "topics": '*',
            "topic_attr": "metrics,names",
            "analysis_attr": "metrics",
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
            var items = list.selectAll(".all-topic-sidebar-items")
                .data(topics)
                .enter()
                .append("li")
                .classed(".all-topic-sidebar-items", true)
                .classed("list-group-item", true)
                .text(function(d) {
                    return d[0] + ": " +d[1];
                })
                .on("click", function(d) {
                    this.selectionModel.set({ "topic": d[0] });
                }.bind(this));
            
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
                        d3.selectAll(".all-topic-sidebar-items").sort(ascendingSort);
                        ascending = false;
                    } else {
                        d3.selectAll(".all-topic-sidebar-items").items.sort(descendingSort);
                        ascending = true;
                    }
                });
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        var subViewHtml = "";
        if(this.info !== undefined) {
            subViewHtml = this.info.renderHelpAsHtml();
        }
        return "<h4>All Topics</h4>"+
               "<p>Use the 'Sort By' dropdown menu to choose how to sort the topics on the sidebar.  "+
               "The topics will be sorted in ascending order, to reverse the order select the sort by option again.</p>"+
               subViewHtml;
    },
});

var TopicView = DefaultView.extend({
    
    readableName: "Topics",
    
    initialize: function() {
        this.listenTo(this.selectionModel, "change:topic", this.render);
    },
    
    render: function() {
        this.$el.empty();
        if(this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<div id=\"topics-over-time\"></div><div id=\"info\"></div>");
            this.disposeOfViews();
            if(this.selectionModel.nonEmpty(["topic"])) {
                this.subView = new SingleTopicSubView({ el: "#info", settingsModel: this.settingsModel });
            } else {
                this.subView = new AllTopicSubView({ el: "#info", settingsModel: this.settingsModel });
            }
            this.subView.render();
        } else {
            this.$el.html("<p>You should select a <a href=\"#datasets\">dataset and analysis</a> before proceeding.</p>");
        }
    },
    
    renderHelpAsHtml: function() {
        if(this.subView !== undefined) {
            return this.subView.renderHelpAsHtml();
        }
        return DefaultView.prototype.renderHelpAsHtml();
    },
    
    disposeOfViews: function() {
        if(this.subView !== undefined) {
            this.subView.dispose();
        }
    },
    
    cleanup: function() {
        this.disposeOfViews();
    },
    
});

// Add the Topic View to the top level menu
globalViewModel.addViewClass([], TopicView);
