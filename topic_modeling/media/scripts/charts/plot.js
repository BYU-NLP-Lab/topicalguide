
//this is our trigger for updating the graph
//function update() {}

/** The Controls **/
var PlotControls = Backbone.View.extend({
  xcontrol : null,
  ycontrol : null,
  rcontrol : null,
  setUp : false,

  initialize: function (options) {
   var parent = this.parent = options.parent;
   this.xcontrol = this.$('#plot-document-x-control');
   this.ycontrol = this.$('#plot-document-y-control');
   this.rcontrol = this.$('#plot-document-r-control');

  },
  
  setUpControls: function(options, viewer) {
    if(!this.setUp) {
      this.setUpControl(this.xcontrol, 'X Axis', options, viewer);
      this.setUpControl(this.ycontrol, 'Y Axis', options, viewer);
      this.setUpControl(this.rcontrol, 'Radius', options, viewer);
      this.setUp = true;
    }
  },
    

  setUpControl: function(control, title, options, viewer) {
    control.append('<h4>' + title + '</h4>');
    control.append('<form class="plot-documents-select">');
    //add in preselected value
    for(var k = 0; k < options.length; k++) {
    control.append(
        '<input type="radio" name="' + title + '" value="' + options[k] + '" ' + 
        (k == 0 ? 'checked' : '') + '>' + options[k] + '</br>');
    }
    control.append('</form>');
    //when we change the options here, make the changes in the graph
    //TODO:
    //var update = _.bind(this.parent.update, this.parent);
    control.on("click", function() { viewer.update(); });
    //control.on("keyup", update_fn, false);
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
  },

});

/** The Info **/
var PlotInfo = Backbone.View.extend({

  initialize: function () {
  },

  clear: function () {
  },

  show: function () {
    this.$el.show();
  },
  
  hide: function () {
    this.$el.hide();
  },

  populate: function(doc) {
    var div = $('#info-plot-documents');
    div.html('');
    div.append('<h4>' + doc.name + '</h4>');
    //TODO Correctly populate the info box

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
    xRange : d3.scale.linear().range([60, 720 - 20]), // x range function, left and right padding
    yRange : d3.scale.linear().range([30, 720 - 60]), // y range function
    rRange : d3.scale.linear().range([5, 20]), // radius range function - ensures the radius is between 5 and 20
    drawingData : null,
    width: 720,
    height: 720,
    margins : {top: 20, right: 20, bottom: 20, left: 60}, // margins around the graph
    /**
    **/
  },

  /**
    return the url to grab your data (can be dependent on options)
    look in fancy.html (the template) to see what urls are available in the
    global URLS variable (and you can add your own to that object).
  **/
  url: function () {
    return URLS['documents']['metrics'];
  },

  /** setup the d3 layout, etc. Everything you can do without data **/
  setup_d3: function () {
    var xAxis = d3.svg.axis().scale(this.options.xRange).tickSize(16).tickSubdivide(true); // x axis function
    var yAxis = d3.svg.axis().scale(this.options.yRange).tickSize(10).orient("right").tickSubdivide(true); // y axis function

  // add in the x axis
  this.maing.append("svg:g") // container element
    .attr("class", "x axis") // so we can style it with CSS
    .attr("transform", "translate(0," + (this.options.height - this.options.margins.bottom - 20) + ")") // move into position
    .call(xAxis); // add to the visualisation

  // add in the y axis
  this.maing.append("svg:g") // container element
    .attr("class", "y axis") // so we can style it with CSS
    .call(yAxis); // add to the visualisation

  //set up listeners for the controls
  
  },

  update: function () {
    console.log("update()");
    var documents = this.svg.selectAll("circle").data(this.drawingData, function (d) { return d.id;}),
    axes = this.getAxes(),
    xRange = this.options.xRange,
    yRange = this.options.yRange,
    rRange = this.options.rRange,
    width = this.options.width,
    height = this.options.height,
    bottomMargin = this.options.margins.bottom,
    info = this.info;
    //console.log(this.drawingData);

    documents.enter()
      .insert("svg:circle")
        .attr("cx", function (doc) { return xRange (doc.fields[axes.xAxis]); })
        .attr("cy", function (doc) { return height - yRange (doc.fields[axes.yAxis]) - bottomMargin; })
        .style("opacity", 0)
        .style("fill", "0x0000FF")
        .on("click", function (doc) { info.populate(doc); } );

    xRange.domain([
      d3.min(this.drawingData, function (doc) { return +doc.fields[axes.xAxis]; }),
      d3.max(this.drawingData, function (doc) { return +doc.fields[axes.xAxis]; })
    ]);
    yRange.domain([
      d3.min(this.drawingData, function (doc) { return +doc.fields[axes.yAxis]; }),
      d3.max(this.drawingData, function (doc) { return +doc.fields[axes.yAxis]; })
    ]);
    rRange.domain([
      d3.min(this.drawingData, function (doc) { return +doc.fields[axes.rAxis]; }),
      d3.max(this.drawingData, function (doc) { return +doc.fields[axes.rAxis]; })
    ]);

    //TODO axis transformation

    documents.transition().duration(1500).ease("exp-in-out")
      .style("opacity", 1)
      .style("fill", "0x000000")
      .attr("r", function(doc) { return rRange (doc.fields[axes.rAxis]); })
      .attr("cx", function (doc) { return xRange (doc.fields[axes.xAxis]); })
      .attr("cy", function (doc) { return height - yRange (doc.fields[axes.yAxis]) - bottomMargin; });

  },

  /** populate everything! data is the JSON response from your url(). For
   * information on the return values of specific urls, look at the docs for
   * the function (probably in topic_modeling/visualize/topics/ajax.py)
   *
   * NOTE: this data is cached in localStorage unless you click "refresh" at
   * the bottom of the right-hand bar
   */
  load: function (data) {
    console.log(data);
    documents = data.documents;
    metrics = data.metrics;
    metadata = data.metadata;
    fields = Array();
    fields = fields.concat(metrics);
    for(var field in metadata) {
      if(metadata[field] == 'int' || metadata[field] == 'float')
        fields.push(field);
    }

    this.setUpControls(fields);

    this.drawingData = [];
    var k = 0;
    for(var docid in documents) {
      this.drawingData.push(documents[docid]);
      if (k > 8)
        break;
      k++;
    }
    this.update();
  },

  setUpControls: function(fields) {
    this.controls.setUpControls(fields, this);

  },


  redraw: function() {

  },

  getAxes: function() {
    var x = $("#plot-document-x-control input:checked").val();
    var y = $("#plot-document-y-control input:checked").val();
    var r = $("#plot-document-r-control input:checked").val();
    return {
      xAxis: x,
      yAxis: y,
      rAxis: r
    };
  },


});

