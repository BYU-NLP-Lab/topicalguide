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


/** The main visualization class
 *
 * Instance Variables:
 *   svg:      the $(svg) element
 *   maing:    the <g> element that you should add things to that are to be
 *             effected by the zoom object.
 *   zoom:     a zoom object for resizing your visualization
 *   options:  a dictionary of the {dict} passed in at initialization,
 *             extending the "defaults" dict
 *   info:     the info object
 *   menu:     the menu object
 *   controls: the controls object
 **/
var TopicsOverTimeView = DefaultView.extend({
    readableName: "Topics Over Time",

    initialize: function() {
    },
    
    cleanup: function() {
    },

    /** setup the d3 layout, etc. Everything you can do without data **/
    render: function () {
        this.$el.html("<svg id=\"tot-svg\"></svg>");
        this.svg = this.$el.find("#tot-svg");
        this.maing = d3.select(this.el).select("#tot-svg").append("g");
        this.setUpProperties();
        this.setUpAxes();    
        this.tooltip = d3.select("body").append("div")
                                        .attr("class", "tooltip")
                                        .style("opacity", 0)
                                        .style("height", "38px");
    },

  setUpProperties: function() {

    this.margins = {left : (this.width / 12), // for y tick labels 
                    bottom : (this.height / 12), // for x axis tick labels, and x/r axis labels
                    top : (this.height / 18), // for y axis label and doc count
                    right : (this.width / 30)}; // so circles centers don't land on the border

    // x range function, left and right padding
    this.xRange = d3.scale.linear().range([this.margins.left, this.width - this.margins.right]);

    // y range function
    this.yRange = d3.scale.linear().range([this.height - this.margins.bottom, this.margins.top]);

    this.documents = null;
    this.topicData = null;
    this.selectedTopicIds = null;
    this.selectedTopicData = null;
    this.lineChart = null;
    this.bars = null;
    this.topLabelSpacing = Math.round(this.height / 32);
    this.xAxisMargin = Math.round(this.height / 13);
    this.tickLength = Math.round(this.width / 80);
    this.barWidth = 3;
    this.colors = d3.scale.category20(); // Get ordinal scale of 20 colors
    // this.colors = [ "#000000", "#FFFF00", "#800080", "#FFA500", "#ADD8E6", "#CD0000", "#F5DEB3", "#A9A9A9", "#228B22",
    //   "#FF00FF", "#0000CD", "#F4A460", "#EE82EE", "#FF4500", "#191970", "#ADFF2F", "#A52A2A", "#808000", "#DB7093",
    //   "#F08080", "#8A2B2E", "#7FFFD4", "#FF0000", "#00FF00", "#008000", ];
    this.fontSize = $('body').css('font-size');
    //console.log(this);
    _.bindAll(this, "selectTopics", "resize");
    this.event_aggregator.bind("tot:select-topics", this.selectTopics);
    this.event_aggregator.bind("resize", this.resize);

  },

  setUpAxes: function() {
    this.xAxis = d3.svg.axis().scale(this.xRange).tickSize(this.tickLength).tickSubdivide(true); // x axis function
    this.yAxis = d3.svg.axis().scale(this.yRange).tickSize(this.tickLength).orient("left").tickSubdivide(true); // y axis function

    // add in the x axis
    this.maing.append("svg:g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + (this.height - this.margins.bottom) + ")") 
      .call(this.xAxis);

    // add in the y axis
    this.maing.append("svg:g")
      .attr("class", "y axis")
      .attr("transform", "translate(" + this.margins.left + ", 0)")
      .call(this.yAxis);
    
    //these are for svg saving to include the css inline
    $('.axis path').attr("opacity", 1);
    $('.axis text').attr("fill", "#000000");
    //$('.axis .tick').attr("style", "stroke:#000000; opacity:1");
  },

  scaleRanges: function() {
    this.xRange.range([this.margins.left, this.width - this.margins.right]);
    this.yRange.range([this.height - this.margins.bottom, this.margins.top]);

    this.xAxis.scale(this.xRange);
    this.yAxis.scale(this.yRange);
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
      this.topicData[topicId] = this.formatTopicData(topicId);
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

    if (!this.topics) {
        return;
    }

    var topicIds = Array.prototype.slice.call(arguments, 0)[0];
    if (!topicIds) { // If there are no arguments (select all)
      topicIds = [];
    }
    this.selectedTopicIds = topicIds;

    if (topicIds.length > this.topics.length) {
      throw new Error('More topics selected than exist');
    }
    else if (topicIds.length > 1 || topicIds.length === 0) {
      this.showLineChart(topicIds);
      return;
    }
    else if (topicIds.length < 0) {
      throw new Error('Something is wrong with your array length...');
    }

    // Otherwise get the only topic id and transition to bar chart
    var topicId = topicIds[0];

    // Select the topic data
    this.selectedTopicData = this.topicData[topicId];

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

    var minMax = this.getMinMaxTopicValues(topicIds);
    this.scale = minMax.max / this.topicData.max;
    this.topicData.min = minMax.min;
    this.topicData.max = minMax.max;

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

    var data = this.selectedTopicData.data;
    var maxStack = 0;

    // Calculate x domain
    var keys = $.map(data, function(v, i){
      return i;
    });

    var range = this.getYearRange(this.documents);
    this.xRange.domain([ range.min, range.max ]);

    this.barWidth = (this.width - this.margins.right - this.margins.left) / (range.max - range.min);

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
    this.yRange.domain([ yMin, yMax ]);

    // Set color domain
    this.colors.domain(_.range(0, maxStack));//[ 0, maxStack ]);
  },

  /**
   * Scale the axes for all topics
   *
   * Precondition: The topic data is set
   * Postcondition: The lineChart can now be initialized
   */
  scaleLineChartAxes: function() {

    // Set x domain
    var range = this.getYearRange(this.documents);
    this.xRange.domain([ range.min, range.max ]);

    // Set y domain
    this.yRange.domain([ 0, this.topicData.max ]);

    // set color domain
    var topicKeys = $.map(this.topics, function(value, key) { return key; }); // Get all topic IDs (they are the keys)
    this.colors.domain(_.range(topicKeys[0], topicKeys[topicKeys.length - 1]));// [ topicKeys[0], topicKeys[topicKeys.length - 1] ]);
  },

  /**
   * Initializes the dimensions, colors, and events of each bar in the bar chart
   *
   * Precondition: Axes are correctly set for the selected topic
   * Postcondition: Bars can be transitioned into place
   */
  initBars: function() {

    var xRange = this.xRange;
    var yRange = this.yRange;
    var height = this.height;
    var bottomMargin = this.margins.bottom;
    var tooltip = this.tooltip;
    var svg = this.svg;
    var data = this.selectedTopicData.data;
    var colors = this.colors;

    var getOnBarMouseover = this.getOnBarMouseover;
    var getOnBarMouseout = this.getOnBarMouseout;
    var select = this.selectTopics;
    var vis = this;

    // Delete existing elements to conserve memory
    this.svg.selectAll(".bar").data([]).exit().remove();

    // Set the data for the bars
    this.bars = this.svg.selectAll(".bar")
          .data(this.selectedTopicData.yearIndices);

    // Append SVG elements with class "bar"
    this.bars.enter()
          .append("svg:rect")
          .attr("class", "bar")
          .attr("x", function(d) { return xRange(d.year); })
          .attr("y", this.height - bottomMargin)
          .attr("width", this.barWidth)
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

    var xRange = this.xRange;
    var yRange = this.yRange;
    var colors = this.colors;
    var topics = this.topics;
    var tooltip = this.tooltip;
    var height = this.height;
    var bottomMargin = this.margins.bottom;
    var leftMargin = this.margins.left;
    var data = null;

    // Function for creating lines - sets x and y value at every point on the line
    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d, i) { return xRange(d.year); })
        .y(function(d, i) { return yRange(data[d.year].totalProbability); }); // Use the total value for this year

    // Delete existing lines to conserve memory (this could be optimized)
    this.svg.selectAll(".chart.line").data([]).exit().remove();

    this.lineChart = {};

    // Append SVG element path for each requested topic
    for (var topicId in this.topics) {
        var topic = this.topicData[topicId];
        var indices = topic.yearIndices.filter(function(item) { return item.index === 0; }); // Filter indices to only draw one point per year
        indices.topicId = topic.yearIndices.topicId;
        data = topic.data;
        // Create lineChart SVG line element for this topic
        var path = this.svg.append("svg:path")
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
   * Precondition: xRange and yRange have been set to the correct domain and range
   * Postcondition: Bars can be initialized and will fit within the axes
   *
   * duration - The duration of the transition in ms (0 is instant)
   */
  transitionAxes: function(duration) {

    var t = this.svg.transition().duration(duration);//.ease("exp-in-out");
    t.select(".x.axis").call(this.xAxis);
    t.select(".y.axis").call(this.yAxis);

    // Translate x axis in case the whole visualization moves
    var xAxisEl = $('#topics-over-time .x.axis');
    var translate = this.parseTransformAttr(xAxisEl.attr("transform")).translate;
    $({ transform : translate[1] }).animate({ transform : this.height - this.margins.bottom }, // Magical jQuery attribute animation
                                            { duration : duration,
                                              step : function(now) {
                                                xAxisEl.attr("transform", "translate(" + translate[0] + "," + now + ")");
                                              }
                                            });
    
    //this makes the css inline for saving the svg
    $('.axis .tick').attr("style", "stroke:#000000; opacity:1");
    $('.axis text').css("font-size", "this.fontSize");
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

    var xRange = this.xRange;
    var yRange = this.yRange;
    var height = this.height;
    var bottomMargin = this.margins.bottom;
    var data = this.selectedTopicData.data;

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
          return yRange(probability);
        })
      .attr("height", function(d) { return height - yRange(data[d.year][d.index].probability) - bottomMargin; });
  },

  /**
   * Transition the bars in the chart into hiding (from end height to hformatTopicDataeight 0 and end y to bottom y)
   *
   * Precondition: Bars have been initialized
   *
   * bars - D3 entered bar element to transition
   * duration - The duration of the transition in ms (0 is instant)
   */
  transitionBarsDown: function(duration) {

    var height = this.height;
    var bottomMargin = this.margins.bottom;

    // Make transparent and transition y and height to 0
    var bars = this.svg.selectAll(".bar")
      .transition().duration(duration)
      .style("opacity", 0)
      .attr("y", height - bottomMargin)
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

    var topics = _.extend({}, this.topics);

    if (topicIds === null) {
      topicIds = []; // Hide all topics
    }
    else if (topicIds.length === 0) { // If we want ALL topics (default)
      topicIds = $.map(topics, function(value, key) { return key; }); // Copy topic id keys into id array
    }

    // Transition wanted topics into view
    // Start with map of all topics - remove wanted ones and leave unwanted ones
    var delayOrder = 0;
    for (var topicIdIndex in topicIds) {
      var topicId = topicIds[topicIdIndex];
      if (topics[topicId] === undefined)
        throw new Error('Invalid topic id given');
      else {
        this.transitionLineOut(this.lineChart[topicId], topicId, delayOrder, duration);
        delete topics[topicId];
      }
      ++delayOrder;
    }

    // Hide unwanted topics
    // Loop through topics left in topic map because they were not specified in topicIds
    delayOrder = 0;
    for (var topicId in topics) {
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

    var xRange = this.xRange;
    var yRange = this.yRange;
    var topicData = this.topicData;
    var colors = this.colors;

    // Register event variables
    var getOnPathMouseover = this.getOnPathMouseover;
    var getOnPathMouseout = this.getOnPathMouseout;
    var select = this.selectTopics;
    var vis = this;

    // Function for creating lines - sets x and y value at every point on the line
    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d, i) { return xRange(d.year); })
        .y(function(d, i) { var data = topicData[topicId].data;
                            return yRange(data[d.year].totalProbability);
                          });

    path
        .style("stroke", function(d) { return colors(d.topicId); })
        .on("mouseover", getOnPathMouseover(vis))
        .on("mouseout", getOnPathMouseout(vis))
        .on("click", function(d) {
          select.call(vis, [d.topicId]);
        });

    // Make lines opaque and do magical line unfolding transition
    var scale = this.scale;
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

    var tooltip = this.tooltip;
    // var length = path.node().getTotalLength();

    path
      .on("mouseover", null)
      .on("mouseout", null)
      .on("click", null);

    // Make sure tooltip disappears
    tooltip.transition()
      .duration(200)
      .style("opacity", 0.0);

    // Make lines transparent and do magical line folding
    path.transition().duration(duration)
      .delay(delayOrder * 15)
      // .attr("stroke-dashoffset", length) // Fold lines
      .style("opacity", 0.0);
  },

  resize: function(options) { 

    VisualizationView.prototype.resize.call(this, options);

    this.scaleRanges();
    this.selectTopics(this.selectedTopicIds);
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
   * Formats the data for the selected topic
   * Sorts year indices array in ascending order
   *
   * Precondition: Given topic exists in the dataset
   * Precondition: Documents object has been initialized from data
   * Postcondition: The axes and bars can now be initialized and set
   *
   * topicId - The ID of the selected topic
   */
  formatTopicData: function(topicId) {

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
    for(var docid in this.documents) {
      if (this.documents.hasOwnProperty(docid)) {
        var thisDocument = this.documents[docid];
        var topicProbability = thisDocument.fields[topicId];
        var documentData = {};
        
        // Not all topics are defined for each document
        if (topicProbability !== undefined) {

          // Get relevant topic-document info
          documentData.probability = topicProbability;
          documentData.title = thisDocument.fields.title;
          documentData.author = thisDocument.fields.author_name;
          documentData.docId = docid;
          var year = thisDocument.fields.year;

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
    }

    // Sort topics by year so that line chart gets drawn correctly
    topicData.yearIndices.sort(function(a, b) { return d3.ascending(a.year, b.year); });

    return topicData;
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

    if (topicIds.length === 0) {
      topicIds = $.map(this.topics, function(value, key) { return key; });
    }

    for (var index in topicIds) {
      var topicId = topicIds[index];
      // Get min and max probability for the given topic
      if (min === -1 || min > this.topicData[topicId].min)
        min = this.topicData[topicId].min;

      if (max === -1 || max < this.topicData[topicId].max)
        max = this.topicData[topicId].max;
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
    for(var docid in documents) {
      var docYear = documents[docid].fields.year;
      if (minYear === -1 || docYear < minYear) {
        minYear = docYear;
      }
      if (maxYear === -1 || docYear > maxYear) {
        maxYear = docYear;
      }
    }

    return { min: minYear, max: maxYear };
  },

//+++++++++++++++++++++++++++++++++++++++++++++++    EVENT HANDLERS    +++++++++++++++++++++++++++++++++++++++++++++++\\

  getOnBarMouseover: function(context) {

    return function(d) {
      var tooltip = context.tooltip;
      var data = context.selectedTopicData.data;

      tooltip.transition()
        .duration(200)
        .style("opacity", 0.9);
      tooltip.html(data[d.year][d.index].title + " " + d.year)
        .style("left", (d3.event.pageX + 8) + "px")
        .style("top", (d3.event.pageY) + "px");
      d3.select(this)
        .style("fill", "brown");
    }
  },

  getOnBarMouseout: function(context) {

    return function(d) {
      var tooltip = context.tooltip;
      var colors = context.colors;

      tooltip.transition()
        .duration(200)
        .style("opacity", 0.0); 
      d3.select(this)
        .style("fill", colors(d.index)); 
    }
  },

  getOnPathMouseover: function(context) {

    return function(d) {
      var tooltip = context.tooltip;
      var topics = context.topics;

      tooltip.transition()
        .duration(200)
        .style("opacity", 0.9)
      tooltip.html(d.topicId + " " + topics[d.topicId])
        .style("left", (d3.event.pageX + 8) + "px")
        .style("top", (d3.event.pageY) + "px");
      d3.select(this)
        .style("stroke", "brown"); 
    }
  },

  getOnPathMouseout: function(context) {

    return function(d) {
      var tooltip = context.tooltip;
      var colors = context.colors;

      tooltip.transition()
        .duration(200)
        .style("opacity", 0.0); 
      d3.select(this)
        .style("stroke", colors(d.topicId));
    }
  },

});

globalViewModel.addViewClass([], TopicsOverTimeView);
