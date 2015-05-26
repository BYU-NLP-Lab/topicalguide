"use strict";

var DEBUG_ROUTER = false;
/*
 * The router ensures that the correct visualization is displayed using Backbone's routing scheme.
 */
var Router = Backbone.Router.extend({
    
    initialize: function(args) {
        // Catches the special case of no fragment path or query string (the root path).
        this.route(/^$/, "rootView");
        // Catches all routes except for the root path.
        this.route(/^([^\\?]*)([\\?](.*))?$/, "changeView");
        
        // Listen to various models.
        this.viewModel = args.viewModel;
        this.selectionModel = args.selectionModel;
        this.tgView = args.tgView; // Used to get the current view's settings.
        this.listenTo(this.viewModel, "change:currentView", this.changeCurrentView);
        this.listenTo(this.viewModel, "change:currentViewInstance", this.changeCurrentViewInstance);
        this.listenTo(this.selectionModel, "change", this.changeSelection);
        this.settingsModel = this.viewModel.get("currentViewInstance").settingsModel;
        if(tg.js.isDefined(this.settingsModel)) { // The view may not exist yet.
            this.listenTo(this.settingsModel, "change", this.changeSettings);
        }
    },
    
    dispose: function() {},
    
    /**
     * Builds the current URL.
     */
    generateURL: function() {
        var settings = "";
        var selection = {};
        
        if(tg.js.isDefined(this.settingsModel)) {
            settings = JSON.stringify(this.tgView.currentView.settingsModel.attributes);
        }
        
        if(tg.js.isDefined(this.selectionModel)) {
            selection = this.selectionModel.getAllSelections();
        }
        
        var hash = _.extend(
            { settings: settings },
            selection
        );
        
        return this.viewModel.getCurrentPath()+"?"+hashToUrl(hash);
    },
    
    /**
     * Called after the current view was changed.
     * Unbinds from the current view's settings events and re-binds to the new views events.
     * Changes the URL and creates a new entry in the site history.
     */
    changeCurrentView: function() {
        if(DEBUG_ROUTER) console.log("Router.changeCurrentView");
        this.navigate(this.generateURL(), { trigger: false, replace: false });
    },
    
    /**
     * Called after the view instance is created.
     * Unbinds from the current view's settings events and re-binds to the new views events.
     */
    changeCurrentViewInstance: function() {
        if(DEBUG_ROUTER) console.log("Router.changeCurrentViewInstance");
        if(tg.js.isDefined(this.settingsModel)) {
            this.stopListening(this.settingsModel);
        }
        this.settingsModel = this.viewModel.get("currentViewInstance").settingsModel;
        if(tg.js.isDefined(this.settingsModel)) {
            this.listenTo(this.settingsModel, "change", this.changeSettings);
        }
    },
    
    /**
     * Called after the selection changes.
     * Changes the URL and creates a new entry in the site history.
     */
    changeSelection: function() {
        if(DEBUG_ROUTER) console.log("Router.changeSelection");
        this.navigate(this.generateURL(), { trigger: false, replace: false });
    },
    
    /**
     * Called after the settings of the current view are changed.
     * Changes the URL and updates the current entry in the site history.
     */
    changeSettings: function() {
        if(DEBUG_ROUTER) console.log("Router.changeSettings");
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
        var settings = {};
        if("settings" in selection) {
            if(selection["settings"] !== "") { // Don't try to parse invalid JSON.
                settings = JSON.parse(selection.settings);
            }
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
