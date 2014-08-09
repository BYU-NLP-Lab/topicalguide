/*
 * To create a view extend the DefaultView and then call globalViewModel.addViewClass as specified
 * to add the view to the nav bar.
 */

/*
 * The DefaultView acts as an interface for other views to use so the proper methods and attributes
 * are implemented.
 */
var DefaultView = Backbone.View.extend({
    
    // A human readable name for this view.
    readableName: "Default Page",
    
    // A handy loading shortcut.
    loadingTemplate: "<p class=\"text-center\"><img src=\"/site-media/images/large-spinner.gif\"/></p><p class=\"text-center\">Loading...</p>",
    
    /* 
     * It's recommended to use these models in case someone customizes your view.
     * Don't forget to unbind events in the case that the objects are global models 
     * otherwise they will maintain a reference to your view causing it not to get garbage
     * collected (i.e. a memory leak).
     */
    dataModel: globalDataModel,
    selectionModel: globalSelectionModel,
    favsModel: globalFavoritesModel,
    
    /*
     * Any needed model event binding should be done in here.
     */
    initialize: function() {},
    
    /*
     * Render visualization in the given element (i.e. this.el and this.$el).
     * To use d3 try d3.select(this.el).
     */
    render: function() {
        this.$el.html("<p>Welcome to the Default Page. You're seeing this message either because this view is not implemented or this view doesn't exist.</p>");
    },
    
    /*
     * Remove this from any model events this is bound to and call cleanup on any subviews.
     * This is called when the view is being disposed of.
     * This is done to prevent memory leaks.
     * Also, it is really annoying to have a view you just disposed of to jump back onto the screen.
     */
    cleanup: function() {},
    
    /*
     * Return the HTML of the help message desired.
     */
    renderHelpAsHtml: function() {
        return "<p>The creators of this view didn't create a help page for you. "+
               "If it helps any here's some music for you <span class=\"glyphicon glyphicon-music\"></span>.</p>";
    },
    
    /*
     * Convinient function to render an error message in the $el element.
     */
    renderError: function(msg) {
        this.$el.html("<p>Oops, there was a server error: "+msg+"</p>");
    },
});

/*
 * Easy to inject icons, most useful/common is the star icon for marking favorites.
 */
var icons = {
    emptyStar: "<span class=\"glyphicon glyphicon-star-empty gold\"></span>",
    filledStar: "<span class=\"glyphicon glyphicon-star gold\"></span>",
    help: "<span class=\"glyphicon glyphicon-question-sign blue\"></span>",
    settings: "<span class=\"glyphicon glyphicon-cog pewter\"></span>",
};
