"use strict";

var TopicsOverTimeView = DefaultView.extend({

    mainTemplate:
        "<div id=\"plot-view\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>"+
        "<div id=\"plot-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",

    controlsTemplate:
        "<h3><b>Controls</b></h3>"+
        "<hr />"+
        "<div>"+
        "   <label for=\"topics-control\">Topics</label>"+
        "   <select id=\"topics-control\" type=\"selection\" class=\"form-control\" name=\"Topics\" style=\"height:200px\" multiple></select>"+
        "</div>"+
        "<br />"+
        "<div>"+
        "   <label for=\"metadata-control\">Metadata</label>"+
        "   <select id=\"metadata-control\" type=\"selection\" class=\"form-control\" name=\"Metadata\" style=\"height:30px\"></select>"+
        "</div>"+
        "<br />"+
        "<div>"+
        "   <label for=\"graph-control\">Graph Type</label>"+
        "   <br />"+
        "   <input id=\"graph-control\" type=\"checkbox\" checked data-toggle=\"toggle\" data-on=\"Stacked\" data-off=\"Overlaid\" data-onstyle=\"success\" data-offstyle=\"warning\" data-size=\"small\">"+
        "</div>",

    readableName: "Topics Over Time",
    shortName: "topics_over_time",

    initialize: function() {
        this.selectionModel.on("change:analysis", this.render, this);
        this.model = new Backbone.Model();
        this.settings = new Backbone.Model();
        this.lineChart = null;
    },
    
    cleanup: function() {
        this.selectionModel.off(null, null, this);
    },
    
    getQueryHash: function() {
        var selections = this.selectionModel.attributes;
        return {
            "datasets": selections.dataset,
            "analyses": selections.analysis,
            "topics": "*",
            "topic_attr": "names",
            "documents": "*",
            "document_attr": ["metadata", "metrics", "top_n_topics"],
            "document_continue": 0,
            "document_limit": 1000,
        };
    },
    
    render: function() {
        this.$el.empty();
        
        if(!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<p>You should select a <a href=\"#datasets\">dataset and analysis</a> before proceeding.</p>");
            return;
        }
        
        d3.select(this.el).html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash(this.getQueryHash(), function(data) {
            this.$el.html(this.mainTemplate);
            
            var analysisData = data.datasets[selections['dataset']].analyses[selections['analysis']];
            var processedAnalysis = this.processAnalysis(analysisData);
            this.model.set(processedAnalysis);
            this.model.set({
                // Dimensions of svg viewBox.
                dimensions: {
                    width: 800,
                    height: 800,
                },
                
                // Duration of the transitions.
                duration: 800, // 8/10 of a second
                
                textHeight: 16,

                colorSpectrum: {
                    a: "#B2007D",
                    b: "#19B200"
                },

                graphToggleMap: {
                    "on": "Stacked",
                    "off": "Overlaid",
                    "Stacked": "on",
                    "Overlaid": "off",
                },
            });

            var topics = this.model.get("topics");
            var minMax = this.getMinMaxTopicValues([]);
            this.xInfo = {
                min: 0,
                max: 0,
                type: "int",
                title: "",
                text: [],
                rangeMax: 800,
                noData: {},
            };
            this.yInfo = {
                min: minMax.min,
                max: minMax.max,
                type: "float",
                title: "topic percentage",
                text: [],
                rangeMax: 800,
                noData: {},
            };
            this.meta = "",
            
            this.renderControls();
            this.renderPlot();
            this.model.on("change", this.transition, this);
        }.bind(this), this.renderError.bind(this));
    },

    renderControls: function() {
        var that = this;
        var controls = d3.select(this.el).select("#plot-controls");
        controls.html(this.controlsTemplate);

        // Get selects to be populated
        var topicSelect = this.topicSelect = controls.select("#topics-control");
        var raw_topics = this.model.attributes.raw_topics;
        for (var key in raw_topics) {
            var topic = raw_topics[key];
            topicSelect
                .append("option")
                .attr("value", key)
                .text(this.dataModel.getTopicName(key));
        }

        // Get Metadata options
        var metadataSelect = this.metadataSelect = controls.select("#metadata-control");
        var metadata = this.model.get("metadata_types");
        var defaultMetadata = null;
        for (var index in metadata) {
            var type = metadata[index];
            if (defaultMetadata === null) defaultMetadata = type;
            metadataSelect
                .append("option")
                .attr("value", type)
                .text(toTitleCase(type.replace('_', ' ')));
        }

        var graphTypeToggle = this.graphTypeToggle = $("#plot-controls #graph-control").bootstrapToggle();
        var gtMap = this.model.get("graphToggleMap");

        if (this.settingsModel.has("topicSelection")) {
            var jTopicSelect = $('#topics-control');
            jTopicSelect.val(this.settingsModel.get("topicSelection"));
        }
        if (this.settingsModel.has("metadataSelection")) {
            metadataSelect.property("value", this.settingsModel.get("metadataSelection"));
        }
        if (this.settingsModel.has("graphType")) {
            var checkboxProp = gtMap[this.settingsModel.get("graphType")];
            graphTypeToggle.bootstrapToggle(checkboxProp);
        }

        this.topicChanged =  function topicChange() {
            var selected = $("#plot-controls #topics-control").find(":selected");
            var selected_array = selected.map(function() {
                return this.value;
            })
            .get();
            that.settingsModel.set({ topicSelection: selected_array });
        };

        topicSelect.on("change", this.topicChanged);
        metadataSelect.on("change", function metadataChanged() {
            var value = metadataSelect.property("value");
            that.settingsModel.set({ metadataSelection: value });
        });
        graphTypeToggle.on("change", function graphTypeChanged() {
            var value = gtMap[graphTypeToggle.prop("checked") ? "on" : "off"];
            that.settingsModel.set({ "graphType": value });
        });

        var defaultSettings = {
            topicSelection: [],
            metadataSelection: defaultMetadata,
            graphType: gtMap["on"],
        }

        this.settingsModel.set(_.extend({}, defaultSettings, this.settingsModel.attributes));

    },

    renderPlot: function() {
        var that = this;
        
        // Data variables.
        var documents = this.model.attributes.documents;
        var topics = this.model.attributes.topics;
        var raw_topics = this.model.attributes.raw_topics;
        // Dimensions.
        var dim = this.model.attributes.dimensions;
        var textHeight = this.model.attributes.textHeight;
        var duration = this.model.attributes.duration;
        
        // Create scales and axes.
        var xScale = d3.scale.linear()
            .domain([0, 1])
            .range([0, dim.width]);
        var yScale = d3.scale.linear()
            .domain([0, 1])
            .range([dim.height, 0]);
        var xAxis = d3.svg.axis().scale(xScale).orient("bottom");
        var yAxis = d3.svg.axis().scale(yScale).orient("left");
        
        // Render the scatter plot.
        var view = d3.select(this.el).select("#plot-view").html("");
        
        var svg = this.svg = view.append("svg")
            .attr("width", "100%")
            .attr("height", "90%")
            .attr("viewBox", "0, 0, "+dim.width+", "+dim.height)
            .attr("preserveAspectRatio", "xMidYMin meet")
            .append("g");
        // Hidden group to render the axis before making transitions so everything appears correctly.
        this.xAxisHidden = svg.append("g")
            .attr("id", "x-hidden")
            .attr("transform", "translate(0,"+dim.height+")")
            .style({ "opacity": "0", "fill": "none", "stroke": "white", "shape-rendering": "crispedges" });
        this.yAxisHidden = svg.append("g")
            .attr("id", "y-hidden")
            .attr("transform", "translate(0,0)")
            .style({ "opacity": "0", "fill": "none", "stroke": "white", "shape-rendering": "crispedges" });
        // Render xAxis.
        this.xAxisGroup = svg.append("g")
            .attr("id", "x-axis")
            .attr("transform", "translate(0,"+dim.height+")")
            .style({ "fill": "none", "stroke": "black", "shape-rendering": "crispedges", "stroke-width": "1.5px" });
        this.xAxisText = this.xAxisGroup.append("text");
        this.yAxisGroup = svg.append("g")
            .attr("id", "y-axis")
            .attr("transform", "translate(0,0)")
            .style({ "fill": "none", "stroke": "black", "shape-rendering": "crispedges", "stroke-width": "1.5px" });
        this.yAxisText = this.yAxisGroup.append("text");
        // Render scatter plot container.
        this.plot = svg.append("g")
            .attr("id", "plot");
        this.legend = svg.append("g")
            .attr("class", "legend")
            .attr("transform", "translate(80,30)")
            .style("fill", "white")
            .style("stroke", "black")
            .style("opacity", 0.8)
            .style("font-size", "12px")
            .style("shape-rendering", "crispedges");
        this.tip = null;
        
        // Create listeners.
        this.settingsModel.on("change:topicSelection", this.calculateYAxis, this);
        this.settingsModel.on("change:metadataSelection", this.calculateXAxis, this);
        this.settingsModel.on("change:graphType", this.calculateYAxis, this);
//        this.settingsModel.on("change:xSelection", this.calculateXAxis, this);
//        this.settingsModel.on("change:ySelection", this.calculateYAxis, this);
//        this.settingsModel.on("change:radiusSelection", this.calculateRadiusAxis, this);
//        this.settingsModel.on("change:colorSelection", this.calculateColorAxis, this);
        
        this.calculateAll();
    },
    
    getType: function(value) {
        var type = "text";
        if($.isNumeric(value) && !(value instanceof String)) {
            if(Math.floor(value) === value) {
                type = "int";
            } else {
                type = "float";
            }
        }
        return type;
    },
    
    getNoData: function(value) {
        var data = this.model.attributes.data;
        var noData = {};
        var group = "metadata";
        for(var key in data) {
            var val = data[key][group][value];
            if(val === undefined || val === null) {
                noData[key] = true;
            }
        }
        
        return {
            noData: noData,
        };
    },
    
    calculateAll: function() {
        this.calculateXAxis(false);
        this.calculateYAxis();
//        this.calculateRadiusAxis(false);
//        this.calculateColorAxis();
    },
    
    calculateXAxis: function(transition) {
        var selection = this.settingsModel.get("metadataSelection");
        this.xInfo = _.extend(this.xInfo, this.getNoData(selection.value));
        if(transition !== false) this.transition();
    },

    calculateYAxis: function(transition) {
        var selection = this.settingsModel.get("topicSelection");
        this.yInfo = _.extend(this.yInfo, this.getNoData(selection.value));
        if(transition !== false) this.transition();
    },
    
    getFormat: function(type) {
        if(type === "float") {
            return d3.format(",.2f");
        } else if (type === "int") {
            return d3.format(".0f");
        } else {
            return function(s) { 
                if(s === undefined) return "undefined";
                else return s.slice(0, 20); 
            };
        }
    },
    
    getSelectionInfo: function(value, excluded) {
        var data = this.model.get("documents");
        var group = "metadata";
        var min = Number.MAX_VALUE;
        var max = -Number.MAX_VALUE;
        var avg = 0;
        var total = 0;
        var count = 0;
        var text = {}; // Used if the type is determined to be text.
        var type = false;
        for(var key in data) {
            if(key in excluded) continue;
            var val = data[key][group][value];
            
            if(!type) { // Set the type.
                type = this.getType(val);
                if(type === "text") {
                    min = 0;
                    max = 0;
                } else {
                    min = val;
                    max = val;
                }
            }
            
            if(type !== "text") {
                val = parseFloat(val);
                if(val < min) min = val;
                if(val > max) max = val;
                total += val;
                count++;
            } else {
                text[val] = true;
            }
        }
        
        this.settingsModel.set({ metadataOptions: _.keys(text) });

        if(type === "text") {
            var domain = [];
            for(var k in text) domain.push(k);
            domain.sort();
            domain.push("");
            text = domain;
        }
        
        if(min === Number.MAX_VALUE && max === -Number.MAX_VALUE) {
            min = 0;
            max = 0;
        }
        
        if(count > 0) {
            avg = total/count;
        }
        
        return {
            min: min, 
            max: max+1, 
            avg: avg,
            type: type, 
            text: text, 
            title: toTitleCase(value.replace('_', ' ')),
        };
    },

    getTopicSelectionInfo: function(topicIds, excluded) {
        var minMax = this.getMinMaxTopicValues(topicIds);
        var avg = 0;
        var type = "float";
        var text = {};
        var title = "Topic Proportion";
        
        return {
            min: 0, 
            max: minMax.max, 
            avg: avg,
            type: type, 
            text: text, 
            title: title,
        };
    },
    
    getScale: function(info, range) {
        var scale = d3.scale.linear().domain([info.min, info.max]).range(range);
        scale.type = "LINEAR";
        if(info.type === "text") {
            scale = d3.scale.ordinal().domain(info.text).rangePoints(range);
            scale.type = "ORDINAL";
        }
        return scale;
    },

    getColorScale: function(a, b, count) {
        var interval = 1.0 / (count - 1);
        var interpolator = d3.interpolateHsl(a, b);
        var scale = function(val) {
            if (val * interval > 1.0) return interpolator(1.0);
            return interpolator(val * interval);
        };
        return scale;
    },

    callLegend: function() {
        this.legend.call(d3.legend);
        var that = this;
        var gItems = this.legend.select(".legend-items"),
            items = this.legend.selectAll(".legend-items text"),
            color = "steelblue",
            text = null,
            textBack = null,
            path = null,
            rect = null;

        var gBox = gItems.node().getBBox();
        var x = gBox.x;
        var width = gBox.width;
        items
            .on("mouseover", function(d, i) {
                path = d3.select('path.chart.line[data-legend="'+d.key+'"]');
                rect = d3.selectAll('rect.bar[data-legend="'+d.key+'"]');
                text = d3.select(this);
                var bbox = text.node().getBBox();
                textBack = d3.select(this.parentNode).insert("rect", "text")
                    .attr("x", x)
                    .attr("y", bbox.y)
                    .attr("height", bbox.height)
                    .attr("width", width)
                    .style("fill", "lightgray")
                    .style("stroke", "none");
                if (path && !path.empty()) {
                    color = path.style("stroke");
                    path.style("stroke", "steelblue");
                }
                else if (rect && !rect.empty()) {
                    color = rect.style("fill");
                    rect.style("fill", "steelblue");
                }
                else {
                    path = rect = text = null;
                }

            })
            .on("mouseout", function(d, i) {
                if (textBack) textBack.remove();
                if (path && !path.empty()) {
                    path.style("stroke", color);
                }
                else if (rect && !rect.empty()) {
                    rect.style("fill", color);
                }
                path = rect = text = null;
            })
            .on("click", function(d, i) {
                var textValue = text.text();
                var topicSelect = $("#plot-controls #topics-control");
                var value = topicSelect.find("option").filter(function() {
                    return $(this).html().toLowerCase() === textValue.toLowerCase();
                })
                .val();
                topicSelect.val(value);
                if (textBack) textBack.remove();
                that.topicChanged();
            });
    },
    
    getInfo: function(group, value) {
    },
    
    transition: function() {
        // Collect needed information.
        var model = this.model.attributes;
        var dim = model.dimensions;
        var transitionDuration = model.duration;
        var metadataSelection = this.settingsModel.get("metadataSelection");
        var topicSelection = this.settingsModel.get("topicSelection");
        var xExclude = this.xInfo.noData;
        var yExclude = {};//this.yInfo.noData;
        var allExclude = _.extend({}, xExclude, yExclude);
        var xInfo = _.extend(this.xInfo, this.getSelectionInfo(metadataSelection, allExclude));
        var yInfo = _.extend(this.yInfo, this.getTopicSelectionInfo(topicSelection, allExclude));
        
        var textHeight = model.textHeight;
        
        // Set axes at a starting point.
        var yScale = this.getScale(yInfo, [yInfo.rangeMax, 0]);
        var yFormat = this.getFormat(yInfo.type);
        var yAxis = d3.svg.axis().scale(yScale).orient("left").tickFormat(yFormat);
        this.yAxisHidden.call(yAxis);
        var yAxisDim = this.yAxisHidden[0][0].getBBox();
        
        var xScale = this.getScale(xInfo, [0, xInfo.rangeMax]);
        var xFormat = this.getFormat(xInfo.type);
        var xAxis = d3.svg.axis().scale(xScale).orient("bottom").tickFormat(xFormat);
        this.xAxisHidden.call(xAxis);
        this.xAxisHidden.selectAll("g").selectAll("text")
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", ".15em")
            .attr("transform", "rotate(-65)");
        var xAxisDim = this.xAxisHidden[0][0].getBBox();
        
        // Move the hidden axes.
        var yAxisX = textHeight + yAxisDim.width;
        var yAxisY = textHeight/2;
        var yAxisLength = yInfo.rangeMax = dim.height - textHeight - yAxisY - xAxisDim.height;
        yScale = this.getScale(yInfo, [yInfo.rangeMax, 0]);
        yAxis = d3.svg.axis().scale(yScale).orient("left").tickFormat(yFormat);
        this.yAxisHidden.attr("transform", "translate("+yAxisX+","+yAxisY+")")
            .call(yAxis);
        yAxisDim = this.yAxisHidden[0][0].getBBox();
        var yAxisBar = this.yAxisHidden.select(".domain")[0][0].getBBox();
        
        var xAxisX = yAxisX;
        var xAxisY = yAxisY + yAxisBar.height;
        var xAxisLength = xInfo.rangeMax = dim.width - xAxisX - textHeight/2;
        xScale = this.getScale(xInfo, [0, xInfo.rangeMax]);
        xAxis = d3.svg.axis().scale(xScale).orient("bottom").tickFormat(xFormat);
        this.xAxisHidden.attr("transform", "translate("+xAxisX+","+xAxisY+")")
            .call(xAxis)
            .selectAll("g").selectAll("text")
                .style("text-anchor", "end")
                .attr("dx", "-.8em")
                .attr("dy", ".15em")
                .attr("transform", "rotate(-65)");
        xAxisDim = this.xAxisHidden[0][0].getBBox();
        
        // Transition the visible axes to final spot.
        yAxisX = textHeight + yAxisDim.width;
        yAxisY = textHeight/2;
        yAxisLength = yInfo.rangeMax = dim.height - textHeight - yAxisY - xAxisDim.height;
        yScale = this.getScale(yInfo, [yInfo.rangeMax, 0]);
        yAxis = d3.svg.axis().scale(yScale).orient("left").tickFormat(yFormat);
        this.yAxisGroup.transition()
            .duration(transitionDuration)
            .attr("transform", "translate("+yAxisX+","+yAxisY+")")
            .call(yAxis);
        this.yAxisText.transition()
            .duration(transitionDuration)
            .attr("transform", "rotate(-90)")
            .attr("x", -yAxisLength/2)
            .attr("y", -yAxisDim.width - 4)
            .style("text-anchor", "middle")
            .text(yInfo.title);
        
        xAxisX = yAxisX;
        xAxisY = yAxisY + yAxisBar.height;
        xAxisLength = xInfo.rangeMax = dim.width - xAxisX - textHeight/2;
        xScale = this.getScale(xInfo, [0, xInfo.rangeMax]);
        xAxis = d3.svg.axis().scale(xScale).orient("bottom").tickFormat(xFormat);
        this.xAxisGroup.transition()
            .duration(transitionDuration)
            .attr("transform", "translate("+xAxisX+","+xAxisY+")")
            .call(xAxis)
            .selectAll("g").selectAll("text")
                .style("text-anchor", "end")
                .attr("dx", "-.8em")
                .attr("dy", ".15em")
                .attr("transform", "rotate(-65)");
        this.xAxisText.transition()
            .duration(transitionDuration)
            .attr("x", xAxisLength/2)
            .attr("y", xAxisDim.height)
            .style({ "text-anchor": "middle", "dominant-baseline": "hanging" })
            .text(xInfo.title);
        
        //d3.select(this.svg.selectAll("#x-axis text")[0].pop()).remove();
        // Transition scatter plot.
        this.plot.transition()
            .duration(transitionDuration)
            .attr("transform", "translate("+xAxisX+","+yAxisY+")");

        this.selectTopics();
        this.callLegend();
        
    },
    
    renderHelpAsHtml: function() {
        return "<p>Note that with all the selections (except Color) a document is dropped if that document doesn't have the selected datum.</p>"+
               "<h4>X and Y Axes</h4>"+
               "<p>Select the data to sort the documents according to the data along the specified axis.</p>"+
               "<h4>Radius</h4>"+
               "<p>With text data that smaller the radius the earlier in the alphabet the text occurs.</p>"+
               "<h4>Color</h4>"+
               "<p>With text data the color is chosen from a spectrum of colors. With numeric data the color "+
               "is between blue, off-white, and red. Off-white is average, blue is below average and red is above average. "+
               "Note that documents without the selected data value will be displayed as steelblue.</p>";
    },

    /**
     * Select a number of topics
     *
     * Precondition: Given topic exists in the dataset
     *
     * inputs - Any number of topic ids as arguments
     *          If a single topic is selected, it will move on to the histogram (bar chart)
     */
    selectTopics: function() {

        if (!this.model.get("raw_topics")) {
            return;
        }

        var topicIds = this.settingsModel.get("topicSelection");

        if (topicIds.length > 1 || topicIds.length === 0) {
            this.showLineChart(topicIds);
            return;
        }
        else if (topicIds.length < 0) {
            throw new Error('Something is wrong with your array length...');
        }

        // Otherwise get the only topic id and transition to bar chart
        var topicId = topicIds[0];

        // Select the topic data
        this.settingsModel.set({ selectedTopicData: this.model.get("topics")[topicId] });

        // Transition the line chart into hiding
        if (this.lineChart !== null)
            this.transitionLineChart(null, 1000);

        // Initialize and make the bar chart for the selected topic visible
        this.setBarChart();
    },

    /**
     * Deselect a topic and make the line chart appear
     *
     * Precondition: None
     * Postcondition: The line chart is visible and interactive
     */
    showLineChart: function(topicIds) {

        // Hide the bar chart
        if (this.bars) {
            this.unsetBarChart();
        }

        var topics = this.model.get("topics");
        var minMax = this.getMinMaxTopicValues(topicIds);
        topics.min = minMax.min;
        topics.max = minMax.max;

        // Initialize the line chart
        if (this.lineChart === null) { // Conditional breaks scaling
            this.initLineChart();
        }

        // Transition the line chart into view
        this.transitionLineChart(topicIds, 1000);

    },

    /**
     * Make the axes and bar chart visible, correct, and interactive
     * 
     * Precondition: The selected topic data has been set (call setTopicData)
     * Postcondition: Chart is now interactive
     */
    setBarChart: function() {

        // Initialize bars
        this.initBars();

        // Make the axes transition to the new data domain
    //    this.transitionAxes(1500);

        // Transition the bars into place
        this.transitionBarsUp(1500);
    },

    /**
     * Make the bar chart disappear
     */
    unsetBarChart: function() {

        // Transition the bars into hiding
        this.transitionBarsDown(1500);

        this.bars
            .attr("data-legend", null);
            
        this.bars = null;
    },

    /**
     * Initializes the dimensions, colors, and events of each bar in the bar chart
     *
     * Precondition: Axes are correctly set for the selected topic
     * Postcondition: Bars can be transitioned into place
     */
    initBars: function() {

        var dim = this.model.attributes.dimensions;
        var yInfo = this.yInfo;
        var xScale = this.getScale(this.xInfo, [0, this.xInfo.rangeMax]);
        var yScale = this.getScale(this.yInfo, [this.yInfo.rangeMax, 0]);
        var colors = this.model.get("colorSpectrum");
        var documents = this.model.get("documents");
        var height = dim.height;
        var svg = this.svg;
        var selTopicData = this.settingsModel.get("selectedTopicData");
        var data = selTopicData.data;
        var yearDomain = xScale.domain();
        var yearRange = xScale.range();
        var barWidth = this.getBarWidth(xScale);

        var getOnBarMouseover = this.getOnBarMouseover;
        var getOnBarMouseout = this.getOnBarMouseout;
        var select = this.selectTopics;
        var that = this;

        // Delete existing elements to conserve memory
        this.plot.selectAll(".bar").data([]).exit().remove();

        // Set the data for the bars
        var selectedMetadata = this.settingsModel.get("metadataSelection");
        var data = selTopicData[selectedMetadata].data;
        var indices = selTopicData[selectedMetadata].metaIndices;

        this.bars = this.plot.selectAll(".bar")
            .data(indices);

        // Init d3 tip
        this.tip = d3.tip(this.svg.nearestViewportElement)
            .attr("class", "d3-tip")
            .offset([-73, 0])
            .html(function(d) {
                var datum = data[d.meta][d.index];
                var roundedProb = Math.round((datum.probability*1000).toFixed(2))/10;
                var html = "<strong>Document:</strong> <span style='color:red'>" + datum.doc_id + "</span>"+
                    "<br />"+
                    "<strong>Percent of Topic:</strong> <span style='color:red'>" + roundedProb + "%</span>"+
                    "<br />"+
                    "<strong>" + toTitleCase(selectedMetadata.replace('_', ' ')) + ":</strong> <span style='color:red'>" + d.meta + "</span>";

                return html;
            });
        this.svg.call(this.tip);

        var colorScale = this.getColorScale(colors.a, colors.b, 1);

        // Append SVG elements with class "bar"
        this.bars.enter()
            .append("svg:rect")
            .attr("class", "bar")
            .attr("x", function(d) { return xScale(d.meta); })
            .attr("y", yScale(yInfo.min))
            .attr("width", barWidth)
            .attr("height", 0)
            .style("padding", 10)
            .style("fill", function(d, i) { return colorScale(1); })
            .style("opacity", 0)
            .style("stroke", "white")
            .style("stroke-opacity", 0.3)
            .attr("data-tg-document-name", function(d) {
                return data[d.meta][d.index].doc_id;
            })
            .classed("tg-select", true)
            .on("mouseover", function(d) {
                that.tip.show(d);
                d3.select(this).style("fill", "red");
            })
            .on("mouseout", function(d) {
                that.tip.hide(d);
                d3.select(this).style("fill", colorScale(1));
            });

        this.bars
            .attr("data-legend", selTopicData.name);

        return this.bars;
    },


    getBarWidth: function(scale) {
        var dDomain = null;
        var width = 3;
        var domain = scale.domain();
        var range = scale.range();
        if(scale.type === "ORDINAL") {
            var diff = range[1] - range[0];
            var diffD = diff / 10;
            width = diff - diffD < width ? width : diff - diffD;
        }
        else if(scale.type === "LINEAR") {
            var pWidth = (range[1] - range[0]) / (domain[1] - domain[0]);
            var pWidthD = pWidth / 10;
            width = pWidth - pWidthD < width ? width : pWidth - pWidthD;
        }
        return width;
    },

    /**
     * Initializes the line chart for all topics
     *
     * Precondition: Axes correctly set for the line chart
     * Postcondition: Line chart can be transitioned into place
     */
    initLineChart: function() {
 
        var dim = this.model.attributes.dimensions;
        var xScale = this.getScale(this.xInfo, [0, this.xInfo.rangeMax]);
        var yScale = this.getScale(this.yInfo, [this.yInfo.rangeMax, 0]);
        var raw_topics = this.model.get("raw_topics");
        var topicIds = this.settingsModel.get("topicSelection");
        var topics = this.model.get("topics");
        var height = dim.height;
        var data = null;

        // Function for creating lines - sets x and y value at every point on the line
        var line = d3.svg.line()
            .interpolate("basis")
            .x(function(d, i) { return xScale(d.meta); })
            .y(function(d, i) { return yScale(data[d.meta].totalProbability); }); // Use the total value for this metadata value

        // Delete existing lines to conserve memory (this could be optimized)
        this.svg.selectAll(".chart.line").data([]).exit().remove();

        this.lineChart = {};

        // Append SVG element path for each requested topic
        for (var topicId in raw_topics) {
            var topic = topics[topicId];
            var metaTopic = topic[this.settingsModel.get("metadataSelection")];
            var indices = metaTopic.metaIndices.filter(function(item) { return item.index === 0; }); // Filter indices to only draw one point per year
            indices.topicId = topicId;
            data = metaTopic.data;
            // Create lineChart SVG line element for this topic
            var path = this.plot.append("svg:path")
              .datum(indices)
              .attr("class", "chart line")
              .attr("d", line)
              .style("opacity", 0)
              .style("stroke", "steelblue")
              .style("fill", "none");

           this.lineChart[topicId] = path;
        }
    },

    /**
     * Transitions the axes into the set domains and ranges
     *
     * Precondition: xScale and yScale have been set to the correct domain and range
     * Postcondition: Bars can be initialized and will fit within the axes
     *
     * duration - The duration of the transition in ms (0 is instant)
     */
    transitionAxes: function(duration) {

        var dim = this.model.attributes.dimensions;
        var margin = this.model.attributes.margin;

        var xAxisEl = this.svg.select("#x-axis");
        var xAxis = this.xAxis;
        var xScale = this.xScale;

        var yAxisEl = this.svg.select("#y-axis");
        var yAxis = this.yAxis;
        var yScale = this.yScale;

        var xAxisDim;
        var yAxisDim;

        var endall = function(transition, callback) {
            var n = 0;
            transition
                .each(function() { ++n; })
                .each("end", function() {
                    var axis = d3.select(this);
                    --n;
                    if (n == 1) {
                        axis.call(xAxis);
                        xAxisDim = axis[0][0].getBBox();
                    }
                    else if (n == 0) {
                        axis.call(yAxis);
                        yAxisDim = axis[0][0].getBBox();
                    }
                    if (!n)
                        callback.apply(this, arguments); 
                });
        }

        var halfDur = duration / 2;
        var t = this.svg.transition().duration(halfDur);//.ease("exp-in-out");
        t.selectAll("#x-axis, #y-axis")
            .style("opacity", 0)
            .call(endall, function() {
                xScale
                    .range([
                        margin.left + yAxisDim.width,
                        dim.width - margin.right
                    ]);
                yScale
                    .range([
                        dim.height - margin.bottom - xAxisDim.height,
                        margin.top
                    ]);
                xAxis.scale(xScale);
                yAxis.scale(yScale);
                xAxisEl.call(xAxis);
                yAxisEl.call(yAxis);
            });

        var dim = this.model.attributes.dimensions;
    
        t = t.transition();
        t.select("#x-axis").style("opacity", 1);
        t.select("#y-axis").style("opacity", 1);

    },

    /**
     * Transitions the bars in the chart into place (from height 0 to end height and bottom y to end y)
     *
     * Precondition: Bars have been initialized
     * Precondition: Bars are at the correct x coordinates   
     *
     * bars - D3 entered bar element to transition
     * duration - The duration of the transition in ms (0 is instant)
     */
    transitionBarsUp: function(duration) {

        var dim = this.model.attributes.dimensions;
        var yInfo = this.yInfo;
        var xInfo = this.xInfo;
        var xScale = this.getScale(this.xInfo, [0, this.xInfo.rangeMax]);
        var yScale = this.getScale(this.yInfo, [this.yInfo.rangeMax, 0]);
        var height = dim.height;
        var selectedMetadata = this.settingsModel.get("metadataSelection");
        var data = this.settingsModel.get("selectedTopicData")[selectedMetadata].data;
        var graphType = this.settingsModel.get("graphType");
        var barWidth = this.getBarWidth(xScale);

        // Make opaque and transition y and height into final positions
        var bars = this.svg.selectAll(".bar")
            .transition().duration(duration)
            .style("opacity", 1)
            .attr("x", function(d) { return xScale(d.meta); })
            .attr("y", function(d) {
                var probability = 0;
                if (d.index in data[d.meta])
                    probability = data[d.meta][d.index].probability;
                data[d.meta].forEach(function(value, index, array) { // Get cumulative value (stack 'em up)
                    if (graphType !== "Overlaid") {
                        if (index < d.index) probability += value.probability;
                    }
                });
                return yScale(probability);
            })
            .attr("height", function(d) {
                var probability = 0;
                if (d.index in data[d.meta])
                    probability = data[d.meta][d.index].probability;
                return yScale(yInfo.min) - yScale(probability); 
                })
            .attr("width", function(d) {
                var width = barWidth;
                if (graphType === "Overlaid")
                    width = width - 2*d.index < 2 ? 2 : width - 2*d.index;
                return width;
            })
    },

    /**
     * Transition the bars in the chart into hiding (from end height to height 0 and end y to bottom y)
     *
     * Precondition: Bars have been initialized
     *
     * bars - D3 entered bar element to transition
     * duration - The duration of the transition in ms (0 is instant)
     */
    transitionBarsDown: function(duration) {

        var dim = this.model.attributes.dimensions;
        var height = dim.height;
        var yScale = this.getScale(this.yInfo, [this.yInfo.rangeMax, 0]);
        var yInfo = this.yInfo;

    // Make transparent and transition y and height to 0
    var bars = this.svg.selectAll(".bar")
        .transition().duration(duration)
        .style("opacity", 0)
        .attr("y", yScale(yInfo.min))
        .attr("height", 0);
    },

    /**
     * Transitions the line chart according to the given topic ids
     *
     * topicIds - An array of topic ids. If topic id is given, will transition into place
     *                                    If topic id is not given, will transition into hiding
     *                                    If topicIds is empty, will transition ALL topics into place
     *                                    If topicIds is null, will transition ALL topics into hiding
     * duration - The duration of the transition in ms (0 is instant)
     */
    transitionLineChart: function(topicIds, duration) {

        var raw_topics = _.extend({}, this.model.attributes.raw_topics);

        if (topicIds === null) {
            topicIds = []; // Hide all topics
        }

        // Transition wanted topics into view
        // Start with map of all topics - remove wanted ones and leave unwanted ones
        var delayOrder = 0;
        var lastProbabilities = {};
        for (var topicIdIndex in topicIds) {
            var topicId = topicIds[topicIdIndex];
            if (raw_topics[topicId] === undefined)
                throw new Error('Invalid topic id given');
            else {
                this.transitionLineOut(this.lineChart[topicId], topicId, delayOrder, duration, lastProbabilities);
                delete raw_topics[topicId];
            }
            ++delayOrder;
        }

        // Hide unwanted topics
        // Loop through topics left in topic map because they were not specified in topicIds
        delayOrder = 0;
        for (var topicId in raw_topics) {
          this.transitionLineIn(this.lineChart[topicId], delayOrder, duration);
          ++delayOrder;
        }
    },

    /**
     * Transitions the given svg path element into place
     *
     * path - The path element to transition
     * topicId - The topic id of this path element
     * delayOrder - The order of this path in the current transition (used for delays -- Give 0 for no delay)
     * duration - The duration of the transition in ms (0 is instant)
     */
    transitionLineOut: function(path, topicId, delayOrder, duration, lastProbabilities) {

        // Get data objects
        var xScale = this.getScale(this.xInfo, [0, this.xInfo.rangeMax]);
        var yScale = this.getScale(this.yInfo, [this.yInfo.rangeMax, 0]);
        var topics = this.model.get("topics");
        var topicSelection = this.settingsModel.get("topicSelection");
        var selectedMetadata = this.settingsModel.get("metadataSelection");
        var colors = this.model.get("colorSpectrum");
        var colorScale = this.getColorScale(colors.a, colors.b, topicSelection.length);

        // Register event variables
        var getOnPathMouseover = this.getOnPathMouseover;
        var getOnPathMouseout = this.getOnPathMouseout;
        var select = this.selectTopics;
        var that = this;
        var graphType = this.settingsModel.get("graphType");

        // Function for creating lines - sets x and y value at every point on the line
        var line = d3.svg.line()
            .interpolate("basis")
            .x(function(d, i) { return xScale(d.meta); })
            .y(function(d, i) { var data = topics[topicId][selectedMetadata].data;
                                var probability = data[d.meta].totalProbability;
                                if (graphType === "Stacked" && d.meta in lastProbabilities)
                                    probability += lastProbabilities[d.meta];
                                var y = yScale(probability);
                                //console.log(probability);
                                lastProbabilities[d.meta] = probability;
                                return y;
                              });

        var topic = topics[topicId];
        var metaTopic = topic[this.settingsModel.get("metadataSelection")]
        var indices = metaTopic.metaIndices.filter(function(item) { return item.index === 0; }); // Filter indices to only draw one point per year
        indices.topicId = topicId;
        var data = metaTopic.data;

        path
            .datum(indices)
            .attr("data-legend", function(d) { return topics[topicId].name; })
            .style("stroke", function(d) { return colorScale(delayOrder); })
            .on("click", function(d) {
                select.call(that, [d.topicId]);
            });

        // Make lines opaque
        path.transition().duration(duration)
            .delay(delayOrder * 15)
            .attr("d", line)
            .style("opacity", 1);
    },

    /**
     * Transitions the given svg path into hiding
     *
     * path - The path element to transition
     * delayOrder - The order of this path in the current transition (used for delays -- give 0 for no delay)
     * duration - The duration of the transition in ms (0 is instant)
     */
    transitionLineIn: function(path, delayOrder, duration) {

//    var tooltip = this.tooltip;
    // var length = path.node().getTotalLength();

        path
            .attr("data-legend", null)
            .on("click", null);

    // Make sure tooltip disappears
//    tooltip.transition()
//      .duration(200)
//      .style("opacity", 0.0);

    // Make lines transparent and do magical line folding
        path.transition().duration(duration)
            .delay(delayOrder * 15)
      // .attr("stroke-dashoffset", length) // Fold lines
            .style("opacity", 0.0);
    },

    resize: function(options) { 

//    VisualizationView.prototype.resize.call(this, options);

//    this.scaleRanges();
//    this.selectTopics();
    },

//++++++++++++++++++++++++++++++++++++++++++++++++++    HELPERS    ++++++++++++++++++++++++++++++++++++++++++++++++++\\

    /**
     * Formats the data for all topics
     * 
     * topics and documents - 
     */
    processAnalysis: function(analysisData) {
        var documents = {};
        var topics = {};
        var raw_topics = {};
        var metadataInfo = {};
        if ('topics' in analysisData && 'documents' in analysisData) {
            raw_topics = analysisData.topics;
            documents = analysisData.documents;
            for (var doc in documents) {
                documents[doc].topics = this.normalizeTopicPercentage(documents[doc].topics);
            }
            this.normalizeDocumentPercentage(documents);
            metadataInfo = this.getMetadataInfo(documents);

            for (var topic in analysisData.topics) {
                var processedTopic = this.processTopicData(topic, documents, metadataInfo);
                var topicData = topics[topic] = processedTopic.data
                topics[topic].name = this.dataModel.getTopicName(topic);
            }

        } else {
            console.log('Error with data returned from server');
        }
        topics.min = 0;
        topics.max = 0;
        return {
            documents: documents,
            topics: topics,
            raw_topics: raw_topics,
            metadata_types: _.keys(metadataInfo),
            metadataInfo: metadataInfo,
        }
    },

    getMetadataInfo: function(documents) {
        var metadataInfo = {};
        // loop through documents
        for (var docId in documents) {
            var doc = documents[docId];
            // get document metadata
            if (!("metadata" in doc)) continue;
            var metadata = doc.metadata;
            for (var meta in metadata) {
                // add metadata type to object
                if (!(meta in metadataInfo))
                    metadataInfo[meta] = [];
                var info = metadataInfo[meta];

                // add metadatum to object
                var datum = metadata[meta];
                if (info.indexOf(datum) < 0) info.push(datum);
            }
        }

        for (var meta in metadataInfo) {
            var info = metadataInfo[meta];
            info.sort(function(a, b) {
                var order = d3.ascending(a, b);
                if (!isNaN(a - b))
                    order = a - b;
                return order;
            });
        }
        return metadataInfo;
    },

    /**
     * Formats the data for the selected topic
     * Sorts indices array in ascending order
     *
     * Precondition: Given topic exists in the dataset
     * Precondition: Documents object has been initialized from data
     * Postcondition: The axes and bars can now be initialized and set
     *
     * topicId - The ID of the selected topic
     * documents - The data for all of the analyzed documents
     */
    processTopicData: function(topicId, documents, metadataInfo) {

        var topicData = {};
        var metadata_list = [];

        // Initialize topicData object
        for (var meta in metadataInfo) {
            topicData[meta] = {};
            topicData[meta].metaIndices = [];
            topicData[meta].topicMin = 0;
            topicData[meta].topicMax = 0;
            var data = topicData[meta].data = {};
            for (var index in metadataInfo[meta]) {
                var datum = metadataInfo[meta][index];
                var metadata = [];
                metadata.totalProbability = 0;
                data[datum] = metadata;
            }
        }

        // Get topic percentage in all documents
        for(var doc_id in documents) {
            var doc = documents[doc_id];
            var topicProbability = doc.topics[topicId];
            var documentData = {};
            documentData.doc_id = doc_id;
            
            if (!("metadata" in doc)) continue;

            // Not all topics are defined for each document
            if (topicProbability !== undefined) {

                // Get relevant topic-document info
                documentData.probability = topicProbability;
                for (var meta in doc.metadata) {
                    var topicMeta = topicData[meta];
                    var data = topicData[meta].data;
                    var datum = doc.metadata[meta];

                    var metadata = data[datum];
                    metadata.totalProbability += documentData.probability;
                    metadata.push(documentData);

                    if (topicMeta.topicMin === 0 || topicMeta.topicMin > metadata.totalProbability)
                        topicMeta.topicMin = metadata.totalProbability
                    
                    if (topicMeta.topicMax === 0 || topicMeta.topicMax < metadata.totalProbability)
                        topicMeta.topicMax = metadata.totalProbability;

                }
            }
        }

        for (var meta in topicData) {
            var topicMeta = topicData[meta];
            var data = topicMeta.data;
            var indices = topicMeta.metaIndices;
            var info = metadataInfo[meta];
            var min, max;
            min = max = 0;
//            console.log(data, metadataInfo[meta]);
            for (var index in metadataInfo[meta]) {
                var datum = metadataInfo[meta][index];
                var values = data[datum];
                values.sort(function(a, b) {
                    return d3.descending(a.probability, b.probability);
                });
                for (var index in values) {
                    if (index === "totalProbability") {
                        if (values.length === 0) {
                            index = 0;
                        }
                        else continue;
                    }
                    else {
                        var value = values[index];

                        // Get min and max single index values
                        if (min === 0 || min > value.probability)
                            min = value.probability;
                        if (max === 0 || max < value.probability)
                            max = value.probability;
                    }

                    var metaIndex = { meta : datum,
                                      index: parseInt(index) };
                    indices.push(metaIndex);
                }
            }
            topicMeta.docMin = min;
            topicMeta.docMax = max;
        }

        // Sort metadata values
        for (var meta in topicData) {
            var topicMeta = topicData[meta];
            topicMeta.metaIndices.sort(function(a, b) {
                var order = d3.ascending(a.meta, b.meta);
                if (!isNaN(a.meta - b.meta))
                    order = a.meta - b.meta;
                if (order === 0) {
                    order = d3.ascending(a.index, b.index);
                }
                return order;
            });
        }

        return {
            data: topicData,
        }
    },

    /**
     * Normalizes the topic data in each document to give the percentage in the document rather than the number of tokens in the document
     *
     * rawDocumentTopics - JS object with each topic as a property, keyed by ID with the number of tokens from the topic in the document as the value
     */
    normalizeTopicPercentage: function(rawDocumentTopics) {
        var topics = {};
        _.extend(topics, rawDocumentTopics);
        var keys = _.keys(topics);
        var totalTokens = 0;
        // Get normalizing count
        for (var topic in topics) {
            totalTokens += topics[topic];
        }
        // Normalize topic percentages
        for (var topic in topics) {
            topics[topic] = topics[topic] / totalTokens;
        }
        return topics;
    },

    normalizeDocumentPercentage: function(documents) {
        var metadataToDoc = {};
        var tokenCounts = {};
        for (var doc_id in documents) {
            var doc = documents[doc_id];
            var tokenCount = doc.metrics['Token Count'];
            for (var topic_id in doc.topics) {
                var percentage = doc.topics[topic_id];
                var topicTokenCount = percentage * tokenCount;
                if (!(topic_id in tokenCounts)) tokenCounts[topic_id] = 0;
                tokenCounts[topic_id] += topicTokenCount;
            }
        }
        for (var topic_id in tokenCounts) {
            var round = Math.round(tokenCounts[topic_id]);
            tokenCounts[topic_id] = round;
        }
        for (var doc_id in documents) {
            var doc = documents[doc_id];
            var tokenCount = doc.metrics['Token Count'];
            for (var topic_id in doc.topics) {
                var percentage = doc.topics[topic_id];
                var topicTokenCount = percentage * tokenCount;
                var newPercentage = topicTokenCount / tokenCounts[topic_id];
                doc.topics[topic_id] = newPercentage;
            }
        }
    },

    /**
     * Gets the min and max probabilities for all of the given topics
     * Useful for finding the appropriate range of y values for the line chart
     *
     * topicIds - An ARRAY of topic ids
     */
    getMinMaxTopicValues: function(topicIds) {

        var min = 0;
        var max = 0;
        var topics = this.model.get("topics");
        var selectedMetadata = this.settingsModel.get("metadataSelection");
        var selectedTopicData = this.settingsModel.get("selectedTopicData");
        var graphType = this.settingsModel.get("graphType");

        if (topicIds.length > 1 && graphType === "Stacked") {
            var info = this.model.get("metadataInfo")[selectedMetadata];
            for (var datumIndex in info) {
                var datum = info[datumIndex];
                var datumTotal = 0;
                for (var topicIndex in topicIds) {
                    var topicId = topicIds[topicIndex];
                    var topicData = topics[topicId][selectedMetadata].data;
                    if (!(datum in topicData)) continue;
                    var prob = topicData[datum].totalProbability;
                    datumTotal += prob;
                }
                if (min === 0 || min > datumTotal)
                    min = datumTotal;
                if (max === 0 || max < datumTotal)
                    max = datumTotal;
            }
        }
        else {
            if(selectedMetadata) {
                var minKey = "topicMin";
                var maxKey = "topicMax";
                if (topicIds.length === 0) {
                    topicIds = _.keys(this.model.get("raw_topics"));
                }
                else if (topicIds.length === 1 && graphType === "Overlaid") {
                    minKey = "docMin";
                    maxKey = "docMax";
                }

                for (var index in topicIds) {
                    var topicId = topicIds[index];
                    // Get min and max probability for the given topic
                    if (min === 0 || min > topics[topicId][selectedMetadata][minKey])
                        min = topics[topicId][selectedMetadata][minKey];

                    if (max === 0 || max < topics[topicId][selectedMetadata][maxKey])
                        max = topics[topicId][selectedMetadata][maxKey];
                }
            }
        }

        return { min: min,
                 max: max };
    },

//+++++++++++++++++++++++++++++++++++++++++++++++    EVENT HANDLERS    +++++++++++++++++++++++++++++++++++++++++++++++\\

    getOnBarMouseover: function(context) {

        return function(d) {
            d3.select(this)
                .style("fill", "brown");
        }
    },

    getOnBarMouseout: function(context) {

        return function(d) {
            d3.select(this)
                .style("fill", "steelblue"); 
        }
    },

});

addViewClass(["Visualizations"], TopicsOverTimeView);

