"use strict";

var CirclePackingView = DefaultView.extend({

  totalData: {},
  percentageData: {},
  displayData: {},
  topicArray: [],
  numTopics: 1,
  numTokens: 1,
  calcTotal: true,

  readableName: "Top Topics",
  shortName: "circlepack",

  mainTemplate:
"<div id=\"plot-view\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>" +
"<div id=\"plot-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",

  controlsTemplate:
"<h3><b>Controls</b></h3>"+
"<hr />"+
"<div>"+
"  <label for=\"top-n-control\">Number of Topics</label>"+
"  <select id=\"top-n-control\" type=\"selection\" class=\"form-control\" name=\"Number of Topics\"></select>"+
"</div>"+
"<div>"+
"  <label for=\"document-token-control\">Document Token Requirement</label>"+
"  <select id=\"document-token-control\" type=\"selection\" class=\"form-control\" name=\"Document Token Requirement\"></select>"+
"</div>"+
"<hr />"+
"<div>"+
"  <label for=\"calculation-control\">Top Topics Calculation Method</label>"+
"  <div id=\"calculation-control\" class=\"onoffswitch\">"+
"    <input type=\"checkbox\" name=\"onoffswitch\" class=\"onoffswitch-checkbox\" id=\"myonoffswitch\" checked>"+
"    <label class=\"onoffswitch-label\" for=\"myonoffswitch\">"+
"      <span class=\"onoffswitch-inner\"></span>"+
"      <span class=\"onoffswitch-switch\"></span>"+
"    </label>"+
"  </div>"+
"</div>",


  initialize: function() {
    this.numTopics = 20;
    this.numTokens = 50;
    this.topicArray = [];
    for (var i = 1; i <= 100; i++) {
      this.topicArray.push(i);
    }
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

    var topicSelector = controls.select('#top-n-control');
    var tokenSelector = controls.select('#document-token-control');

    var topicOptions = topicSelector
      .selectAll('option')
      .data(self.topicArray)
      .enter()
      .append('option')
      .attr('value', function(d) { return d; })
      .text(function(d) { return d; });

    var tokenOptions = tokenSelector
      .selectAll('option')
      .data(self.topicArray)
      .enter()
      .append('option')
      .attr('value', function(d) { return d; })
      .text(function(d) { return d; });

    topicOptions[0][self.numTopics-1].selected = true;
    tokenOptions[0][self.numTokens-1].selected = true;

    topicSelector.on('change', function (value) {
      var selectedIndex = topicSelector.property('selectedIndex');
      self.numTopics = selectedIndex + 1;
      self.alterDisplayData(self.numTopics, self.numTokens, self.calcTotal);
    });

    tokenSelector.on('change', function (value) {
      var selectedIndex = tokenSelector.property('selectedIndex');
      self.numTokens = selectedIndex + 1;
      self.alterDisplayData(self.numTopics, self.numTokens, self.calcTotal);
    });

    d3.select(this.el).select('#calculation-control')
      .on("click", function onCalculationChange() {
        self.calcTotal = document.getElementById('myonoffswitch').checked;
        self.alterDisplayData(self.numTopics, self.numTokens, self.calcTotal);
      });	
  },

  alterDisplayData: function(topics, tokens, total) {
    var self = this;
    self.displayData = {};
    if (total) {
      self.displayData = (function() {
        var displaydata = {};
        displaydata.name = "topics";
        displaydata.children = [];
        var limit = Math.min(self.totalData.children.length, topics);
        for (var i = 0; i < limit; i++) {
          displaydata.children.push(JSON.parse(JSON.stringify(self.totalData.children[i])));
        }
        for (var j = 0; j < displaydata.children.length; j++) {
        //Delete documents with too small of token amounts
          for (var k = 0; k < displaydata.children[j].children.length; k++) {
            if (displaydata.children[j].children[k].size < tokens) {
              displaydata.children[j].children.splice(k, 1);
              k--;
            }
          }
        }
        return displaydata;
      })();
    } else {
      self.displayData = (function() {
        var displaydata = {};
        displaydata.name = "topics";
        displaydata.children = [];
        var limit = Math.min(self.percentageData.children.length, topics);
        for (var i = 0; i < limit; i++) {
          displaydata.children.push(JSON.parse(JSON.stringify(self.percentageData.children[i])));
        }
        for (var j = 0; j < displaydata.children.length; j++) {
          //Delete documents with too small of token amounts
          for (var k = 0; k < displaydata.children[j].children.length; k++) {
            if (displaydata.children[j].children[k].size < tokens) {
              displaydata.children[j].children.splice(k, 1);
              k--;
            }
          }
        }
        return displaydata;
      })();
    }
    self.renderChart();
  },


  renderChart: function() {
    var self = this;

    var el = d3.select(self.el).select("#plot-view");
    el.select("svg").remove();

    var margin = 20,
      diameter = 960;

    var color = d3.scale.linear()
      .domain([-1, 5])//original values: -1, 5
      .range(["hsl(152,80%,80%)", "hsl(228,30%,40%)"])//original values: hsl(152,80%,80%), hsl(228,30%,40%)
      .interpolate(d3.interpolateHcl);

    var pack = d3.layout.pack()
      .padding(2)
      .size([diameter - margin, diameter - margin])
      .value(function(d) { return d.size; })

    var svg = el.append("svg")
      .attr("width", diameter)
      .attr("height", diameter)
      .append("g")
      .attr("transform", "translate(" + diameter / 2 + "," + diameter / 2 + ")");

    var root = JSON.parse(JSON.stringify(self.displayData));

    var focus = root,
      nodes = pack.nodes(root),
      view;

    var circle = svg.selectAll("circle")
      .data(nodes)
      .enter().append("circle")
      .attr("class", function(d) { return d.parent ? d.children ? "node" : "node node--leaf" : "node node--root"; })
      .style("fill", function(d) { return d.children ? color(d.depth) : "WHITE"; })
      .on("click", function(d) { 
        if (!d.children) {
          onDocumentClick(d.name, 0);
        }
        else {
          if (focus !== d) {
            zoom(d), d3.event.stopPropagation();
          }
        }
      });

    var text = svg.selectAll("text")
      .data(nodes)
      .enter().append("text")
      .attr("class", "label")
      .style("fill-opacity", function(d) { return d.parent === root ? 1 : 0; })
      .style("display", function(d) { return d.parent === root ? null : "none"; })
      .text(function(d) { 
        var title = "";
        if (d.position) { title += (d.position.toString() + ": "); }
        title += d.name;
        return title; });

    var node = svg.selectAll("circle,text");

    el.style("background", color(-10));

    zoomTo([root.x, root.y, root.r * 2 + margin]);

    function zoom(d) {
      var focus0 = focus; focus = d;

      var leaves = document.getElementsByClassName("node--leaf");
      for (var i in leaves) {
        if (leaves[i].style !== undefined) {
          if (d.parent === root) { leaves[i].style.pointerEvents = "auto"; }
          else { leaves[i].style.pointerEvents = ""; }
        }
      }		

      var transition = d3.transition()
        .duration(d3.event.altKey ? 7500 : 750)
        .tween("zoom", function(d) {
          var i = d3.interpolateZoom(view, [focus.x, focus.y, focus.r * 2 + margin]);
          return function(t) { zoomTo(i(t)); };
        });

      transition.selectAll("text")
        .filter(function(d) {
          if (d === undefined) {
            return false;
          } else {
            return d.parent === focus || this.style.display === "inline";
          }
        })
        .style("fill-opacity", function(d) { return d.parent === focus ? 1 : 0; })
        .each("start", function(d) { if (d.parent === focus) this.style.display = "inline"; })
        .each("end", function(d) { if (d.parent !== focus) this.style.display = "none"; });
    }

    function zoomTo(v) {
      var k = diameter / v[2]; view = v;
      node.attr("transform", function(d) { return "translate(" + (d.x - v[0]) * k + "," + (d.y - v[1]) * k + ")"; });
      circle.attr("r", function(d) { return d.r * k; });
    }

    function onDocumentClick(d, i) {
      if (self.settingsModel.attributes.removing) {
        self.removedDocuments[d.key] = true;
        d3.select(this).transition()
          .duration(duration)
          .attr("r", 0);
      } else {
        self.selectionModel.set({ document: d });
      }
    };

    d3.select(self.frameElement).style("height", diameter + "px");
  },

  render: function() {
    var self = this;

    this.$el.empty();
    if (!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
      this.$el.html("<p>You should select a <a href=\"#datasets\">dataset and analysis</a> before proceeding.</p>");
      return;
    }
    d3.select(this.el).html(this.loadingTemplate);		

    var selections = this.selectionModel.attributes;

    this.dataModel.submitQueryByHash(this.getQueryHash(), function(data) {
      self.$el.html(self.mainTemplate);	    

      var analysis = data.datasets[selections.dataset].analyses[selections.analysis];
      var documents = analysis.documents;

      console.log(documents);

      //Populate totalData with all topic info
      self.totalData = (function() {
        var newdata = {};
        newdata.name = "topics";
        newdata.children = [];
        for (var i = 0; i < 100; i++) {
          var topic = {};
          topic.name = analysis.topics[i].names["Top 2"];
          topic.children = [];
          topic.total = "";
          newdata.children.push(topic);
        }
        for (var key in documents) {
          for (var j = 0; j < 100; j++) {
            if (documents[key] !== undefined && documents[key].topics[j] !== undefined) {
              var docObj = {};
              docObj.name = key;
              docObj.size = documents[key].topics[j]; 
              newdata.children[j].children.push(docObj);
            }
          }
        }
        return newdata;
      })();

      //Populate percentageData with all topic info
      self.percentageData = (function() {
        var newdata = {};
        newdata.name = "topics";
        newdata.children = [];
        for (var i = 0; i < 100; i++) {
          var topic = {};
          topic.name = analysis.topics[i].names["Top 2"];
          topic.children = [];
          topic.total = "";
          topic.percentage = 0;
          newdata.children.push(topic);
        }
        for (var key in documents) {
          for (var j = 0; j < 100; j++) {
            if (documents[key] !== undefined && documents[key].topics[j] !== undefined) {
              var docObj = {};
              docObj.name = key;
              docObj.size = documents[key].topics[j];
              newdata.children[j].children.push(docObj);
              newdata.children[j].percentage += (docObj.size / documents[key].metrics["Token Count"]);
            }
          }
        }
        for (var k = 0; k < 100; k++) {
          newdata.children[k].percentage = newdata.children[k].percentage / Object.keys(documents).length;
          newdata.children[k].total = (newdata.children[k].percentage).toString() + "%";//add rounding here
        }
        return newdata;
      })();

      //Sort totalData by top topic
      self.totalData.children.sort(function(a, b) {
        var keyA = 0;
        var keyB = 0;
        for (var i = 0; i < a.children.length; i++) {
          keyA += a.children[i].size;
        }
        for (var j = 0; j < b.children.length; j++) {
          keyB += b.children[j].size;
        }
        if (keyA > keyB) return -1;
        if (keyA < keyB) return 1;
        return 0;
      });

      //Sort percentageData by top topic (average percentage)
      self.percentageData.children.sort(function(a, b) {
        var keyA = a.percentage;
        var keyB = b.percentage;
        if (keyA > keyB) return -1;
        if (keyA < keyB) return 1;
        return 0;
      });

      //Assign values to topics for display
      for (var t = 0; t < self.totalData.children.length; t++) {
        var tot = 0;
        for (var d = 0; d < self.totalData.children[t].children.length; d++) {
          tot += self.totalData.children[t].children[d].size;
        }
        self.totalData.children[t].total = tot.toString();
        self.totalData.children[t].position = t + 1;
      }

      for (var p = 0; p < self.percentageData.children.length; p++) {
        self.percentageData.children[p].position = p + 1;
      }

      self.renderControls();
      self.alterDisplayData(self.numTopics, self.numTokens, self.calcTotal)
    })	
  },

  renderHelpAsHtml: function() {
    return "<p>Note that the larger circles represent the top topics and the small, white circles represent documents with the top number of tokens associated with that topic.</p>"+
    "<h4>Number of Topics</h4>"+
    "<p>Changing this number will change the number of topics displayed. The topics shown will always be the most common topics, based on the choice of calculation.</p>"+
    "<h4>Document Token Requirement</h4>"+
    "<p>This number represents how many tokens (words) in a document must be associated with the given topic in order for the document to be included in the topic circle. Increasing this number will decrease the number of documents shown in the topic, and decreasing this number will increase the number of documents shown.</p>"+
    "<h4>Top Topics Calculation Method</h4>"+
    "<p>When this is set to \"Total Tokens,\" the top topics will be calculated by how many tokens (words) in the entire dataset are associated with each topic. When it is set to \"Average Percentage,\" the top topics will be calculated by finding the average makeup of that topic per document over all documents.<p>";
  },
});

var CirclePackingViewManager = DefaultView.extend({

  readableName: "Top Topics",
  shortName: "circlepack",

  mainTemplate:
"<div id=\"plot-view-container\" class=\"container-fluid\" style=\"overflow: hidden;\"></div>" +
"<div id=\"document-info-view-container\" class=\"container-fluid\"></div>",

  initialize: function() {
    this.circlePackingView = new CirclePackingView(_.extend({}, this.getAllModels()));
    this.documentInfoView = new SingleDocumentView(_.extend({}, this.getAllModels()));
  },

  cleanup: function() {	
    this.circlePackingView.dispose();
    this.documentInfoView.dispose();
  },

  render: function() {
    this.$el.html(this.mainTemplate);
    this.circlePackingView.setElement(this.$el.find("#plot-view-container"));
    this.documentInfoView.setElement(this.$el.find("#document-info-view-container"));
    this.circlePackingView.initialize();
    this.circlePackingView.render();
    this.documentInfoView.render();
  },

  renderHelpAsHtml: function() {
    return this.circlePackingView.renderHelpAsHtml();
  },
});

addViewClass(["Visualizations"], CirclePackingViewManager);
