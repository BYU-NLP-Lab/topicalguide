"use strict";

var NewView = DefaultView.extend({
    
    readableName: "Hello",
    shortName: "hello",
    
    mainTemplate: 
"<div id=\"plot-view-container\" class=\"container-fluid\"></div>"+
"<div id=\"document-info-view-container\" class=\"container-fluid\"></div>",
    
    initialize: function() {
    },
    
    cleanup: function() {
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
      var selections = this.selectionModel.attributes;
      console.log(selections)
	
      var that = this;
      this.dataModel.submitQueryByHash(this.getQueryHash(), function(data) {
        console.log(data)
	var margin = {top: 20, right: 20, bottom: 30, left: 50},
    width = 960 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;

var parseDate = d3.time.format("%d-%b-%y").parse;

var x = d3.time.scale()
    .range([0, width]);

var y = d3.scale.linear()
    .range([height, 0]);

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

var line = d3.svg.line()
    .x(function(d) { return x(d.date); })
    .y(function(d) { return y(d.close); });

var svg = d3.select(that.el).append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

d3.tsv("data.tsv", function(error, data) {
  if (error) throw error;

  data.forEach(function(d) {
    d.date = parseDate(d.date);
    d.close = +d.close;
  });

  x.domain(d3.extent(data, function(d) { return d.date; }));
  y.domain(d3.extent(data, function(d) { return d.close; }));

  svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

  svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("Price ($)");

  svg.append("path")
      .datum(data)
      .attr("class", "line")
      .attr("d", line);
      })
    },
    
    renderHelpAsHtml: function() {
    },
});

addViewClass(["Visualizations"], NewView);
