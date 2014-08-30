/*
 * To create a view extend the DefaultView and then call globalViewModel.addViewClass as specified
 * to add the view to the nav bar.
 */

/*
 * The DefaultView acts as an interface for other views to use so the proper methods and attributes
 * are implemented.
 * 
 * It is recommended that you use the listenTo function to bind to model events so it gets cleaned up
 * for you.
 * 
 * It is also recommended that you work fully within the element (el or $el) given to the view.
 */
var DefaultView = function(options) {
    var defaults = {
        "dataModel": globalDataModel,
        "selectionModel": globalSelectionModel,
        "favsModel": new FavoritesModel(),
        "settingsModel": new Backbone.Model(),
    };
    if(options !== undefined) {
        for(key in defaults) {
            if(key in options) {
                defaults[key] = options[key];
            }
        }
    }
    this.self1 = this;
    _.extend(this, defaults);
    Backbone.View.apply(this, arguments);
}

_.extend(DefaultView.prototype, Backbone.View.prototype, {
    
    // A human readable name for this view.
    readableName: "Default Page",
    
    // A handy loading shortcut.
    loadingTemplate: "<p class=\"text-center\"><img src=\"/site-media/images/large-spinner.gif\"/></p><p class=\"text-center\">Loading...</p>",
    
    /*
     * Any needed model event binding should be done in here.
     */
    initialize: function(options) {
        this.self2 = this;
    },
    
    /*
     * Render visualization in the given element (i.e. this.el and this.$el).
     * To use d3 try d3.select(this.el).
     */
    render: function() {
        this.$el.html("<p>Welcome to the Default Page. You're seeing this message either because this view is not implemented, this view doesn't exist, or an error occurred while trying to render the view.</p>");
    },
    
    /*
     * Call dispose on any sub-views and perform any other necessary cleanup operations.
     */
    cleanup: function() {},
    
    /*
     * Removes all events for you and removes the $el from the DOM.
     */
    dispose: function() {
        this.cleanup();
        if(this.dataModel) this.dataModel.off(null, null, this);
        if(this.selectionModel) this.selectionModel.off(null, null, this);
        if(this.favsModel) {
            this.favsModel.off(null, null, this);
            this.favsModel.dispose();
        }
        if(this.settingsModel) this.settingsModel.off(null, null, this);
        this.remove();
        console.log("dispose: "+(this.self1 === this));
    },
    
    /*
     * Return the HTML of the help message desired.
     */
    renderHelpAsHtml: function() {
        return "<p>The creators of this view didn't create a help page for you.</p>";
    },
    
    /*
     * Convenient function to render an error message in the $el element.
     */
    renderError: function(msg) {
        this.$el.html("<p>Oops, there was a server error: "+msg+"</p>");
    },
});
DefaultView.extend = Backbone.View.extend;

/*
 * Easy to inject icons, most useful/common is the star icon for marking favorites.
 */
var icons = {
    emptyStar: "<span class=\"glyphicon glyphicon-star-empty gold\"></span>",
    filledStar: "<span class=\"glyphicon glyphicon-star gold\"></span>",
    help: "<span class=\"glyphicon glyphicon-question-sign blue\"></span>",
    settings: "<span class=\"caret\" style=\"text-size: 1.5em\"></span>",
    share: "<span class=\"glyphicon glyphicon-plus\"></span>",
    document: "<span class=\"glyphicon glyphicon-book brown document\"></span>",
    previous: "<span class=\"glyphicon glyphicon-chevron-left green previous\"></span>",
    next: "<span class=\"glyphicon glyphicon-chevron-right green next\"></span>",
    loading: "<p class=\"text-center\"><img src=\"/site-media/images/large-spinner.gif\"/></p><p class=\"text-center\">Loading...</p>",
};
