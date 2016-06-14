"use strict";

var CirclePackingView = DefaultView.extend({

  //Global variables
  totalData: {},
  percentageData: {},
  displayData: {},
  topicArray: [],
  documentArray: [],
  numTopics: 1,
  numDocuments: 1,
  calcTotal: true,

  //View names
  readableName: "Top Topics", //This will be displayed on the "Visualizations" dropdown menu
  shortName: "circlepack",

  //HTML templates
  mainTemplate:
"<div id=\"plot-controls-circles\" class=\"col-xs-3 text-center\" style=\"float: right;\"></div>" +
"<div id=\"plot-view-circles\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>",

  controlsTemplate:
"<h3><b>Controls</b></h3>"+
"<hr />"+
"<div>"+
"  <label for=\"top-n-control\">Number of Topics</label>"+
"  <select id=\"top-n-control\" type=\"selection\" class=\"form-control\" name=\"Number of Topics\"></select>"+
"</div>"+
"<div>"+
"  <label for=\"document-control\">Documents Displayed Per Topic</label>"+
"  <select id=\"document-control\" type=\"selection\" class=\"form-control\" name=\"Documents Displayed Per Topic\"></select>"+
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

  //Initializes control values
  initialize: function() {
    this.numTopics = 20; //Found this to be a reasonable number for most datasets
    this.numDocuments = 10; //Found this to be a reasonable number for most datasets
  },

  //Don't know the purpose of this; just put it here because it is in all other visualizations
  cleanup: function() {
  },

  //Returns data from analysis; copied from other visualizations
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

  //Sets up and renders controls
  renderControls: function() {
    var self = this;

    var controls = d3.select(this.el).select('#plot-controls-circles');
    controls.html(self.controlsTemplate);	

    var topicSelector = controls.select('#top-n-control');
    var documentSelector = controls.select('#document-control');

    //Populates "Number of Topics" control dropdown with integers from 1 to the number of topics via topicArray
    var topicOptions = topicSelector
      .selectAll('option')
      .data(self.topicArray)
      .enter()
      .append('option')
      .attr('value', function(d) { return d; })
      .text(function(d) { return d; });

    //Populates "Documents Displayed Per Topic" control dropdown with integers from 1 to the number of documents via documentArray
    var documentOptions = documentSelector
      .selectAll('option')
      .data(self.documentArray)
      .enter()
      .append('option')
      .attr('value', function(d) { return d; })
      .text(function(d) { return d; });

    //Sets original control values to numTopics and numDocuments
    topicOptions[0][self.numTopics-1].selected = true;
    documentOptions[0][self.numDocuments-1].selected = true;

    //Sets up behavior of controls
    topicSelector.on('change', function (value) {
      var selectedIndex = topicSelector.property('selectedIndex');
      self.numTopics = selectedIndex + 1;
      self.alterDisplayData(self.numTopics, self.numDocuments, self.calcTotal);
    });

    documentSelector.on('change', function (value) {
      var selectedIndex = documentSelector.property('selectedIndex');
      self.numDocuments = selectedIndex + 1;
      self.alterDisplayData(self.numTopics, self.numDocuments, self.calcTotal);
    });

    d3.select(this.el).select('#calculation-control')
      .on("click", function onCalculationChange() {
        self.calcTotal = document.getElementById('myonoffswitch').checked;
        self.alterDisplayData(self.numTopics, self.numDocuments, self.calcTotal);
      });	
  },

  //Changes what displayData contains based on control values
  alterDisplayData: function(topics, docs, total) {
    var self = this;
    self.displayData = {};
    if (total) { //Populates displayData with totalData
      self.displayData = (function() {
        var displaydata = {};
        displaydata.name = "topics";
        displaydata.children = [];
        var limit = Math.min(self.totalData.children.length, topics);
        for (var i = 0; i < limit; i++) {
          displaydata.children.push(JSON.parse(JSON.stringify(self.totalData.children[i])));
        }
        for (var j = 0; j < displaydata.children.length; j++) {
          //Delete documents 
          displaydata.children[j].children.splice(docs, displaydata.children[j].children.length);
        }
        return displaydata;
      })();
    } else { //Populates displayData with percentageData
      self.displayData = (function() {
        var displaydata = {};
        displaydata.name = "topics";
        displaydata.children = [];
        var limit = Math.min(self.percentageData.children.length, topics);
        for (var i = 0; i < limit; i++) {
          displaydata.children.push(JSON.parse(JSON.stringify(self.percentageData.children[i])));
        }
        for (var j = 0; j < displaydata.children.length; j++) {
          //Delete documents
          displaydata.children[j].children.splice(docs, displaydata.children[j].children.length);
        }
        return displaydata;
      })();
    }
    self.renderChart();
  },

  //Renders the chart with displayData (code largely borrowed from d3 example) 
  renderChart: function() {
    var self = this;

    var el = d3.select(self.el).select("#plot-view-circles");
    el.select("svg").remove(); //Remove previous renderings

    var margin = 20,
      diameter = 960;

    var color = d3.scale.linear()
      .domain([-1, 5])//original values: -1, 5
      .range(["hsl(152,80%,80%)", "hsl(228,30%,40%)"])
      .interpolate(d3.interpolateHcl);

    var pack = d3.layout.pack()
      .padding(2)
      .size([diameter - margin, diameter - margin])
      .value(function(d) { return d.size / d.topicProminence; }); //Alter this function to change sizes of document circles

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
          else if (d.parent) {
            zoom(d.parent), d3.event.stopPropagation();
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
        //if (d.position) { title += (d.position.toString() + ": "); } //Uncomment this to see topic's real positions on visualization
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

  //Gets initial data and renders chart and controls 
  render: function() {
    var self = this;

    this.$el.empty();
    if (!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
      this.$el.html("<p>You should select a <a href=\"#datasets\">dataset and analysis</a> before proceeding.</p>");
      return;
    }
    d3.select(this.el).html(this.loadingTemplate);		

    var selections = this.selectionModel.attributes;

    //Gets topic info from server and creates objects from data
    this.dataModel.submitQueryByHash(this.getQueryHash(), function(data) {
      self.$el.html(self.mainTemplate);	    

      var analysis = data.datasets[selections.dataset].analyses[selections.analysis];
      var documents = analysis.documents;
      
      //Initializes topicArray and documentArray with numbers of topics and documents
      var topicCounter = 1;
      for (var key in analysis.topics) {
        self.topicArray.push(topicCounter)
        topicCounter++;
      }
      var documentCounter = 1;
      for (var key in documents) {
        self.documentArray.push(documentCounter)
        documentCounter++;
      }

      //Populate totalData with all topic info
      self.totalData = (function() {
        var newdata = {};
        newdata.name = "topics";
        newdata.children = [];
        for (var i = 0; i < Object.keys(analysis.topics).length; i++) {
          var topic = {};
          topic.name = analysis.topics[i].names["Top 2"];
          topic.children = [];
          topic.total = 0;
          newdata.children.push(topic);
        }
        for (var key in documents) {
          for (var j = 0; j < Object.keys(analysis.topics).length; j++) {
            if (documents[key] !== undefined && documents[key].topics[j] !== undefined) {
              var docObj = {};
              docObj.name = key;
              docObj.size = documents[key].topics[j];
              docObj.topicProminence = 0 
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
        for (var i = 0; i < Object.keys(analysis.topics).length; i++) {
          var topic = {};
          topic.name = analysis.topics[i].names["Top 2"];
          topic.children = [];
          topic.total = 0;
          topic.percentage = 0;
          newdata.children.push(topic);
        }
        for (var key in documents) {
          for (var j = 0; j < Object.keys(analysis.topics).length; j++) {
            if (documents[key] !== undefined && documents[key].topics[j] !== undefined) {
              var docObj = {};
              docObj.name = key;
              docObj.size = (documents[key].topics[j] / documents[key].metrics["Token Count"]) * 100;
              docObj.topicProminence = 0
              newdata.children[j].children.push(docObj);
              newdata.children[j].percentage += docObj.size / 100;
            }
          }
        }
        for (var k = 0; k < Object.keys(newdata.children).length; k++) {
          newdata.children[k].percentage = newdata.children[k].percentage / Object.keys(documents).length;
          newdata.children[k].total = newdata.children[k].percentage;
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

      //Sort documents within each topic by topic tokens or topic percentage
      for (var td = 0; td < self.totalData.children.length; td++) {
        self.totalData.children[td].children.sort(function(a, b) {
          var keyA = a.size;
          var keyB = b.size;
          if (keyA > keyB) return -1;
          if (keyA < keyB) return 1;
          return 0;
        });
      }
      for (var pd = 0; pd < self.percentageData.children.length; pd++) {
        self.percentageData.children[pd].children.sort(function(a, b) {
          var keyA = a.size;
          var keyB = b.size;
          if (keyA > keyB) return -1;
          if (keyA < keyB) return 1;
          return 0;
        });
      } 

      //Assign values to topics
      for (var t = 0; t < self.totalData.children.length; t++) {
        var tot = 0;
        for (var d = 0; d < self.totalData.children[t].children.length; d++) {
          tot += self.totalData.children[t].children[d].size;
          self.totalData.children[t].children[d].topicProminence = t + 1;
        }
        self.totalData.children[t].total = tot;
        self.totalData.children[t].position = t + 1;
      }

      for (var p = 0; p < self.percentageData.children.length; p++) {
        self.percentageData.children[p].position = p + 1;
        for (var c = 0; c < self.percentageData.children[p].children.length; c++) {
          self.percentageData.children[p].children[c].topicProminence = p + 1; 
        }
      }

      self.renderControls();
      self.alterDisplayData(self.numTopics, self.numDocuments, self.calcTotal)
    })	
  },

  //Returns HTML for instructions
  renderHelpAsHtml: function() {
    return "<p>Note that the larger circles represent the top topics and the small, white circles represent documents with the top number of tokens associated with that topic.</p>"+
    "<h4>Number of Topics</h4>"+
    "<p>Changing this number will change the number of topics displayed. The topics shown will always be the most common topics, based on the choice of calculation.</p>"+
    "<h4>Documents Displayed Per Topic</h4>"+
    "<p>This number represents how many documents (white cirlces) will be displayed per topic. The documents displayed will always be the documents with the top number of tokens associated with that topic.</p>"+
    "<h4>Top Topics Calculation Method</h4>"+
    "<p>When this is set to \"Total Tokens,\" the top topics will be calculated by how many tokens (words) in the entire dataset are associated with each topic. When it is set to \"Average Percentage,\" the top topics will be calculated by finding the average makeup of that topic per document over all documents.<p>";
  }
});

//Wrapper class; contains CirclePackingView and SingleDocumentView
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
