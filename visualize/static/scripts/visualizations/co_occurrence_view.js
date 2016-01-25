"use strict";

var CoOccurrenceView = DefaultView.extend({

    topicData: {},

    readableName: "Co-Occurrence",
    shortName: "co-occur",

    mainTemplate:
"<div id=\"plot-view\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>" +
"<div id=\"plot-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",

    controlsTemplate:
"<h3><b>Controls</b></h3>" +
"<hr />" +
"<div>" +
"    <label for=\"order-control\">Order:</label>" +
"    <select id=\"order-control\" type=\"selection\" class=\"form-control\" name=\"Order\">" +
"	<option value=\"name\">by Name</option>" +
"	<option value=\"count\">by Frequency</option>" +
"    </select>" +
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

	var orderSelector = controls.select('#order-control');

	orderSelector.on('change', function(value) {
	    //change ordering
	    });

    },

    renderChart: function() {
    },

    render: function() {
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
