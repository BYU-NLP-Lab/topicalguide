/*
 * The views on this page are to give a basic framework from which to create visualizations.
 */
var InfoSubView = Backbone.View.extend({
    initialize: function() {
    },
    
    render: function() {
        this.$el.text("Hello World!");
    },
    
    cleanup: function() {
    }
});

var ControlSubView = Backbone.View.extend({
    initialize: function() {
    },
    
    render: function() {
        this.$el.text("Hello World!");
    },
    
    cleanup: function() {
    }
});

var VisualizationSubView = Backbone.View.extend({
    initialize: function() {
    },
    
    render: function() {
        this.$el.text("Hello World!");
    },
    
    cleanup: function() {
    }
});

var MainView = Backbone.View.extend({
    
    name: "main",
    readableName: "Main View",
    
    /*
     * Any needed model event binding should be done in here.
     */
    initialize: function() {
    },
    
    /*
     * Default template just provides containers for the Info, Control, and Visualization sub views.
     */
    template: $("#generic-view-template").html(),
    
    /*
     * Ensures necessary elements are present for the subviews to render.
     * Ensures that the subview instances are created and then rendered.
     */
    render: function() {
        this.$el.html(this.template);
        this.setupViews();
        this.infoSubView.render();
        this.controlSubView.render();
        this.visualizationSubView.render();
    },
    
    /*
     * Ensures that the views have been created and are given their respective elements.
     * 
     * Precondition: The elements with id's visualization-container, control-container, and 
     * info-container must exist.
     */
    setupViews: function() {
        if(!this.infoSubView) {
            this.infoSubView = new InfoSubView({ el: $("#info-container") });
        }
        if(!this.controlSubView) {
            this.controlSubView = new ControlSubView({ el: $("#control-container") });
        }
        if(!this.visualizationSubView) {
            this.visualizationSubView = new VisualizationSubView({ el: $("#visualization-container") });
        }
    },
    
    /*
     * Remove this from any model events this is bound to and call cleanup on any subviews.
     * This is done to prevent memory leaks.
     */
    cleanup: function() {
        if(!this.infoSubView) {
            this.infoSubView.cleanup();
        }
        if(!this.controlSubView) {
            this.controlSubView.cleanup();
        }
        if(!this.visualizationSubView) {
            this.visualizationSubView.cleanup();
        }
    }
    
});
