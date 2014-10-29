/*
 * The Topics Over Time View.
 */

//~ /** The Info **/
//~ var TopicsOverTimeInfo = InfoView.extend({
//~ 
  //~ initialize: function () {
    //~ InfoView.prototype.initialize.apply(this, arguments);
//~ 
    //~ var label = this.appendItem('<p>Some stuff here</p>');
  //~ },
//~ 
  //~ clear: function () {
    //~ this.$('tbody').empty();
  //~ },
//~ 
  //~ view_plot: function () {
  //~ },
//~ 
  //~ load_topic: function (tid, info) {
    //~ // show yourself
    //~ this.$el.show();
  //~ },
//~ 
  //~ show: function () {
    //~ InfoView.prototype.show.apply(this, arguments);
  //~ },
//~ 
  //~ hide: function () {
    //~ InfoView.prototype.hide.apply(this, arguments);
  //~ },
//~ 
//~ });
//~ 
//~ 
//~ /** The Controls **/
//~ var TopicsOverTimeControls = ControlsView.extend({
//~ 
  //~ initialize: function (options) {
//~ 
    //~ ControlsView.prototype.initialize.apply(this, arguments);
//~ 
    //~ this.loaded = false;
    //~ _.bindAll(this, "load");
    //~ this.event_aggregator.bind("tot:loaded", this.load);
  //~ },
//~ 
  //~ load: function (topics) {
//~ 
    //~ if (!this.loaded) {
      //~ // Set up the topic selector once the data has been loaded
      //~ var html = '<p>Topics</p><select id="topic-selector" size="' + topics.length + '" multiple>';
      //~ for (var topicId in topics) {
        //~ var topic = topics[topicId];
        //~ html += '<option value="' + topicId + '">' + topic + ' ' + topicId + '</option>';
      //~ }
      //~ html += '</select>';
//~ 
      //~ var topicSelector = this.appendItem(html);
      //~ var event_aggregator = this.event_aggregator;
//~ 
      //~ $('#topic-selector').change(function() {
        //~ var topicIds = [];
        //~ $('#topic-selector option:selected').each(function() {
          //~ topicIds.push($(this).val());
        //~ });
        //~ event_aggregator.trigger("tot:select-topics", topicIds);
      //~ });
//~ 
      //~ this.loaded = true;
    //~ }
  //~ },
//~ 
  //~ show: function () {
    //~ ControlsView.prototype.show.call(this, arguments);
  //~ },
//~ 
  //~ hide: function () {
    //~ ControlsView.prototype.hide.apply(this, arguments);
  //~ }
//~ 
//~ });
//


var TopicsOverTimeView = DefaultView.extend({

    mainTemplate:
        "<div id=\"plot-view\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>"+
        "<div id=\"plot-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",

    controlsTemplate:
        "<h3><b>Controls</b></h3>"+
        "<hr />"+
        "<div>"+
        "    <label for=\"topics-control\">Topics</label>"+
        "    <select id=\"topics-control\" type=\"selection\" class=\"form-control\" name=\"Topics\" style=\"height:200px\" multiple></select>"+
        "</div>"+
        "<br />"+
        "<div>"+
        "    <label for=\"metadata-control\">Metadata</label>"+
        "    <select id=\"metadata-control\" type=\"selection\" class=\"form-control\" name=\"Metadata\" style=\"height:200px\"></select>"+
        "</div>",

    readableName: "Topics Over Time",

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
            "document_limit": 50,
            "document_seed": 0,
        };
    },
    
    render: function() {
        this.$el.empty();
        
        if(!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<p>You should select a <a href=\"#\">dataset and analysis</a> before proceeding.</p>");
            return;
        }
        
        d3.select(this.el).html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash(this.getQueryHash(), function(data) {
            this.$el.html(this.mainTemplate);
            
            var analysisData = data.datasets[selections['dataset']].analyses[selections['analysis']];
            console.log(analysisData);
            var processedAnalysis = this.processAnalysis(analysisData);
            console.log(processedAnalysis);
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
            });
            var range = this.getYearRange(this.model.attributes.documents);
//            this.xScale.domain([ range.min, range.max ]);
            var topics = this.model.attributes.topics;
            var minMax = this.getMinMaxTopicValues([]);
            this.xInfo = {
                min: range.min,
                max: range.max,
                type: "int",
                title: "year",
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
        var topicSelect = this.topicsSelect = controls.select("#topics-control");
        var raw_topics = this.model.attributes.raw_topics;
        for (key in raw_topics) {
            topic = raw_topics[key];
            topicSelect
                .append("option")
                .attr("value", key)
                .text(topic.names.Top3);
        }

        topicSelect.on("change", function selectTopics() {
            var selected = $(this).find(":selected");
            var selected_array = selected.map(function() {
                return this.value;
            })
            .get();

            that.selectTopics(selected_array);
        });

        // Get Metadata options
        var metadataSelect = this.metadataSelect = controls.select("#metadata-control");
        var metadata = this.model.attributes.metadata_types;
        for (index in metadata) {
            var type = metadata[index];
            metadataSelect
                .append("option")
                .attr("value", type)
                .text(type);
        }

        metadataSelect.on("change", function selectMetadata() {
            var selected = $(this).find(":selected");
            var selected_array = selected.map(function() {
                return this.value;
            })
            .get();

            //TODO Add selectionModel and use it for these
        
    },

    renderPlot: function() {
        var that = this;
        
        // Data variables.
        var documents = this.model.attributes.documents;
        var topics = this.model.attributes.topics;
        var selectedTopics = this.model.attributes.selectedTopics;
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
            .style({ "fill": "none", "stroke": "black", "shape-rendering": "crispedges" });
        this.xAxisText = this.xAxisGroup.append("text");
        this.yAxisGroup = svg.append("g")
            .attr("id", "y-axis")
            .attr("transform", "translate(0,0)")
            .style({ "fill": "none", "stroke": "black", "shape-rendering": "crispedges" });
        this.yAxisText = this.yAxisGroup.append("text");
        // Render scatter plot container.
        this.plot = svg.append("g")
            .attr("id", "plot");
        
        // Funcionality for document click.
       /* function onDocumentClick(d, i) {
            if(that.settingsModel.attributes.removing) {
                that.removedDocuments[d.key] = true;
                d3.select(this).transition()
                    .duration(duration)
                    .attr("r", 0);
            } else {
                that.selectionModel.set({ document: d.key });
            }
        };*/
        
        // Create listeners.
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
    
    getNoData: function(group, value) {
        var data = this.model.attributes.data;
        var noData = {};
        for(key in data) {
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
//        var selection = this.settingsModel.attributes.xSelection;
//        this.xInfo = _.extend(this.xInfo, this.getNoData(selection.group, selection.value));
        if(transition !== false) this.transition();
    },
    calculateYAxis: function(transition) {
//        var selection = this.settingsModel.attributes.ySelection;
//        this.yInfo = _.extend(this.yInfo, this.getNoData(selection.group, selection.value));
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
    
    // Find the min, max, type, title, and text for the given selection.
    getSelectionInfo: function(group, value, excluded) {
        var data = this.model.attributes.data;
        var groupNames = this.model.attributes.groupNames;
        var valueNames = this.model.attributes.valueNames;
        var min = Number.MAX_VALUE;
        var max = -Number.MAX_VALUE;
        var avg = 0;
        var total = 0;
        var count = 0;
        var text = {}; // Used if the type is determined to be text.
        var type = false;
        for(key in data) {
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
        
        if(type === "text") {
            var domain = [];
            for(k in text) domain.push(k);
            domain.sort();
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
            max: max, 
            avg: avg,
            type: type, 
            text: text, 
            title: groupNames[group]+": "+valueNames[group][value],
        };
    },
    
    getScale: function(info, range) {
        var scale = d3.scale.linear().domain([info.min, info.max]).range(range);
        if(info.type === "text") {
            scale = d3.scale.ordinal().domain(info.text).rangePoints(range);
        }
        return scale;
    },
    
    getInfo: function(group, value) {
    },
    
    transition: function() {
        // Collect needed information.
        var model = this.model.attributes;
        var dim = model.dimensions;
//        var radii = model.radii;
        var transitionDuration = model.duration;
        var xSel = this.settingsModel.attributes.xSelection;
        var ySel = this.settingsModel.attributes.ySelection;
//        var rSel = this.settingsModel.attributes.radiusSelection;
        var cSel = this.settingsModel.attributes.colorSelection;
        var xExclude = this.xInfo.noData;
        var yExclude = this.yInfo.noData;
//        var radiusExclude = this.radiusInfo.noData;
//        var colorExclude = this.colorInfo.noData;
//        var docExclude = this.removedDocuments;
        var allExclude = _.extend({}, xExclude, yExclude);
        var xInfo = this.xInfo;// = _.extend(this.xInfo, this.getSelectionInfo(xSel.group, xSel.value, allExclude));
        var yInfo = this.yInfo;// = _.extend(this.yInfo, this.getSelectionInfo(ySel.group, ySel.value, allExclude));
//        var radiusInfo = this.radiusInfo = _.extend(this.radiusInfo, this.getSelectionInfo(rSel.group, rSel.value, allExclude));
//        var colorInfo = this.colorInfo = _.extend(this.colorInfo, this.getSelectionInfo(cSel.group, cSel.value, _.extend({}, allExclude, colorExclude)));
        
        var textHeight = model.textHeight;
        
        // Set axes at a starting point.
//        var xScale = this.getScale(xInfo, [0, xInfo.rangeMax]);
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
        
        // Transition scatter plot.
        this.plot.transition()
            .duration(transitionDuration)
            .attr("transform", "translate("+xAxisX+","+yAxisY+")");

        this.selectTopics();
        
        // Transition circles.
        var colorScale = null;
            // All this allows us to map onto a spectrum of colors.
            var colors = ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a", 
                          "#d62728", "#ff9896", "#9467bd", "#c5b0d5", "#8c564b", "#c49c94", 
                          "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7", "#bcbd22", "#dbdb8d", 
                          "#17becf", "#9edae5"];
            var colorDomain = d3.scale.ordinal().domain(colors).rangePoints([0, 1], 0).range();
            var numToColor = d3.scale.linear().domain(colorDomain).range(colors);
            colorScale = function ordinalColorScale(val) { return numToColor(ordToNum(val)); };
        
        var totalDocuments = _.size(model.data);
        var totalDisplayed = totalDocuments - _.size(allExclude);
        //this.nodeCount.text("Showing "+totalDisplayed+" of "+totalDocuments + " Documents");
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

    if (!this.model.attributes.raw_topics) {
        return;
    }

    var topicIds = Array.prototype.slice.call(arguments, 0)[0];
    if (!topicIds) {
        topicIds = [];
    }
    this.model.attributes.selectedTopics = topicIds;

//    if (topicIds.length > this.model.attributes.topics.length) {
//      throw new Error('More topics selected than exist');
//    }
//    else 
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
    this.model.set({
        selectedTopicData: this.model.attributes.topics[topicId],
    });

    // Transition the line chart into hiding
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
    if (this.bars !== null) {
      this.unsetBarChart();
    }

    var topics = this.model.attributes.topics;
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
  },

  /**
   * Scale the axes for the selected topic
   *
   * Precondition: A topic has been selected and the topic data is set
   * Postcondition: The bars can now be initialized
   */
  scaleTopicAxes: function() {

    var dim = this.model.attributes.dimensions;
    var data = this.model.attributes.selectedTopicData.data;
    var maxStack = 0;

    // Calculate x domain
    var keys = $.map(data, function(v, i){
      return i;
    });

    var range = this.getYearRange(this.model.attributes.documents);
    this.xScale.domain([ range.min, range.max ]);

    this.model.attributes.barWidth = dim.width / (range.max - range.min);

    // Calculate y domain
    var yMin = 0;
    var yMax = d3.max(keys, function(d) { 
        var sum = 0;
        // Values for each stacked ordinal are summed (because we are looking at the cumulative value)
        data[d].forEach(function(value, index, array) {
          if (index > maxStack) maxStack = index; // Calculate maximum height of stack for color domain
          sum += value.probability;
        });
        return sum;
      });
    yMax *= 100;
    yMax = Math.ceil(yMax);
    yMax /= 100;
    this.yScale.domain([ yMin, yMax ]);

    // Set color domain
    this.colors.domain(_.range(0, maxStack));//[ 0, maxStack ]);
  },

  /**
   * Scale the axes for all topics
   *nsform
   * Precondition: The topic data is set
   * Postcondition: The lineChart can now be initialized
   */
  scaleLineChartAxes: function() {

    // Set x domain
    var range = this.getYearRange(this.model.attributes.documents);
    this.xScale.domain([ range.min, range.max ]);

    // Set y domain
    this.yScale.domain([ 0, this.model.attributes.topics.max ]);

    // set color domain
    var topicKeys = $.map(this.model.attributes.raw_topics, function(value, key) { return key; }); // Get all topic IDs (they are the keys)
    this.colors.domain(_.range(topicKeys[0], topicKeys[topicKeys.length - 1]));// [ topicKeys[0], topicKeys[topicKeys.length - 1] ]);
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
    var height = dim.height;
//    var bottomMargin = this.margins.bottom;
//    var tooltip = this.tooltip;
    var svg = this.svg;
    var selTopicData = this.model.attributes.selectedTopicData;
    var data = selTopicData.data;
    var colors = this.colors;
    var yearDomain = xScale.domain();
    var yearRange = xScale.range();
    var barWidth = (yearRange[1] - yearRange[0]) / (yearDomain[1] - yearDomain[0]);

    var getOnBarMouseover = this.getOnBarMouseover;
    var getOnBarMouseout = this.getOnBarMouseout;
    var select = this.selectTopics;
    var vis = this;

    // Delete existing elements to conserve memory
    this.plot.selectAll(".bar").data([]).exit().remove();

    console.log(selTopicData);
    // Set the data for the bars
    this.bars = this.plot.selectAll(".bar")
          .data(selTopicData['year'].metaIndices);

    // Append SVG elements with class "bar"
    this.bars.enter()
          .append("svg:rect")
          .attr("class", "bar")
          .attr("x", function(d) { return xScale(d.meta); })
          .attr("y", yScale(yInfo.min))
          .attr("width", barWidth)
          .attr("height", 0)
          .style("padding", 10)
          .style("fill", function(d) { return "steelblue"; })
          .style("opacity", 0)
          .on("mouseover", getOnBarMouseover(vis))
          .on("mouseout", getOnBarMouseout(vis))
          .on("click", function(d) {
              select.call(vis);
            });

    return this.bars;
  },

  /**
   * Initializes the line chart for all topics
   *
   * Precondition: Axes correctly set for the line chart
   * Postcondition: Line chart can be transitioned into place
   */
  initLineChart: function() {
 
    var dim = this.model.attributes.dimensions;
//    var xScale = this.xScale;
//    var yScale = this.yScale;
    var xScale = this.getScale(this.xInfo, [0, this.xInfo.rangeMax]);
    var yScale = this.getScale(this.yInfo, [this.yInfo.rangeMax, 0]);
    var colors = this.colors;
    var raw_topics = this.model.attributes.raw_topics;
    var topics = this.model.attributes.topics;
//    var tooltip = this.tooltip;
    var height = dim.height;
//    var bottomMargin = this.margins.bottom;
//    var leftMargin = this.margins.left;
    var data = null;

    // Function for creating lines - sets x and y value at every point on the line
    console.log("X", xScale.range(), xScale.domain());
    console.log("Y", yScale.range(), yScale.domain());
    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d, i) { return xScale(d.meta); })
        .y(function(d, i) { return yScale(data[d.meta].totalProbability); }); // Use the total value for this year

    // Delete existing lines to conserve memory (this could be optimized)
    this.svg.selectAll(".chart.line").data([]).exit().remove();

    this.lineChart = {};

    // Append SVG element path for each requested topic
    console.log(topics);
    for (var topicId in raw_topics) {
        var topic = topics[topicId];
        var metaTopic = topic['year'] // TODO make this switchable GENERALIZED
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

        // This is to initialize the magical unfolding transition
        // NOTE: disabled because this gets screwed up when the axes scale
        //        The length is not updated when the lines are scaled, so they do not get entirely drawn out
        //        It would be cool to fix, but I don't want to waste too much time on it
        //
        // var length = path.node().getTotalLength();
        // path
        //   .attr("stroke-dasharray", length + " " + length)
        //   .attr("stroke-dashoffset", length);

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
    console.log(xScale.range(), yScale.range());
    console.log(this.svg.selectAll("#x-axis, #y-axis"));
    t.selectAll("#x-axis, #y-axis")
        .style("opacity", 0)
        .call(endall, function() {
            console.log(xAxisDim, yAxisDim);
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
            console.log(xScale.range(), yScale.range());
            xAxisEl.call(xAxis);
            yAxisEl.call(yAxis);
        });
    console.log(xScale.range(), yScale.range());
//    each("end", function(d, i) {
//        var transition = d3.select(this);
//        if (i == 0) {
//            d3.select(this).call(xAxis);
//        }
//        else if (i == 1) {
//            d3.select(this).call(yAxis);
//        }
//        console.log(i, d3.select(this), d3.select(this)[0][0].getBBox());
//        xAxisEl.call(xAxis);
//    });
//    t.select("#x-axis").style("opacity", 0).each("end", function() {
//        xAxisEl.call(xAxis);
//    });
//    t.select("#y-axis").style("opacity", 0).each("end", function() {
//        yAxisEl.call(yAxis);
//    });

    var dim = this.model.attributes.dimensions;
    
    t = t.transition();
    t.select("#x-axis").style("opacity", 1);
    t.select("#y-axis").style("opacity", 1);

    

   // t.select("#x-axis")
     //   .attr("transform", "translate(0," + (dim.height - 24) + ")");

    // Translate x axis in case the whole visualization moves
    //var xAxisEl = $('#x-axis');
    //console.log(xAxisEl);
    //var translate = this.parseTransformAttr(xAxisEl.attr("transform")).translate;
  //  $({ transform : translate[1] }).animate({ transform : dim.height }, // Magical jQuery attribute animation
  //                                          { duration : duration,
   //                                           step : function(now) {
   //                                             xAxisEl.attr("transform", "translate(" + translate[0] + "," + now + ")");
   //                                          }
   //                                        });
    
    //this makes the css inline for saving the svg
//    $('.axis .tick').attr("style", "stroke:#000000; opacity:1");
//    $('.axis text').css("font-size", "this.fontSize");
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
        var xScale = this.getScale(this.xInfo, [0, this.xInfo.rangeMax]);
        var yScale = this.getScale(this.yInfo, [this.yInfo.rangeMax, 0]);
        var height = dim.height;
//        var bottomMargin = this.margins.bottom;
        var data = this.model.attributes.selectedTopicData['year'].data;
        console.log(this.model.attributes.selectedTopicData);

        // Make opaque and transition y and height into final positions
        var bars = this.svg.selectAll(".bar")
            .transition().duration(duration)
            .style("opacity", 1)
            .attr("y", function(d) {
                var probability = data[d.meta][d.index].probability;
                data[d.meta].forEach(function(value, index, array) { // Get cumulative value (stack 'em up)
                    if (index < d.index) {
                    probability += value.probability;
                    }
                });
                return yScale(probability);
                })
            .attr("height", function(d) { return yScale(yInfo.min) - yScale(data[d.meta][d.index].probability); });
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
//    var bottomMargin = this.margins.bottom;

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
//    else if (topicIds.length === 0) { // If we want ALL topics (default)
//      topicIds = $.map(raw_topics, function(value, key) { return key; }); // Copy topic id keys into id array
//    }

    // Transition wanted topics into view
    // Start with map of all topics - remove wanted ones and leave unwanted ones
    var delayOrder = 0;
    for (var topicIdIndex in topicIds) {
      var topicId = topicIds[topicIdIndex];
      if (raw_topics[topicId] === undefined)
        throw new Error('Invalid topic id given');
      else {
        this.transitionLineOut(this.lineChart[topicId], topicId, delayOrder, duration);
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
  transitionLineOut: function(path, topicId, delayOrder, duration) {

    // Get data objects
    var xScale = this.getScale(this.xInfo, [0, this.xInfo.rangeMax]);
    var yScale = this.getScale(this.yInfo, [this.yInfo.rangeMax, 0]);
    var topics = this.model.attributes.topics;
    var colors = this.colors;

    // Register event variables
    var getOnPathMouseover = this.getOnPathMouseover;
    var getOnPathMouseout = this.getOnPathMouseout;
    var select = this.selectTopics;
    var vis = this;

    // Function for creating lines - sets x and y value at every point on the line
    console.log(topics);
    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d, i) { return xScale(d.meta); })
        .y(function(d, i) { var data = topics[topicId]['year'].data;
                            return yScale(data[d.meta].totalProbability);
                          });

    path
        .style("stroke", function(d) { return "steelblue"; })
        .on("mouseover", getOnPathMouseover(vis))
        .on("mouseout", getOnPathMouseout(vis))
        .on("click", function(d) {
          select.call(vis, [d.topicId]);
        });

    // Make lines opaque and do magical line unfolding transition
    // var pathTween = this.pathTween;
    path.transition().duration(duration)
      .delay(delayOrder * 15)
      .attr("d", line)
      // .attrTween("d", pathTween(d1, 4))
      // .attr("stroke-dashoffset", 0) // Unfold lines
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
      .on("mouseover", null)
      .on("mouseout", null)
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

  /**
   * For computing the path between line transitions (for use with the attrTween option on path transitions)
   * This is VERY slow for large amounts of data
   *
   * I stole this from a Mike Bostock example
   * 
   * d1 - SVG path string to transition to
   * precision - How accurate the transition should be (less accurate is faster)
   */
  // pathTween: function(d1, precision) {

  //   return function() {
  //     var path0 = this,
  //         path1 = path0.cloneNode(),
  //         n0 = path0.getTotalLength(),
  //         n1 = (path1.setAttribute("d", d1), path1).getTotalLength();

  //     // Uniform sampling of distance based on specified precision.
  //     var distances = [0], i = 0, dt = precision / Math.max(n0, n1);
  //     while ((i += dt) < 1) distances.push(i);
  //     distances.push(1);

  //     // Compute point-interpolators at each distance.
  //     var points = distances.map(function(t) {
  //       var p0 = path0.getPointAtLength(t * n0),
  //           p1 = path1.getPointAtLength(t * n1);
  //       return d3.interpolate([p0.x, p0.y], [p1.x, p1.y]);
  //     });

  //     return function(t) {
  //       return t < 1 ? "M" + points.map(function(p) { return p(t); }).join("L") : d1;
  //     };
  //   };
  // },

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
        var metadata_types = [];
        if ('topics' in analysisData && 'documents' in analysisData) {
//            for (topic in analysisData.topics) {
//                topics[topic] = toTitleCase(topics[topic].names.Top3);
//            }
//            this.model.set({ topics: topics });
            raw_topics = analysisData.topics;
            documents = analysisData.documents;
            for (doc in documents) {
                documents[doc].topics = this.normalizeTopicPercentage(documents[doc].topics);
            }

            for (topic in analysisData.topics) {
                processedTopic = this.processTopicData(topic, documents);
                topics[topic] = processedTopic.data
                metadata_types = _.union(processedTopic.metadata, metadata_types)
                topics[topic].name = toTitleCase(analysisData.topics[topic].names.Top3);
            }
        }
        topics.min = -1;
        topics.max = -1;
        return {
            documents: documents,
            topics: topics,
            selectedTopics: [],
            raw_topics: raw_topics,
            metadata_types: metadata_types,
        }
    },

  /**
   * Formats the data for the selected topic
   * Sorts year indices array in ascending order
   *
   * Precondition: Given topic exists in the dataset
   * Precondition: Documents object has been initialized from data
   * Postcondition: The axes and bars can now be initialized and set
   *
   * topicId - The ID of the selected topic
   * documents - The data for all of the analyzed documents
   */
  processTopicData: function(topicId, documents) {

    var topicData = {};
    var metadata_list = [];
/*
    topicData.yearIndices = [];
    topicData.min = -1;
    topicData.max = -1;
*/
    // Because I don't want to type that again
/*    var yearIndices = topicData.yearIndices;
    yearIndices.topicId = topicId;
    var data = topicData.data;
*/      
    // Get topic percentage in all documents
    for(var doc_id in documents) {
        var doc = documents[doc_id];
        var topicProbability = doc.topics[topicId];
        var documentData = {};
        documentData.doc_id = doc_id;
        
        // Preserve the document metadata in the top level of the document
        if (!('metadata' in doc)) {
            continue;
        }

        // Not all topics are defined for each document
        if (topicProbability !== undefined) {

            // Get relevant topic-document info
            documentData.probability = topicProbability;
            documentData.doc_id = doc_id;
            var metadata = doc.metadata;
            for (meta in metadata) {
                if (metadata_list.indexOf(meta) <= 0)
                    metadata_list.push(meta);

                if (!(meta in topicData)) { // initialize metadata for this topic
                    topicData[meta] = {};
                    topicData[meta].data = {};
                    topicData[meta].metaIndices = [];
                    topicData[meta].min = -1;
                    topicData[meta].max = -1;
                }

                var data = topicData[meta].data;
                var datum = metadata[meta];

                var metaData = data[datum];
                if (metaData === undefined) {
                    metaData = [];
                    metaData.totalProbability = 0;
                    data[datum] = metaData;
                }

                metaData.totalProbability += documentData.probability;
                metaData.push(documentData);

                if (topicData[meta].min === -1 || topicData[meta].min > metaData.totalProbability)
                    topicData[meta].min = metaData.totalProbability
                
                if (topicData[meta].max === -1 || topicData[meta].max < metaData.totalProbability)
                    topicData[meta].max = metaData.totalProbability;

                var metaIndex = { meta : datum,
                                  index : metaData.length - 1 };

                topicData[meta].metaIndices.push(metaIndex);
            }
/*            var year = doc.metadata.year; //TODO Make this work for any metadata

            // Get all previously found entries for the same year as this document (this is for stacking purposes)
            var yearData = data[year];
            if (yearData === undefined) { // Or initialize if necessary
              yearData = [];
              yearData.totalProbability = 0;
              data[year] = yearData;
            }

            // Add this document to the data for this year
            yearData.totalProbability += documentData.probability;
            yearData.push(documentData);

            // Get min and max probability to help set domain for y axis
            if (topicData.min === -1 || topicData.min > yearData.totalProbability)
              topicData.min = yearData.totalProbability;

            if (topicData.max === -1 || topicData.max < yearData.totalProbability)
              topicData.max = yearData.totalProbability;

            // Add to index so we can stack them in bar chart
            var yearIndex = { year : year,
                              index : yearData.length - 1 };

            yearIndices.push(yearIndex);*/
        }
    }

    // How do we sort metadata values?
    // TODO do something with metadata list
    for (i in metadata_list) {
        var meta = metadata_list[i];
        topicData[meta].metaIndices.sort(function(a, b) {
            var order = d3.ascending(a.meta, b.meta);
            if (order === 0) {
                order = d3.ascending(a.index, b.index);
            }
            return order;
        });
    }
    // Sort topics by year so that line chart gets drawn correctly
    //topicData.yearIndices.sort(function(a, b) { return d3.ascending(a.year, b.year); });

    return {
        data: topicData,
        metadata: metadata_list
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
      for (topic in topics) {
          totalTokens += topics[topic];
      }
      // Normalize topic percentages
      for (topic in topics) {
          topics[topic] = topics[topic] / totalTokens;
      }
      return topics;
  },

  /**
   * Gets the min and max probabilities for all of the given topics
   * Useful for finding the appropriate range of y values for the line chart
   *
   * topicIds - An ARRAY of topic ids
   */
  getMinMaxTopicValues: function(topicIds) {

    var min = -1;
    var max = -1;
    var topicData = this.model.attributes.topics;

    if (topicIds.length === 0) {
      topicIds = $.map(this.model.attributes.raw_topics, function(value, key) { return key; });
    }

    for (var index in topicIds) {
      var topicId = topicIds[index];
      // Get min and max probability for the given topic
      if (min === -1 || min > topicData[topicId]['year'].min) //TODO make this switchable GENERALIZED
        min = topicData[topicId]['year'].min;

      if (max === -1 || max < topicData[topicId]['year'].max)
        max = topicData[topicId]['year'].max;
    }

    return { min: min,
             max: max };
  },

  /**
   * Gets the range of years over all documents
   * 
   * return { min: minimum year, max: maximum year }
   */
  getYearRange: function(documents) {

    var minYear = -1;
    var maxYear = -1;
    for(var doc_id in documents) {
      var docYear = documents[doc_id].metadata.year;
      if (minYear === -1 || docYear < minYear) {
        minYear = docYear;
      }
      if (maxYear === -1 || docYear > maxYear) {
        maxYear = docYear;
      }
    }

    return { min: minYear, max: maxYear };
  },

    /**
     * Hashes the html transform attribute
     * i.e. parseTransformAttr('translate(6,5),scale(3,3.5),a(1,1),b(2,23,-34),c(300)')
     *      RETURNS
     *      {
     *          translate: [ '6', '5' ],
     *          scale: [ '3', '3.5' ],
     *          a: [ '1', '1' ],
     *          b: [ '2', '23', '-34' ],
     *          c: [ '300' ]
     *      }
     */
    parseTransformAttr: function(attributes) {
        var b={};
        for (var i in attributes = attributes.match(/(\w+\((\-?\d+\.?\d*,?)+\))+/g)) // for all valid attributes (including negative and decimal)
        {
            var c = attributes[i].match(/[\w\.\-]+/g); // Split transform name and values into array
            b[c.shift()] = c; // First item is name, equal to array of values left
        }
        return b;
    },

//+++++++++++++++++++++++++++++++++++++++++++++++    EVENT HANDLERS    +++++++++++++++++++++++++++++++++++++++++++++++\\

  getOnBarMouseover: function(context) {

    return function(d) {
//      var tooltip = context.tooltip;
//      var data = context.model.attributes.selectedTopicData.data;

//      tooltip.transition()
//        .duration(200)
//        .style("opacity", 0.9);
//      tooltip.html(data[d.year][d.index].title + " " + d.year)
//        .style("left", (d3.event.pageX + 8) + "px")
//        .style("top", (d3.event.pageY) + "px");
      d3.select(this)
        .style("fill", "brown");
    }
  },

  getOnBarMouseout: function(context) {

    return function(d) {
//      var tooltip = context.tooltip;
      var colors = context.colors;

//      tooltip.transition()
//        .duration(200)
//        .style("opacity", 0.0); 
      d3.select(this)
        .style("fill", "steelblue"); 
    }
  },

  getOnPathMouseover: function(context) {

    return function(d) {
//      var tooltip = context.tooltip;
//      var topics = context.topics;

//      tooltip.transition()
//        .duration(200)
//        .style("opacity", 0.9)
//      tooltip.html(d.topicId + " " + topics[d.topicId])
//        .style("left", (d3.event.pageX + 8) + "px")
//        .style("top", (d3.event.pageY) + "px");
      d3.select(this)
        .style("stroke", "brown"); 
    }
  },

  getOnPathMouseout: function(context) {

    return function(d) {
//      var tooltip = context.tooltip;
      var colors = context.colors;

//      tooltip.transition()
//        .duration(200)
//        .style("opacity", 0.0); 
      d3.select(this)
        .style("stroke", "steelblue");
    }
  },

});

globalViewModel.addViewClass(["Visualizations"], TopicsOverTimeView);

