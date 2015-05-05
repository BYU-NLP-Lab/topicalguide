var DEBUG_ROUTER = false;
/*
 * The router ensures that the correct visualization is displayed using Backbone's routing scheme.
 */
var Router = Backbone.Router.extend({
    
    initialize: function(args) {
        // Catches all routes except for the root path.
        this.route(/^([^\\?]*)([\\?](.*))?$/, "changeView");
        // Catches the special case of no fragment path or query string (the root path).
        this.route(/^$/, "rootView");
        // Listen to various models.
        this.viewModel = args.viewModel;
        this.selectionModel = args.selectionModel;
        this.tgView = args.tgView; // Used to get the current view's settings.
        this.listenTo(this.viewModel, "change:currentView", this.changeCurrentView);
        this.listenTo(this.selectionModel, "change", this.changeSelection);
        this.settingsModel = this.tgView.currentView.settingsModel;
        if(this.settingsModel !== null && this.settingsModel !== undefined) { // The view may not exist yet.
            this.listenTo(this.settingsModel, "change", this.changeSettings);
        }
    },
    
    dispose: function() {},
    
    /**
     * Builds the current URL.
     */
    generateURL: function() {
        var hash = _.extend(
            { settings: JSON.stringify(this.tgView.currentView.settingsModel.attributes) },
            this.selectionModel.attributes
        );
        return this.viewModel.getCurrentPath()+"?"+hashToUrl(hash);
    },
    
    /**
     * Called after the current view was changed.
     * Unbinds from the current view's settings events and re-binds to the new views events.
     * Changes the URL and creates a new entry in the site history.
     */
    changeCurrentView: function() {
        this.stopListening(this.settingsModel);
        this.settingsModel = this.tgView.currentView.settingsModel;
        this.listenTo(this.settingsModel, "change", this.changeSettings);
        this.navigate(this.generateURL(), { trigger: false, replace: false });
    },
    
    /**
     * Called after the selection changes.
     * Changes the URL and creates a new entry in the site history.
     */
    changeSelection: function() {
        this.navigate(this.generateURL(), { trigger: false, replace: false });
    },
    
    /**
     * Called after the settings of the current view are changed.
     * Changes the URL and updates the current entry in the site history.
     */
    changeSettings: function() {
        this.navigate(this.generateURL(), { trigger: false, replace: true });
    },
    
    /**
     * Called when the site is at the root.
     */
    rootView: function() {
        if(DEBUG_ROUTER) console.log("Router.rootView");
        this.changeView("", "");
    },
    
    /**
     * Called when the site is routed to a different view.
     */
    changeView: function(path, queryString) {
        if(DEBUG_ROUTER) console.log("Router.changeView called with path=\""+path+"\" query=\""+queryString+"\"");
        // Ensure that arguments are in the accepted domain.
        if(path === undefined || path === null) path = ""; // Path cannot be null.
        if(queryString === undefined || queryString === null) queryString = ""; // Make sure queryString is non-null.
        else if(queryString.length > 0 && queryString[0] === "?") queryString = queryString.slice(1); // Chop off the '?'.
        
        if(DEBUG_ROUTER) console.log("Router.changeView end with path=\""+path+"\" query=\""+queryString+"\"");
        
        // Extract the selection and settings.
        var selection = urlToHash(queryString);
        var settings = "";
        if("settings" in selection) {
            settings = JSON.parse(selection.settings);
            delete selection.settings;
        }
        
        // Change the view.
        this.viewModel.changeView(path, settings);
        
        // Update the selection model.
        this.selectionModel.set(selection);
        
        // Update the query string in the URL to show the current selection.
        if(queryString === "") {
            this.navigate(this.generateURL(), { trigger: false, replace: true });
        }
    },
});
