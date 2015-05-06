"use strict";

/**
 * Responsible for rendering the lists of documents for the user to select a
 * document from.
 */
var AllDocumentsSubView = DefaultView.extend({
    readableName: "All Documents",
    shortName: "all_docs",
    
    initialize: function() {
        var defaults = {
            page: 1,
            docsPerPage: 30,
        };
        // Set the settingsModel to the defaults if the values aren't present already.
        this.settingsModel.set(_.extend(defaults, this.settingsModel.attributes));
    },
    
    cleanup: function(topics) {},
    
    render: function() {
        this.$el.html(this.loadingTemplate);
        
        // Get the total number of documents.
        var dataset = this.selectionModel.get("dataset");
        this.documentCount = this.dataModel.getDatasetDocumentCount(dataset);
        this.maxDocumentsPerRequest = this.dataModel.getServerInfo()['max_documents_per_request'];
        
        // Display the page.
        this.$el.html(this.htmlTemplate);
        d3.selectAll(".all-docs-nav")
            .style("font-size", "1.5em");
        
        // Setup listeners
        this.listenTo(this.settingsModel, "change", this.updateDocumentsRange);
        this.listenTo(this.settingsModel, "change", this.updateAllDocumentsTable);
        
        // Display
        d3.select(this.el).select("#all-docs-total-docs")
            .text(this.documentCount);
        this.updatePageField();
        this.updateDocumentsPerPageField();
        this.updateDocumentsRange();
        this.updateAllDocumentsTable();
    },
    
    htmlTemplate:
"<div id=\"all-docs-top-matter-container\">"+
"    <form role=\"form\" class=\"form-inline center\">"+
"    <div class=\"form-group\">"+
"    <div class=\"input-group\">"+
"        <div class=\"input-group-addon\">Page</div>"+
"        <input id=\"all-docs-page\" class=\"form-control\" type=\"number\" placeholder=\"\">"+
"    </div>"+
"    </div>"+
"    <div class=\"form-group\">"+
"    <div class=\"input-group\">"+
"        <div class=\"input-group-addon\">Documents per Page</div>"+
"        <input id=\"all-docs-num-per-page\" class=\"form-control\" type=\"number\" placeholder=\"\">"+
"    </div>"+
"    </div>"+
"    <div>"+
"        <span>Showing documents <span id=\"all-docs-start-range\"></span> &nbsp;&ndash;&nbsp; <span id=\"all-docs-end-range\"></span> of <span id=\"all-docs-total-docs\">__</span> documents.</span>"+
"    </div>"+
"    </form>"+
"</div>"+
"<div id=\"all-docs-documents-container\">"+
"    <div class=\"row\">"+
"        <div id=\"all-docs-left-nav\" class=\"col-xs-1 text-center\">"+
"           <span id=\"all-docs-beginning\" class=\"pointer all-docs-nav\">" + icons.beginning + "</span>"+
"           <span id=\"all-docs-previous\" class=\"pointer all-docs-nav\">" + icons.previous + "</span>"+
"        </div>"+
"        <div id=\"all-docs-table-container\" class=\"col-xs-10\"></div>"+
"        <div id=\"all-docs-right-nav\" class=\"col-xs-1 text-center\">"+
"           <span id=\"all-docs-next\" class=\"pointer all-docs-nav\">" + icons.next + "</span>"+
"           <span id=\"all-docs-end\" class=\"pointer all-docs-nav\">" + icons.end + "</span>"+
"        </div>"+
"    </div>"+
"</div>",

    events: {
        "click #all-docs-next": "clickNext",
        "click #all-docs-previous": "clickPrevious",
        "click #all-docs-beginning": "clickBeginning",
        "click #all-docs-end": "clickEnd",
        "change #all-docs-page": "changePageNumber",
        "change #all-docs-num-per-page": "changeDocumentsPerPage",
    },
    
    /**
     * Increment the page number.
     */
    clickNext: function(e) {
        this.setPage(this.settingsModel.get("page") + 1);
    },
    
    /**
     * Decrement the page number.
     */
    clickPrevious: function(e) {
        this.setPage(this.settingsModel.get("page") - 1);
    },
    
    /**
     * Set page number to 1.
     */
    clickBeginning: function(e) {
        this.setPage(1);
    },
    
    /**
     * Set the page number to the last possible.
     */
    clickEnd: function(e) {
        this.setPage(this.getLastPage());
    },
    
    /**
     * Jump to the page number.
     */
    changePageNumber: function(e) {
        var page = parseInt(d3.select("#all-docs-page").property("value"));
        if(isInteger(page)) {
            this.setPage(page);
        } else {
            this.updatePageField();
        }
    },
    
    /**
     * Change the documents per page.
     * Update the page number as necessary (keep the first document currently visible, visible on the new page).
     */
    changeDocumentsPerPage: function(e) {
        var perPage = parseInt(d3.select("#all-docs-num-per-page").property("value"));
        if(isInteger(perPage)) {
            this.setDocumentsPerPage(perPage);
        } else {
            this.updateDocumentsPerPageField();
        }
    },
    
    getLastPage: function() {
        return Math.floor(this.documentCount/this.settingsModel.get("docsPerPage") + 1);
    },
    
    /**
     * Gets the document index at the top of the page.
     */
    getDocumentContinue: function() {
        var page = this.settingsModel.get("page");
        var currPerPage = this.settingsModel.get("docsPerPage");
        return (page*currPerPage - currPerPage);
    },
    
    /**
     * Sets the page number, the pageNumber is forced to be in the correct range.
     * pageNumber -- an integer
     */
    setPage: function(pageNumber) {
        var lastPage = this.getLastPage();
        if(pageNumber > lastPage) {
            pageNumber = lastPage;
        }
        if(pageNumber < 1) {
            pageNumber = 1;
        }
        this.settingsModel.set({ page: pageNumber });
        this.updatePageField();
    },
    
    /**
     * Sets the documents per page, the integer is forced to be greater than one
     * and less than or equal to the maximum documents per request.
     */
    setDocumentsPerPage: function(perPage) {
        if(perPage < 1) {
            perPage = 1;
        }
        if(perPage > this.maxDocumentsPerRequest) {
            perPage = this.maxDocumentsPerRequest;
        }
        if(perPage > this.documentCount) {
            perPage = this.documentCount;
        }
        
        var docContinue = this.getDocumentContinue();
        var page = Math.floor((docContinue/perPage) + 1);
        
        this.settingsModel.set({ page: page, docsPerPage: perPage });
        this.updatePageField();
        this.updateDocumentsPerPageField();
    },
    
    /**
     * Updates the page field.
     */
    updatePageField: function() {
        d3.select("#all-docs-page").property("value", this.settingsModel.get("page"));
    },
    
    /**
     * Updates the documents per page field.
     */
    updateDocumentsPerPageField: function() {
        d3.select("#all-docs-num-per-page").property("value", this.settingsModel.get("docsPerPage"));
    },
    
    /**
     * Updates the document index range text.
     */
    updateDocumentsRange: function() {
        var start = this.getDocumentContinue() + 1;
        var end = start + this.settingsModel.get("docsPerPage") - 1;
        if(end > this.documentCount) {
            end = this.documentCount;
        }
        d3.select("#all-docs-start-range").text(start);
        d3.select("#all-docs-end-range").text(end);
    },
    
    /**
     * Updates the table to show the desired documents.
     */
    updateAllDocumentsTable: function() {
        var container = d3.select("#all-docs-table-container").html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selection["dataset"],
                "analyses": selection["analysis"],
                "dataset_attr": "document_count",
                "documents": "*",
                "document_continue": this.getDocumentContinue(),
                "document_limit": this.settingsModel.get("docsPerPage"),
        }, function(data) {
            var documents = extractDocuments(data, this.selectionModel);
            var documentCount = data.datasets[selection["dataset"]].document_count;
            var documentContinue = this.settingsModel.attributes["documentContinue"];
            var displayNDocuments = this.settingsModel.attributes["displayNDocuments"];
            container.html(this.tableTemplate);
            container.select(".col-xs-1")
                .classed("text-center", true);
            var table = container.append("table")
                .classed("table table-hover table-condensed", true);
            
            var header = ["", "Document"];
            var documents = d3.entries(documents).map(function(entry) {
                return [entry.key, entry.key];
            });
            var onClick = function(d, i) {
                this.selectionModel.set({ "document": d[0] });
            }.bind(this);
            createSortableTable(table, {
                header: header, 
                data: documents, 
                onClick: { "1": onClick },
                favicon: [0, "documents", this],
                sortBy: 1,
                sortAscending: true,
            });
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return "<p>Select a document from the list to learn more about it. Use the green arrows to navigate the pages.</p>";
    },
});

/**
 * Renders information about a single document. This view listens to the 
 * selectionModel for a change in the selected document.
 */
var DocumentInfoView = DefaultView.extend({
    readableName: "Single Document Information",
    shortName: "one_doc_info",
    
    htmlTemplate:
"<h3>Document: <span id=\"single-doc-name\"></span></h3>"+
"<div class=\"row\">"+
"    <div id=\"single-doc-left-content\" class=\"col-xs-9\">"+
"    </div>"+
"    <div id=\"single-doc-right-content\" class=\"col-xs-3\">"+
"    </div>"+
"</div>",

    pieChartTemplate:
"<div id=\"single-doc-pie-chart\" class=\"row\">"+
"</div>"+
"<h4 class=\"text-center\">Topics</h4>"+
"<p class=\"text-center\">(sorted by token count)</p>"+
"<div id=\"single-doc-pie-chart-topic-selector\" class=\"row\">"+
"</div>"+
"<p class=\"text-center\"><span>Showing <span id=\"single-doc-showing-n-topics\">__</span> of <span id=\"single-doc-total-topics\">__</span></span></p>"+
"<div id=\"single-doc-pie-chart-legend\" class=\"row\">"+
"</div>",
    
    textTabTemplate:
"<div class=\"row\">"+
"<div class=\"col-xs-12\">"+
"    <div class=\"row\">"+
"        <div class=\"col-xs-12\">"+
"        </div>"+
"    </div>"+
"</div>"+
"</div>",
    
    initialize: function() {
        var defaults = {
            selectedTab: "Text",
            selectedHighlight: "no-highlights",
            topics: "",
            words: "",
            minTopicIndex: 0,
            maxTopicIndex: 0,
            pieChartDuration: 600, // 6/10ths of a second
        };
        this.settingsModel.set(_.extend(defaults, this.settingsModel.attributes));
        this.model = new Backbone.Model();
        this.listenTo(this.selectionModel, "change:document", this.render);
        this.listenTo(this.settingsModel, "change:minTopicIndex", this.changeSelectedTopicsRange);
        this.listenTo(this.settingsModel, "change:maxTopicIndex", this.changeSelectedTopicsRange);
        this.listenTo(this.settingsModel, "change:minTopicIndex", this.requestTopicHighlightData);
        this.listenTo(this.settingsModel, "change:maxTopicIndex", this.requestTopicHighlightData);
        this.listenTo(this.settingsModel, "change:minTopicIndex", this.updateSliderInfo);
        this.listenTo(this.settingsModel, "change:maxTopicIndex", this.updateSliderInfo);
        this.listenTo(this.settingsModel, "change:minTopicIndex", this.updatePieChartAndLegend);
        this.listenTo(this.settingsModel, "change:maxTopicIndex", this.updatePieChartAndLegend);
        
        // Track which topics are selected.
        this.selectedTopics = {};
        var topics = this.settingsModel.get("topics").split(",");
        topics = _.reduce(topics, function(result, item) {
            if(item === "") {
                return result;
            } else {
                result.push(item);
                return result;
            }
        }, []);
        for(var t in topics) {
            this.selectedTopics[t] = false; // Nothing is visible until the pie chart's data is loaded.
        }
    },
    
    /**
     * Remove a topic from a selection.
     */
    removeTopic: function(topicNumber) {
        topicNumber = topicNumber.toString();
        if(topicNumber in this.selectedTopics) {
            delete this.selectedTopics[topicNumber];
        } else {
            return;
        }
        this.updateSelectedTopicsSettings();
    },
    
    /**
     * Add a topic to the selection.
     */
    addTopic: function(topicNumber) {
        topicNumber = topicNumber.toString();
        if(topicNumber in this.selectedTopics) {
            return;
        } else {
            this.selectedTopics[topicNumber] = true;
        }
        this.updateSelectedTopicsSettings();
    },
    
    /**
     * Return true if the topic is selected; false otherwise.
     */
    isTopicSelected: function(topicNumber) {
        return topicNumber.toString() in this.selectedTopics;
    },
    
    /**
     * Returns an object mapping topic numbers to a boolean value.
     * The boolean value is true if the topic number is in the selected range; false otherwise.
     */
    getSelectedTopics: function() {
        return this.selectedTopics;
    },
    
    /**
     * Make sure that the settingsModel stays up-to-date.
     */
    updateSelectedTopicsSettings: function() {
        var s = [];
        for(var t in this.selectedTopics) {
            s.push(t);
        }
        s.sort();
        this.settingsModel.set({ topics: s.join(",") });
    },
    
    /**
     * When the topics range chanes, then the selected topics must be updated.
     */
    changeSelectedTopicsRange: function() {
        var topics = this.getTopicsInSliderRange();
        topics = _.reduce(topics, function(r, t) { r[t.topicNumber.toString()] = true; return r; }, {});
        for(var t in this.selectedTopics) {
            if(t in topics) {
                this.selectedTopics[t] = true;
            } else {
                this.selectedTopics[t] = false;
            }
        }
    },
    
    /**
     * Return a sorted list of topic objects of the form:
     *     { topicNumber: #, tokenCount: # }.
     */
    getTopicsInSliderRange: function() {
        var low = this.settingsModel.get("minTopicIndex");
        var high = this.settingsModel.get("maxTopicIndex");
        return this.sortedTopicTokenCounts.slice(low, high + 1);;
    },
    
    cleanup: function() {
        this.selectionModel.on(null, null, this);
    },
    
    render: function() {
        if(this.selectionModel.get("document") === "") {
            this.$el.html("<p>A document needs to be selected in order to use this view.</p>");
            return;
        }
        
        this.$el.html(this.htmlTemplate);
        
        d3.selectAll("#single-doc-name").text(this.selectionModel.get("document"));
        this.renderTabbedContent();
        this.renderPieChartContent();
    },
    
    documentDoesNotExist: function() {
        // TODO make an error display to the user
        this.selectionModel.set({ "document": "" });
    },
    
    renderPieChartContent: function() {
        var container = d3.select("#single-doc-right-content");
        container.html(this.loadingTemplate);
        this.dataModel.submitQueryByHash({
            "datasets": this.selectionModel.get("dataset"),
            "analyses": this.selectionModel.get("analysis"),
            "documents": this.selectionModel.get("document"),
            "document_attr": ["top_n_topics"],
            
        }, function(data) {
            var documents = extractDocuments(data, this.selectionModel);
            var doc = this.selectionModel.get("document");
            if(!(doc in documents)) {
                this.documentDoesNotExist();
                return;
            }
            
            // Extract the needed data.
            var topicTokenCounts = documents[doc].topics;
            this.sortedTopicTokenCounts = [];
            for(var topicNum in topicTokenCounts) {
                this.sortedTopicTokenCounts.push({
                    topicNumber: topicNum,
                    tokenCount: topicTokenCounts[topicNum],
                });
            }
            
            // Sort descending by topic token counts.
            this.sortedTopicTokenCounts = _.sortBy(this.sortedTopicTokenCounts, function(d) {
                return -d["tokenCount"];
            });
            
            // Create base containers.
            container.html(this.pieChartTemplate);
            
            // Set number of topics
            d3.select("#single-doc-total-topics").text(this.sortedTopicTokenCounts.length);
            
            // Default indices
            var low = 0;
            var high = Math.min(7, this.sortedTopicTokenCounts.length - 1);
            
            // Create the color scale.
            // Space topics far enough apart that they won't be confused.
            var topicNames = [];
            var tempStripeLength = colorPalettes.pastels.length;
            for(var i = 0; i < colorPalettes.pastels.length; i++) {
                for(var j = i; j < this.sortedTopicTokenCounts.length; j += tempStripeLength) {
                    topicNames.push(this.sortedTopicTokenCounts[j].topicNumber.toString());
                }
            }
            this.topicColorScale = colorPalettes.getDiscreteColorScale(topicNames, colorPalettes.pastels);
            
            // Render initial pie chart framework.
            var topPieContainer = d3.select("#single-doc-pie-chart");
            
            var width = topPieContainer[0][0].clientWidth;
            var buffer = 6;
            var pieChartSVG = topPieContainer.append("svg")
                .attr("width", width + buffer)
                .attr("height", width + buffer)
                .classed({ "single-doc-pie-chart": true });
                //~ .attr("id", "test-id");
            
            var x = width/2 + buffer/2;
            var y = x;
            var radius = width/2;
            this.pieChartRadius = radius;
            this.pieGroup = pieChartSVG.append("g")
                .classed("document-pie-chart", true)
                .attr("transform", "translate("+x+","+y+")");
            
            // Create convenience reference for legend.
            this.legendGroup = d3.select("#single-doc-pie-chart-legend");
            
            // Render the slider and set slider events.
            this.$el.find("#single-doc-pie-chart-topic-selector").slider({
                range: true,
                min: 0,
                max: this.sortedTopicTokenCounts.length,
                step: 1,
                values: [low, high],
                slide: function(event, ui) {
                    this.settingsModel.set({
                        minTopicIndex: ui.values[0],
                        maxTopicIndex: ui.values[1],
                    });
                }.bind(this),
                change: function(event, ui) {
                    this.settingsModel.set({
                        minTopicIndex: ui.values[0],
                        maxTopicIndex: ui.values[1],
                    });
                }.bind(this),
            });
            this.settingsModel.set({
                minTopicIndex: low,
                maxTopicIndex: high,
            });
            
            
            
            this.changeSelectedTopicsRange(); // Update which topics are visible.
            this.updateSliderInfo();
            this.updatePieChartAndLegend();
        }.bind(this), this.renderError.bind(this));
    },
    
    /**
     * Change the number of topics shown.
     */
    updateSliderInfo: function() {
        var low = this.settingsModel.get("minTopicIndex");
        var high = this.settingsModel.get("maxTopicIndex");
        d3.select("#single-doc-showing-n-topics").text(high - low + 1);
    },
    
    /**
     * Currently nukes the current display and redraws it.
     */
    updatePieChartAndLegend: function() {
        var data = this.getTopicsInSliderRange();
        var dataTopicNames = [];
        for(var i in data) {
            dataTopicNames.push(data[i].topicNumber.toString());
        }
        var colorScale = colorPalettes.getDiscreteColorScale(dataTopicNames, colorPalettes.pastels);
        
        var outerRadius = this.pieChartRadius;
        var innerRadius = outerRadius * (1/10);
        var bufferRadius = outerRadius * (1/10);
        var allocatedAngleBuffer = (0.03)*2*Math.PI;
        var padAngle = allocatedAngleBuffer*(1/data.length)
        
        var arc = d3.svg.arc()
            .padRadius(outerRadius)
            .innerRadius(innerRadius);
        var pie = d3.layout.pie()
            .padAngle(padAngle)
            .sort(null)
            .value(function(d) { return d.tokenCount; });
        
        var that = this;
        
        // Update the pie chart.
        this.pieGroup.selectAll("path").remove();
        var arcs = this.pieGroup.selectAll("path");
        arcs.data(pie(data.reverse()))
            .enter().append("path")
            .each(function(d) { d.outerRadius = outerRadius - bufferRadius; }) // Modify the outer radius manually to be 1/10th of the full radius.
            .style("stroke", function(d, i) {
                return d3.rgb(that.topicColorScale(d.data.topicNumber.toString())).darker(2);
            })
            .style("stroke-width", "1.5px")
            .style("fill", function(d, i) {
                return that.topicColorScale(d.data.topicNumber.toString());
            })
            .attr("d", arc)
            .classed({
                "single-doc-topic": true,
                //~ "single-doc-topic-pie-slice": true,
                "tg-tooltip": true,
                "pointer": true,
            })
            .attr("data-tg-topic-number", function(d, i) { // Store the topic number on the element for tooltips.
                return d.data.topicNumber;
            })
            .attr("data-placement", "left")
            .attr("data-topic-number", function(d, i) { // Store the topic number on the element.
                return d.data.topicNumber;
            });
        
        
        data.reverse(); // List was reversed for the pie chart, resetting it.
        
        // Update the legend.
        this.legendGroup.selectAll(".single-doc-topic-in-legend").remove();
        var topics = this.legendGroup.selectAll(".single-doc-topic-in-legend");
        var legendEntries = topics.data(data)
            .enter().append("div")
            .classed({ "row": true, "single-doc-topic-in-legend": true })
            .classed("pointer", true);
        legendEntries.append("label").append("input") // Add checkboxes.
            .classed({ "single-doc-topic-legend-checkbox": true })
            .attr("type", "checkbox")
            .attr("data-topic-number", function(d, i) {
                return d.topicNumber;
            })
            .attr("id", function(d, i) { // Label the checkbox for updates.
                return "single-doc-legend-checkbox-topic-"+d.topicNumber;
            })
            .property("checked", function(d, i) {
                return that.isTopicSelected(d.topicNumber);
            });
        legendEntries.append("span") // Add a space between checkbox and color swatch.
            .html("&nbsp;");
        
        legendEntries.append("span") // Add a color swatch.
            .html("&nbsp;")
            .style("display", "inline-block")
            .style("width", "1em")
            .style("background-color", function(d, i) {
                return that.topicColorScale(d.topicNumber);
            })
            .classed("single-doc-topic", true)
            .attr("data-topic-number", function(d, i) { return d.topicNumber; });
        legendEntries.append("span") // Add a space between color swatch and text.
            .html("&nbsp;");
        legendEntries.append("span")
            .text(function(d, i) {
                return that.dataModel.getTopicName(d.topicNumber);
            })
            .attr("id", function(d, i) { // Label the span for hover effects.
                return "single-doc-legend-topic-"+d.topicNumber;
            })
            .classed({ "single-doc-topic": true })
            .attr("data-topic-number", function(d, i) {
                return d.topicNumber;
            });
        
        // Store the "tween" function for mouseover/out events.
        this.mouseoverArcTween = function() {
            d3.select(this).transition().attrTween("d", function(d) {
                var i = d3.interpolate(d.outerRadius, outerRadius);
                return function(t) { d.outerRadius = i(t); return arc(d); }
            });
        };
        this.mouseoutArcTween = function() {
            d3.select(this).transition().attrTween("d", function(d) {
                var i = d3.interpolate(d.outerRadius, outerRadius-bufferRadius);
                return function(t) { d.outerRadius = i(t); return arc(d); }
            });
        };
    },
    
    renderTabbedContent: function() {
        var tabs = {
            "Plain Text": this.renderText.bind(this),
            "Metadata and Metrics": this.renderMetadataAndMetrics.bind(this),
        };
        
        // Set this.settings selected to the selected tab.
        var tabOnClick = function(label) {
            this.settingsModel.set({ selectedTab: label });
        }.bind(this);
        
        var container = d3.select("#single-doc-left-content");
        createTabbedContent(container, { 
            tabs: tabs, 
            selected: this.settingsModel.get("selectedTab"), 
            tabOnClick: tabOnClick, 
        });
    },
    
    renderText: function(title, d3Element) {
        var that = this;
        d3Element.html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selection["dataset"],
                "analyses": selection["analysis"],
                "documents": selection["document"],
                "document_attr": ["text"],
                "topics": "*",
                "topic_attr": "names",
        }, function(data) {
            var documents = extractDocuments(data, this.selectionModel);
            var doc = this.selectionModel.get("document");
            if(!(doc in documents)) {
                this.documentDoesNotExist();
                return;
            }
            
            var text = documents[doc].text;
            var topics = extractTopics(data, this.selectionModel);
            var topicNames = _.reduce(topics, function(result, value, key) { result[key] = value.names.Top3; return result; }, {});
            this.model.set({ text: text, topicNames: topicNames });
            
            // Set up the form.
            var container = d3Element.html("").append("div")
                .classed("container-fluid", true)
                .html(this.textTabTemplate);
            // Set up text div.
            container.append("div")
                .classed("row", true)
                .append("div")
                .classed("col-xs-12", true)
                .attr("id", "highlighted-text")
                .text("");
            
            this.listenTo(this.settingsModel, "change:selectedHighlight", this.highlightChanged);
            this.listenTo(this.settingsModel, "change:words", this.requestWordHighlightData);
            this.listenTo(this.settingsModel, "change:topics", this.requestTopicHighlightData);
            this.highlightChanged();
        }.bind(this), this.renderError.bind(this));
    },
    
    highlightChanged: function() {
        var input = d3.select("#topic-word-input");
        var submit = d3.select("#topic-word-submit-button");
        var selected = this.settingsModel.get("selectedHighlight");
        
        if(selected === "no-highlights") {
            input.attr("disabled", "true").attr("placeholder", "")
                .property("value", "");
            submit.attr("disabled", "true");
            this.highlightText();
        } else if(selected === "topic-highlights") {
            var topics = this.settingsModel.attributes.topics;
            input.attr("disabled", null).attr("placeholder", "Enter topics by number.")
                .property("value", topics.length===0?"":topics.join(" "));
            submit.attr("disabled", null);
            this.requestTopicHighlightData();
        } else if(selected === "word-highlights") {
            var words = this.settingsModel.attributes.words;
            input.attr("disabled", null).attr("placeholder", "Enter words.")
                .property("value", words.length===0?"":words.join(" "));
            submit.attr("disabled", null);
            this.requestWordHighlightData();
        }
    },
    
    requestTopicHighlightData: function() {
        var topics = this.settingsModel.get("topics");
        if(topics.length === 0) {
            this.highlightText();
            return;
        }
        
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "documents": selection["document"],
            "topics": topics,
            "topic_attr": ["word_token_documents_and_locations"],
        }, function(data) {
            var doc = selection.document;
            var topics = extractTopics(data, this.selectionModel);
            var justTopics = {};
            var tokens = [];
            for(var topic in topics) {
                var docTokens = topics[topic].word_token_documents_and_locations;
                if(doc in docTokens) {
                    var docTokens = docTokens[doc];
                    for(var i = 0; i < docTokens.length; i++) {
                        var t = docTokens[i];
                        tokens.push([t[0], t[1], topic]);
                    }
                    justTopics[topic] = true;
                }
            }
            this.highlightText(justTopics, tokens);
        }.bind(this), this.renderError.bind(this));
    },
    
    requestWordHighlightData: function() {
        var words = this.settingsModel.get("words");
        if(words.length === 0) {
            this.highlightText();
            return;
        }
        
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "documents": selection["document"],
            "document_attr": ["word_token_topics_and_locations"],
            "words": words,
        }, function(data) {
            var topicsAndLocations = extractDocuments(data, this.selectionModel)[selection.document].word_token_topics_and_locations;
            var topics = {};
            var tokens = [];
            for(var word in topicsAndLocations) {
                var tempTokens = topicsAndLocations[word];
                for(var i = 0; i < tempTokens.length; i++) {
                    topics[tempTokens[i][0]] = true;
                    var start = tempTokens[i][1];
                    tokens.push([start, start+word.length, tempTokens[i][0]]);
                }
            }
            this.highlightText(topics, tokens);
        }.bind(this), this.renderError.bind(this));
    },
    
    /**
     * Highlight the given
     * topics -- 
     * tokens --
     */
    highlightText: function(topics, tokens) {
        var container = d3.select(this.el).select("#highlighted-text").html("");
        
        if(topics === undefined || tokens === undefined || (_.size(topics) === 0 && tokens.length === 0)) {
            var html = this.model.attributes.text.split("\n");
            html = _.reduce(html, function(result, item) { 
                if(item === "") {
                    return result;
                } else {
                    result.push(item);
                    return result;
                }
            }, []);
            container.append("div").classed("row container-fluid", true).append("h4").text("Document Text");
            container.append("div").classed("row container-fluid", true)
                .html(html.join("<br><br>"));
            return;
        }
        
        // Get and format data and create color scale.
        var text = this.model.attributes.text;
        var topicNames = this.model.attributes.topicNames;
        var topicsArray = _.reduce(topics, function(result, value, key) { result.push(key); return result; }, []);
        topicsArray.sort(function(a, b) { return parseInt(a) - parseInt(b); });
        tokens.sort(function(a, b) { return parseInt(a[0]) - parseInt(b[0]); }); // Put tokens in ascending order.
        var colorScale = this.topicColorScale;
        
        // Convenience function to make sure that text is not drowned out.
        function hexToRGBA(hex, alpha) {
            var r = parseInt(hex.slice(1,3), 16);
            var g = parseInt(hex.slice(3,5), 16);
            var b = parseInt(hex.slice(5,7), 16);
            var a = 0.3;
            return "rgba("+r+","+g+","+b+","+a+")";
        }
        
        // Makes sure that newlines are displayed.
        function detectNewLine(array, inputText) {
            var tmp = inputText.split("\n");
            for(var i = 0; i < tmp.length-1; i++) {
                if(tmp[i] !== "") {
                    array.push(tmp[i]);
                    array.push("");
                }
            }
            if(tmp[tmp.length-1] !== "") {
                array.push(tmp[tmp.length-1]);
            } else {
                array.push("");
            }
        }
        
        // Parse tokens from the beginning of the text.
        var textFragments = [];
        var textFragmentToTopic = {};
        for(var i = 0; i < tokens.length; i++) {
            var token = tokens[i];
            var tokenText = text.slice(token[0], token[1]);
            if(i === 0 && token[0] !== 0) {
                var previousText = text.slice(0, token[0]);
                detectNewLine(textFragments, previousText);
            }
            textFragments.push(tokenText);
            textFragmentToTopic[textFragments.length-1] = token[2];
            if(i === tokens.length-1) {
                var nextText = text.slice(token[1], text.length);
                detectNewLine(textFragments, nextText);
            } else {
                var nextText = text.slice(token[1], tokens[i+1][0]);
                detectNewLine(textFragments, nextText);
            }
        }
        
        var isFragmentToDisplay = function(d, i) {
            if(i.toString() in textFragmentToTopic) {
                return this.getSelectedTopics()[textFragmentToTopic[i.toString()].toString()];
            } else {
                return null;
            }
        }.bind(this);
        
        // Text header.
        container.append("div").classed("row container-fluid", true).append("h4").text("Document Text");
        var content = container.append("div").classed("row container-fluid", true);
        content.selectAll("span")
            .data(textFragments)
            .enter().append("span")
            .style("background-color", function(d, i) {
                if(isFragmentToDisplay(d, i)) {
                    return hexToRGBA(colorScale(textFragmentToTopic[i]));
                } else {
                    return null;
                }
            })
            .classed("highlighted-word", isFragmentToDisplay)
            .classed("single-doc-topic", isFragmentToDisplay)
            .classed("pointer", isFragmentToDisplay)
            .classed("tg-tooltip", isFragmentToDisplay)
            .attr("data-topic-number", function(d, i) {
                if(isFragmentToDisplay(d, i)) {
                    return textFragmentToTopic[i.toString()];
                } else {
                    return null;
                }
            })
            .attr("data-tg-topic-number", function(d, i) {
                if(isFragmentToDisplay(d, i)) {
                    return textFragmentToTopic[i.toString()];
                } else {
                    return null;
                }
            })
            .each(function(d) {
                if(d === "") {
                    d3.select(this).html("<br><br>");
                } else {
                    d3.select(this).text(d);
                }
            });
    },
    
    
    
    renderMetadataAndMetrics: function(title, d3Element) {
        d3Element.html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selection["dataset"],
                "analyses": selection["analysis"],
                "documents": selection["document"],
                "document_attr": ["metadata", "metrics"],
        }, function(data) {
            var documents = extractDocuments(data, this.selectionModel);
            var doc = this.selectionModel.get("document");
            if(!(doc in documents)) {
                this.documentDoesNotExist();
                return;
            }
            var document = documents[doc];
            
            d3Element.html("");
            var container = d3Element.append("div");
            createTableFromHash(container, document.metadata, ["Key", "Value"], "metadata");
            createTableFromHash(container, document.metrics, ["Metric", "Value"], "metrics");
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return "<h4>Text</h4>"+
        "<p>Displays the text of the document as given to the import system. "+
        "Select one of the highlighting methods. "+
        "Topic Highlights will allow you to specify topics in the text field (by their numbers) and Word Highlights takes words. "+
        "The text box takes topics or words separated by spaces, tabs, or commas. "+
        "Click submit once you've entered your selection.</p>"+
        "<h4>Metadata and Metrics</h4>"+
        "<p>The metadata and metrics of the document in key value pairs.</p>";
    },
    
    events: {
        "mouseover .single-doc-topic": "mouseoverHighlightTopics",
        "mouseout .single-doc-topic": "mouseoutHighlightTopics",
        "click .single-doc-topic": "clickTopic",
        "change .single-doc-topic-legend-checkbox": "changeCheckBox",
    },
    
    /**
     * e -- event
     * Return the topic number.
     */
    getTopicNumberFromEvent: function(e) {
        return d3.select(e.target).attr("data-topic-number");
    },
    
    /**
     * Highlight the topic when the user hovers over a topic based element.
     * Relies on the data-topic-number attribute of the event element to work properly.
     */
    mouseoverHighlightTopics: function(e) {
        var that = this;
        var topicNumber = this.getTopicNumberFromEvent(e);
        // Highlight legend topic text.
        d3.select("#single-doc-legend-topic-"+topicNumber)
            .style("background-color", "lightblue");
        // Animate pie slice.
        this.pieGroup.selectAll("path")
            .filter(function(d, i) {
                return d.data.topicNumber === topicNumber;
            })
            .transition(this.settingsModel.get("pieChartDuration"))
            .style("fill", function(d, i) {
                return d3.rgb(that.topicColorScale(d.data.topicNumber)).darker(0.5);
            })
            .each(this.mouseoverArcTween);
        
        // Increase size of word highlights.
        d3.select("#highlighted-text").selectAll(".highlighted-word")
            .filter(function(d, i) {
                var num = d3.select(this).attr("data-topic-number");
                return num.toString() === topicNumber.toString();
            })
            .style("outline-style", "solid")
            .style("outline-color", function(d, i) {
                var num = d3.select(this).attr("data-topic-number");
                return d3.rgb(that.topicColorScale(num)); //.darker(1);
            });
    },
    
    /**
     * Unhighlights the topic when the user stops hovering over a topic based element.
     * Relies on the data-topic-number attribute of the event element to work properly.
     */
    mouseoutHighlightTopics: function(e) {
        var that = this;
        var topicNumber = this.getTopicNumberFromEvent(e);
        // Unhighlight legend topic text.
        d3.select("#single-doc-legend-topic-"+topicNumber)
            .style("background-color", null);
        // Animate pie slice.
        this.pieGroup.selectAll("path")
            .filter(function(d, i) {
                return d.data.topicNumber === topicNumber;
            })
            .transition(this.settingsModel.get("pieChartDuration"))
            .style("fill", function(d, i) {
                return that.topicColorScale(d.data.topicNumber);
            })
            .each(this.mouseoutArcTween);
        
        // Increase size of word highlights.
        d3.select("#highlighted-text").selectAll(".highlighted-word")
            .filter(function(d, i) {
                var num = d3.select(this).attr("data-topic-number");
                return num.toString() === topicNumber.toString();
            })
            .style("outline-style", null)
            .style("outline-color", null);
    },
    
    clickTopic: function(e) {
        this.toggleTopicSelection(this.getTopicNumberFromEvent(e));
    },
    
    changeCheckBox: function(e) {
        this.toggleTopicSelection(this.getTopicNumberFromEvent(e));
    },
    
    toggleTopicSelection: function(topicNumber) {
        var that = this;
        
        // Add/remove the topic from the selection.
        if(this.isTopicSelected(topicNumber)) {
            this.removeTopic(topicNumber);
        } else {
            this.addTopic(topicNumber);
        }
        
        // Check the checkbox.
        this.legendGroup.selectAll(".single-doc-topic-legend-checkbox")
            .filter(function(d) {
                return d.topicNumber.toString() === topicNumber.toString();
            })
            .each(function(d) {
                d3.select(this).property("checked", that.isTopicSelected(d.topicNumber));
            });
    },
});

var SingleDocumentSubView = DefaultView.extend({
    readableName: "View Single Document",
    
    initialize: function() {},
    
    mainTemplate: "<div id=\"single-doc-topmatter\" class=\"col-xs-12\"></div>"+
                  "<div id=\"document-info-container\" class=\"col-xs-12\"></div>",
    
    cleanup: function(topics) {
        if(this.docInfoView !== undefined) {
            this.docInfoView.dispose();
        }
    },
    
    render: function() {
        this.$el.html(this.mainTemplate);
        this.renderTopMatter();
        if(this.docInfoView === undefined) {
            this.docInfoView = new DocumentInfoView(_.extend({ el: $("#document-info-container")}, this.getAllModels()));
        }
        this.docInfoView.render();
    },
    
    renderTopMatter: function() {
        var top = d3.select("#single-doc-topmatter");
        top.append("button")
            .classed("btn btn-default", true)
            .attr("type", "button")
            .html("<span class=\"glyphicon glyphicon-chevron-left pewter\"></span> Back to All Documents")
            .on("click", function() {
                this.selectionModel.set({ "document": "" });
            }.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return this.docInfoView.renderHelpAsHtml();
    },
});

/**
 * Combines the above two views.
 */
var DocumentView = DefaultView.extend({
    
    readableName: "Documents",
    shortName: "documents",
    
    initialize: function() {
        var defaults = { selectedTab: "Text" };
        this.settingsModel.set(_.extend(defaults, this.settingsModel.attributes));
        this.listenTo(this.selectionModel, "change:document", this.render, this);
    },
    
    cleanupViews: function() {
        if(this.subView !== undefined) {
            this.subView.dispose();
        }
    },
    
    cleanup: function() {
        this.cleanupViews();
        this.selectionModel.off(null, this.render, this);
    },
    
    render: function() {
        if(this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<div id=\"info\"></div>");
            this.cleanupViews();
            if(this.selectionModel.nonEmpty(["document"])) {
                this.subView = new SingleDocumentSubView(_.extend({ el: "#info"}, this.getAllModels()));
            } else {
                this.subView = new AllDocumentsSubView(_.extend({ el: "#info"}, this.getAllModels()));
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
});

// Add the Document View to the top level menu
addViewClass([], DocumentView);
