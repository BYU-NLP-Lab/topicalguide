/**
 * To create a view extend the DefaultView and then call globalViewModel.addViewClass as specified
 * to add the view to the nav bar.
 */

/**
 * Easy to inject icons used throughout the site.
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
    beginning: "<span class=\"glyphicon glyphicon-step-backward green beginning\"></span>",
    end: "<span class=\"glyphicon glyphicon-step-forward green end\"></span>",
    
    loading: "<p class=\"text-center\"><img src=\"/static/images/large-spinner.gif\"/></p><p class=\"text-center\">Loading...</p>",
    
    pencil: "<span class=\"glyphicon glyphicon-pencil purple\"></span>",
};

var globalDefaultModels = null;

/**
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
        userModel: new Backbone.Model(),
        dataModel: new Backbone.Model(),
        selectionModel: new Backbone.Model(),
        favsModel: new Backbone.Model(),
        settingsModel: new Backbone.Model(),
        viewModel: new Backbone.Model(),
    };
    if(options === undefined || options === null) {
        options = {};
    }
    if(globalDefaultModels !== null) {
        _.extend(options, globalDefaultModels);
    }
    _.extend(this, options);
    
    Backbone.View.apply(this, arguments);
}

_.extend(DefaultView.prototype, Backbone.View.prototype, {
    
    // A human readable name for this view.
    readableName: "Default Page",
    shortName: "default",
    
    // A handy loading shortcut.
    loadingTemplate: icons.loading,
    
    /**
     * Any needed model event binding should be done in here.
     */
    initialize: function(options) {},
    
    /**
     * Render visualization in the given element (i.e. this.el and this.$el).
     * To use d3 try d3.select(this.el).
     */
    render: function() {
        this.$el.html("<p>Welcome to the Default Page. You're seeing this message either because this view is not implemented, this view doesn't exist, or an error occurred while trying to render the view.</p>");
    },
    
    /**
     * Call dispose on any sub-views and perform any other necessary cleanup operations.
     */
    cleanup: function() {},
    
    /**
     * Removes all events for you and removes the $el from the DOM.
     */
    dispose: function() {
        this.cleanup();
        if(this.dataModel) this.dataModel.off(null, null, this);
        if(this.selectionModel) this.selectionModel.off(null, null, this);
        if(this.favsModel) this.favsModel.off(null, null, this);
        if(this.settingsModel) this.settingsModel.off(null, null, this);
        this.remove();
    },
    
    /**
     * Return the HTML of the help message desired.
     */
    renderHelpAsHtml: function() {
        return "<p>The creators of this view didn't create a help page for you.</p>";
    },
    
    /**
     * Convenient function to render an error message in the $el element.
     */
    renderError: function(msg) {
        this.$el.html("<p>Oops, there was a server error: "+msg+"</p>");
    },
});
DefaultView.extend = Backbone.View.extend;


/*
 * The NavigationView is responsible for updating the navigation bar to reflect the appropriate selection.
 */
var NavigationView = DefaultView.extend({
    // initialize must be called after the body is ready so the element is present
    initialize: function() {
        this.listenTo(this.viewModel, "change", this.render);
    },
    
    template: $("#tg-nav-template").html(),
    compiledItemTemplate: _.template(
        "<% if(active) { %>"+
        "    <li class=\"active\">"+
        "<% } else { %>"+
        "    <li>"+
        "<% } %>"+
        "<a href=\"<%= href %>\"><%= name %></a></li>"
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
        
        // Get data.
        var paths = this.viewModel.getAvailableViewClassPaths();
        
        for(key in paths) {
            this.addViewToMenuBar(key, paths[key]);
        }
        
        return;
        //~ 
        //~ // Render the navigation bar.
        //~ var menu = this.viewModel.navigation;
        //~ var bar = this.$el.find("#main-nav-bar");
        //~ this.renderMenu(bar, menu, true);
        
        // Render the settings dropdown.
        //~ bar.parent().append(this.settingsTemplate);
        //~ var settingsMenu = d3.select(this.el).select("#main-nav-settings")
            //~ .selectAll("li")
            //~ .data(d3.entries(this.viewModel.settings))
            //~ .enter()
            //~ .append("li")
            //~ .on("click", function(d) {
                //~ that.viewModel.changeSettingsView(d.key);
                //~ $("#main-nav-settings-modal").modal("show");
            //~ })
            //~ .append("a")
            //~ .text(function(d) { return d.key; });
        
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
    },
    
    addViewToMenuBar: function(viewName, path) {
        var bar = d3.select("#tg-nav-bar");
        var insertionPoint = bar;
        for(i in path) {
            var readableName = path[i];
            var menuName = encodeURIComponent(readableName);
            var menuId = "tg-nav-bar-menu-item-"+menuName;
            if(insertionPoint.select("#"+menuId).empty()) { // Add menu.
                var menuComponent = insertionPoint.append("li")
                    .classed("dropdown", true);
                menuComponent.append("a")
                    .classed({ "dropdown-toggle": true, "pointer": true })
                    .attr("data-toggle", "dropdown")
                    .text(readableName)
                    .append("span")
                    .classed("caret", true);
                menuComponent.append("ul")
                    .classed("dropdown-menu", true)
                    .attr("role", "menu")
                    .attr("id", menuId);
                insertionPoint = insertionPoint.select("#"+menuId);
            } else { // Use menu.
                insertionPoint = insertionPoint.select("#"+menuId);
            }
        }

        insertionPoint.append("li")
            .append("a")
            .attr("href", "#"+viewName)
            .text(this.viewModel.getReadableViewName(viewName));
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
    
    events: {
        "click #main-nav-help": "clickHelp",
    },
    
    clickHelp: function() {
        
    },
    
    
    //~ /**
     //~ * Change the settings view to the one specified.
     //~ * Return nothing.
     //~ */
    //~ changeSettingsView: function(readableName) {
        //~ this.settingsView.dispose();
        //~ $("#main-nav-settings-modal").remove();
        //~ $("#main-all-modals-container").append("<div id=\"main-nav-settings-modal\"  class=\"modal fade\" tabindex=\"-1\" role=\"dialog\" aria-labelledby=\"settingsModal\" aria-hidden=\"true\"></div>");
        //~ var init = {
            //~ el: $("#main-nav-settings-modal"),
        //~ }
        //~ _.extend(init, this.models);
        //~ 
        //~ if(readableName in this.settings) {
            //~ this.settingsView = new this.settings[readableName](init);
        //~ } else {
            //~ this.settingsView = new DefaultView(init);
        //~ }
        //~ this.settingsView.render();
    //~ },
    
    
});




/**
 * The entire page.
 * 
 * Document Tooltips:
 * Requires the class "tg-tooltip" class to be set.
 * Requires a name stored under the "data-tg-document-name" attribute.
 * 
 * Topic Tooltips:
 * Requires the class "tg-tooltip" class to be set.
 * Requires a number stored under the "data-tg-topic-number" attribute.
 * 
 * Favorites:
 * Add the class "tg-fav" to the ...
 * 
 */
var TopicalGuideView = DefaultView.extend({
    
    readableName: "The Topical Guide",
    shortName: "tg",
    
    initialize: function() {
        var that = this;
        
        // Create the data models used for registering events.
        this.viewModel = new ViewModel();
        this.selectionModel = new SelectionModel();
        this.userModel = new UserModel();
        this.dataModel = new DataModel({
            selectionModel: this.selectionModel,
        });
        this.selectionModel.setDataModel(this.dataModel);
        this.favsModel = new FavoritesModel({
            selectionModel: this.selectionModel,
        });
        
        this.models = {
            dataModel: this.dataModel,
            userModel: this.userModel,
            selectionModel: this.selectionModel,
            favsModel: this.favsModel,
            viewModel: this.viewModel,
        };
        
        // Create dummy views as placeholders for those that will be added.
        this.currentView = new DefaultView();
        
        // TODO move this functionality to the navView
        this.helpView = new DefaultView();
        this.favsView = new DefaultView();
        this.topicNamesView = new DefaultView();
        this.settingsView = new DefaultView();
        
        
        // Bind to the viewModel to create and destroy views as needed.
        this.listenTo(this.viewModel, "change:currentView", this.changeCurrentView);
        this.listenTo(this.viewModel, "change:helpView", this.changeHelpView);
        this.listenTo(this.viewModel, "change:favsView", this.changeFavsView);
        this.listenTo(this.viewModel, "change:topicNamesView", this.changeTopicNamesView);
        
        // Create site-wide tooltip functionality.
        $("body").tooltip({
            placement: "auto",
            container: "body",
            selector: ".tg-tooltip",
            title: function() {
                console.log('trigger');
                var el = $(this);
                if(tg.dom.hasAttr(el, "data-tg-document-name")) {
                    var docName = el.attr("data-tg-document-name");
                    return docName;
                } else if(tg.dom.hasAttr(el, "data-tg-topic-number")) {
                    var topicNumber = el.attr("data-tg-topic-number");
                    return that.dataModel.getTopicName(topicNumber);
                }
                throw new Exception("No data was set for the tooltip to properly display.");
            },
        });
        
        // Start the router.
        this.router = new Router({
            viewModel: this.viewModel,
            selectionModel: this.selectionModel,
            tgView: this,
        });
        Backbone.history.start({ pushState: false });
    },
    
    setRouter: function(router) {
        this.router = router;
    },
    
    render: function() {
        var html = d3.select("#tg-main-template").html();
        this.$el.html(html);
        
        this.navView = new NavigationView(_.extend({ el: $("#tg-nav"), tgView: this }, this.models));
        this.navView.render();
    },
    
    renderHelpAsHtml: function() {
        return "<p>Hopefully you never see this...</p>";
    },
    
    cleanup: function() {
        this.navView
    },
    
    events: {
        "click .tg-fav": "clickFavorite", // Create site wide favorites functionality.
    },
    
    clickFavorite: function(e) {
        var el = e.target;
        var type = null;
        var clsName = null;
        var favsModel = this.favsModel;
        if(this.dom.hasAttr(el, "tg-data-dataset-name")) {
            type = "datasets";
            clsName = "tg-data-dataset-name";
        } else if(this.dom.hasAttr(el, "tg-data-analyis-name")) {
            type = "analyses";
            clsName = "tg-data-analyis-name";
        } else if(this.dom.hasAttr(el, "tg-data-topic-number")) {
            type = "topics";
            clsName = "tg-data-topic-number";
        } else if(this.dom.hasAttr(el, "tg-data-document-name")) {
            type = "documents";
            clsName = "tg-data-document-name";
        } else if(this.dom.hasAttr(el, "tg-data-topic-name-scheme")) {
            type = "topicNames";
            clsName = "tg-data-topic-name-scheme";
        }
        if(clsName !== null) {
            var value = $(el).attr(clsName).toString();
            if(favsModel.has(type, value)) {
                favsModel.remove({ type: value });
                el.classed({ "glyphicon": true, "glyphicon-star": false, "glyphicon-star-empty": true, "gold": true });
            } else {
                favsModel.add({ type: value });
                el.classed({ "glyphicon": true, "glyphicon-star": true, "glyphicon-star-empty": false, "gold": true });
            }
        }
    },
    
    changeCurrentView: function() {
        // Destroy current view.
        this.currentView.dispose();
        $("#tg-current-view-container").remove();
        // Create new div element.
        $("#tg-views-container").append("<div id=\"tg-current-view-container\"></div>");
        // Create new settings for the new view.
        var settingsModel = new SettingsModel();
        var init = {
            el: $("#tg-current-view-container"),
            settingsModel: settingsModel,
            selectionModel: this.selectionModel,
        };
        _.extend(init, this.models);
        
        // Find the current class to display.
        var viewClass = null;
        if(this.viewModel.get("currentView") === "") {
            var homeView = this.viewModel.get("rootView");
            if(homeView !== "") {
                viewClass = this.viewModel.getViewClass(homeView);
            }
        } else {
            viewClass = this.viewModel.getCurrentViewClass();
        }
        // Resort to the default view if the current view isn't registered yet.
        if(viewClass === undefined || viewClass === null) {
            viewClass = DefaultView;
        }
        
        // Create the new view.
        this.currentView = new viewClass(init);
        
        try {
            console.log("Rendering " + this.viewModel.get("currentView"));
            this.currentView.render();
        } catch(err) {
            console.log("The following error occurred while trying to render the view: " + err);
            console.log(err.stack);
        }
        
        // Change page title.
        $("head").find("title").html("Topical Guide &mdash; "+this.currentView.readableName);
    },
    
    changeHelpView: function() {
        this.helpView.dispose();
        $("#tg-nav-help-modal").remove();
        $("#tg-all-modals-container").append("<div id=\"main-nav-help-modal\"  class=\"modal fade\" tabindex=\"-1\" role=\"dialog\" aria-labelledby=\"helpModal\" aria-hidden=\"true\"></div>");
        
        var init = {
            el: $("#main-nav-help-modal"),
        };
        _.extend(init, this.models);
        
        var helpViewClass = this.viewModel.getHelpViewClass();
        this.helpView = new helpViewClass(init);
        this.helpView.render();
    },
    
    changeFavsView: function() {
        this.favsView.dispose();
        
        var init = {};
        _.extend(init, this.models);
        
        var favsViewClass = this.viewModel.getFavoritesViewClass();
        this.favsView = new favsViewClass(init);
        this.favsView.render();
    },
    
    changeTopicNamesView: function() {
        this.topicNamesView.dispose();
        
        var init = {};
        _.extend(init, this.models);
        
        var topicNamesViewClass = this.viewModel.getTopicNamesViewClass();
        this.topicNamesView = new topicNameViewClass(init);
        this.topicNamesView.render();
    },
    
});

