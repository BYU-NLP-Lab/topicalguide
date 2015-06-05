"use strict";

/*
 * Displays all topics in a table format that can be sorted.
 */
var TopicWordsView = DefaultView.extend({
    
    readableName: "Topic Words",
    shortName: "all_topic_words",
    
    baseTemplate:
'<div id="form-container" class="row container-fluid"></div>'+
'<div id="table-container" class="row container-fluid"></div>',
    
    formTemplate:
'<form role="form">'+
'    <div class="form-group col-xs-3">'+
'        <label for="words-input">Filter by Words</label>'+
'        <input id="words-input" class="form-control" type="text" placeholder="Enter words..."></input>'+
'    </div>'+
'    <div class="form-group col-xs-2">'+
'        <label for="metadata-attribute-input">Filter by Metadata Attribute</label>'+
'        <select id="metadata-attribute-input" class="form-control" type="selection" placeholder="Enter metadata attribute..."></select>'+
'    </div>'+
'    <div class="form-group col-xs-4">'+
'        <label>Filter by Metadata Value</label>'+
'        <div class="all-topics-metadata-value-form"></div>'+
//~ '        <input id="metadata-value-input" class="form-control" type="text" placeholder="Enter metadata value..."></input>'+
'    </div>'+
'    <div class="form-group col-xs-2">'+
'        <label for="top-words-input">Top Words</label>'+
'        <input id="top-words-input" class="form-control" type="number" placeholder="Enter a #."></input>'+
'    </div>'+
'    <div class="form-group col-xs-1">'+
'        <label for="submit-button"></label>'+
'        <input id="submit-button" class="btn btn-default" type="submit"></input>'+
'    </div>'+
'</form>',
    
    initialize: function() {
        var settings = _.extend({ "words": "*", "topicTopNWords": 10, "sortBy": 1, "sortAscending": true }, this.settingsModel.attributes)
        this.settingsModel.set(settings);
        this.listenTo(this.settingsModel, "multichange", this.renderTopicsTable);
        this.listenTo(this.selectionModel, "change:topicNameScheme", this.renderTopicsTable);
    },
    
    cleanup: function(topics) {
        this.metadataValueWidget.dispose();
    },
    
    render: function() {
        this.$el.html(this.baseTemplate);
        this.renderForm();
        this.renderTopicsTable();
    },
    
    renderForm: function() {
        var container = d3.select("#form-container").html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        // Make a request
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "dataset_attr": ["document_metadata_types"],
        }, function(data) {
            container.html("");
        
            var that = this;
            var settings = this.settingsModel.attributes;
            var words = settings["words"].split(/[\s,]+/).join(" ");
            var topNWords = settings["topicTopNWords"];
            
            var attribute = this.selectionModel.get("metadataName");
            var value = this.selectionModel.get("metadataValue");
            
            var types = data.datasets[this.selectionModel.get("dataset")].document_metadata_types;
            var attributes = _.map(types, function(type, attr) { return attr; });
            //~ console.log(attributes);

            // Create the form
            var el = d3.select(this.el).select("#form-container");
            el.html(this.formTemplate);
            el.select("#words-input").property("value", words);
            el.select("#top-words-input").property("value", topNWords);
            
            this.metadataValueWidget = new MetadataValueWidget(_.extend({ el: this.$el.find(".all-topics-metadata-value-form").get(0) }, this.getAllModels()));
            this.metadataValueWidget.render();
            
            var select = el.select("#metadata-attribute-input");
            select.selectAll("option").data(attributes).enter().append("option")
                .text(function (attr) { return tg.str.toTitleCase(attr.replace(/_/g, " ")); })
                .property("value", function (attr) { return attr; });
            select.property("value", attribute);
            el.select("form").on("submit", function() {
                d3.event.preventDefault();
                that.formSubmit();
            });
            
        }.bind(this), this.renderError.bind(this));
    },
    
    events: {
        "change #metadata-attribute-input": "changeMetadataAttribute",
    },
    
    changeMetadataAttribute: function(e) {
        console.log("Metadata attribute changed.");
        this.selectionModel.set({ metadataName: $(e.currentTarget).find(":selected").val() });
    },
    
    formSubmit: function() {
        var words = d3.select("#words-input").property("value").split(/[\s,]+/);
        words = _.map(words, function(word) { return word.trim().toLowerCase(); });
        words = _.filter(words, function(word) { return word !== ""; });
        words.sort();
        words = _.uniq(words, true);
        words = words.join(",");
        var topNWords = parseInt(d3.select("#top-words-input").property("value"));
        this.settingsModel.set({ words: words });
        if($.isNumeric(topNWords) && topNWords > 0) {
            this.settingsModel.set({ topicTopNWords: topNWords });
        }
        this.selectionModel.set({ metadataName: $("#metadata-attribute-input option:selected").val() });
        console.log("Selected value: " + $("#metadata-value-input").val() );
        
        this.settingsModel.trigger("multichange");
    },
    
    renderTopicsTable: function() {
        var container = d3.select("#table-container").html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        var settings = this.settingsModel.attributes;
        var queryHash = {
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "topics": "*",
            "words": settings["words"],
            "top_n_words": settings["topicTopNWords"],
            "topic_attr": ["metrics", "names", "top_n_words"],
            "analysis_attr": "metrics",
        }
        if (selection["metadataName"] !== "") {
            if (selection["metadataValue"] !== "") {
                queryHash["metadata_name"] = selection["metadataName"];
                queryHash["metadata_value"] = selection["metadataValue"];
            }
            if (selection["metadataRange"] !== "") {
                queryHash["metadata_name"] = selection["metadataName"];
                queryHash["metadata_range"] = selection["metadataRange"];
            }
        }
        
        // Make a request
        this.dataModel.submitQueryByHash(queryHash, function(data) {
			var that = this;
			
            container.html("");
            
            // Create HTML table element.
            var table = container.append("table")
                .attr("id", "topics-table")
                .classed("table table-hover table-condensed", true);
            // Table header.
            var header = ["", "#", "% of Corpus", "Name", "Top Words", "% of Topic", "Temperature"];
            // Format data.
            var totalTokens = data.datasets[this.selectionModel.get("dataset")].analyses[this.selectionModel.get("analysis")].metrics["Token Count"];
            var topNWords = settings['topicTopNWords'];
            var topics = extractTopics(data, this.selectionModel);
            topics = d3.entries(topics).map(function(d) {
                var wordObjects = d.value["words"];
                var wordTypes = [];
                for(var key in wordObjects) wordTypes.push(key);
                wordTypes.sort(function(a, b) { return wordObjects[b]["token_count"]-wordObjects[a]["token_count"]; });
                var words = wordTypes.slice(0, topNWords).join(" ");
                var wordsTokenCount = _.reduce(wordTypes, function(sum, word) { return sum + wordObjects[word]["token_count"]; }, 0);
                var topicTokenCount = parseFloat(d.value.metrics["Token Count"]);
                var topicTemperature = parseFloat(d.value.metrics["Temperature"].toPrecision(4));
                return [
                    parseFloat(d.key),
                    parseFloat(d.key),
                    (topicTokenCount*100)/totalTokens,
                    that.dataModel.getTopicNameRaw(d.key),
                    words,
                    (wordsTokenCount*100)/topicTokenCount,
                    topicTemperature
                ];
            });
            topics = topics.filter(function(item) { return item[4] !== ""; });
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
                temperatures: [6],
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

// Add the Topic View to the top level menu
addViewClass(["Topic"], TopicWordsView);
