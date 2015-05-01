/*
 * The code on this page is responsible for updating the navigation and views, ensuring that 
 * url fragments are routed correctly and the nav bar stays up-to-date.
 */

var DEBUG_VIEWMODEL = false;
/*
 * The ViewModel is responsible for tracking which view is selected. This is primarily used with
 * the visualizations page where views are being swapped.
 * Bindable events include changedView, addedView, removedView, addedSettings.
 */
var ViewModel = Backbone.Model.extend({
    
    /**
     * models -- must contain: all of the models made in a TopicalGuideView
     */
    initialize: function(models) {
        this.selectionModel = models.selectionModel;
        models.viewModel = this;
        models.models = models;
        this.models = models;
        
        // TODO this should not be in the model.
        $("#main-container").append("<div id=\"main-view-container\"></div>");
        this.currentView = new DefaultView({ el: $("#main-view-container") });
        this.setHelpViewClass(DefaultView);
        this.setFavoritesViewClass(DefaultView);
        this.settingsView = new DefaultView({ el: $("#main-nav-settings-modal") });
        this.listenTo(this, "addedView", this.checkViewIsCurrent);
        this.listenTo(this, "removedView", this.checkViewIsCurrent);
    },
    
    currentView: null,
    currentPath: "",
    currentViewSettings: {},
    
    rootViewClass: DefaultView,
    paths: {}, // view class shortname to ViewClass mapping
    navigation: {}, // Information presented so the NavigationView can render the menus.
    
    helpView: null,
    helpViewClass: null,
    
    favsView: null,
    favsViewClass: null,
    
    settingsView: null,
    settings: {}, // view class shortname to SettingsClass mapping
    
    /**
     * Triggered when a view is added to make sure that the current view is up-to-date.
     */
    checkViewIsCurrent: function() {
        var path = this.currentPath;
        var cls = null;
        if(path === "") {
            cls = this.rootViewClass;
        } else if(path in this.paths) {
            cls = this.paths[path].viewClass;
        } else {
            cls = DefaultView;
        }
        
        if(!(this.currentView instanceof cls)) {
            this.currentView.dispose();
            
            $("#main-container").append("<div id=\"main-view-container\"></div>");
            
            var settingsModel = new SettingsModel();
            settingsModel.setSelectionModel(this.selectionModel);
            settingsModel.setViewPath(path);
            settingsModel.load();
            settingsModel.set(this.currentViewSettings);
            
            var init = {
                el: $("#main-view-container"),
                settingsModel: settingsModel,
                selectionModel: this.selectionModel,
            };
            _.extend(init, this.models);
            this.currentView = new cls(init);
            
            try {
                this.currentView.render();
            } catch(err) {
                console.log("The following error occurred while trying to render the view: " + err);
                console.log(err.stack);
            }
            
            // Change page title.
            $("head").find("title").html("Topical Guide &mdash; "+this.currentView.readableName);
            // Trigger a "changedView" event.
            this.trigger("changedView");
        }
    },
    
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
        this.currentViewSettings = settings;
        
        this.currentView.dispose();
        
        path = path.toLowerCase();
        this.currentPath = path; // Must go before the settings are set as the router listens for changes to update the url.
        this.selectionModel.set(settings.selection); // alert any views that the selection has changed
        
        $("#main-container").append("<div id=\"main-view-container\"></div>");
        
        var settingsModel = new SettingsModel();
        settingsModel.setSelectionModel(this.selectionModel);
        settingsModel.setViewPath(path);
        settingsModel.load();
        settingsModel.set(settings.settings);
        
        var init = {
            el: $("#main-view-container"),
            settingsModel: settingsModel,
            selectionModel: this.selectionModel,
        };
        _.extend(init, this.models);
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
            console.log(err.stack);
        }
        
        console.log(this.settings);
        
        // Change page title.
        $("head").find("title").html("Topical Guide &mdash; "+this.currentView.readableName);
        // Trigger a "changedView" event.
        this.trigger("changedView");
    },
    
    /**
     * Change the settings view to the one specified.
     * Return nothing.
     */
    changeSettingsView: function(readableName) {
        this.settingsView.dispose();
        $("#main-nav-settings-modal").remove();
        $("#main-all-modals-container").append("<div id=\"main-nav-settings-modal\"  class=\"modal fade\" tabindex=\"-1\" role=\"dialog\" aria-labelledby=\"settingsModal\" aria-hidden=\"true\"></div>");
        var init = {
            el: $("#main-nav-settings-modal"),
        }
        _.extend(init, this.models);
        
        if(readableName in this.settings) {
            this.settingsView = new this.settings[readableName](init);
        } else {
            this.settingsView = new DefaultView(init);
        }
        this.settingsView.render();
    },
    
    /**
     * Set the root view to the given class.
     * Return nothing.
     */
    setRootViewClass: function(rootClass) {
        this.rootViewClass = rootClass;
        this.trigger("addedView");
    },
    
    /**
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
        if(path in this.paths) {
            console.log("Cannot add a path that already exists.");
        }
        
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
        if(this.helpView !== null) {
            this.helpView.dispose();
        }
        $("#main-nav-help-modal").remove();
        $("#main-all-modals-container").append("<div id=\"main-nav-help-modal\"  class=\"modal fade\" tabindex=\"-1\" role=\"dialog\" aria-labelledby=\"helpModal\" aria-hidden=\"true\"></div>");
        
        var init = {
            el: $("#main-nav-help-modal"),
        };
        _.extend(init, this.models);
        
        this.helpView = new helpViewClass(init);
        this.helpView.render();
        this.trigger("addedSettings");
    },
    
    /*
     * Set the favorites quick select view class.
     * Warning: only set after the DOM is loaded.
     */
    setFavoritesViewClass: function(favsViewClass) {
        this.favsViewClass = favsViewClass;
        if(this.favsView !== null) {
            this.favsView.dispose();
        }
        var init = {};
        _.extend(init, this.models);
        this.favsView = new favsViewClass(init);
        this.favsView.render();
        this.trigger("addedSettings");
    },
});


/*
 * The NavigationView is responsible for updating the navigation bar to reflect the appropriate selection.
 */
var NavigationView = DefaultView.extend({
    // initialize must be called after the body is ready so the element is present
    initialize: function() {
        this.listenTo(this.viewModel, "changedView", this.render);
        this.listenTo(this.viewModel, "addedView", this.render);
        this.listenTo(this.viewModel, "removedView", this.render);
        this.listenTo(this.viewModel, "addedSettings", this.render);
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
    settingsTemplate: 
        "<ul class=\"nav navbar-nav navbar-right\">"+
        "    <li><a id=\"main-nav-favs\" style=\"cursor: pointer;\">"+icons.filledStar+"</a></li>"+
        "    <li><a id=\"main-nav-help\" style=\"cursor: pointer;\">"+icons.help+"</a></li>"+
        "    <li class=\"dropdown\" style=\"cursor: pointer;\">"+
        "        <a class=\"dropdown-toggle\" data-toggle=\"dropdown\">"+icons.settings+"</a>"+
        "        <ul id=\"main-nav-settings\" class=\"dropdown-menu\" role=\"menu\"></ul>"+
        "    </li>"+
        "</ul>",
    
    /*
     * Renders the navigation bar according to what views are available in the
     * provided viewModel.
     */
    render: function() {
        var that = this;
        this.$el.html(this.template);
        
        // Render the navigation bar.
        var menu = this.viewModel.navigation;
        var bar = this.$el.find("#main-nav-bar");
        this.renderMenu(bar, menu, true);
        
        // Render the settings dropdown.
        bar.parent().append(this.settingsTemplate);
        var settingsMenu = d3.select(this.el).select("#main-nav-settings")
            .selectAll("li")
            .data(d3.entries(this.viewModel.settings))
            .enter()
            .append("li")
            .on("click", function(d) {
                that.viewModel.changeSettingsView(d.key);
                $("#main-nav-settings-modal").modal("show");
            })
            .append("a")
            .text(function(d) { return d.key; });
        
        // Add help modal functionality.
        $("#main-nav-help").on("click", function(elem) {
            that.viewModel.helpView.render();
            $("#main-nav-help-modal").modal("show");
        });
        
        // Add favorites popover functionality.
        var enter = function() { // Make the popover appear on hover.
            $(this).popover("show");
            $(".popover").on("mouseleave", function() {
                $("#main-nav-favs").popover("hide");
            })
        };
        var exit = function() { // Make the popover disappear on hover out.
            setTimeout(function() {
                if(!$(".popover:hover").length) {
                    $("#main-nav-favs").popover("hide");
                }
            }, 100);
        };
        var favs = $("#main-nav-favs");
        favs.popover({ // Create the settings.
                "html": true,
                "trigger": "manual",
                "viewport": "body",
                "container": "body",
                "placement": "bottom",
                "animation": true,
                "title": function() { return that.viewModel.favsView.readableName; },
                "content": function() { 
                    that.viewModel.favsView.render(); 
                    return that.viewModel.favsView.$el.html();
                },
            })
            .on("mouseenter", enter)
            .on("mouseleave", exit);
        
        return this;
    },
    
    // Helper function for rendering menus.
    // Return true if an item is the current selection; false otherwise.
    renderMenu: function(bar, menu, isTopMenu) {
        var isSelected = false;
        for(key in menu) {
            if(!menu[key].menu) { // Found a leaf node.
                var isActive = false;
                if(menu[key].path === this.viewModel.currentPath) {
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

/**
 * The entire page.
 */
var TopicalGuideView = DefaultView.extend({
    readableName: "The Topical Guide",
    
    initialize: function() {
        // Create the data models used for registering events.
        this.userModel = new UserModel();
        this.selectionModel = new SelectionModel();
        this.dataModel = new DataModel({
            selectionModel: this.selectionModel,
        });
        this.selectionModel.setDataModel(this.dataModel);
        this.favsModel = new FavoritesModel({
            selectionModel: this.selectionModel,
        });
        this.viewModel = new ViewModel({
            dataModel: this.dataModel,
            userModel: this.userModel,
            selectionModel: this.selectionModel,
            favsModel: this.favsModel,
        });
        
        // Start the router.
        this.router = new Router({
            viewModel: this.viewModel,
            selectionModel: this.selectionModel,
        });
        Backbone.history.start({ pushState: false });
        
        this.models = {
            dataModel: this.dataModel,
            userModel: this.userModel,
            selectionModel: this.selectionModel,
            favsModel: this.favsModel,
            viewModel: this.viewModel,
        };
    },
    
    setRouter: function(router) {
        this.router = router;
    },
    
    render: function() {
        // This function is called when the framework wants you to create your view.
        // Make sure your entire view stays in the given element (this.el or this.$el).
        // this.el is a DOM element
        // this.$el is a query element
        this.navView = new NavigationView(_.extend({ el: $("#main-nav") }, this.models));
        this.navView.render();
        this.$el.html("<p>This is just an example view.</p>");
    },
    
    renderHelpAsHtml: function() {
        return "<p>Hopefully you never see this...</p>";
    },
    
    cleanup: function() {
    },
});

