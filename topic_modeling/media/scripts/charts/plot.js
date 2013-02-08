
//this is our trigger for updating the graph
//function update() {}

/** The Controls **/
var PlotControls = Backbone.View.extend({

  initialize: function (options) {
    var parent = this.parent = options.parent;
    // setup elements. The el is #controls-[name]
   /*here we set up the controls for the various axis
     The user is allowed to select what variable is put on what axis.
    TODO Set up color controls
    TODO Set up controls by attribute value
   */
   var displayNames = ['Number of tokens', 'Number of types', 'Topic Entropy'];
   var values = ['tokens', 'types', 'tentropy'];
   this.$('x-plot').append('<h2>X Axis</h2>');
   this.$('y-plot').append('<h2>Y Axis</h2>');
   this.$('r-plot').append('<h2>Radius</h2>');
   this.setUpControl(this.$('x-plot'), 'x-plot', displayNames, values);
   this.setUpControl(this.$('y-plot'), 'y-plot', displayNames, values);
   this.setUpControl(this.$('r-plot'), 'r-plot', displayNames, values);
  },

  setUpControl: function(control, name,  displayNames, values) {
      control.append('<ul id="' + name + '">');
    //add in preselected value
      for(var k = 0; k < displayNames.length; k++) {
      control.append(
        '<li><label><input type="radio" name="' + name + '"' +
          'value="' + values[k] +'">' + displayNames[k] + '</label></li>');
    }
    control.append('</ul>');
    //when we change the options here, make the changes in the graph
    var update = _.bind(this.parent.update, this.parent);
    control.on("click", update, false);
    control.on("keyup", update, false);
  },

  show: function () {
    this.$el.show();
  },

  hide: function () {
    this.$el.hide();
  }
});


/** The Menus **/
var PlotMenu = Backbone.View.extend({

  initialize: function (options) {
    var parent = this.parent = options.parent;
    // setup elements. The el is #menu-[name]
   //Eventually we want to be able to switch between looking at documents
   //to looking at topics
  },

  show: function () {
    this.$el.show();
  },

  hide: function () {
    this.$el.hide();
  }
});

/** The Info **/
var PlotInfo = Backbone.View.extend({

  initialize: function () {
  },

  clear: function () {
  }
});

/*****************************************************
 * Data: [currently loaded, 

/** The main visualization class
 *
 * Instance Variables:
 *   svg:      the $(svg) element
 *   maing:    the <g> element that you should add things too that are to be
 *             effected by the zoom object.
 *   zoom:     a zoom object for resizing your visualization
 *   options:  a dictionary of the {dict} passed in at initialization,
 *             extending the "defaults" dict
 *   info:     the info object
 *   menu:     the menu object
 *   controls: the controls object
 *
 * **/
var PlotViewer = MainView.add(VisualizationView, {
  name: 'plot-documents',
  title: '2D Plots',
  menu_class: PlotMenu,
  info_class: PlotInfo,
  controls_class: PlotControls,

  /** any defaults that you want. In the class, this.options will be populated
  * with these defaults + an options dictionary passed in when the object is
  * initialized **/
  defaults: {
    width : 720, // width of the graph.  How do we make this variable.  We don't want zooming
    height : 720, // height of the graph
    margins : {top: 20, right: 20, bottom: 20, left: 60}, // margins around the graph
    rRange : d3.scale.linear().range([5, 20]), // radius range function - ensures the radius is between 5 and 20
    /**
    **/
    data : null
  },

  /**
    return the url to grab your data (can be dependent on options)
    look in fancy.html (the template) to see what urls are available in the
    global URLS variable (and you can add your own to that object).
  **/
  url: function () {
      /*
      data should be in this format
        {data : { documents : [{<document values: id, <metrics>, <attributes>>}]}}
    return "url to get data I need";
    */
  },

  /** setup the d3 layout, etc. Everything you can do without data **/
  setup_d3: function () {
    var xRange = d3.scale.linear().range([this.options.margins.left, this.options.width - this.options.margins.right]); // x range function
    var yRange = d3.scale.linear().range([this.options.height - this.options.margins.top, this.options.margins.bottom]); // y range function
    var xAxis = d3.svg.axis().scale(xRange).tickSize(16).tickSubdivide(true); // x axis function
    var yAxis = d3.svg.axis().scale(yRange).tickSize(10).orient("right").tickSubdivide(true); // y axis function

  // add in the x axis
  this.maing.append("svg:g") // container element
    .attr("class", "x axis") // so we can style it with CSS
    .attr("transform", "translate(0," + this.options.height + ")") // move into position
    .call(xAxis); // add to the visualisation

  // add in the y axis
  this.maing.append("svg:g") // container element
    .attr("class", "y axis") // so we can style it with CSS
    .call(yAxis); // add to the visualisation

  // load data, process it and draw it
  //update ();
  
  },

  update: function () {
  },

  /** populate everything! data is the JSON response from your url(). For
   * information on the return values of specific urls, look at the docs for
   * the function (probably in topic_modeling/visualize/topics/ajax.py)
   *
   * NOTE: this data is cached in localStorage unless you click "refresh" at
   * the bottom of the right-hand bar
   */
  load: function (data) {
  },


  redraw: function() {

  }

});
