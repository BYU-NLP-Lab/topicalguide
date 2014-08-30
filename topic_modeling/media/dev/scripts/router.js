/*
 * The code on this page is responsible for updating the navigation and views, ensuring that 
 * url fragments are routed correctly and the nav bar stays up-to-date.
 */

var DEBUG_VIEWMODEL = false;
/*
 * The ViewModel is responsible for tracking which view is selected. This is primarily used with
 * the visualizations page where views are being swapped.
 * Bindable events include currentView, addedView, removedView, addedSettings.
 */
var ViewModel = Backbone.Model.extend({
    
    initialize: function() {
        $("#main-container").append("<div id=\"main-view-container\"></div>");
        this.currentView = new DefaultView({ el: $("#main-view-container") });
        this.helpView = new DefaultView({ el: $("#main-nav-help-modal") });
        this.settingsView = new DefaultView({ el: $("#main-nav-settings-modal") });
        this.favsView = new DefaultView();
    },
    
    rootViewClass: DefaultView,
    currentView: null,
    paths: {},
    navigation: {},
    currentPath: "",
    helpViewClass: null,
    helpView: null,
    favsViewClass: null,
    favsView: null,
    settingsView: null,
    settings: {},
    
    /*
     * Change the view to the one specified. No-op if the name doesn't exist.
     * Store the view name in sessionStorage.lastViewName.
     * 
     * path - Unique path for the view.
     * settings - Non-null hash containing the settings for the view. The hash may be empty.
     * Return nothing.
     */
    changeView: function(path, settings) {
        if(DEBUG_VIEWMODEL) console.log("ViewModel.changeView path=\""+path+"\" settings=\""+hashToUrl(settings)+"\"");
        var defaults = {
            selection: {},
            settings: {},
        };
        settings = _.extend(defaults, settings);
        
        this.currentView.dispose();
        
        path = path.toLowerCase();
        this.currentPath = path; // Must go before the settings are set as the router listens for changes to update the url.
        globalSelectionModel.set(settings.selection); // alert any views that the selection has changed
        
        //
        $("#main-container").append("<div id=\"main-view-container\"></div>");
        var settingsModel = new Backbone.Model();
        settingsModel.set(settings.settings);
        var init = {
            el: $("#main-view-container"),
            settingsModel: settingsModel,
        };
        if(path === "")
            this.currentView = new this.rootViewClass(init);
        else if(path in this.paths)
            this.currentView = new this.paths[path].viewClass(init);
        else
            this.currentView = new DefaultView(init);
        
        
        try {
            this.currentView.render();
        } catch(err) {
            console.log("The following error occurred while trying to render the view: " + err);
        }
        
        
        // Change page title.
        $("head").find("title").html("Topical Guide &mdash; "+this.currentView.readableName);
        this.trigger("changeView");
    },
    
    /*
     * Change the settings view to the one specified.
     * Return nothing.
     */
    changeSettingsView: function(readableName) {
        this.settingsView.dispose();
        if(readableName in this.settings) {
            this.settingsView = new this.settings[readableName]({ el: $("#main-nav-settings-modal") });
        } else {
            this.settingsView = new DefaultView({ el: $("#main-nav-settings-modal") });
        }
        this.settingsView.render();
    },
    
    /*
     * Set the root view to the given class.
     * Return nothing.
     */
    setRootViewClass: function(rootClass) {
        this.rootViewClass = rootClass;
    },
    
    /*
     * Add a view. Will not override another existing view.
     * 
     * readablePath - An array with human readable names that will be used to create the route
     *                and update the navigation bar.
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
            pathList.push(encodeURIComponent(menuItem.replace(/ /g, "_")));
        });
        var path = pathList.join("/").toLowerCase();
        if(DEBUG_VIEWMODEL) console.log("Path: " + path);
        
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
        
        if(DEBUG_VIEWMODEL) console.log("ViewModel.addViewClass path=\""+path+"\"");
        this.trigger("addedView");
    },
    
    /*
     * Add a settings view.
     * settingsClass - A class inheriting from default.
     */
    addSettingsClass: function(settingsClass) {
        this.settings[settingsClass.prototype.readableName] = settingsClass;
        this.trigger("addedSettings");
    },
    
    /*
     * Set the help view class. 
     * Warning: only set after the DOM is loaded.
     */
    setHelpViewClass: function(helpViewClass) {
        this.helpViewClass = helpViewClass;
        this.helpView.dispose();
        this.helpView = new helpViewClass({ el: $("#main-nav-help-modal") });
        this.helpView.render();
        this.trigger("addedSettings");
    },
    
    /*
     * Set the favorites quick select view class.
     * Warning: only set after the DOM is loaded.
     */
    setFavoritesViewClass: function(favsViewClass) {
        this.favsViewClass = favsViewClass;
        this.favsView.dispose();
        this.favsView = new favsViewClass();
        this.favsView.render();
        this.trigger("addedSettings");
    },
});
var globalViewModel = new ViewModel();


/*
 * The NavigationView is responsible for updating the navigation bar to reflect the appropriate selection.
 */
var NavigationView = DefaultView.extend({
    // initialize must be called after the body is ready so the element is present
    initialize: function() {
        this.listenTo(globalViewModel, "changeView", this.render);
        this.listenTo(globalViewModel, "addedView", this.render);
        this.listenTo(globalViewModel, "removedView", this.render);
        this.listenTo(globalViewModel, "addedSettings", this.render);
    },
    
    template: $("#main-nav-template").html(),
    compiledItemTemplate: _.template(
        "<% if(active) { %>"+
        "    <li class=\"active\">"+
        "<% } else { %>"+
        "    <li>"+
        "<% } %>"+
        "<a href=\"<%= href %>\"><%= name %></a></li>"
    ),
    compiledDropdownTemplate: _.template(
        "<a class=\"dropdown-toggle\" data-toggle=\"dropdown\" style=\"cursor: pointer;\"><%= name %><% if(isTopMenu) { %><span class=\"caret\"></span><% } %></a>"+
        "<ul class=\"dropdown-menu\" role=\"menu\"></ul>"
    ),
    settingsTemplate: "",
        //~ "<ul class=\"nav navbar-nav navbar-right\">"+
        //~ "    <li><a id=\"main-nav-favs\" style=\"cursor: pointer;\">"+icons.filledStar+"</a></li>"+
        //~ "    <li><a id=\"main-nav-help\" style=\"cursor: pointer;\">"+icons.help+"</a></li>"+
        //~ "    <li class=\"dropdown\" style=\"cursor: pointer;\">"+
        //~ "        <a class=\"dropdown-toggle\" data-toggle=\"dropdown\">"+icons.settings+"</a>"+
        //~ "        <ul id=\"main-nav-settings\" class=\"dropdown-menu\" role=\"menu\"></ul>"+
        //~ "    </li>"+
        //~ "</ul>",
    
    /*
     * Renders the navigation bar according to what views are available in the globalViewModel.
     */
    render: function() {
        this.$el.empty();
        this.$el.html(this.template);
        
        // Render the navigation bar.
        var menu = globalViewModel.navigation;
        var bar = this.$el.find("#main-nav-bar");
        this.renderMenu(bar, menu, true);
        
        // Render the settings dropdown.
        //~ bar.parent().append(this.settingsTemplate);
        //~ var settingsMenu = d3.select(this.el).select("#main-nav-settings")
            //~ .selectAll("li")
            //~ .data(d3.entries(globalViewModel.settings))
            //~ .enter()
            //~ .append("li")
            //~ .on("click", function(d) {
                //~ globalViewModel.changeSettingsView(d.key);
                //~ $("#main-nav-settings-modal").modal("show");
            //~ })
            //~ .append("a")
            //~ .text(function(d) { return d.key; });
        //~ 
        //~ // Add help modal functionality.
        //~ $("#main-nav-help").on("click", function(elem) {
            //~ globalViewModel.helpView.render();
            //~ $("#main-nav-help-modal").modal("show");
        //~ });
        //~ 
        //~ // Add favorites popover functionality.
        //~ var enter = function() { // Make the popover appear on hover.
            //~ $(this).popover("show");
            //~ $(".popover").on("mouseleave", function() {
                //~ $("#main-nav-favs").popover("hide");
            //~ })
        //~ };
        //~ var exit = function() { // Make the popover disappear on hover out.
            //~ setTimeout(function() {
                //~ if(!$(".popover:hover").length) {
                    //~ $("#main-nav-favs").popover("hide");
                //~ }
            //~ }, 100);
        //~ };
        //~ var favs = $("#main-nav-favs");
        //~ favs.popover({ // Create the settings.
                //~ "html": true,
                //~ "trigger": "manual",
                //~ "viewport": "body",
                //~ "container": "body",
                //~ "placement": "bottom",
                //~ "animation": true,
                //~ "title": function() { return globalViewModel.favsView.readableName; },
                //~ "content": function() { globalViewModel.favsView.render(); return globalViewModel.favsView.$el.html(); },
            //~ })
            //~ .on("mouseenter", enter)
            //~ .on("mouseleave", exit);
        //~ 
        //~ return this;
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
                // The reason for escaping the path here is because the href seems to get unescaped upon clicking.
                // This would mess with the setup.
                bar.append(this.compiledItemTemplate({ "active": isActive, "href": "#"+encodeURIComponent(menu[key].path), "name": key }));
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
    },
});


var DEBUG_ROUTER = false;
/*
 * The router ensures that the correct visualization is displayed using Backbone's routing scheme.
 */
var Router = Backbone.Router.extend({
    
    initialize: function() {
        // Catches all routes except for the root path.
        this.route(/^([^\\?]*)([\\?](.*))?$/, "changeView");
        // Catches the special case of no fragment path or query string (the root path).
        this.route(/^$/, "rootView");
        globalSelectionModel.on("multichange", this.updateQueryString, this);
    },
    
    dispose: function() {
        globalSelectionModel.off(null, null, this);
    },
    
    previousQuery: "",
    
    /*
     * Updates the query string in the url bar and sets the history so the back button works.
     */
    updateQueryString: function() {
        if(DEBUG_ROUTER) console.log("Updating query string, replacing in browser history.");
        this.navigate(globalViewModel.currentPath +"?"+ hashToUrl(globalSelectionModel.attributes), {trigger: false, replace: false});
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
            this.navigate(path +"?"+ hashToUrl(globalSelectionModel.attributes), {trigger: false, replace: true});
        }
        this.previousQuery = queryString;
        if(DEBUG_ROUTER) console.log("Router.changeView end with path=\""+path+"\" query=\""+queryString+"\"");
        globalViewModel.changeView(path, { selection: urlToHash(queryString) });
    },
});


// Execution begins once the page is loaded.
// The views need some page elements that must be loaded in order to work.
var router;
var navView;
$(function startApplication() {
    // Cleanup cached api queries
    for(key in localStorage) {
        if(key.slice(0,3) === "api") {
            delete localStorage[key];
        }
    }
    // Start the router
    navView = new NavigationView({ el: $("#main-nav") });
    navView.render();
    router = new Router();
    Backbone.history.start({ pushState: false });
});
