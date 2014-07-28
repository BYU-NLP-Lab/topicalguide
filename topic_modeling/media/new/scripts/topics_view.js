var AllTopicSubView = DefaultView.extend({
    
    initialize: function() {
        globalFilterModel.on("change:words", this.renderForm, this);
        globalFilterModel.on("change:topicTopNWords", this.renderForm, this);
        globalSettingsModel.on("change:topicDisplayNWords", this.renderForm, this);
        globalFilterModel.on("change:words", this.renderTopicsTableCallback, this);
        globalFilterModel.on("change:topicTopNWords", this.renderTopicsTableCallback, this);
        globalSettingsModel.on("change:topicDisplayNWords", this.renderTopicsTableCallback, this);
    },
    
    render: function() {
        this.$el.html("");
        this.$el.append("<div id=\"form-container\"></div><div id=\"table-container\"></div>");
        this.renderForm();
        this.renderTopicsTable();
    },
    
    getFilters: function() {
        return globalFilterModel.getWithDefaults({ "words": "*", "topicTopNWords": 10 });
    },
    
    getSettings: function() {
        return globalSettingsModel.getWithDefaults({ "topicDisplayNWords": 10 });
    },
    
    // Helper function to clear out the container.
    clearTopicsTable: function(){
        d3.select("#table-container").html("");
    },
    
    renderTopicsTableOnError: function(msg) {
        this.clearTopicsTable();
        d3.select("#table-container").append("p").text("Huh. An error occurred: "+msg);
    },
    
    // Helper function to put the data in the format needed to generate the topics table.
    formatData: function(data) {
        
    },
    
    cleanup: function(topics) {
        globalFilterModel.off(null, this.renderForm, this);
        globalFilterModel.off(null, this.renderForm, this);
        globalSettingsModel.off(null, this.renderForm, this);
        globalFilterModel.off(null, this.renderTopicsTable, this);
        globalFilterModel.off(null, this.renderTopicsTable, this);
        globalSettingsModel.off(null, this.renderTopicsTable, this);
    },
    
    // Requires that a div is created for it.
    renderForm: function() {
        var filters = globalFilterModel.getWithDefaults({ "words": "*", "topicTopNWords": 10 });
        var words = filters["words"];
        words = words.split(",").join(" ");
        var topNWords = filters["topicTopNWords"];
        var displayNWords = globalSettingsModel.getWithDefaults({ "topicDisplayNWords": 10 })["topicDisplayNWords"];
        
        // Create a form
        var el = d3.select("#form-container");
        el.html("");
        var form = el.append("form")
            .attr("role", "form");
        // Instructions.
        var group = form.append("div")
            .classed("form-group col-xs-12", true);
        group.append("label").attr("for", "input-instructions").text("Instructions");
        group.append("p")
            .attr("id", "input-instructions")
            .text("To filter the topics enter words separated by commas, use the splat ('*') symbol to indicate all words. "+
                  "The 'Top Words' field will limit results to the amount indicated taking the most common words. "+
                  "The 'Display Words' field will limit what you see on the screen to a reasonable size.");
        // Words
        group = form.append("div")
            .classed("form-group col-xs-6", true);
        group.append("label").attr("for", "words-input").text("Filter Topics by Words");
        group.append("input").attr("type", "email").classed("form-control", true).attr("id", "words-input")
            .attr("placeholder", "Enter words...").property("value", words);
        // Top Words
        group = form.append("div")
            .classed("form-group col-xs-2", true);
        group.append("label").attr("for", "top-words-input").text("Top Words");
        group.append("input").attr("type", "number").classed("form-control", true).attr("id", "top-words-input")
            .attr("placeholder", "Enter a #...").property("value", topNWords);
        // Display Words
        group = form.append("div")
            .classed("form-group col-xs-2", true);
        group.append("label").attr("for", "display-words-input").text("Display Words");
        group.append("input").attr("type", "number").classed("form-control", true).attr("id", "display-words-input")
            .attr("placeholder", "Enter a #...").property("value", displayNWords);
        // Display Words
        group = form.append("div")
            .classed("form-group col-xs-2", true);
        group.append("label").attr("for", "submit-button").text("Submit");
        group.append("button").attr("type", "button").classed("btn btn-default", true).attr("id", "submit-button")
            .style("display", "block")
            .style("width", "100%")
            .text("Submit")
            .on("click", this.formSubmit);
    },
    
    formSubmit: function() {
        var words = d3.select("#words-input").property("value").split(",");
        words = _.map(words, function(word) { return word.trim(); });
        words = _.filter(words, function(word) { return word !== ""; });
        words.sort();
        words = _.uniq(words, true);
        words = words.join(",");
        console.log(JSON.stringify(words));
        var topNWords = parseInt(d3.select("#top-words-input").property("value"));
        var displayNWords = parseInt(d3.select("#display-words-input").property("value"));
        globalFilterModel.set({ words: words });
        if($.isNumeric(topNWords) && topNWords > 0) {
            globalFilterModel.set({ topicTopNWords: topNWords });
        }
        if($.isNumeric(displayNWords) && topNWords > 0) {
            globalSettingsModel.set({ topicDisplayNWords: displayNWords });
        }
    },
    
    renderTopicsTableCallback: function() {
        this.renderTopicsTable();
    },
    
    renderTopicsTable: function(data) {
        if(data == undefined || _.size(data) === 0) {
            // No data implies we need to make a request
            this.clearTopicsTable();
            d3.select("#table-container").append("p").text("Loading...");
            var filters = this.getFilters();
            var data = globalSelectionModel.getListed(["dataset", "analysis"])
            // Make a request
            globalDataModel.submitQueryByHash({
                "datasets": data["dataset"],
                "analyses": data["analysis"],
                "topics": "*",
                "words": filters["words"],
                "top_n_words": filters["topicTopNWords"],
                "topic_attr": "metrics,names",
                "dataset_attr": "metrics",
                "word_metrics": "token_count",
            }, this.renderTopicsTable.bind(this), this.renderTopicsTableOnError.bind(this));
        } else {
            // Render the table.
            this.clearTopicsTable();
            
            // Create help message.
            d3.select("#table-container").append("h4").text("Help");
            var helpText = "The '% of Corpus' column is the amount of the corpus the topic makes up by word count. "+
                "Due to stopwords (i.e. the, a, this, etc.) the percentages may not add up to 100. "+
                "The '% of Topic' column is the amount of the topic that the words make up by count.";
            d3.select("#table-container").append("p").text(helpText);
            
            // Create table.
            d3.select("#table-container").append("table")
                .attr("id", "topics-table")
                .classed("table table-hover table-condensed", true);
            
            // Get basic data.
            var datasetTokens = extractSubHash(globalSelectionModel.get("dataset"), data).metrics["Token Count"];
            var topics = extractSubHash("topics", data);
            var displayNWords = this.getSettings()['topicDisplayNWords'];
            
            // Map the topics into the format as given by tableHeader
            // Mainly [[Number, ...]...]
            topics = d3.entries(topics).map(function(d) {
                var wordObjects = d.value["words"];
                var wordTypes = [];
                for(key in wordObjects) wordTypes.push(key);
                wordTypes.sort(function(a, b) { return wordObjects[b]["token_count"]-wordObjects[a]["token_count"]; });
                var words = wordTypes.slice(0, displayNWords).join(" ");
                var wordsTokenCount = _.reduce(wordTypes, function(sum, word) { return sum + wordObjects[word]["token_count"]; }, 0);
                var topicTokenCount = parseFloat(d.value.metrics["Number of tokens"]);
                return [parseFloat(d.key), topicTokenCount/datasetTokens, d.value.names["Top3"], words, wordsTokenCount/topicTokenCount];
            });
            topics = topics.filter(function(item) { return item[3] != ""; });
            var maxCorpusPercentage = topics.reduce(function(p, c, i, a) { return (p > c[1])?p:c[1]; }, 0);
            var table = d3.select("#topics-table");
            var tableHeader = ["#", "% of Corpus", "Name", "Top Words", "% of Topic"];
            
            var ascending = true;
            var lastColumn = 0;
            
            var headerRow = table.append("thead")
                .append("tr").selectAll("tr")
                .data(tableHeader)
                .enter()
                .append("th")
                .append("a")
                .on("click", function(d, i) {
                    var topicsSortAscending = function(a, b) {
                        if($.isNumeric(a[i]) && $.isNumeric(b[i])) return parseFloat(a[i]) - parseFloat(b[i]);
                        else return a[i].localeCompare(b[i]);
                    };
                    var topicsSortDescending = function(a, b) { return topicsSortAscending(b, a); };
                    if(lastColumn !== i) ascending = true;
                    lastColumn = i;
                    if(ascending) {
                        ascending = false;
                        tableRows.sort(topicsSortAscending);
                    } else {
                        ascending = true;
                        tableRows.sort(topicsSortDescending); 
                    }
                })
                .style("text-align", function(d, i) { return (i === tableHeader.length-1)?"right":"left"; })
                .classed({ "nounderline": true })
                .style("white-space", "nowrap")
                .text(function(title) { return title+" "; })
                .append("span")
                .classed({"glyphicon": true, "glyphicon-sort": true});
            
            var tableRows = table.append("tbody")
                .selectAll("tr")
                .data(topics)
                .enter().append("tr");
            
            var tableDefinitions = tableRows.selectAll("td")
                .data(function(d) { return d; })
                .enter()
                .append("td");
            
            tableDefinitions.filter(function(d, i) { return (i === 1 || i === 4)?false:true; })
                .append("span")
                .text(function(d) { return d; });
                //~ .style("text-align", function(d, i) { return (i === tableHeader.length-1)?"right":"left"; });
            
            var corpusPercentage = tableDefinitions.filter(function(d, i) { return (i === 1)?true:false; });
            
            var corpusSvg = corpusPercentage.append("svg")
                .attr("width", 60)
                .attr("height", "1em");
            
            corpusSvg.append("rect")
                .attr("height", "100%")
                .attr("width", "100%")
                .attr("fill", "blue");
            
            corpusSvg.append("rect")
                .attr("height", "100%")
                .attr("width", function(d) { return (1-(d/maxCorpusPercentage)) * 60; })
                .attr("fill", "whitesmoke");
            
            var text = corpusPercentage.append("span")
                .text(function(d) { return " "+(d*100).toFixed(2)+"%"; })
                .attr("fill", "black")
                .attr("padding-left", "5px");
            
            var topicPercentage = tableDefinitions.filter(function(d, i) { return (i === 4)?true:false; });
            
            var topicSvg = topicPercentage.append("svg")
                .attr("width", 60)
                .attr("height", "1em");
            
            topicSvg.append("rect")
                .attr("height", "100%")
                .attr("width", "100%")
                .attr("fill", "blue");
            
            topicSvg.append("rect")
                .attr("height", "100%")
                .attr("width", function(d) { return (1-d) * 60; })
                .attr("fill", "whitesmoke");
            
            text = topicPercentage.append("span")
                .text(function(d) { return " "+(d*100).toFixed(2)+"%"; })
                .attr("fill", "black")
                .attr("padding-left", "5px");
        }
    },
});

var TopicView = DefaultView.extend({
    
    readableName: "Topics",
    
    initialize: function() {
        globalSelectionModel.on("change:dataset", this.render, this);
        globalSelectionModel.on("change:analysis", this.render, this);
        globalSelectionModel.on("change:topic", this.render, this);
        globalDataModel.on("change:topics", this.render, this);
    },
    
    render: function() {
        if(globalSelectionModel.nonEmpty(["dataset", "analysis"])) {
            if(globalSelectionModel.nonEmpty(["topic"])) {
                this.cleanupViews();
                this.$el.html("<p>You selected a topic. No visualizations are up currently.</p>");
            } else {
                this.cleanupViews();
                this.allTopicsView = new AllTopicSubView({ el: this.$el });
                this.allTopicsView.render();
            }
        } else {
            this.$el.html("<p>You should select a <a href=\"#\">dataset and analysis</a> before proceeding.</p>");
        }
    },
    
    cleanupViews: function() {
        if(this.allTopicsView !== undefined) {
            this.allTopicsView.cleanup();
        }
    },
    
    cleanup: function() {
        this.cleanupViews();
        globalSelectionModel.off(null, this.render, this);
        globalDataModel.off(null, this.render, this);
    }
    
});

// Add the Topic View to the top level menu
globalViewModel.addViewClass([], TopicView);
