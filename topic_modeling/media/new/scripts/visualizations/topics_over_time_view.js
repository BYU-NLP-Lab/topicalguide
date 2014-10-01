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

    readableName: "Topics Over Time",

    initialize: function() {
        this.selectionModel.on("change:analysis", this.render, this);
        this.model = new Backbone.Model();
        this.settings = new Backbone.Model();
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
    
    /** setup the d3 layout, etc. Everything you can do without data **/
    render: function () {
        this.$el.empty();

        if(!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<p>You should select a <a href=\"#\">dataset and analysis</a> before proceeding.</p>");
            return;
        }
        
        d3.select(this.el).html(this.loadingTemplate);
        console.log(this.selectionModel);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash(this.getQueryHash(), function(data) {
            this.$el.html(this.mainTemplate);
            
            var analysisData = data.datasets[selections['dataset']].analyses[selections['analysis']];
            var processedAnalysis = this.processAnalysis(analysisData);
            console.log(processedAnalysis);
            this.model.set(processedAnalysis);

            this.renderPlot();
        }.bind(this), this.renderError.bind(this));

        
//        this.svg = this.$el.find("#tot-svg");
//        this.maing = d3.select(this.el).select("#tot-svg").append("g");
//        this.setUpProperties();
//        this.setUpAxes();    
//        this.tooltip = d3.select("body").append("div")
//                                        .attr("class", "tooltip")
//                                        .style("opacity", 0)
//                                       .style("height", "38px");
    },

    renderPlot: function() {
        var that = this;

        this.setUpProperties();

        var dim = this.model.attributes.dimensions;

//        var margins = {left : (dim.width / 12), // for y tick labels 
//                        bottom : (dim.height / 12), // for x axis tick labels, and x/r axis labels
//                        top : (dim.height / 18), // for y axis label and doc count
//                        right : (dim.width / 30)}; // so circles centers don't land on the border
        var view = d3.select(this.el).select('#plot-view').html("");

        var svg = this.svg = view.append('svg')
            .attr("width", "100%")
            .attr("height", "90%")
            .attr("viewBox", "0, 0, "+dim.width+", "+dim.height)
            .attr("preserveAspectRatio", "xMidYMin meet")
            .append("g");

        // Render scatter plot container.
        this.plot = svg.append("g")
            .attr("id", "plot");

        this.setUpAxes();
        this.selectTopics();
    },

    getScale: function(info, range) {
        var scale = d3.scale.linear().domain([info.min, info.max]).range(range);
        if(info.type === "text") {
            scale = d3.scale.ordinal().domain(info.text).rangePoints(range);
        }
        return scale;
    },
    
  setUpProperties: function() {

    this.model.set({
        dimensions: {
            width: 800,
            height: 800
        },
    });

    var dim = this.model.attributes.dimensions;

    this.model.set({
        duration: 800,

        topLabelSpacing: Math.round(dim.height / 32),

        xAxisMargin: Math.round(dim.height / 13),

        margin: {
            top: 10,
            bottom: 10,
            left: 0,
            right: 0
        },

        tickLength: Math.round(dim.width / 80),

        barWidth: 3,

        fontSize: 16
    });

    var margin = this.model.attributes.margin;

    this.xScale = d3.scale.linear()
        .range([margin.left, dim.width - margin.right]);

    this.yScale = d3.scale.linear()
        .range([dim.height - margin.bottom, margin.top]);

    this.lineChart = null;
    this.bars = null;
    this.colors = d3.scale.category20(); // Get ordinal scale of 20 colors
    // this.colors = [ "#000000", "#FFFF00", "#800080", "#FFA500", "#ADD8E6", "#CD0000", "#F5DEB3", "#A9A9A9", "#228B22",
    //   "#FF00FF", "#0000CD", "#F4A460", "#EE82EE", "#FF4500", "#191970", "#ADFF2F", "#A52A2A", "#808000", "#DB7093",
    //   "#F08080", "#8A2B2E", "#7FFFD4", "#FF0000", "#00FF00", "#008000", ];
    //console.log(this);
//    _.bindAll(this, "selectTopics", "resize");
//    this.event_aggregator.bind("tot:select-topics", this.selectTopics);
//    this.event_aggregator.bind("resize", this.resize);

  },

  setUpAxes: function() {
    var tickLe = this.model.attributes.tickLength;
    var dim = this.model.attributes.dimensions;

    this.xAxis = d3.svg.axis()
        .scale(this.xScale)
        .orient("bottom");
//        .tickSubdivide(true);

    this.yAxis = d3.svg.axis()
        .scale(this.yScale)
        .orient("left");
//        .tickSubdivide(true);

    // add in the x axis
    this.svg.append("g")
        .attr("id", "x-axis")
        .attr("transform", "translate(0," + dim.height + ")") 
        .call(this.xAxis)
        .style({ "fill": "none", "stroke": "black", "shape-rendering": "crispedges" })
        .style("opacity", 0);

    // add in the y axis
    this.svg.append("g")
        .attr("id", "y-axis")
        .attr("transform", "translate(0, 0)")
        .call(this.yAxis)
        .style({ "fill": "none", "stroke": "black", "shape-rendering": "crispedges" })
        .style("opacity", 0);
    
    //these are for svg saving to include the css inline
//    $('.axtransformis path').attr("opacity", 1);
//    $('.axis text').attr("fill", "#000000");
    //$('.axis .tick').attr("style", "stroke:#000000; opacity:1");
  },
    
    scaleRanges: function(left) {
        this.xScale.range([this.margins.left, this.width - this.margins.right]);
        this.yScale.range([this.height - this.margins.bottom, this.margins.top]);

        this.xAxis.scale(this.xScale);
        this.yAxis.scale(this.yScale);
        // d3.selectAll('.x.axis').attr("transform", "translate(0," + (this.height - this.margins.bottom) + ")");
        // console.log(d3.selectAll('.x.axis').attr("transform"));
    },

  /** populate everything! data is the JSON response from your url(). For
   * information on the return values of specific urls, look at the docs for
   * the function (probably in topic_modeling/visualize/topics/ajax.py)
   *
   * NOTE: this data is cached in localStorage unless you click "refresh" at
   * the bottom of the right-hand bar
   */
  load: function(data) {
    console.log(data);

    this.metrics = data.metrics;
    this.metadata = data.metadata;
    this.topics = data.topics;
    this.documents = data.documents;

    this.topicData = {};
    this.topicData.min = -1;
    this.topicData.max = -1;
    for(var topicId in this.topics) {
      this.topicData[topicId] = this.processTopicData(topicId);
    }

    this.selectTopics(); // Select all topics by default
    this.event_aggregator.trigger("tot:loaded", this.topics);
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
        topicIds = this.model.attributes.selectedTopics = [];
    }

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
//    this.scale = minMax.max / topics.max;
    topics.min = minMax.min;
    topics.max = minMax.max;

    // Scale axes to lineChart (data for all topics)
    this.scaleLineChartAxes();

    // Make the axes transition to the domain of the full lineChart
    this.transitionAxes(1500);

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

    // Scale axes to topic data
    this.scaleTopicAxes();

    // Initialize bars
    this.initBars();

    // Make the axes transition to the new data domain
    this.transitionAxes(1500);

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
    var xScale = this.xScale;
    var yScale = this.yScale;
    var height = dim.height;
//    var bottomMargin = this.margins.bottom;
//    var tooltip = this.tooltip;
    var svg = this.svg;
    var selTopicData = this.model.attributes.selectedTopicData;
    var data = selTopicData.data;
    var colors = this.colors;
    var barWidth = this.model.attributes.barWidth;

    var getOnBarMouseover = this.getOnBarMouseover;
    var getOnBarMouseout = this.getOnBarMouseout;
    var select = this.selectTopics;
    var vis = this;

    // Delete existing elements to conserve memory
    this.plot.selectAll(".bar").data([]).exit().remove();

    // Set the data for the bars
    this.bars = this.plot.selectAll(".bar")
          .data(selTopicData.yearIndices);

    // Append SVG elements with class "bar"
    this.bars.enter()
          .append("svg:rect")
          .attr("class", "bar")
          .attr("x", function(d) { return xScale(d.year); })
          .attr("y", height)
          .attr("width", barWidth)
          .attr("height", 0)
          .style("padding", 10)
          .style("fill", function(d) { return colors(d.index); })
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
    var xScale = this.xScale;
    var yScale = this.yScale;
    var colors = this.colors;
    var raw_topics = this.model.attributes.raw_topics;
    var topics = this.model.attributes.topics;
//    var tooltip = this.tooltip;
    var height = dim.height;
//    var bottomMargin = this.margins.bottom;
//    var leftMargin = this.margins.left;
    var data = null;

    // Function for creating lines - sets x and y value at every point on the line
    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d, i) { return xScale(d.year); })
        .y(function(d, i) { return yScale(data[d.year].totalProbability); }); // Use the total value for this year

    // Delete existing lines to conserve memory (this could be optimized)
    this.svg.selectAll(".chart.line").data([]).exit().remove();

    this.lineChart = {};

    // Append SVG element path for each requested topic
    for (var topicId in raw_topics) {
        var topic = topics[topicId];
        var indices = topic.yearIndices.filter(function(item) { return item.index === 0; }); // Filter indices to only draw one point per year
        indices.topicId = topic.yearIndices.topicId;
        data = topic.data;
        // Create lineChart SVG line element for this topic
        var path = this.plot.append("svg:path")
          .datum(indices)
          .attr("class", "chart line")
          .attr("d", line)
          .style("opacity", 0)
          .style("stroke", colors(topicId))
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
            xAxisEl.call(xAxis);
            yAxisEl.call(yAxis);
        });
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
    var xScale = this.xScale;
    var yScale = this.yScale;
    var height = dim.height;
//    var bottomMargin = this.margins.bottom;
    var data = this.model.attributes.selectedTopicData.data;

    // Make opaque and transition y and height into final positions
    var bars = this.svg.selectAll(".bar")
      .transition().duration(duration)
      .style("opacity", 1)
      .attr("y", function(d) {
          var probability = data[d.year][d.index].probability;
          data[d.year].forEach(function(value, index, array) { // Get cumulative value (stack 'em up)
            if (index < d.index) {
              probability += value.probability;
            }
          });
          return yScale(probability);
        })
      .attr("height", function(d) { return height - yScale(data[d.year][d.index].probability); });
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
//    var bottomMargin = this.margins.bottom;

    // Make transparent and transition y and height to 0
    var bars = this.svg.selectAll(".bar")
      .transition().duration(duration)
      .style("opacity", 0)
      .attr("y", height)
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
    else if (topicIds.length === 0) { // If we want ALL topics (default)
      topicIds = $.map(raw_topics, function(value, key) { return key; }); // Copy topic id keys into id array
    }

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

    var xScale = this.xScale;
    var yScale = this.yScale;
    var topics = this.model.attributes.topics;
    var colors = this.colors;

    // Register event variables
    var getOnPathMouseover = this.getOnPathMouseover;
    var getOnPathMouseout = this.getOnPathMouseout;
    var select = this.selectTopics;
    var vis = this;

    // Function for creating lines - sets x and y value at every point on the line
    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d, i) { return xScale(d.year); })
        .y(function(d, i) { var data = topics[topicId].data;
                            return yScale(data[d.year].totalProbability);
                          });

    path
        .style("stroke", function(d) { return colors(d.topicId); })
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
        var selectedTopics = [];
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
                topics[topic] = this.processTopicData(topic, documents);
                topics[topic].name = toTitleCase(analysisData.topics[topic].names.Top3);
                selectedTopics.push(topic);
            }
        }
        topics.min = -1;
        topics.max = -1;
        return {
            documents: documents,
            topics: topics,
            selectedTopics: selectedTopics,
            raw_topics: raw_topics,
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
    topicData.yearIndices = [];
    topicData.data = {};
    topicData.min = -1;
    topicData.max = -1;

    // Because I don't want to type that again
    var yearIndices = topicData.yearIndices;
    yearIndices.topicId = topicId;
    var data = topicData.data;
      
    // Get topic percentage in all documents
    for(var doc_id in documents) {
        var doc = documents[doc_id];
        var topicProbability = doc.topics[topicId];
        var documentData = {};
        documentData.doc_id = doc_id;
        
        // Preserve the document metadata in the top level of the document
        if ('metadata' in doc) {
            _.extend(documentData, doc.metadata);
        }

        // Not all topics are defined for each document
        if (topicProbability !== undefined) {

            // Get relevant topic-document info
            documentData.probability = topicProbability;
            documentData.doc_id = doc_id;
            var year = doc.metadata.year; //TODO Make this work for any metadata

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

            yearIndices.push(yearIndex);
        }
    }

    // Sort topics by year so that line chart gets drawn correctly
    topicData.yearIndices.sort(function(a, b) { return d3.ascending(a.year, b.year); });

    return topicData;
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
      topicIds = $.map(topicData, function(value, key) { return key; });
    }

    for (var index in topicIds) {
      var topicId = topicIds[index];
      // Get min and max probability for the given topic
      if (min === -1 || min > topicData[topicId].min)
        min = topicData[topicId].min;

      if (max === -1 || max < topicData[topicId].max)
        max = topicData[topicId].max;
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
        .style("fill", colors(d.index)); 
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
        .style("stroke", colors(d.topicId));
    }
  },

});

globalViewModel.addViewClass(["Visualizations"], TopicsOverTimeView);

