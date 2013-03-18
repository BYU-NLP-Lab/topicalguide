
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
    $("</br><h4>Remove Documents</h4>").appendTo($('#controls-plot-documents'));
    this.removeButton = $("<button style='display:block'>Remove Documents</button>").appendTo($('#controls-plot-documents'));
    this.removeButton.on("click", function () { control.removeButtonClicked(); });
    this.allButton = $("<button style='display:block'>Add Removed Documents</button>").appendTo($('#controls-plot-documents'));
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
      this.removeButton.html('Remove Documents');
      this.parent.update(true);
    }
    else {
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
    var select = '<select name="' + title + '">';

    if(title == 'Radius' || options.length === 0) {
      select += '<option value="uniform">Uniform</option>'; 
    }

    for(var k = 0; k < options.length; k++) {
       select += '<option value="' + options[k] + '">' + options[k] + '</option>';
    }
    select += '<option value="none" disabled>-----Topics-----</option>';
    for (var topic_id in topics)
    {
      var topic_name = topics[topic_id];
      select += '<option value="' + topic_id + '">' +
              topic_name + '</option>';
    }
    select += '</select>';
    select = $(select);
    control.append(select);

    select.on("change", function() { viewer.update(); });
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

  //this creates three separate tables instead of just one
  populateOriginal: function(doc) {
    this.docDisplay.html('</br><h4>' + doc.name + '</h4>');
    var topTopics = this.parent.getTopTopics(doc);
    //TODO Why do we not get shading on alternate table rows?

    //this.docDisplay.append('<h5>Metrics</h5>');

    var table = $('<table class="documents table-stripped" cellpadding="3">').appendTo(this.docDisplay);
    var tableHtml = '<thead><tr><th>Metric</th><th>Value</th></tr></thead>';
    for(var index in this.parent.metrics) {
      var fieldName = this.parent.metrics[index];
      var fieldValue = doc.fields[fieldName];
      tableHtml += '<tr><td valign="top">' + fieldName + '</td>' +
          '<td valign="top">' + this.formatField(fieldValue) + '</td></tr>';
    }
    table.html(tableHtml);

    //this.docDisplay.append('<h5>MetaData</h5>');
    table = $('<table class="documents table-stripped" cellpadding="3">').appendTo(this.docDisplay);
    tableHtml = '<thead><tr><th>Metadata</th><th>Value</th></tr></thead>';
    for(var fieldName in this.parent.metadata) {
      var fieldValue = doc.fields[fieldName];
      tableHtml += '<tr><td valign="top">' + fieldName + '</td>' +
          '<td valign="top">' + fieldValue + '</td></tr>';
    }
    table.html(tableHtml);

    //this.docDisplay.append('<h5>Top 10 Topics</h5>');
    table = $('<table class="documents table-stripped" cellpadding="3">').appendTo(this.docDisplay);
    tableHtml = '<thead><tr><th>Top 10 Topic</th><th>Value</th></tr></thead>';
    for(var index in topTopics) {
      var topic = topTopics[index];
      tableHtml += '<tr><td valign="top">' + topic.name + '</td>' +
          '<td valign="top">' + this.formatField(topic.val) + '</td></tr>';
    }
    table.html(tableHtml);
  },

  //accesses the view via this.parent which is set during view setup
  populate: function(doc) {
    this.docDisplay.html('</br><h4>' + doc.name + '</h4>');
    var topTopics = this.parent.getTopTopics(doc);

    var table = $('<table class="documents table-stripped" cellpadding="3">').appendTo(this.docDisplay);
    var tableHtml = '<tbody align="left" valign="top">';
    tableHtml += '<tr><th>Metric</th><th>Value</th></tr>';
    for(var index in this.parent.metrics) {
      var fieldName = this.parent.metrics[index];
      var fieldValue = doc.fields[fieldName];
      tableHtml += '<tr><td>' + fieldName + '</td>' +
          '<td>' + this.formatField(fieldValue) + '</td></tr>';
    }

    tableHtml += '<tr><th>Metadata</th><th>Value</th></tr>';
    for(var fieldName in this.parent.metadata) {
      var fieldValue = doc.fields[fieldName];
      tableHtml += '<tr><td>' + fieldName + '</td>' +
          '<td>' + fieldValue + '</td></tr>';
    }

    tableHtml += '<tr><th>Top 10 Topics</th><th>Value</th></tr>';
    for(var index in topTopics) {
      var topic = topTopics[index];
      tableHtml += '<tr><td>' + topic.name + '</td>' +
          '<td>' + this.formatField(topic.val) + '</td></tr>';
    }
    tableHtml += '</tbody>';
    table.html(tableHtml);
  },

  formatField: function(n) {
    if(typeof n === 'number') {
      if(n % 1 == 0)
        return String(n);
      else
        return n.toFixed(3);
    }
    else
      return n;
  },

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
  lastAxes : null,
  removingDocs : false,

  defaults: {
    xRange : d3.scale.linear().range([60, 630 - 20]), // x range function, left and right padding
    yRange : d3.scale.linear().range([630 - 60, 30]), // y range function
    rRange : d3.scale.linear().range([5, 15]), // radius range function - ensures the radius is between 5 and 20
    data : null,
    width: 630,
    height: 630,
    margins : {top: 20, right: 20, bottom: 20, left: 60}, // margins around the graph
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
    this.setUpAxes();
    this.setUpLabels();
    this.tooltip = d3.select("body").append("div")
                                    .attr("class", "tooltip")
                                    .style("opacity", 0);
    this.info.parent = this;
  },

  setUpAxes: function() {
    this.xAxis = d3.svg.axis().scale(this.options.xRange).tickSize(10).tickSubdivide(true); // x axis function
    this.yAxis = d3.svg.axis().scale(this.options.yRange).tickSize(10).orient("right").tickSubdivide(true); // y axis function
    // add in the x axis
    this.maing.append("svg:g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + (this.options.height - this.options.margins.bottom - 20) + ")") 
      .call(this.xAxis);

    // add in the y axis
    this.maing.append("svg:g")
      .attr("class", "y axis")
      .call(this.yAxis);

  },

  setUpLabels: function() {
    this.xLabel = this.svg.append("text")
                          .attr("class", "x label").attr("text-anchor", "end")
                          .attr("x", this.options.width - 10).attr("y", this.options.height - 5)
                          .text("X Label");

    this.yLabel = this.svg.append("text")
                          .attr("class", "y label").attr("text-anchor", "start")
                          .attr("x", 5).attr("y", 20)
                          .text("Y Label");

    this.rLabel = this.svg.append("text")
                          .attr("class", "r label").attr("text-anchor", "start")
                          .attr("x", 5).attr("y", this.options.height - 5)
                          .text("Circle Radius: ");

    this.countLabel = this.svg.append("text")
                          .attr("class", "label").attr("text-anchor", "end")
                          .attr("x", this.options.width - 10).attr("y", 20)
                          .text("Doc Count: ");
  },

  filter: function(data, axes, override) {
    if(!override && !this.shouldFilter(axes)) {
      return this.drawingData;
    }
    console.log("filter()");
    var filteredData = Array();
    for (var index in data) {
      var doc = data[index];
      if(this.isDefined(doc, axes))
        filteredData.push(doc);
    }
    return filteredData;
  },

  isDefined: function(doc, axes) {
      return doc.fields[axes.xAxis] && doc.fields[axes.yAxis] &&
         (axes.rAxis == 'uniform' || doc.fields[axes.rAxis]) &&
         (axes.cAxis == 'uniform' || doc.fields[axes.cAxis]) && doc.included;
  },

  //this is an optimization that can be turned off
  shouldFilter: function(newAxes) {
    var lastAxes = this.lastAxes;
    var axes = ['xAxis', 'yAxis', 'rAxis'];

    for(var k = 0; k < axes.length; k++) {
      var axis = axes[k];
      if(lastAxes[axis] != newAxes[axis] && 
        ($.isNumeric(lastAxes[axis]) || $.isNumeric(newAxes[axis])) )
          return true;
    }
    return false;
  },

  shouldUpdate: function(newAxes) {
    var lastAxes = this.lastAxes;
    return lastAxes && 
           lastAxes.xAxis == newAxes.xAxis &&
           lastAxes.yAxis == newAxes.yAxis &&
           lastAxes.rAxis == newAxes.rAxis &&
           lastAxes.cAxis == newAxes.cAxis;
  },

  update: function (override) {
    var axes = this.getAxes();
    if(!override && this.shouldUpdate(axes)) {
      return;
    }
    console.log("update()");
    this.drawingData = this.filter(this.data, axes, override);
    this.lastAxes = axes;

    var documents = this.svg.selectAll("circle").data(this.drawingData, function (doc) { return doc.id;});
    this.setDocEnter(documents, axes);
    this.scaleAxes(axes);
    this.setAxisLabels(axes);
    this.setAxesTransition();
    this.setDocTransition(documents, axes);
    this.setDocExit(documents);
  },

  setDocEnter: function(documents, axes) {
    var xRange = this.options.xRange,
    yRange = this.options.yRange,
    rRange = this.options.rRange,
    info = this.info,
    colors = this.options.colors, 
    nomMaps = this.nomMaps,
    tooltip = this.tooltip,
    viewRef = this;

    documents.enter()
      .insert("svg:circle")
        .attr("cx", function (doc) { return xRange(doc.fields[axes.xAxis]); })
        .attr("cy", function (doc) { return yRange(doc.fields[axes.yAxis]); })
        .style("opacity", 0)
        .style("fill", function(doc) { return colors[nomMaps[axes.cAxis][doc.fields[axes.cAxis]] % colors.length]; })
        //updates the infobox and handles removing documents.
        //TODO: Does this have to be anonymous.  If we define it
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

  },

  setDocTransition: function(documents, axes) {
    var colors = this.options.colors,
    nomMaps = this.nomMaps,
    xRange = this.options.xRange,
    yRange = this.options.yRange,
    rRange = this.options.rRange;

    documents.transition().duration(1500).ease("exp-in-out")
      .style("opacity", 1)
      .style("fill", function(doc) { return colors[nomMaps[axes.cAxis][doc.fields[axes.cAxis]] % colors.length]; })
      //.style("fill", function(doc) { return colors(nomMaps[axes.cAxis][doc.fields[axes.cAxis]]); })
      .attr("r", function(doc) { return (axes.rAxis == 'uniform') ? 7 :rRange(doc.fields[axes.rAxis]); })
      .attr("cx", function (doc) { return xRange(doc.fields[axes.xAxis]); })
      .attr("cy", function (doc) { return yRange(doc.fields[axes.yAxis]); });
  },

  setDocExit: function(documents) {
    documents.exit().transition().duration(1500).ease("exp-in-out")
      .attr("r", 0)
      .style("opacity", 0)
        .remove();

  },


  setAxesTransition: function() {
    var t = this.svg.transition().duration(1500).ease("exp-in-out");
    t.select(".x.axis").call(this.xAxis);
    t.select(".y.axis").call(this.yAxis);
  },

  //Change visual scale to fit the input domains
  scaleAxes: function(axes) {
    this.options.xRange.domain([
      d3.min(this.drawingData, function (doc) { return +doc.fields[axes.xAxis]; }),
      d3.max(this.drawingData, function (doc) { return +doc.fields[axes.xAxis]; })
    ]);
    this.options.yRange.domain([
      d3.min(this.drawingData, function (doc) { return +doc.fields[axes.yAxis]; }),
      d3.max(this.drawingData, function (doc) { return +doc.fields[axes.yAxis]; })
    ]);
    this.options.rRange.domain([
      d3.min(this.drawingData, function (doc) { return +doc.fields[axes.rAxis]; }),
      d3.max(this.drawingData, function (doc) { return +doc.fields[axes.rAxis]; })
    ]);
  },

  //Topics are recognized by a numerical value
  setAxisLabels: function(axes) {
    var x_label = "";
    if($.isNumeric(axes.xAxis))
      x_label = "Topic: " + this.topics[axes.xAxis];
    else
      x_label = axes.xAxis;
    this.xLabel.text("X: " + x_label);

    var y_label = "";
    if($.isNumeric(axes.yAxis))
      y_label = "Topic: " + this.topics[axes.yAxis];
    else
      y_label = axes.yAxis;
    this.yLabel.text("Y: " + y_label);

    var r_label = "";
    if($.isNumeric(axes.rAxis))
      r_label = "Topic: " + this.topics[axes.rAxis];
    else
      r_label = axes.rAxis;
    this.rLabel.text("Circle Radius: " + r_label);

    this.countLabel.text("Doc Count: " + this.drawingData.length);
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
    var documents = server_data.documents;
    this.metrics = server_data.metrics;
    this.metadata = server_data.metadata;
    this.topics = server_data.topics;
    var cont_fields = Array();
    var nom_fields = Array();
    cont_fields = cont_fields.concat(this.metrics);
    for(var field in this.metadata) {
      if(this.metadata[field] == 'int' || this.metadata[field] == 'float')
        cont_fields.push(field);
      else
        nom_fields.push(field);
    }

    this.setUpControls(cont_fields, nom_fields, this.topics);

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
    if (!nom_fields.length) {
        this.nomMaps['uniform'] = 0;
    }
    //console.log(this.nomMaps);
    this.update(true);
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

  getTopTopics: function(doc) {
    var topics = Array();
    for(var index in doc.fields) {
      if($.isNumeric(index))
        topics.push(index);
    }

    topics.sort(
      function (topic_1, topic_2) {
        if(topic_1 == topic_2) {
          return 0;
        }
        else {
          return doc.fields[topic_2] - doc.fields[topic_1];
        }
      });

    var topicResult = Array();
    var numTopTopics = 10;
    for(var k = 0; k < numTopTopics; k++) {
      var topicNum = topics[k];
      var topicName = this.topics[topicNum];
      var topicValue = doc.fields[topicNum];
      var topic = new Object();
      topic.num = topicNum;
      topic.name = topicName;
      topic.val = topicValue;
      topicResult.push(topic);
    }

    return topicResult;
  },

  redraw: function() {

  },


  getAxes: function() {
    var x = $("option:selected", this.controls.xcontrol).val();
    var y = $("option:selected", this.controls.ycontrol).val();
    var r = $("option:selected", this.controls.rcontrol).val();
    var c = $("option:selected", this.controls.ccontrol).val();
    return { xAxis: x, yAxis: y, rAxis: r, cAxis: c };
  },

});

