"use strict";

var CirclePackingView = DefaultView.extend({

    readableName: "Circle Packing",
    shortName: "circlepack",

    mainTemplate:
"<div id=\"plot-view-container\" class=\"container-fluid\"></div>" +
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
	console.log(selections);
	var that = this;

	this.dataModel.submitQueryByHash(this.getQueryHash(), function(data) {
	    console.log(data);

	    var analysis = data.datasets[selections.dataset].analyses[selections.analysis];
	    var documents = analysis.documents;

	    var newData = (function() {
		//Create JSON
		var newdata = {};
		newdata.name = "topics";
		newdata.children = [];
		for (var i = 0; i < 100; i++) {
		    var topic = {};
		    topic.name = analysis.topics[i].names["Top 3"];
		    topic.children = [];
		    newdata.children.push(topic);
		}
		for (var doc = 0; doc < documents.length; doc++) {
		    for (var j = 0; j < 100; j++) {
			console.log("document topic amnt: " + documents[doc].topics[j]);
			if (documents[doc].topics[j] > 20) {
			    var docObj = {};
			    docObj.name = documents[doc].key;
			    docObj.size = documents[doc].topics[j]; 
			    newdata.children[j].children.push(docObj);
                        }
		    }
                }
		return newdata;    
	    })();

	    console.log("NEW DATA:");
	    console.log(newData);
	    
	    var margin = 20,
		diameter = 960;

	    var color = d3.scale.linear()
		.domain([-1, 5])
		.range(["hsl(152,80%,80%)", "hsl(228,30%,40%)"])
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

	    d3.json("/static/scripts/visualizations/flare.json", function(error, root) {
		if (error) throw error;

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
	    });

	    d3.select(self.frameElement).style("height", diameter + "px");

	})
    },

    renderHelpAsHtml: function() {
    },
});

addViewClass(["Visualizations"], CirclePackingView);
