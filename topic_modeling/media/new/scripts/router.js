/*
 * The code on this page is responsible for updating the navigation and views, ensuring that 
 * url fragments are routed correctly.
 */

/*
 * Parse url arguments to a hash.
 */
function urlToHash(args) {
    var hash = {};
    var items = args.split('&');
    if(items[0] !== "") {
        for(i=0; i<items.length; i++) {
            var keyAndValue = items[i].split('=');
            if(keyAndValue[1]===undefined) keyAndValue.push("")
            hash[unescape(keyAndValue[0])] = unescape(keyAndValue[1]);
        }
    }
    return hash;
}

/*
 * Convert a hash to url arguments.
 */
function hashToUrl(hash) {
    var items = [];
    _.forOwn(hash, function(value, key) {
        items.push(escape(key) + '=' + escape(value));
    });
    return items.join('&');
}


/*
 * The DefaultView acts as an interface for other views to use so the proper methods and attributes
 * are implemented.
 */
var DefaultView = Backbone.View.extend({
    
    // A human readable name for this view.
    readableName: "Default Page",
    
    /*
     * Any needed model event binding should be done in here.
     */
    initialize: function() {},
    
    /*
     * Render visualization to the given element.
     */
    render: function() {
        this.$el.html("<p>Welcome to the Default Page</p>");
    },
    
    /*
     * Remove this from any model events this is bound to and call cleanup on any subviews.
     * This is done to prevent memory leaks.
     */
    cleanup: function() {}
});

/*
 * The LoadingView will display a loading symbol when the information you're waiting for is loading.
 * Once the query is fulfilled, your renderLoaded function is called with the data requested.
 */
var LoadingView = Backbone.View.extend({
    
    readableName: "Loading View",
    
    mainQuery: function() {
        return "api?datasets=*&analyses=*&dataset_attr=metadata,metrics&analysis_attr=metdata,metrics";
    },
    
    initialize: function(args) {
        if("mainQuery" in args) {
            this.mainQuery = args.mainQuery;
        }
        var hash = {};
        hash[this.mainQuery] = "unloaded";
        globalDataModel.set(hash);
        globalDataModel.on("change:"+this.mainQuery, this.render, this);
    },
    
    render: function() {
        this.renderAction(globalDataModel.get(this.mainQuery));
    },
    
    // The view argument is the DatasetView object. Because "this" refers to the renderAction object.
    renderAction:function(status){
        if(status === "loading") {
            this.$el.html("<p>Loading...</p>");
        } else if(status === "unloaded") {
            this.$el.html("<p>Making request for data...</p>");
            globalDataModel.requestData(this.mainQuery);
        } else if(status === "loaded") {
            this.renderLoaded(globalDataModel.getData(this.mainQuery));
        } else if(status === "error") {
            this.$el.html("<p>An error was encountered with your request.</p");
        } else {
            this.$el.html("<p>Unknown status encountered: "+status+"</p");
        }
    },
    
    renderLoaded: function(data) {
        this.$el.html("<p>Override the \"renderLoaded\" function to use your loaded data: "+JSON.stringify(data)+"</p");
    },
    
    cleanup: function() {
        globalDataModel.off(null, this.render, this);
    }
    
});

var DEBUG_VIEWMODEL = false;
/*
 * The ViewModel is responsible for tracking which view is selected. This is primarily used with
 * the visualizations page where views are being swapped.
 * Bindable events include currentView, addedView, removedView.
 */
var ViewModel = Backbone.Model.extend({
    
    initialize: function() {
        this.currentView = new DefaultView({ el: $("#main-container") });
    },
    
    rootViewClass: DefaultView,
    currentView: null,
    currentPath: "",
    paths: {},
    navigation: {},
    settings: {},
    
    /*
     * Change the view to the one specified. No-op if the name doesn't exist.
     * Store the view name in sessionStorage.lastViewName.
     * 
     * name - Unique identifier for the view.
     * settings - Non-null hash containing the settings for the view. The hash may be empty.
     * 
     * TODO post settings to the settings model
     */
    changeView: function(path, settings) {
        if(DEBUG_VIEWMODEL) console.log("ViewModel.changeView path=\""+path+"\" settings=\""+hashToUrl(settings)+"\"");
        
        this.currentView.cleanup();
        if(path === "")
            this.currentView = new this.rootViewClass({ el: $("#main-container") });
        else if(path in this.paths)
            this.currentView = new this.paths[path].viewClass({ el: $("#main-container") });
        else
            this.currentView = new DefaultView({ el: $("#main-container") });
        this.currentView.render();
        this.currentPath = path;
        this.set({currentView: path }); // alert listeners that the property has changed
        globalSelectionModel.set(settings); // alert any views that the selection has changed
    },
    
    /*
     * Set the root view to the given class.
     */
    setRootViewClass: function(rootClass) {
        this.rootViewClass = rootClass;
    },
    
    /*
     * Add a view. Will not override another existing view.
     * 
     * readablePath - An array with human readable names that will be used to create the route
     *                and update the navigation object.
     * view - The view class from which the view can be constructed.
     *        Must have render(settings) and cleanup() functions defined.
     *        Must have name and readableName variables defined on prototype.
     */
    addViewClass: function(readablePath, viewClass) {
        // The readable name will become part of the path
        readablePath.push(viewClass.prototype.readableName);
        
        // Create url path from readable path and store class.
        var pathList = [];
        _(readablePath).forEach(function(menuItem) {
            pathList.push(escape(menuItem));
        });
        var path = pathList.join("/");
        
        // Check for already existent path.
        if(path in this.paths)
            console.log("Cannot add a path that already exists.");
        
        // Create navigation path.
        var menu = this.navigation;
        for(i=0; i < readablePath.length; i++) {
            var name = readablePath[i];
            if(name in menu) {
                var item = menu[name];
                if(i == (readablePath.length-1)) {
                    if(item.menu) {
                        console.log("Cannot turn existing menu into a link.");
                        return;
                    } else {
                        console.log("Cannot squash an existing link with a new link.");
                        return;
                    }
                } else {
                    if(item.menu) {
                        menu = item.items;
                    } else {
                        console.log("Cannot turn existing link into a menu.");
                        return;
                    }
                }
            } else {
                if(i == (readablePath.length-1)) {
                    menu[name] = {menu: false, path:path};
                } else {
                    menu[name] = {menu: true, items: {}};
                    menu = menu[name].items;
                }
            }
        }
        
        // Add the new path.
        this.paths[path] = {
            readablePath: readablePath,
            viewClass: viewClass
        };
        
        this.set({ addedView: path });
        if(DEBUG_VIEWMODEL) console.log("ViewModel.addViewClass path=\""+path+"\"");
    },
    
    addSettingsClass: function(settingsClass) {
        this.settings[settingsClass.prototype.readableName] = settingsClass;
    },
});
var globalViewModel = new ViewModel();


/*
 * The NavigationView is responsible for updating the navigation bar to reflect the appropriate selection.
 */
var NavigationView = Backbone.View.extend({
    // initialize must be called after the body is ready so the element is present
    initialize: function() {
        this.render();
        globalViewModel.on("change:currentView", this.render, this);
        globalViewModel.on("change:addedView", this.render, this);
        globalViewModel.on("change:removedView", this.render, this);
    },
    
    template: $("#main-nav-template").html(),
    compiledItemTemplate: _.template($("#main-nav-item-template").html()),
    compiledDropdownTemplate: _.template($("#main-nav-dropdown-template").html()),
    compiledSettingsTemplate: _.template($("#main-nav-settings-template").html()),
    
    /*
     * Renders the navigation bar according to what views are available in the globalViewModel.
     */
    render: function() {
        this.$el.html(this.template);
        
        // render the rest of the navigation bar
        var menu = globalViewModel.navigation;
        var bar = this.$el.find("#main-nav-bar");
        this.renderMenu(bar, menu, true);
        
        // render the settings dropdown
        bar.parent().append(this.compiledSettingsTemplate({}));
        var settingsMenu = bar.parent().find("#main-nav-settings");
        var settings = globalViewModel.settings;
        for(name in settings) {
            settingsMenu.append("<li><a>"+name+"</a></li>");
        }
        
        
        return this;
    },
    
    // Helper function for rendering menus.
    // Return true if an item is the current selection; false otherwise.
    renderMenu: function(bar, menu, isTopMenu) {
        var isSelected = false;
        for(key in menu) {
            if(!menu[key].menu) { // Found a leaf node.
                var isActive = false;
                if(menu[key].path === globalViewModel.currentPath) {
                    isActive = isSelected = true;
                }
                bar.append(this.compiledItemTemplate({ "active": isActive, "href": "#"+menu[key].path, "name": key }));
            } else { // Found a menu.
                bar.append("<li></li>");
                var lastItem = bar.children("li").last();
                if(isTopMenu) {
                    lastItem.addClass("dropdown");
                } else {
                    lastItem.addClass("dropdown-submenu");
                }
                
                lastItem.html(this.compiledDropdownTemplate({ "name": key, "isTopMenu": isTopMenu}));
                var subBar = lastItem.children("ul").last();
                if(this.renderMenu(subBar, menu[key].items, false))
                    lastItem.addClass("active");
            }
        }
        return isSelected;
    }
});


var DEBUG_ROUTER = false;
/*
 * The router ensures that the correct visualization is displayed using Backbone's routing scheme.
 */
var Router = Backbone.Router.extend({
    
    initialize: function() {
        this.route(/^([^\\?]*)([\\?](.*))?$/, "changeView");
        this.route(/^$/, "rootView");
    },
    
    rootView: function() {
        if(DEBUG_ROUTER) console.log("Router.rootView");
        this.changeView("", "");
    },
    
    changeView: function(path, queryString) {
        if(queryString===undefined || queryString===null) queryString = "";
        else if(queryString.length > 0) queryString = queryString.slice(1);
        if(DEBUG_ROUTER) console.log("Router.changeView called with path=\""+path+"\" query=\""+queryString+"\"");
        globalViewModel.changeView(path, urlToHash(queryString));
    },
});


// Execution begins once the page is loaded.
// The views need some page elements that must be loaded in order to work.
var router;
var navView;
$(document).ready(function() {
    for(key in localStorage) {
        if(key.slice(0,3) == "api") {
            delete localStorage[key];
        }
    }
    navView = new NavigationView({ el: $("#main-nav") });
    router = new Router();
    Backbone.history.start();
});
