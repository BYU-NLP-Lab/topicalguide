"use strict";

var CirclePackingView = DefaultView.extend({

    readableName: "Top Topics",
    shortName: "circlepack",

    mainTemplate:
"<div id=\"plot-view\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>" +
"<div id=\"plot-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",

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

	this.$el.empty();

	if (!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
	    this.$el.html("<p>You should select a <a href=\"#datasets\">dataset and analysis</a> before proceeding.</p>");
	    return;
	}

        var selections = this.selectionModel.attributes;
	console.log(selections);
	var that = this;

	this.dataModel.submitQueryByHash(this.getQueryHash(), function(data) {

	    var analysis = data.datasets[selections.dataset].analyses[selections.analysis];
	    var documents = analysis.documents;

	    //Create object with all data
	    var newData = (function() {
		var newdata = {};
		newdata.name = "topics";
		newdata.children = [];
		for (var i = 0; i < 100; i++) {
		    var topic = {};
		    topic.name = analysis.topics[i].names["Top 3"];
		    topic.children = [];
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

	    //Sort object by top topic
	    newData.children.sort(function(a, b) {
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

	    //Get actual data to display
	    var displayData = (function() {
		var displaydata = {};
		displaydata.name = "topics";
		displaydata.children = [];
		var limit = Math.min(newData.children.length, 20);//TODO substitute controller amount
		for (var i = 0; i < limit; i++) {
		    displaydata.children.push(newData.children[i]);
		}
		for (var j = 0; j < displaydata.children.length; j++) {
		    //Delete documents with too small of token amounts
		    for (var k = 0; k < displaydata.children[j].children.length; k++) {
		        if (displaydata.children[j].children[k].size < 50) { //TODO substitute controller amount
			    displaydata.children[j].children.splice(k, 1);
			    k--;
			}	
		    }
		}
		return displaydata;
	    })();
	    
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

	    var svg = d3.select(that.el).append("svg")
		.attr("width", diameter)
		.attr("height", diameter)
	      .append("g")
		.attr("transform", "translate(" + diameter / 2 + "," + diameter / 2 + ")");

	    var root = JSON.parse(JSON.stringify(displayData));

		var focus = root,
		    nodes = pack.nodes(root),
		    view;
		
		var circle = svg.selectAll("circle")
		    .data(nodes)
		  .enter().append("circle")
		    .attr("class", function(d) { return d.parent ? d.children ? "node" : "node node--leaf" : "node node--root"; })
		    .style("fill", function(d) { return d.children ? color(d.depth) : null; })
		    .on("click", function(d) { if (focus !== d) zoom(d), d3.event.stopPropagation(); });

		var text = svg.selectAll("text")
		    .data(nodes)
		  .enter().append("text")
		    .attr("class", "label")
		    .style("fill-opacity", function(d) { return d.parent === root ? 1 : 0; })
		    .style("display", function(d) { return d.parent === root ? null : "none"; })
		    .text(function(d) { return d.name; });

		var node = svg.selectAll("circle,text");

		d3.select(that.el)
		    .style("background", color(-10))
		    .on("click", function() { zoom(root); });

		zoomTo([root.x, root.y, root.r * 2 + margin]);

		function zoom(d) {
		    var focus0 = focus; focus = d;

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
		    if (that.settingsModel.attributes.removing) {
			that.removedDocuments[d.key] = true;
			d3.select(this).transition()
			    .duration(duration)
			    .attr("r", 0);
		    } else {
			that.selectionModel.set({ document: d.key });
		    }
		};

	    d3.select(self.frameElement).style("height", diameter + "px");

	})
    },

    renderHelpAsHtml: function() {
    },
});

var CirclePackingViewManager = DefaultView.extend({

	readableName: "Top Topics",
	shortName: "circlepack",

	mainTemplate:
"<div id=\"plot-view-container\" class=\"container-fluid\"></div>" +
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
	    this.circlePackingView.render();
	    this.documentInfoView.render();
	},

	renderHelpAsHtml: function() {
	    return this.circlePackingView.renderHelpAsHtml();
	},
});

addViewClass(["Visualizations"], CirclePackingViewManager);
