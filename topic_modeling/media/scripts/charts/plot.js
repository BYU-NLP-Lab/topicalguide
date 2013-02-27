
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
   this.ccontrol = this.$('#plot-document-c-control');

  },
  
  setUpControls: function(cont_options, nom_options, viewer) {
    if(!this.setUp) {
      this.setUpControl(this.xcontrol, 'X Axis', cont_options, viewer);
      this.setUpControl(this.ycontrol, 'Y Axis', cont_options, viewer);
      this.setUpControl(this.rcontrol, 'Radius', cont_options, viewer);
      this.setUpControl(this.ccontrol, 'Color', nom_options, viewer);
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
    colors : [
      "#981C30",
      "#989415",
      "#1E4559",
      "#7F7274",
      "#4C4A12",
      "#4B0612",
      "#1EAAE4",
      "#AD5E71",
      "#000000",
      "#0000FF",
      "#8A2BE2",
      "#A52A2A",
      "#D2691E",
      "#DC143C",
      "#00FFFF",
      "#00008B",
      "#008B8B",
      "#B8860B",
      "#006400",
      "#8B008B",
      "#556B2F",
      "#FF8C00",
      "#8B0000",
      "#8FBC8F",
      "#2F4F4F",
      "#00CED1",
      "#696969"
    ],
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
    var documents = this.svg.selectAll("circle").data(this.drawingData, function (doc) { return doc.id;}),
    axes = this.getAxes(),
    xRange = this.options.xRange,
    yRange = this.options.yRange,
    rRange = this.options.rRange,
    width = this.options.width,
    height = this.options.height,
    bottomMargin = this.options.margins.bottom,
    info = this.info,
    colors = this.options.colors,
    nomMaps = this.nomMaps;
    //console.log(colors);
    //console.log(this.drawingData);

    documents.enter()
      .insert("svg:circle")
        .attr("cx", function (doc) { return xRange (doc.fields[axes.xAxis]); })
        .attr("cy", function (doc) { return height - yRange (doc.fields[axes.yAxis]) - bottomMargin; })
        .style("opacity", 0)
        .style("fill", function(doc) { return colors[nomMaps[axes.cAxis][doc.fields[axes.cAxis]] % colors.length]; })
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
      .style("fill", function(doc) { return colors[nomMaps[axes.cAxis][doc.fields[axes.cAxis]] % colors.length]; })
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
    var cont_fields = Array();
    var nom_fields = Array();
    cont_fields = cont_fields.concat(metrics);
    for(var field in metadata) {
      if(metadata[field] == 'int' || metadata[field] == 'float')
        cont_fields.push(field);
      else
        nom_fields.push(field);
    }


    this.setUpControls(cont_fields, nom_fields);

    this.drawingData = [];
    var k = 0;
    for(var docid in documents) {
      this.drawingData.push(documents[docid]);
      if (k > 100)
        break;
      k++;
    }
    this.setUpNomMap(this.drawingData, nom_fields);
    console.log(this.nomMaps);
    this.update();
  },

  setUpNomMap: function(data, fields) {
    this.nomMaps = new Object();
    for(var j = 0; j < fields.length; j++) {
      var field = fields[j];
      var counter = 0;
      var map = Object();
      for(var k = 0; k < data.length; k++) {
        var doc = data[k];
        var value = doc.fields[field];
        map[value] = counter;
        counter++;
      }
      this.nomMaps[field] = map;
    }
  },


  setUpControls: function(cont_fields, nom_fields) {
    this.controls.setUpControls(cont_fields, nom_fields, this);

  },


  redraw: function() {

  },

  getAxes: function() {
    var x = $("#plot-document-x-control input:checked").val();
    var y = $("#plot-document-y-control input:checked").val();
    var r = $("#plot-document-r-control input:checked").val();
    var c = $("#plot-document-c-control input:checked").val();
    return {
      xAxis: x,
      yAxis: y,
      rAxis: r,
      cAxis: c
    };
  },

  randomColor: function() {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for(var i = 0; i < 6; i++)
      color += letters[Math.round(Math.random() * 15)];
    console.log(color);
    return color;
  },
    


});

