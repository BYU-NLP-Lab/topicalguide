"use strict";

var TreemapView = DefaultView.extend({
    
    readableName: "Treemap",
    shortName: "treemap",
    
    redirectTemplate:
'<div class="text-center">'+
'   <button class="treemap-redirect btn btn-default">'+
'       <span class="glyphicon glyphicon-chevron-left pewter"></span> Datasets'+
'   </button>'+
'   <span> You need to select a dataset and analysis before using this view. </span>'+
'</div>',

    baseTemplate:
'TREEEeeeEEEee Map View....',
    
    initialize: function initialize() {
        this.listenTo(this.selectionModel, "change:analysis", this.render);
    },
    
    cleanup: function cleanup() {},
    
    render: function render() {
        if(!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html(this.redirectTemplate);
        } else {
            this.$el.html(this.baseTemplate);
        }
    },
    
    events: {
        "click .treemap-redirect": "clickRedirect",
    },
    
    clickRedirect: function clickRedirect() {
        this.viewModel.set({ currentView: "datasets" });
    },
    
});

addViewClass(["Visualizations"], TreemapView);
