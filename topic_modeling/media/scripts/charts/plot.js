
/** The Controls **/
var PlotControls = ControlsView.extend({
  xcontrol : null, ycontrol : null, rcontrol : null, setUp : false,

  initialize: function (options) {

    ControlsView.prototype.initialize.apply(this, arguments);

    var parent = this.parent = options.parent; // This isn't really a parent, it's the plot-documents main view...

    this.createItems();
    //We will save this for another milestone
    /*
      this.filterButton = this.appendItem("<button style='display:block'>Filter</button>");
      this.filterButton.on("click", function() { parent.filterButtonClicked(); });
    */
  },

  createItems: function() {

    var control = this;

    this.xcontrol = this.appendItem('<div id="plot-document-x-control" class="plot-document-controls"></div>');
    this.ycontrol = this.appendItem('<div id="plot-document-y-control" class="plot-document-controls"></div>');
    this.rcontrol = this.appendItem('<div id="plot-document-r-control" class="plot-document-controls"></div>');
    this.ccontrol = this.appendItem('<div id="plot-document-c-control" class="plot-document-controls"></div>');

    var removeLabel = this.appendItem("</br><h4>Remove Documents</h4>");
    this.removeButton = this.appendItem("<button style='display:block'>Remove Documents</button>");
    this.removeButton.on("click", function () { control.removeButtonClicked(); });

    this.allButton = this.appendItem("<button style='display:block'>Add Removed Documents</button>");
    this.allButton.on("click", function () { control.allButtonClicked(); });

    this.saveButton = this.appendItem("<button style='display:block'>Save</button>");
    this.saveButton.on("click", function () { control.saveButtonClicked(); });

    this.hiddenSvgForm = this.appendItem('<form id="svg_export_form" method="POST" style="display:none;visibility:hidden">' +
                                         ' <input type="hidden" name="svg" /> </form>');
  },

  //note that this does not get any css for the svg.  It must all be put inline
  saveButtonClicked: function() {
    //console.log("save button clicked");
    var viewDom = document.getElementById("plot-documents");
    var svg = viewDom.getElementsByTagName("svg")[0];
    var contents = viewDom.innerHTML;

    var url = 'http://' + document.location.host + '/save-svg/';
    //console.log(url);

    $('#svg_export_form > input[name=svg]').val(contents);
    $('#svg_export_form').attr('action', url);
    $('#svg_export_form').submit();
  },

  allButtonClicked: function () {
    this.parent.includeAllDocuments();
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
      //these pre selected options work well for state of the union
      $("option:eq(4)", this.xcontrol).attr('selected', true);
      //$("option:eq(7)", this.ycontrol).attr('selected', true);
      $("option:eq(1)", this.ccontrol).attr('selected', true);
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
    if(topics)
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
    ControlsView.prototype.show.call(this, arguments);
  },

  hide: function () {
    ControlsView.prototype.hide.apply(this, arguments);
  }
});


/** The Menus **/
var PlotMenu = Backbone.View.extend({

  initialize: function (options) {
    var parent = this.parent = options.parent;
    // setup elements. The el is #menu-[name]
  },

  show: function () { this.$el.show(); },

  hide: function () { this.$el.hide(); },
});

/** The Info **/
var PlotInfo = InfoView.extend({

  initialize: function () {

    InfoView.prototype.initialize.apply(this, arguments);

    var detailsbutton = this.appendItem('</br><a href="#" class="btn btn-primary btn-small view-details-btn">View Document Details</a>');
    var contents = this.appendItem('<div class="contents"></div>');
    
    this.docDisplay = this.$('>.contents');
  },

  clear: function () { },

  //this creates three separate tables instead of just one
  populateOriginal: function(doc) {
    this.docDisplay.html('</br><h4>' + doc.name + '</h4>');
    var topTopics = this.parent.getTopTopics(doc);
    //TODO Why do we not get shading on alternate table rows?

    //this.docDisplay.append('<h5>Metrics</h5>');

    var table = $('<table class="documents table-striped" cellpadding="3">').appendTo(this.docDisplay);
    var tableHtml = '<thead><tr><th>Metric</th><th>Value</th></tr></thead>';
    for(var index in this.parent.metrics) {
      var fieldName = this.parent.metrics[index];
      var fieldValue = doc.fields[fieldName];
      tableHtml += '<tr><td valign="top">' + fieldName + '</td>' +
          '<td valign="top">' + this.formatField(fieldValue) + '</td></tr>';
    }
    table.html(tableHtml);

    //this.docDisplay.append('<h5>MetaData</h5>');
    table = $('<table class="documents table-striped" cellpadding="3">').appendTo(this.docDisplay);
    tableHtml = '<thead><tr><th>Metadata</th><th>Value</th></tr></thead>';
    for(var fieldName in this.parent.metadata) {
      var fieldValue = doc.fields[fieldName];
      tableHtml += '<tr><td valign="top">' + fieldName + '</td>' +
          '<td valign="top">' + fieldValue + '</td></tr>';
    }
    table.html(tableHtml);

    //this.docDisplay.append('<h5>Top 10 Topics</h5>');
    table = $('<table class="documents table-striped" cellpadding="3">').appendTo(this.docDisplay);
    tableHtml = '<thead><tr><th>Top 10 Topic</th><th>Value</th></tr></thead>';
    for(var index in topTopics) {
      var topic = topTopics[index];
      tableHtml += '<tr><td valign="top">' + topic.name + '</td>' +
          '<td valign="top">' + this.formatField(topic.val) + '</td></tr>';
    }
    table.html(tableHtml);
    this.$el.show();
  },

  //accesses the view via this.parent which is set during view setup
  populate: function(doc) {
    this.docDisplay.html('</br><h4>' + doc.name + '</h4>');
    var details_url = location.href.split('/').slice(0,-1).join('/') + '/documents/' + doc.id;
    this.preload_popover(details_url);
    var topTopics = this.parent.getTopTopics(doc);

    var table = $('<table class="documents table-striped" cellpadding="3">').appendTo(this.docDisplay);
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
    this.$el.show();
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
 *             extending the "defaults" dict *   info:     the info object *   menu:     the menu object *   controls: the controls object * * **/
var PlotViewer = MainView.add(VisualizationView, {
  name: 'plot-documents',
  title: '2D Plots',
  menu_class: PlotMenu,
  info_class: PlotInfo,
  controls_class: PlotControls,
  
  /** any defaults that you want. In the class, this.options will be populated
   * with these defaults + an options dictionary passed in when the object is
   * initialized **/
  setUpProperties: function () {
    this.lastAxes = null;
    this.removingDocs = false;
    this.width = this.base_defaults.width;
    this.height = this.base_defaults.height;
    this.margins = {left : (this.width / 12), // for y tick labels 
                    bottom : (this.height / 10), // for x axis tick labels, and x/r axis labels
                    top : (this.height / 18), // for y axis label and doc count
                    right : (this.width / 30)}; // so circles centers don't land on the border
    // x range function, left and right padding
    this.xRange = d3.scale.linear().range([this.margins.left, this.width - this.margins.right]);
    // y range function
    this.yRange = d3.scale.linear().range([this.height - this.margins.bottom, this.margins.top]);
    this.rMax =  Math.round(this.width / 47);
    this.rMin =  Math.round((this.rMax / 3));
    this.rUniform = this.rMin + Math.round(0.3 * (this.rMax - this.rMin));
    this.rRange = d3.scale.linear().range([this.rMin, this.rMax]); // radius range function - ensures the radius is a certain range
    this.data = null;
    this.topLabelSpacing = Math.round(this.height / 32);
    this.xAxisMargin = Math.round(this.height / 13);
    this.tickLength = Math.round(this.width / 63);
    this.colors = [ "#000000", "#FFFF00", "#800080", "#FFA500", "#ADD8E6", "#CD0000", "#F5DEB3", "#A9A9A9", "#228B22",
      "#FF00FF", "#0000CD", "#F4A460", "#EE82EE", "#FF4500", "#191970", "#ADFF2F", "#A52A2A", "#808000", "#DB7093",
      "#F08080", "#8A2B2E", "#7FFFD4", "#FF0000", "#00FF00", "#008000", ];
    this.fontSize = $('body').css('font-size');
    //console.log(this);
    _.bindAll(this, "resize");
    this.event_aggregator.bind("resize", this.resize);

  },

  defaults: {
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
    //this rect is for svg saving
    //console.log("setup()");
    var tmp = $("#plot-documents rect");
    tmp.attr("fill", "white");
    this.setUpProperties();
    this.setUpAxes();
    this.setUpLabels();
    this.tooltip = d3.select("body").append("div")
                                    .attr("class", "tooltip")
                                    .style("opacity", 0);
    this.populateFilter();
    this.info.parent = this;
  },

  //TODO: finish
  setUpFilter: function(data) {
    //console.log('setUpFilter()');
    //console.log(data);
    this.metrics = data.metrics;
    this.metadata = data.metadata;
    this.topics = data.topics;

    var fields = Array();
    fields = fields.concat(this.metrics);
    for(var field in this.metadata) {
      fields.push(field);
    }

    this.filterDialog = $('<div id=#plot-document-filter-dialog title="Document Filter" ></div>');
    var addFilter = $("<button style='display:block'>Add Filter</button>").appendTo(this.filterDialog);
    var self = this;
    addFilter.on("click", function() { self.addFilter(); });
  },

  addFilter: function() {
    //console.log("addFilter()");

  },

  populateFilter: function() {
    //var url = 'http://' + document.location.host + '/feeds/document-metrics/datasets...';
    //hard coded url for now
    //console.log("popluateFilter");
    //var url = '/feeds/document-plot-filter/datasets/state_of_the_union/analyses/lda100topics';
    var url = '/feeds/document-plot-filter' + location.pathname.split('/').slice(0, -1).join('/');
    var self = this;
    $.ajax({
      method: 'GET',
      url: url,
      }).done(function (data) { self.setUpFilter(data) });
  },

  setUpAxes: function() {
    this.xAxis = d3.svg.axis().scale(this.xRange).tickSize(this.tickLength).tickSubdivide(true); // x axis function
    this.yAxis = d3.svg.axis().scale(this.yRange).tickSize(this.tickLength).orient("right").tickSubdivide(true); // y axis function
    // add in the x axis
    this.maing.append("svg:g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + (this.height - this.xAxisMargin) + ")") 
      .call(this.xAxis);

    // add in the y axis
    this.maing.append("svg:g")
      .attr("class", "y axis")
      .call(this.yAxis);
    
    //these are for svg saving to include the css inline
    $('.axis path').attr("opacity", 0);
    $('.axis text').attr("fill", "#000000");
    //$('.axis .tick').attr("style", "stroke:#000000; opacity:1");
  },

  setUpLabels: function() {
    this.xLabel = this.svg.append("text")
                          .attr("class", "x label").attr("text-anchor", "end")
                          .attr("x", this.width - 10).attr("y", this.height - 5)
                          .text("X Label").attr('font-size', this.fontSize);

    this.yLabel = this.svg.append("text")
                          .attr("class", "y label").attr("text-anchor", "start")
                          .attr("x", 5).attr("y", this.topLabelSpacing)
                          .text("Y Label").attr('font-size', this.fontSize);

    this.rLabel = this.svg.append("text")
                          .attr("class", "r label").attr("text-anchor", "start")
                          .attr("x", 5).attr("y", this.height - 5)
                          .text("Circle Radius: ").attr('font-size', this.fontSize);

    this.countLabel = this.svg.append("text")
                          .attr("class", "label").attr("text-anchor", "end")
                          .attr("x", this.width - 10).attr("y", this.topLabelSpacing)
                          .text("Doc Count: ").attr('font-size', this.fontSize);
  },

  scaleRanges: function() {    // x range function, left and right padding
    this.xRange = d3.scale.linear().range([this.margins.left, this.width - this.margins.right]);
    // y range function
    this.yRange = d3.scale.linear().range([this.height - this.margins.bottom, this.margins.top]);
    this.rMax =  Math.round(this.width / 47);
    this.rMin =  Math.round((this.rMax / 3));
    this.rUniform = this.rMin + Math.round(0.3 * (this.rMax - this.rMin));
    this.rRange = d3.scale.linear().range([this.rMin, this.rMax]); // radius range function - ensures the radius is a certain range

    this.xAxis.scale(this.xRange);
    this.yAxis.scale(this.yRange);
  },

  filterData: function(data, axes, override) {
    if(!override && !this.shouldFilter(axes)) {
      return this.drawingData;
    }
    //console.log("filter()");
    var filteredData = Array();
    for (var index in data) {
      var doc = data[index];
      if(this.shouldDisplay(doc, axes))
        filteredData.push(doc);
    }
    return filteredData;
  },

  //if a document should be displayed under these axes
  //TODO: Allow a user to filter out documents 1% for topics
  shouldDisplay: function(doc, axes) {
      return doc.included &&
         doc.fields[axes.xAxis] && doc.fields[axes.yAxis] &&
         (axes.rAxis == 'uniform' || doc.fields[axes.rAxis]) &&
         doc.fields[axes.cAxis];
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
           lastAxes.xAxis == newAxes.xAxis && lastAxes.yAxis == newAxes.yAxis &&
           lastAxes.rAxis == newAxes.rAxis && lastAxes.cAxis == newAxes.cAxis;
  },

  update: function (override) {
    var axes = this.getAxes();
    if(!override && this.shouldUpdate(axes)) {
      return;
    }
    //console.log("update()");
    this.drawingData = this.filterData(this.data, axes, override);
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
    var xRange = this.xRange,
    yRange = this.yRange,
    rRange = this.rRange,
    info = this.info,
    colors = this.colors, 
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
        //TODO: Does this have to be anonymous?
        .on("click", this.getDocClickHandler())
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

  getDocClickHandler: function() {
    var viewRef = this;
    return function (doc) {
             if(viewRef.removingDocs) {
               viewRef.tooltip.transition().duration(200).style("opacity", 0.0);
               $(this).remove();
               doc.included = false;
             }
             else
               viewRef.info.populate(doc);
           };
  },

  setDocTransition: function(documents, axes) {
    var colors = this.colors,
    nomMaps = this.nomMaps,
    xRange = this.xRange,
    yRange = this.yRange,
    rRange = this.rRange,
    rUniform = this.rUniform;

    //transiting is not working in firefox now... but it still works in chrome...
    documents.transition().duration(1500)
      .style("opacity", 1)
      .style("fill", function(doc) { return colors[nomMaps[axes.cAxis][doc.fields[axes.cAxis]] % colors.length]; })
      .attr("r", function(doc) { return (axes.rAxis == 'uniform') ? rUniform :rRange(doc.fields[axes.rAxis]); })
      .attr("cx", function (doc) { return xRange(doc.fields[axes.xAxis]); })
      .attr("cy", function (doc) { return yRange(doc.fields[axes.yAxis]); });
  },

  setDocExit: function(documents) {
    documents.exit().transition().duration(1500)
      .attr("r", 0)
      .style("opacity", 0)
        .remove();
  },

  setAxesTransition: function() {
    var t = this.svg.transition().duration(1500);
    t.select(".x.axis").call(this.xAxis);
    t.select(".y.axis").call(this.yAxis);

    // Translate x axis in case the whole visualization moves
    var xAxisEl = $('#plot-documents .x.axis');
    var translate = this.parseTransformAttr(xAxisEl.attr("transform")).translate;
    $({ transform : translate[1] }).animate({ transform : this.height - this.xAxisMargin }, // Magical jQuery attribute animation
                                            { duration : 1500,
                                              step : function(now) {
                                                xAxisEl.attr("transform", "translate(" + translate[0] + "," + now + ")");
                                              }
                                            });

    //this makes the css inline for saving the svg
    $('.axis .tick').attr("style", "stroke:#000000; opacity:1");
    $('.axis text').css("font-size", this.fontSize);
  },

  //Change visual scale to fit the input domains
  scaleAxes: function(axes) {
    this.xRange.domain([
      d3.min(this.drawingData, function (doc) { return +doc.fields[axes.xAxis]; }),
      d3.max(this.drawingData, function (doc) { return +doc.fields[axes.xAxis]; })
    ]);
    this.yRange.domain([
      d3.min(this.drawingData, function (doc) { return +doc.fields[axes.yAxis]; }),
      d3.max(this.drawingData, function (doc) { return +doc.fields[axes.yAxis]; })
    ]);
    this.rRange.domain([
      d3.min(this.drawingData, function (doc) { return +doc.fields[axes.rAxis]; }),
      d3.max(this.drawingData, function (doc) { return +doc.fields[axes.rAxis]; })
    ]);
  },

  //Topics are recognized by a numerical value
  setAxisLabels: function(axes) {
    this.xLabel.text("X: " + this.getName(axes.xAxis));
    this.yLabel.text("Y: " + this.getName(axes.yAxis));
    this.rLabel.text("Circle Radius: " + this.getName(axes.rAxis));
    this.countLabel.text("Doc Count: " + this.drawingData.length);
  },

  getName: function(axisOption) {
    if($.isNumeric(axisOption))
      return this.topics[axisOption];
    else
      return axisOption;
  },

  filterServerData: function(popup) {
    //console.log("filterServerData()");

    var postFilters = this.getSelectedFilters();
    //console.log(postFilters);
    var url = this.url();
    var self = this;
    $.ajax({
      url : url,
      method: "POST",
      data: postFilters,
    }).done(function (data) { self.load(data); $(popup).dialog("close"); } );
  },

  getSelectedFilters: function() {
    return new Object();
  },

  filterButtonClicked: function() {
    // console.log("Filter Button Clicked");
    var self = this;
    this.filterDialog.dialog({
      buttons: [
        {
          text: "Filter",
          click: function() {
            self.filterServerData(this);
            $(this).dialog("close");
          }
        },
        {
          text: "Cancel",
          click: function() { $(this).dialog("close"); }
        }
      ]
    });
    this.filterDialog.dialog("open");
  },

  /** populate everything! data is the JSON response from your url(). For
   * information on the return values of specific urls, look at the docs for
   * the function (probably in topic_modeling/visualize/topics/ajax.py)
   *
   * NOTE: this data is cached in localStorage unless you click "refresh" at
   * the bottom of the right-hand bar
   */
  load: function (server_data) {
    //console.log(server_data);
    var documents = server_data.documents;

    this.metrics = server_data.metrics;
    this.metadata = server_data.metadata;
    this.topics = server_data.topics;
    var cont_fields = Array();
    var nom_fields = Array();
    cont_fields = cont_fields.concat(this.metrics);
    for(var field in this.metadata) {
      if(field == 'year' || this.metadata[field] == 'int' || this.metadata[field] == 'float')
        cont_fields.push(field);
      else
        nom_fields.push(field);
    }

    this.controls.setUpControls(cont_fields, nom_fields, this.topics, this);

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
    this.setUpNomMap(this.data, nom_fields);

    //console.log(this.nomMaps);
    this.update(true);
  },

  //this maps the nominal field values to an index in the color array
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

  //returns the Top topics of a document 
  getTopTopics: function(doc) {
    var topics = Array();
    for(var index in doc.fields) {
      if($.isNumeric(index))
        topics.push(index);
    }

    //sort topics by document composition
    topics.sort(function (topic_1, topic_2) { return doc.fields[topic_2] - doc.fields[topic_1]; });

    var topicResult = Array();
    var numTopTopics = 10;
    for(var k = 0; k < numTopTopics; k++) {
      var topic = new Object();
      topic.num = topics[k];
      topic.name = this.topics[topic.num];
      topic.val = doc.fields[topic.num];
      topicResult.push(topic);
    }
    return topicResult;
  },

  redraw: function() { },

  resize: function(options) {
    VisualizationView.prototype.resize.call(this, options);

    this.scaleRanges();
    this.update(true);
  },

  getAxes: function() {
    var x = $("option:selected", this.controls.xcontrol).val();
    var y = $("option:selected", this.controls.ycontrol).val();
    var r = $("option:selected", this.controls.rcontrol).val();
    var c = $("option:selected", this.controls.ccontrol).val();
    return { xAxis: x, yAxis: y, rAxis: r, cAxis: c };
  },
    
  includeAllDocuments: function() {
    for(doc_id in this.data)
    {
      var doc = this.data[doc_id];
      doc.included = true;
    }
    this.update(true);
    this.removingDocs = false;
  }

});

