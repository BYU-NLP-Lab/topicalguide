"use strict";

var CoOccurrenceView = DefaultView.extend({

  topicData: {},
  cutoff: 100,

  readableName: "Co-Occurrence",
  shortName: "co-occur",

  mainTemplate:
"<div id=\"plot-view\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>" +
"<div id=\"plot-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",

  controlsTemplate:
"<h3><b>Controls</b></h3>" +
"<hr />" +
"<div>" +
"  <label for=\"order-control\">Order</label>" +
"  <select id=\"order-control\" type=\"selection\" class=\"form-control\" name=\"Order\">" +
"    <option value=\"name\">by Name</option>" +
"    <option value=\"count\">by Frequency</option>" +
"    <option value=\"group\">by Cluster</option>" +
"  </select>" +
"</div>",

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

  renderControls: function() {
    var self = this;

    var controls = d3.select(this.el).select('#plot-controls');
    controls.html(self.controlsTemplate);

    //var orderSelector = controls.select('#order-control');

    //orderSelector.on('change', function(value) {
      //change ordering
//  });

  },

  renderChart: function() {
    var self = this;

    var el = d3.select(self.el).select("#plot-view");
    el.select("svg").remove();

    var margin = {top: 145, right: 10, bottom: 145, left: 145},
      width = 800,
      height = 800;

    var x = d3.scale.ordinal().rangeBands([0, width]),
      z = d3.scale.linear().domain([0, 4]).clamp(true),
      c = d3.scale.category10().domain(d3.range(10));

    var svg = el.append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .style("margin-left", margin.left + "px")
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var data = JSON.parse(JSON.stringify(self.topicData));
      var matrix = [],
        nodes = data.nodes,
        n = nodes.length;

      //Compute index per node
      nodes.forEach(function(node, i) {
        node.index = i;
        node.count = 0;
        matrix[i] = d3.range(n).map(function(j) { return {x: j, y: i, z: 0}; });
      });

      //Convert links to matrix; count character occurrences
      data.links.forEach(function(link) {
        matrix[link.source][link.target].z += link.value;
        matrix[link.target][link.source].z += link.value;
        matrix[link.source][link.source].z += link.value;
        matrix[link.target][link.target].z += link.value;
        nodes[link.source].count += link.value;
        nodes[link.target].count += link.value;
      });

      //Precompute the orders
      var orders = {
        name: d3.range(n).sort(function(a, b) { return d3.ascending(nodes[a].name, nodes[b].name); }),
        count: d3.range(n).sort(function(a, b) { return nodes[b].count - nodes[a].count; }),
        group: d3.range(n).sort(function(a, b) { return nodes[b].group - nodes[a].group; })
      };

      //The default sort order
      x.domain(orders.name);

      svg.append("rect")
        .attr("class", "matrix-background")
        .attr("width", width)
        .attr("height", height);

      var row = svg.selectAll(".row")
        .data(matrix)
        .enter().append("g")
        .attr("class", "row")
        .attr("transform", function(d, i) { return "translate(0," + x(i) + ")"; })
        .each(rowfunc);

      row.append("line")
        .attr("x2", width);

      row.append("text")
        .attr("x", -6)
        .attr("y", x.rangeBand() / 5)
        .attr("dy", ".32em")
        .attr("text-anchor", "end")
        .text(function(d, i) { return nodes[i].name; });

      var column = svg.selectAll(".column")
        .data(matrix)
        .enter().append("g")
        .attr("class", "column")
        .attr("transform", function(d, i) { return "translate(" + x(i) + ")rotate(-90)"; });

      column.append("text")
        .attr("class", "top")
        .attr("x", 6)
        .attr("y", x.rangeBand() / 5)
        .attr("dy", ".32em")
        .attr("text-anchor", "start")
        .text(function(d, i) { return nodes[i].name; });

      column.append("text")
        .attr("class", "bottom")
        .attr("x", function(d, i) { return -((d3.selectAll(".row").size() * 8) + 6); })//(number of rows * 8) + 6
        .attr("y", x.rangeBand() / 5)
        .attr("dy", ".32em")
        .attr("text-anchor", "end")
        .text(function(d, i) { return nodes[i].name; });

      function rowfunc(row) {
        var cell = d3.select(this).selectAll(".cell")
          .data(row.filter(function(d) { return d.z; }))
          .enter().append("rect")
          .attr("class", "cell")
          .attr("x", function(d) { return x(d.x); })
          .attr("width", x.rangeBand())
          .attr("height", x.rangeBand())
          .style("fill-opacity", function(d) { return z(d.z); })
          .style("fill", function(d) { return nodes[d.x].group == nodes[d.y].group ? c(nodes[d.x].group) : null; })
          .on("mouseover", mouseover)
          .on("mouseout", mouseout);
      }

      function mouseover(p) {
        d3.selectAll(".row text").classed("active", function(d, i) { return i == p.y; });
        d3.selectAll(".column text").filter(".top").classed("active", function(d, i) { return i == p.x; });
        d3.selectAll(".column text").filter(".bottom").classed("active", function(d, i) { return i == p.x; });
      }

      function mouseout() {
        d3.selectAll("text").classed("active", false);
      }

      d3.select(self.el).select("#plot-controls").select("#order-control").on("change", function() {
        //clearTimeout(timeout);
        order(this.value);
      });

      function order(value) {
        x.domain(orders[value]);

        var t = svg.transition().duration(2500);

        t.selectAll(".row")
          .delay(function(d, i) { return x(i) * 4; })
          .attr("transform", function(d, i) { return "translate(0," + x(i) + ")"; })
          .selectAll(".cell")
          .delay(function(d) { return x(d.x) * 4; })
          .attr("x", function(d) { return x(d.x); });

        t.selectAll(".column")
          .delay(function(d, i) { return x(i) * 4; })
          .attr("transform", function(d, i) { return "translate(" + x(i) + ")rotate(-90)"; });
      }

      //var timeout = setTimeout(function() {
        //order("group");
        //d3.select(self.el)
          //.select("#plot-controls")
          //.select("#order-control")
          //.property("selectedIndex", 2)
          //.node().focus();
      //}, 5000);

  },

  render: function() {
    var self = this;

    this.$el.empty();

    var selections = this.selectionModel.attributes;

    this.dataModel.submitQueryByHash(this.getQueryHash(), function(data) {
      self.$el.html(self.mainTemplate);

      var analysis = data.datasets[selections.dataset].analyses[selections.analysis];
      console.log(analysis);
      var documents = analysis.documents;

      var averageTokenCount = function(docs) {
        var total = 0;
        for (var key in docs) {
          if (docs[key] !== undefined) {
            total += docs[key].metrics["Token Count"];
          }
        }
        var average = total / _.size(docs);
        return average;
      };

      var clusterWords = (function() {
        var allWords = [];
        for (var topic in analysis.topics) {
          if (topic !== undefined) {
            var top4 = analysis.topics[topic].names["Top 4"].split(", ");
            var there = false;
            for (var w in top4) {
              for (var word in allWords) {
                if (allWords[word].name.includes(top4[w]) || top4[w].includes(allWords[word].name)) {
                  allWords[word].value += 1;
                  there = true;
                  if (allWords[word].name.length > top4[w].length) {
                    allWords[word].name = top4[w];
                  }
                  break;
                }
              }
              if (!there) {
                var newWord = {};
                newWord.name = top4[w];
                newWord.value = 1;
                allWords.push(newWord);
              }
              there = false;
            }
          }
        }
        allWords.sort(function(a, b) {
          var keyA = a.value;
          var keyB = b.value;
          if (keyA > keyB) return -1;
          if (keyA < keyB) return 1;
          return 0;
        });
        console.log(allWords);
        return allWords;
      })();	

      var numGroups = 0;
      for (var o = 0; o < clusterWords.length; o++) {
        if (clusterWords[o].value <= 5) {
          numGroups = o - 1;
          break;
        }
      }

      self.topicData = (function() {
        var newdata = {};
        newdata.nodes = [];
        newdata.links = [];
        //Populate nodes
        for (var i = 0; i < _.size(analysis.topics); i++) {
          var topic = {};
          topic.name = analysis.topics[i].names["Top 2"];
          //var assigned = false;
          //for (var grp = 0; grp < numGroups; grp ++) {
          //  if (analysis.topics[i].names["Top 4"].includes(clusterWords[grp].name)) {
          //    topic.group = grp;
          //    assigned = true;
          //    break;
          //  }
          //}
          //if (!assigned) topic.group = numGroups;
          topic.group = 0; 
          newdata.nodes.push(topic);
        }
        //Populate links
        //var cutoff = averageTokenCount(documents) / 25;
        //console.log(cutoff);
        var recentLink = {};
        for (var a = 0; a < _.size(analysis.topics); a++) {
          for (var b = a+1; b < _.size(analysis.topics); b++) {
            for (var key in documents) {
              if (documents[key] !== undefined && documents[key].topics[a] >= self.cutoff 
                  && documents[key].topics[b] >= self.cutoff) {
                if (recentLink !== {} && recentLink.source == b && recentLink.target == a) {
                  newdata.links[newdata.links.length - 1].value += 1;
                }
                else {
                  recentLink = {};
                  recentLink.source = b;
                  recentLink.target = a;
                  recentLink.value = 1;
                  newdata.links.push(recentLink);
                }
              }
            }
          }
        }
        //Normalize by min value
        //var min = newdata.links[0].value;
        //for (var l = 1; l < newdata.links.length; l++) {
        //  if (newdata.links[l].value < min) {
        //    min = newdata.links[l].value;
        //  }
        //}
        //for (var m = 0; m < newdata.links.length; m++) {
        //  newdata.links[m].value = newdata.links[m].value / min;
        //}
        console.log(newdata);
        return newdata; 
      })();

      self.renderControls();
      self.renderChart();
    });
  },

  renderHelpAsHtml: function() {
  }
});

var CoOccurrenceViewManager = DefaultView.extend({

  readableName: "Co-Occurrence",
  shortName: "co-occur",

  mainTemplate:
"<div id=\"plot-view-container\" class=\"container-fluid\" style=\"overflow: hidden;\"></div>" +
"<div id=\"document-info-view-container\" class=\"container-fluid\"></div>",

  initialize: function() {
    this.coOccurrenceView = new CoOccurrenceView(_.extend({}, this.getAllModels()));
  },

  cleanup: function() {
    this.coOccurrenceView.dispose();
  },

  render: function() {
    this.$el.html(this.mainTemplate);
    this.coOccurrenceView.setElement(this.$el.find("#plot-view-container"));
    this.coOccurrenceView.initialize();
    this.coOccurrenceView.render();
  },

  renderHelpAsHtml: function() {
    return this.coOccurrenceView.renderHelpAsHtml();
  },
});

addViewClass(["Visualizations"], CoOccurrenceViewManager);
