var DEBUG_ROUTER = true;
/*
 * The router ensures that the correct visualization is displayed using Backbone's routing scheme.
 */
var Router = Backbone.Router.extend({
    
    initialize: function(args) {
        // Catches all routes except for the root path.
        this.route(/^([^\\?]*)([\\?](.*))?$/, "changeView");
        // Catches the special case of no fragment path or query string (the root path).
        this.route(/^$/, "rootView");
        // Listen to the view model.
        this.viewModel = args.viewModel;
        this.viewModel.on("changedView", this.listenToNewView, this);
        this.selectionModel = args.selectionModel;
    },
    
    dispose: function() {},
    
    previousQuery: "",
    
    /*
     * Updates the query string in the url bar and sets the history so the back button works.
     */
    updateQueryString: function() {
        if(DEBUG_ROUTER) console.log("Updating query string, replacing in browser history.");
        var hash = _.extend({ settings: JSON.stringify(this.viewModel.currentView.settingsModel) },
            this.viewModel.currentView.selectionModel.attributes);
        this.navigate(this.viewModel.currentPath +"?"+ hashToUrl(hash), {trigger: false, replace: false});
    },
    
    rootView: function() {
        if(DEBUG_ROUTER) console.log("Router.rootView");
        this.changeView("", "");
    },
    
    changeView: function(path, queryString) {
        if(DEBUG_ROUTER) console.log("Router.changeView called with path=\""+path+"\" query=\""+queryString+"\"");
        if(path === undefined || path === null) path = "";
        if(queryString === undefined || queryString === null) queryString = ""; // Make sure queryString is non-null.
        else if(queryString.length > 0) queryString = queryString.slice(1); // Chop off the '?'.
        
        if(queryString === "") {
            // If the query string differs from the selection model attributes query string
            // then replace the url without adding an entry in the browser history.
            this.navigate(path +"?"+ hashToUrl(this.selectionModel.attributes), {trigger: false, replace: true});
        }
        this.previousQuery = queryString;
        if(DEBUG_ROUTER) console.log("Router.changeView end with path=\""+path+"\" query=\""+queryString+"\"");
        var selection = urlToHash(queryString);
        var settings = "";
        if("settings" in selection) {
            settings = JSON.parse(selection.settings);
            delete selection.settings;
        }
        this.viewModel.changeView(path, { selection: selection, settings: settings });
    },
    
    listenToNewView: function() {
        this.stopListening();
        this.listenTo(this.viewModel.currentView.selectionModel, "change", this.updateQueryString);
        this.listenTo(this.viewModel.currentView.settingsModel, "change", this.updateQueryString);
    },
});
