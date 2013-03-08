
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

    var control = this;
    $("</br><h4>Removing</h4>").appendTo($('#controls-plot-documents'));
    this.removeButton = $("<button>Remove Documents</button>").appendTo($('#controls-plot-documents'));
    this.removeButton.on("click", function () { control.removeButtonClicked(); });
    this.allButton = $("<button>Add Removed Documents</button>").appendTo($('#controls-plot-documents'));
    this.allButton.on("click", function () { control.allButtonClicked(); });
  },

  allButtonClicked: function () {
    for(doc_id in this.parent.data)
    {
      var doc = this.parent.data[doc_id];
      doc.included = true;
    }
    this.parent.update(true);
    this.parent.removingDocs = false;
    this.removeButton.html('Remove Documents');
  },

  removeButtonClicked : function () {
    if(this.parent.removingDocs) {
      console.log("Done Removing");
      //TODO enable controls
      this.removeButton.html('Remove Documents');
      this.parent.update(true);
    }
    else {
      //$("select", this.xcontrol).attr('disabled', 'disabled');
      //TODO disable controls
      console.log("Removing");
      this.removeButton.html('Done');
    }
    this.parent.removingDocs = !this.parent.removingDocs;
  },
  
  setUpControls: function(cont_options, nom_options, topics, viewer) {
    if(!this.setUp) {
      this.setUpControl(this.xcontrol, 'X Axis', cont_options, topics, viewer);
      this.setUpControl(this.ycontrol, 'Y Axis', cont_options, topics, viewer);
      this.setUpControl(this.rcontrol, 'Radius', cont_options, topics, viewer);
      this.setUpControl(this.ccontrol, 'Color', nom_options, null, viewer);
      this.setUp = true;
    }
  },

  setUpControl: function(control, title, options, topics, viewer) {
    control.append('<h4>' + title + '</h4>');
    control.append('<form class="plot-documents-select">');
    //add in preselected value
    for(var k = 0; k < options.length; k++) {
    control.append(
        '<input type="radio" name="' + title + '" value="' + options[k] + '" ' + 
        (k == 0 ? 'checked' : '') + '>' + options[k] + '</br>');
    }
    
    //For uniform Radius
    if(title == 'Radius') {
    control.append('<input type="radio" name="' + title + '" value="uniform">Uniform</br>'); 
    }
    
    if(topics != null) {
      this.dropdown = this.createTopicDropDown(topics);
      control.append('<input type="radio" name="' + title + '"value ="topic">Topic');
      control.append(this.dropdown);
      control.append('</br>');

      //select changed listener selects the topic bullet
      var select = $("select", control);
      var radio = $("[value=topic]", control);
      select.on("change", function() {console.log("change"); radio.attr('checked', true); } );
    }

    control.append('</form>');
    control.on("click", function() { viewer.update(); });
    control.on("keyup", function() { viewer.update(); });
  },

  createTopicDropDown: function(topics) {
    var html = '<select name="topic">';
    for (var topic_id in topics)
    {
      var topic_name = topics[topic_id];
      html += '<option value="' + topic_id + '">' +
              topic_name + '</option>';
    }
    html += '</select>';
    return html;
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
  //TODO display the number of documents shown

  initialize: function () {
    this.docDisplay = $("<div></div>").appendTo($('#info-plot-documents'));
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
    this.docDisplay.html('</br><h4>' + doc.name + '</h4>');
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
 *             extending the "defaults" dict *   info:     the info object *   menu:     the menu object *   controls: the controls object * * **/ var PlotViewer = MainView.add(VisualizationView, { name: 'plot-documents', title: '2D Plots', menu_class: PlotMenu, info_class: PlotInfo, controls_class: PlotControls, /** any defaults that you want. In the class, this.options will be populated * with these defaults + an options dictionary passed in when the object is
  * initialized **/
  defaults: {
    xRange : d3.scale.linear().range([60, 630 - 20]), // x range function, left and right padding
    yRange : d3.scale.linear().range([630 - 60, 30]), // y range function
    rRange : d3.scale.linear().range([5, 15]), // radius range function - ensures the radius is between 5 and 20
    data : null,
    width: 630,
    height: 630,
    margins : {top: 20, right: 20, bottom: 20, left: 60}, // margins around the graph
    //colors array is replaced by the d3 color scheme
    colors : [ "#000000", "#FFFF00", "#800080", "#FFA500", "#ADD8E6", "#CD0000", "#F5DEB3", "#A9A9A9", "#228B22",
      "#FF00FF", "#0000CD", "#F4A460", "#EE82EE", "#FF4500", "#191970", "#ADFF2F", "#A52A2A", "#808000", "#DB7093",
      "#F08080", "#8A2B2E", "#7FFFD4", "#FF0000", "#00FF00", "#008000", ],
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
    this.xAxis = d3.svg.axis().scale(this.options.xRange).tickSize(10).tickSubdivide(true); // x axis function
    this.yAxis = d3.svg.axis().scale(this.options.yRange).tickSize(10).orient("right").tickSubdivide(true); // y axis function

  // add in the x axis
  this.maing.append("svg:g") // container element
    .attr("class", "x axis") // so we can style it with CSS
    .attr("transform", "translate(0," + (this.options.height - this.options.margins.bottom - 20) + ")") // move into position
    .call(this.xAxis); // add to the visualisation

  // add in the y axis
  this.maing.append("svg:g") // container element
    .attr("class", "y axis") // so we can style it with CSS
    .call(this.yAxis); // add to the visualisation

  this.tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

  this.lastAxes = null;
  this.removingDocs = false;

  },

  filter: function(data, axes, override) {
    if(!override && !this.firstTime && !this.shouldFilter(axes)) {
      return this.drawingData;
    }
    //console.log("filter()");
    var filteredData = Array();
    for (var index in data) {
      var doc = data[index];
      if(doc.fields[axes.xAxis] && doc.fields[axes.yAxis] &&
        (axes.rAxis == 'uniform' || doc.fields[axes.rAxis]) &&
         doc.fields[axes.cAxis] && doc.included) {
        filteredData.push(doc);
      }
    }
    return filteredData;
  },

  //we don't need to refilter if we change from a non-topic to a non-topic
  //this is an optimization that can be turned off
  shouldFilter: function(newAxes) {
    if(this.lastAxes.xAxis != newAxes.xAxis) {
      if($.isNumeric(this.lastAxes.xAxis) || $.isNumeric(newAxes.xAxis))
        return true;
    }
    
    if(this.lastAxes.yAxis != newAxes.yAxis) {
      if($.isNumeric(this.lastAxes.yAxis) || $.isNumeric(newAxes.yAxis))
        return true;
    }

    if(this.lastAxes.rAxis != newAxes.rAxis) {
      if($.isNumeric(this.lastAxes.rAxis) || $.isNumeric(newAxes.rAxis))
        return true;
    }
    return false;
  },

  same: function(newAxes) {
    if(!this.lastAxes)
      return false;

    return this.lastAxes.xAxis == newAxes.xAxis &&
           this.lastAxes.yAxis == newAxes.yAxis &&
           this.lastAxes.rAxis == newAxes.rAxis &&
           this.lastAxes.cAxis == newAxes.cAxis;
  },

  update: function (override) {
    /*
      Most of these variables are just copied from this namespace so that
        the anonomous functions can access them
    */
    var axes = this.getAxes();
    if(!override && this.same(axes)) {
      return;
    }
    console.log("update()");
    this.drawingData = this.filter(this.data, axes, override);
    this.lastAxes = axes;

    var documents = this.svg.selectAll("circle").data(this.drawingData, function (doc) { return doc.id;}),
    xRange = this.options.xRange,
    yRange = this.options.yRange,
    rRange = this.options.rRange,
    width = this.options.width,
    height = this.options.height,
    bottomMargin = this.options.margins.bottom,
    info = this.info,
    colors = /*d3.scale.category20();*/this.options.colors, //d3 doesn't keep consistent colors
    nomMaps = this.nomMaps,
    tooltip = this.tooltip,
    viewRef = this;

    //TODO set up the click handler for the circles to remove themselves

    //sets up the circles
    documents.enter()
      .insert("svg:circle")
        .attr("cx", function (doc) { return xRange(doc.fields[axes.xAxis]); })
        .attr("cy", function (doc) { return yRange(doc.fields[axes.yAxis]); })
        .style("opacity", 0)
        .style("fill", function(doc) { return colors[nomMaps[axes.cAxis][doc.fields[axes.cAxis]] % colors.length]; })
        //updates the infobox
        .on("click", function (doc) {
                              if(viewRef.removingDocs) {
                                viewRef.tooltip.transition().duration(200).style("opacity", 0.0);
                                $(this).remove();
                                doc.included = false;
                              }
                              else
                                info.populate(doc);
                              } )
        //tooltips
        .on("mouseover", function(doc) {
          tooltip.transition()
            .duration(200)
            .style("opacity", 0.9);
          tooltip.html(doc.name)
            .style("left", (d3.event.pageX + 8) + "px")
            .style("top", (d3.event.pageY) + "px"); })
        .on("mouseout", function(doc) {
          tooltip.transition()
            .duration(200)
            .style("opacity", 0.0); });
          
    //Change visual scale to fit the new input domains
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

	// transition function for the axes
    var t = this.svg.transition().duration(1500).ease("exp-in-out");
    t.select(".x.axis").call(this.xAxis);
    t.select(".y.axis").call(this.yAxis);

    //transition function for the circles
    documents.transition().duration(1500).ease("exp-in-out")
      .style("opacity", 1)
      .style("fill", function(doc) { return colors[nomMaps[axes.cAxis][doc.fields[axes.cAxis]] % colors.length]; })
      //.style("fill", function(doc) { return colors(nomMaps[axes.cAxis][doc.fields[axes.cAxis]]); })
      .attr("r", function(doc) { return (axes.rAxis == 'uniform') ? 7 :rRange(doc.fields[axes.rAxis]); })
      .attr("cx", function (doc) { return xRange(doc.fields[axes.xAxis]); })
      .attr("cy", function (doc) { return yRange(doc.fields[axes.yAxis]); });

    documents.exit().transition().duration(1500).ease("exp-in-out")
      .attr("r", 0)
      .style("opacity", 0)
        .remove();

    this.firstTime = false;
  },

  /** populate everything! data is the JSON response from your url(). For
   * information on the return values of specific urls, look at the docs for
   * the function (probably in topic_modeling/visualize/topics/ajax.py)
   *
   * NOTE: this data is cached in localStorage unless you click "refresh" at
   * the bottom of the right-hand bar
   */
  load: function (server_data) {
    console.log(server_data);
    this.firstTime = true;
    var documents = server_data.documents;
    var metrics = server_data.metrics;
    var metadata = server_data.metadata;
    var topics = server_data.topics;
    var cont_fields = Array();
    var nom_fields = Array();
    cont_fields = cont_fields.concat(metrics);
    for(var field in metadata) {
      if(metadata[field] == 'int' || metadata[field] == 'float')
        cont_fields.push(field);
      else
        nom_fields.push(field);
    }

    this.setUpControls(cont_fields, nom_fields, topics);

    this.data = [];
    var k = 0;
    var docLimit = 1000;
    for(var docid in documents) {
      var doc = documents[docid];
      doc.included = true;
      this.data.push(doc);
      if (k > docLimit)
        break;
      k++;
    }
    //console.log(this.data);
    this.setUpNomMap(this.data, nom_fields);
    //console.log(this.nomMaps);
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
        if(!map[value]){
        map[value] = counter;
        counter++;
        }
      }
      this.nomMaps[field] = map;
    }
  },


  setUpControls: function(cont_fields, nom_fields, topics) {
    this.controls.setUpControls(cont_fields, nom_fields, topics, this);

  },


  redraw: function() {

  },

  getAxes: function() {
    var x = this.getValue($("#plot-document-x-control"));
    var y = this.getValue($("#plot-document-y-control"));
    var r = this.getValue($("#plot-document-r-control"));
    var c = this.getValue($("#plot-document-c-control"));
    return {
      xAxis: x,
      yAxis: y,
      rAxis: r,
      cAxis: c
    };
  },

  getValue: function(element) {
    var val = $("input:checked", element).val();
    if(val == 'topic')
    {
      val = $("option:selected", element).val();
    }
    return val;
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

