"use strict";

/**
 * Renders information about a single document. This view listens to the 
 * selectionModel for a change in the selected document.
 */
var SingleDocumentView = DefaultView.extend({
    readableName: "Document Information",
    shortName: "single_document",
    
    redirectTemplate:
'<div class="text-center">'+
'   <button class="single-doc-redirect btn btn-default">'+
'       <span class="glyphicon glyphicon-chevron-left pewter"></span> All Documents'+
'   </button>'+
'   <span> You need to select a document to see any information. </span>'+
'</div>',
    
    baseTemplate:
'<h3>Document: <span class="single-doc-name"></span><span class="single-doc-fav"></span></h3>'+
'<div class="row">'+
'    <div class="single-doc-left-content col-xs-9">'+
'    </div>'+
'    <div class="single-doc-right-content col-xs-3">'+
'    </div>'+
'</div>',

    pieChartTemplate:
'<div class="single-doc-pie-chart row">'+
'</div>'+
'<h4 class="text-center">Topics</h4>'+
'<p class="text-center">(sorted by token count)</p>'+
'<div class="single-doc-pie-chart-topic-selector row">'+
'</div>'+
'<p class="text-center"><span>Showing <span class="single-doc-showing-n-topics">__</span> of <span class="single-doc-total-topics">__</span></span></p>'+
'<div class="single-doc-pie-chart-legend row">'+
'</div>',
    
    initialize: function initialize() {
        var defaults = {
            selectedTab: "Text",
            selectedTopics: "",
            minTopicIndex: 0,
            maxTopicIndex: 0,
        };
        this.settingsModel.set(_.extend(defaults, this.settingsModel.attributes));
        
        this.model = new Backbone.Model({
            selectedTopics: {}, // Key tracks the selected topics, value tracks whether to show the topic highlights. 
            topicTokens: {}, // Track what topic data has been loaded from the server.
            text: "", // Store the raw document text.
            topicTokenCounts: [],
        });
        
        this.listenTo(this.selectionModel, "change:document", this.render);
        this.listenTo(this.settingsModel, "change:minTopicIndex", this.changeSelectedTopicsRange);
        this.listenTo(this.settingsModel, "change:maxTopicIndex", this.changeSelectedTopicsRange);
        this.listenTo(this.settingsModel, "change:minTopicIndex", this.updateSliderInfo);
        this.listenTo(this.settingsModel, "change:maxTopicIndex", this.updateSliderInfo);
        
        
        // Track which topics are selected.
        var selectedTopics = this.model.get("selectedTopics"); // Empty object.
        var topics = this.settingsModel.get("selectedTopics").split(",");
        _.reduce(topics, function(result, t) {
            if(t === "") {
                return result;
            } else {
                result[t] = false; // Nothing is visible until the pie chart's data is loaded.
                return result;
            }
        }, selectedTopics);
    },
    
    cleanup: function cleanup() {},
    
    renderHelpAsHtml: function renderHelpAsHtml() {
        return "<h4>Text</h4>"+
        "<p>Displays the text of the document as given to the import system. "+
        "Select one of the highlighting methods. "+
        "Topic Highlights will allow you to specify topics in the text field (by their numbers) and Word Highlights takes words. "+
        "The text box takes topics or words separated by spaces, tabs, or commas. "+
        "Click submit once you've entered your selection.</p>"+
        "<h4>Metadata and Metrics</h4>"+
        "<p>The metadata and metrics of the document in key value pairs.</p>";
    },
    
    render: function render() {
        var that = this;
        
        if(this.selectionModel.get("document") === "") {
            this.$el.html(this.redirectTemplate);
            return;
        }
        
        this.$el.html(this.baseTemplate);
        
        // Set the document name and the favs icon.
        var docName = this.selectionModel.get("document");
        var docNameEl = this.$el.find(".single-doc-name");
        var docNameFavEl = this.$el.find(".single-doc-fav");
        docNameEl.text(docName+" ");
        docNameFavEl.attr("data-tg-document-name", docName);
        docNameFavEl.addClass("tg-fav");
        tg.site.initFav(docNameFavEl.get(0), this.favsModel);
        
        this.renderTabbedContent();
        this.renderPieChartContent();
    },
    
    renderTabbedContent: function renderTabbedContent() {
        var tabs = {
            "Text": this.renderText.bind(this),
            "Metadata and Metrics": this.renderMetadataAndMetrics.bind(this),
        };
        
        var selectedTab = this.settingsModel.get("selectedTab");
        
        // Set this.settings selected to the selected tab.
        var tabOnClick = function tabOnClick(label) {
            this.settingsModel.set({ selectedTab: label });
        }.bind(this);
        
        var container = d3.select(this.el).select(".single-doc-left-content");
        
        tg.gen.createTabbedContent(container[0][0], { 
            tabs: tabs, 
            selected: selectedTab, 
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
        }, function(data) {
            var documents = extractDocuments(data, this.selectionModel);
            var documentName = this.selectionModel.get("document");
            if(!(documentName in documents)) {
                this.documentDoesNotExist();
                return;
            }
            
            var text = documents[documentName].text;
            this.model.set({ text: text });
            
            // Set up the form.
            var container = d3Element.html("").append("div")
                .classed("container-fluid", true)
                .append("div")
                .classed("row", true)
                .classed("single-doc-text-container container-fluid", true);
            
            this.listenTo(this.settingsModel, "change:minTopicIndex", this.changeSelectedTopicsInSettings);
            this.listenTo(this.settingsModel, "change:maxTopicIndex", this.changeSelectedTopicsInSettings);
            this.listenTo(this.settingsModel, "change:selectedTopics", this.changeSelectedTopicsInSettings);
            this.changeSelectedTopicsInSettings();
        }.bind(this), this.renderError.bind(this));
    },
    
    /**
     * Update the text and highlights.
     */
    updateText: function updateText() {
        var container = d3.select(this.el).select(".single-doc-text-container").html("");
        
        var selectedTopics = this.getSelectedTopics();
        var topicTokenData = this.getTopicTokenData();
        
        // Get and format data and create color scale.
        var text = this.model.get("text");
        var tokens = _.reduce(topicTokenData, function(result, value, key) {
            if(key in selectedTopics && selectedTopics[key]) {
                for(var i in value) {
                    var tok = value[i];
                    result.push([tok[0], tok[1], key]);
                }
            }
            return result;
        }, []);
        
        
        // Short circuit things if there are no tokens to highlight.
        if(tokens.length === 0) { // Make sure the text is displayed even if there are no highlights.
            container.html(text.replace(/\r?\n/g, '<br />'));
        }
        
        tokens.sort(function(a, b) { return parseInt(a[0]) - parseInt(b[0]); }); // Put tokens in ascending order.
        var colorScale = this.topicColorScale;
        
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
        var content = container.append("div").classed("row container-fluid", true);
        content.selectAll("span")
            .data(textFragments)
            .enter().append("span")
            .style("background-color", function(d, i) {
                if(isFragmentToDisplay(d, i)) {
                    return tg.color.hexToRGBA(colorScale(textFragmentToTopic[i]));
                } else {
                    return null;
                }
            })
            .classed("highlighted-word", isFragmentToDisplay)
            .classed("single-doc-topic", isFragmentToDisplay)
            .classed("pointer", isFragmentToDisplay)
            .classed("tg-tooltip", isFragmentToDisplay)
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
    
    /**
     * Request the topic-token data and call updateText as needed.
     */
    changeSelectedTopicsInSettings: function changeSelectedTopicsInSettings() {
        var topics = this.getSelectedTopics();
        var topicTokenData = this.getTopicTokenData();
        
        for(var topic in topics) {
            if(!(topic in topicTokenData)) {
                var datasetName = this.selectionModel.get("dataset");
                var analysisName = this.selectionModel.get("analysis");
                var documentName = this.selectionModel.get("document");
                this.dataModel.submitQueryByHash({
                    "datasets": datasetName,
                    "analyses": analysisName,
                    "documents": documentName,
                    "topics": topic,
                    "topic_attr": ["word_token_documents_and_locations"],
                }, function(data) {
                    var topicData = data.datasets[datasetName].analyses[analysisName].topics;
                    for(var t in topicData) {
                        var docTokens = topicData[t].word_token_documents_and_locations[documentName];
                        topicTokenData[t] = docTokens;
                    }
                    this.updateText();
                }.bind(this), this.renderError.bind(this));
            }
        }
        
        this.updateText(); // Always update in case topics were deselected.
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
    
    /**
     * Remove a topic from a selection.
     */
    removeTopic: function(topicNumber) {
        topicNumber = topicNumber.toString();
        var selectedTopics = this.getSelectedTopics();
        if(topicNumber in selectedTopics) {
            delete selectedTopics[topicNumber];
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
        var selectedTopics = this.getSelectedTopics();
        if(topicNumber in selectedTopics) {
            return;
        } else {
            selectedTopics[topicNumber] = true;
        }
        this.updateSelectedTopicsSettings();
    },
    
    /**
     * Return true if the topic is selected; false otherwise.
     */
    isTopicSelected: function(topicNumber) {
        return topicNumber.toString() in this.model.get("selectedTopics");
    },
    
    /**
     * Returns an object mapping topic numbers to a boolean value.
     * The boolean value is true if the topic number is in the selected range; false otherwise.
     */
    getSelectedTopics: function() {
        return this.model.get("selectedTopics");
    },
    
    getTopicTokenData: function getTopicTokenData() {
        return this.model.get("topicTokens");
    },
    
    /**
     * Make sure that the settingsModel stays up-to-date.
     */
    updateSelectedTopicsSettings: function() {
        var s = [];
        var selectedTopics = this.getSelectedTopics();
        for(var t in selectedTopics) {
            s.push(t);
        }
        s.sort();
        this.settingsModel.set({ selectedTopics: s.join(",") });
    },
    
    /**
     * When the topics range changes, then the selected topics must be updated.
     */
    changeSelectedTopicsRange: function() {
        var topics = this.getTopicsInSliderRange();
        topics = _.reduce(topics, function(r, t) { r[t.topicNumber.toString()] = true; return r; }, {});
        var selectedTopics = this.getSelectedTopics();
        for(var t in selectedTopics) {
            if(t in topics) {
                selectedTopics[t] = true;
            } else {
                selectedTopics[t] = false;
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
        return this.getSortedTopicTokenCounts().slice(low, high + 1);;
    },
    
    getSortedTopicTokenCounts: function getSortedTopicTokenCounts() {
        return this.model.get("topicTokenCounts");
    },
    
    documentDoesNotExist: function() {
        this.renderError('The document "' + this.selectionModel.get("document") + '" was not found.');
        this.selectionModel.set({ "document": "" });
    },
    
    renderPieChartContent: function() {
        var container = d3.select(this.el).select(".single-doc-right-content");
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
            var sortedTopicTokenCounts = [];
            for(var topicNum in topicTokenCounts) {
                sortedTopicTokenCounts.push({
                    topicNumber: topicNum,
                    tokenCount: topicTokenCounts[topicNum],
                });
            }
            
            // Sort descending by topic token counts.
            sortedTopicTokenCounts = _.sortBy(sortedTopicTokenCounts, function(d) {
                return -d["tokenCount"];
            });
            
            this.model.set("topicTokenCounts", sortedTopicTokenCounts);
            
            // Create base containers.
            container.html(this.pieChartTemplate);
            
            // Set number of topics
            d3.select(this.el).select(".single-doc-total-topics").text(sortedTopicTokenCounts.length);
            
            // Default indices
            var low = 0;
            var high = Math.min(7, sortedTopicTokenCounts.length - 1);
            
            // Create the color scale.
            // Space topics far enough apart that they won't be confused.
            var topicNames = [];
            var tempStripeLength = colorPalettes.pastels.length;
            for(var i = 0; i < colorPalettes.pastels.length; i++) {
                for(var j = i; j < sortedTopicTokenCounts.length; j += tempStripeLength) {
                    topicNames.push(sortedTopicTokenCounts[j].topicNumber.toString());
                }
            }
            this.topicColorScale = colorPalettes.getDiscreteColorScale(topicNames, colorPalettes.pastels);
            
            // Render initial pie chart framework.
            var topPieContainer = d3.select(this.el).select(".single-doc-pie-chart");
            
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
            this.legendGroup = d3.select(this.el).select(".single-doc-pie-chart-legend");
            
            // Render the slider and set slider events.
            this.$el.find(".single-doc-pie-chart-topic-selector").slider({
                range: true,
                min: 1,
                max: sortedTopicTokenCounts.length,
                step: 1,
                values: [low+1, high+1],
                slide: function(event, ui) {
                    this.settingsModel.set({
                        minTopicIndex: ui.values[0]-1,
                        maxTopicIndex: ui.values[1]-1,
                    });
                }.bind(this),
                change: function(event, ui) {
                    this.settingsModel.set({
                        minTopicIndex: ui.values[0]-1,
                        maxTopicIndex: ui.values[1]-1,
                    });
                }.bind(this),
            });
            this.settingsModel.set({
                minTopicIndex: low,
                maxTopicIndex: high,
            });
            
            this.listenTo(this.settingsModel, "change:minTopicIndex", this.changeSelectedTopicsRange);
            this.listenTo(this.settingsModel, "change:maxTopicIndex", this.changeSelectedTopicsRange);
            this.listenTo(this.settingsModel, "change:minTopicIndex", this.updateSliderInfo);
            this.listenTo(this.settingsModel, "change:maxTopicIndex", this.updateSliderInfo);
            this.listenTo(this.settingsModel, "change:minTopicIndex", this.updatePieChartAndLegend);
            this.listenTo(this.settingsModel, "change:maxTopicIndex", this.updatePieChartAndLegend);
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
        d3.select(this.el).select(".single-doc-showing-n-topics").text(high - low + 1);
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
                "single-doc-topic-toggle": true,
                "tg-tooltip": true,
                "pointer": true,
            })
            .attr("data-tg-topic-number", function(d, i) { // Store the topic number on the element for tooltips.
                return d.data.topicNumber;
            })
            .attr("data-placement", "left")
            .attr("data-tg-topic-number", function(d, i) { // Store the topic number on the element.
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
            .attr("data-tg-topic-number", function(d, i) {
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
            .classed("single-doc-topic single-doc-topic-toggle", true)
            .attr("data-tg-topic-number", function(d, i) { return d.topicNumber; });
        legendEntries.append("span") // Add a space between color swatch and text.
            .html("&nbsp;");
        legendEntries.append("span")
            .text(function(d, i) {
                return that.dataModel.getTopicName(d.topicNumber);
            })
            .attr("id", function(d, i) { // Label the span for hover effects.
                return "single-doc-legend-topic-"+d.topicNumber;
            })
            .classed({ "single-doc-topic single-doc-topic-toggle tg-topic-name-auto-update": true })
            .attr("data-tg-topic-number", function(d, i) {
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
    
    events: {
        "click .single-doc-redirect": "clickRedirect",
        "mouseover .single-doc-topic": "mouseoverHighlightTopics",
        "mouseout .single-doc-topic": "mouseoutHighlightTopics",
        "click .single-doc-topic-toggle": "clickTopic",
        "change .single-doc-topic-legend-checkbox": "changeCheckBox",
    },
    
    /**
     * Redirect to all documents view.
     */
    clickRedirect: function clickRedirect(e) {
        this.viewModel.set({ currentView: "all_documents" });
    },
    
    /**
     * e -- event
     * Return the topic number.
     */
    getTopicNumberFromEvent: function(e) {
        return d3.select(e.target).attr("data-tg-topic-number");
    },
    
    /**
     * Highlight the topic when the user hovers over a topic based element.
     * Relies on the data-tg-topic-number attribute of the event element to work properly.
     */
    mouseoverHighlightTopics: function(e) {
        var that = this;
        var topicNumber = this.getTopicNumberFromEvent(e);
        // Highlight legend topic text.
        d3.select(this.el).select(".single-doc-legend-topic-"+topicNumber)
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
        d3.select(this.el).select(".highlighted-text").selectAll(".highlighted-word")
            .filter(function(d, i) {
                var num = d3.select(this).attr("data-tg-topic-number");
                return num.toString() === topicNumber.toString();
            })
            .style("outline-style", "solid")
            .style("outline-color", function(d, i) {
                var num = d3.select(this).attr("data-tg-topic-number");
                return d3.rgb(that.topicColorScale(num));
            });
    },
    
    /**
     * Unhighlights the topic when the user stops hovering over a topic based element.
     * Relies on the data-tg-topic-number attribute of the event element to work properly.
     */
    mouseoutHighlightTopics: function(e) {
        var that = this;
        var topicNumber = this.getTopicNumberFromEvent(e);
        // Unhighlight legend topic text.
        d3.select(this.el).select(".single-doc-legend-topic-"+topicNumber)
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
        d3.select(this.el).select(".highlighted-text").selectAll(".highlighted-word")
            .filter(function(d, i) {
                var num = d3.select(this).attr("data-tg-topic-number");
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

// Add the Document View to the top level menu
addViewClass(["Document"], SingleDocumentView);
