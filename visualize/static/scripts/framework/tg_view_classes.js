"use strict";

/**
 * The DefaultView acts as an interface for other views to use so the proper 
 * methods and attributes are implemented.
 * 
 * Also, this view allows certain models to be injected into the "this" context
 * of your class.
 * 
 * It is recommended that you use the listenTo function to bind to model events so it gets cleaned up
 * for you.
 * 
 * It is also recommended that you work fully within the element (el or $el) given to the view.
 */
var DefaultView = function(options) {
    var defaults = {
        tgView: null,
        userModel: new Backbone.Model(),
        dataModel: new Backbone.Model(),
        selectionModel: new Backbone.Model(),
        favsModel: new Backbone.Model(),
        settingsModel: new Backbone.Model(),
        viewModel: new Backbone.Model(),
    };
    
    if(options !== undefined) {
        for(var key in defaults) {
            if(key in options) {
                defaults[key] = options[key];
                delete options[key];
            }
        }
    }
    
    _.assign(this, defaults);
    
    this.getAllModels = function() {
        return {
            userModel: this.userModel,
            dataModel: this.dataModel,
            selectionModel: this.selectionModel,
            favsModel: this.favsModel,
            settingsModel: this.settingsModel,
            viewModel: this.viewModel,
        };
    }.bind(this);
    
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


/**
 * The NavigationView is responsible for updating the navigation bar to 
 * reflect the appropriate selection and available views.
 */
var NavigationView = DefaultView.extend({
    
    initialize: function() {
        this.settingsView = new DefaultView();
        this.listenTo(this.viewModel, "change", this.render);
        this.listenTo(this.selectionModel, "change:dataset", this.hideTopicNameSchemes);
        this.listenTo(this.selectionModel, "change:analysis", this.hideTopicNameSchemes);
        this.listenTo(this.selectionModel, "change:dataset", this.hideFavorites);
        this.listenTo(this.selectionModel, "change:analysis", this.hideFavorites);
    },
    
    template: $("#tg-nav-template").html(),
    settingsTemplate: 
        "<ul class=\"nav navbar-nav navbar-right\">"+
        "    <li><a id=\"tg-nav-topic-name-schemes\" class=\"pointer\">"+icons.pencil+"</a></li>"+
        "    <li><a id=\"tg-nav-favs\" class=\"pointer\">"+icons.filledStar+"</a></li>"+
        "    <li><a id=\"tg-nav-help\" class=\"pointer\">"+icons.help+"</a></li>"+
        "    <li class=\"dropdown\" class=\"pointer\">"+
        "        <a class=\"dropdown-toggle\" data-toggle=\"dropdown\">"+icons.settings+"</a>"+
        "        <ul id=\"tg-nav-settings\" class=\"dropdown-menu\" role=\"menu\"></ul>"+
        "    </li>"+
        "</ul>",
    modalTemplate: 
"<div class=\"modal-dialog\">"+
"    <div class=\"modal-content\">"+
"        <div class=\"modal-header\">"+
"            <button type=\"button\" class=\"close\" data-dismiss=\"modal\"><span aria-hidden=\"true\">&times;</span><span class=\"sr-only\">Close</span></button>"+
"            <h3 class=\"modal-title\">Modal title</h3>"+
"        </div>"+
"        <div class=\"modal-body\">"+
"            Modal Body"+
"        </div>"+
"        <div class=\"modal-footer\">"+
"            <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>"+
"        </div>"+
"    </div>"+
"</div>",
    
    /**
     * Renders the navigation bar according to what views are available in the
     * provided viewModel.
     */
    render: function() {
        var that = this;
        this.$el.html(this.template);
        
        // Create menus.
        var paths = this.viewModel.getAvailableViewClassPaths();
        for(var viewName in paths) {
            this.addViewToMenuBar(viewName, paths[viewName]);
        }
        var selectedName = this.viewModel.get("currentView");
        if(selectedName in paths) {
            this.highlightViewPath(selectedName, paths[selectedName]);
        }
        
        // Create settings icons.
        var bar = this.$el.find("#tg-nav-bar");
        bar.parent().append(this.settingsTemplate);
        
        // Create settings menu.
        var settingsMenu = d3.select("#tg-nav-settings")
            .selectAll("li")
            .data(d3.entries(this.viewModel.getAvailableSettingsViewClasses()))
            .enter()
            .append("li")
            .attr("data-settings-view-name", function(d, i) {
                return d.key;
            })
            .classed("tg-nav-settings-click pointer", true)
            .append("a")
            .text(function(d) { return d.value.prototype.readableName; });
        
        // Add favorites popover functionality.
        var enterFavs = function() { // Make the popover appear on hover.
            $(this).popover("show");
            $(".popover").on("mouseleave", function() {
                $("#tg-nav-favs").popover("hide");
            });
        };
        var exitFavs = function() { // Make the popover disappear on hover out.
            setTimeout(function() {
                if(!$(".popover:hover").length) {
                    $("#tg-nav-favs").popover("hide");
                }
            }, 100);
        };
        $("#tg-nav-favs").popover({ // Create the settings.
                "html": true,
                "trigger": "manual",
                "viewport": "body",
                "container": "#tg-all-content",
                "placement": "bottom",
                "animation": true,
                "title": "Favorites Quick Select",
                "content": this.hoverFavorites.bind(this),
            })
            .on("mouseenter", enterFavs)
            .on("mouseleave", exitFavs);
        
        // Add topic name schemes popover functionality.
        var enterTopicNameSchemes = function() { // Make the popover appear on hover.
            $(this).popover("show");
            $(".popover").on("mouseleave", function() {
                $("#tg-nav-topic-name-schemes").popover("hide");
            });
        };
        var exitTopicNameSchemes = function() { // Make the popover disappear on hover out.
            setTimeout(function() {
                if(!$(".popover:hover").length) {
                    $("#tg-nav-topic-name-schemes").popover("hide");
                }
            }, 100);
        };
        $("#tg-nav-topic-name-schemes").popover({ // Create the settings.
                "html": true,
                "trigger": "manual",
                "viewport": "body",
                "container": "#tg-all-content",
                "placement": "bottom",
                "animation": true,
                "title": "Topic Name Schemes",
                "content": this.hoverTopicNameSchemes.bind(this),
            })
            .on("mouseenter", enterTopicNameSchemes)
            .on("mouseleave", exitTopicNameSchemes);
    },
    
    addViewToMenuBar: function(viewName, path) {
        var bar = d3.select("#tg-nav-bar");
        var insertionPoint = bar;
        for(var i in path) {
            var readableName = path[i];
            var menuName = encodeURIComponent(readableName);
            var menuId = "tg-nav-bar-menu-item-"+menuName;
            if(insertionPoint.select("#"+menuId).empty()) { // Add menu.
                var dropdownMenuType = "dropdown-submenu";
                var showCaret = false;
                if(i === "0") {
                    dropdownMenuType = "dropdown";
                    showCaret = true;
                }
                var menuComponent = insertionPoint.append("li")
                    .classed(dropdownMenuType, true);
                var menuComponentSpan = menuComponent.append("a")
                    .classed({ "dropdown-toggle": true, "pointer": true })
                    .attr("data-toggle", "dropdown")
                    .text(readableName)
                    .append("span");
                if(showCaret) {
                    menuComponentSpan.classed("caret", true);
                }
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
            .attr("data-tg-view-name", viewName)
            .append("a")
            .attr("href", "#"+viewName)
            .text(this.viewModel.getReadableViewName(viewName));
    },
    
    highlightViewPath: function(viewName, path) {
        var menu = d3.select("#tg-nav-bar");
        for(var i in path) {
            var readableName = path[i];
            var menuName = encodeURIComponent(readableName);
            var menuId = "tg-nav-bar-menu-item-"+menuName;
            menu = d3.select(menu.select("#"+menuId)[0][0].parentNode);
            menu.classed("active", true);
        }
        menu.selectAll("li")
            .filter(function() {
                var el = d3.select(this);
                if(el.attr("data-tg-view-name") === viewName) {
                    return true;
                } else {
                    return false;
                }
            })
            .classed("active", true);
    },
    
    events: {
        "click #tg-nav-help": "clickHelp",
        "click .tg-nav-settings-click": "clickSettings",
        "hidden.bs.modal #tg-nav-settings-modal": "hiddenSettingsModal",
    },
    
    hideTopicNameSchemes: function() {
        $("#tg-nav-topic-name-schemes").popover("hide");
    },
    
    hoverTopicNameSchemes: function() {
        var newEl = document.createElement("div");
        var datasetName = this.selectionModel.get("dataset");
        var analysisName = this.selectionModel.get("analysis");
        var topicNameSchemes = this.dataModel.getTopicNameSchemes(datasetName, analysisName);
        var container = d3.select(newEl).append("div");
        if(topicNameSchemes.length === 0) {
            container.append("p")
                .text("No name schemes available. Make sure that you have an analysis selected.");
        } else {
            container.append("ol").selectAll("li")
                .data(topicNameSchemes)
                .enter()
                .append("li")
                .append("a")
                .attr("data-tg-topic-name-scheme", function(d, i) {
                    return d;
                })
                .classed("tg-select nounderline pointer", true)
                .text(function(d, i) {
                    return d;
                });
        }
        return container.html();
    },
    
    hideFavorites: function() {
        $("#tg-nav-favs").popover("hide");
    },
    
    hoverFavorites: function() {
        var that = this;
        var newEl = document.createElement("div");
        // Create containers.
        var container = d3.select(newEl);
        var containers = container.selectAll("div")
            .data(d3.entries(this.favsModel.getAllFavorites()))
            .enter()
            .append("div");
        // Create headers.
        containers.append("h5")
            .append("b")
            .text(function(d, i) { return tg.str.toTitleCase(d.key); });
        // Create lists.
        containers.each(function(favObj, i) {
            var el = d3.select(this);
            if(_.size(favObj.value) === 0) {
                el.append("p")
                    .text("No " + favObj.key + " favorited.");
            } else {
                var type = favObj.key;
                var dataAttr = "";
                var nameFunction = function(x) { return x; };
                if(type === "datasets") {
                    dataAttr = "dataset-name";
                    nameFunction = that.dataModel.getReadableDatasetName.bind(that.dataModel);
                } else if(type === "analyses") {
                    dataAttr = "analysis-name";
                    nameFunction = that.dataModel.getReadableAnalysisNameInContext.bind(that.dataModel);
                } else if(type === "topics") {
                    dataAttr = "topic-number";
                    nameFunction = that.dataModel.getReadableTopicName.bind(that.dataModel);
                } else if(type === "documents") {
                    dataAttr = "document-name";
                }
                
                el.append("ol")
                    .selectAll("li")
                    .data(d3.entries(favObj.value).map(function(entry) { 
                            entry.value = makeSingular(favObj.key);
                            return entry;
                    }))
                    .enter()
                    .append("li")
                    .append("a")
                    .attr("data-tg-"+dataAttr, function(d, i) {
                        return d.key;
                    })
                    .classed("nounderline pointer", true)
                    .classed("tg-select", true)
                    .text(function(d, i) { return nameFunction(d.key); });
            }
        });
        return container.html();
    },
    
    clickHelp: function(e) {
        var el = $("#tg-nav-help-modal");
        el.html(this.modalTemplate);
        
        el.find(".modal-title").text(this.tgView.currentView.readableName + " Help");
        el.find(".modal-body").html(this.tgView.currentView.renderHelpAsHtml());
        
        el.modal("show");
    },
    
    clickSettings: function(e) {
        var el = e.currentTarget;
        if(tg.dom.hasAttr(el, "data-settings-view-name")) {
            var viewName = $(el).attr("data-settings-view-name");
            var viewClass = this.viewModel.getSettingsViewClass(viewName);
            if(viewClass !== null) {
                var modalContainer = $("#tg-nav-settings-modal");
                modalContainer.html(this.modalTemplate);
                modalContainer.find(".modal-title").text(viewClass.prototype.readableName);
                
                var init = {
                    el: modalContainer.find(".modal-content"),
                };
                _.extend(init, this.getAllModels());
                this.settingsView = new viewClass(init);
                this.settingsView.render();
                $("#tg-nav-settings-modal").modal("show");
            }
        }
    },
    
    /**
     * Dispose settingsView upon closing the dialog.
     */
    hiddenSettingsModal: function(e) {
        this.settingsView.dispose();
    },
    
});


var BreadcrumbsView = DefaultView.extend({

    baseTemplate:
"<div class=\"well\" style=\"text-align: justify; margin: 0px 0px 20px 0px; padding: 0px 10px 0px 10px;\">"+
"<div style=\"vertical-align: middle; display: table; width: 100%;\">"+
"<span class=\"tg-nav-breadcrumb-span\"><span>Dataset:&nbsp;</span><span class=\"tg-nav-breadcrumb-dataset blue\"></span></span>"+
"<span class=\"tg-nav-breadcrumb-span\">Document:&nbsp;<span class=\"tg-nav-breadcrumb-document blue\"></span></span>"+
"<span class=\"tg-nav-breadcrumb-span\">Analysis:&nbsp;<span class=\"tg-nav-breadcrumb-analysis blue\"></span></span>"+
"<span class=\"tg-nav-breadcrumb-span\">Topic:&nbsp;<span class=\"tg-nav-breadcrumb-topic blue\"></span></span>"+
"<span class=\"tg-nav-breadcrumb-span\">Topic Name Scheme:&nbsp;<span class=\"tg-nav-breadcrumb-topic-name-scheme blue\"></span></span>"+
"</div>"+
"</div>",
    
    initialize: function() {
        this.listenTo(this.selectionModel, "change:dataset", this.updateDataset);
        this.listenTo(this.selectionModel, "change:analysis", this.updateAnalysis);
        this.listenTo(this.selectionModel, "change:topic", this.updateTopic);
        this.listenTo(this.selectionModel, "change:document", this.updateDocument);
        this.listenTo(this.selectionModel, "change:topicNameScheme", this.updateTopicNameScheme);
        this.listenTo(this.selectionModel, "change:topicNameScheme", this.updateTopic);
    },
    
    cleanup: function() {
    },
    
    render: function() {
        this.$el.html(this.baseTemplate);
        this.updateDataset();
        this.updateAnalysis();
        this.updateTopic();
        this.updateDocument();
        this.updateTopicNameScheme();
        d3.select(this.el).selectAll(".tg-nav-breadcrumb-span")
            .style({ "font-size": "0.7em", "display": "table-cell", "text-align": "center", "vertical-align": "middle" });
    },
    
    updateDataset: function() {
        var selector = ".tg-nav-breadcrumb-dataset";
        var name = this.selectionModel.get("dataset");
        if(name === "") {
            name = "No dataset selected.";
        } else {
            name = this.dataModel.getReadableDatasetName(name);
        }
        this.$el.find(selector).text(name);
    },
    
    updateAnalysis: function() {
        var selector = ".tg-nav-breadcrumb-analysis";
        var name = this.selectionModel.get("analysis");
        if(name === "") {
            name = "No analysis selected.";
        } else {
            name = this.dataModel.getReadableAnalysisNameInContext(name);
        }
        this.$el.find(selector).text(name);
    },
    
    updateTopic: function() {
        var selector = ".tg-nav-breadcrumb-topic";
        var name = this.selectionModel.get("topic");
        if(name === "") {
            name = "No topic selected.";
        } else {
            name = this.dataModel.getReadableTopicName(name);
        }
        this.$el.find(selector).text(name);
    },
    
    updateDocument: function() {
        var selector = ".tg-nav-breadcrumb-document";
        var name = this.selectionModel.get("document");
        if(name === "") {
            name = "No document selected.";
        }
        this.$el.find(selector).text(name);
    },
    
    updateTopicNameScheme: function() {
        var selector = ".tg-nav-breadcrumb-topic-name-scheme";
        var name = this.selectionModel.get("topicNameScheme");
        if(name === "") {
            name = "No name scheme selected.";
        }
        this.$el.find(selector).text(name);
    },
    
});

/**
 * The entire page.
 * 
 * Data Attributes:
 *      data-tg-dataset-name
 *      data-tg-analysis-name
 *      data-tg-topic-number
 *      data-tg-document-name
 *      data-tg-topic-name-scheme
 * 
 * Selection:
 * Set the class "tg-select" and the data will be pulled from the data attribute.
 * 
 * Tooltips:
 * Set the class "tg-tooltip" and the data will be pulled from the data attribute.
 * 
 * Favorites:
 * Set the class "tg-fav" and the data will be pulled from the data attribute.
 * You are responsible for initializing the element.
 * To help you out there is a function called tg.site.initFav (see the 
 * documentation in tg_utilities.js.
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
        
        // Bind to the viewModel to create and destroy views as needed.
        this.listenTo(this.viewModel, "change:currentView", this.changeCurrentView);
        this.listenTo(this.viewModel, "change:availableViews", this.changeAvailableViews);
        
        // Create site-wide tooltip functionality.
        $("body").tooltip({
            placement: "auto",
            container: "body",
            selector: ".tg-tooltip",
            title: function() {
                var el = $(this);
                if(tg.dom.hasAttr(el, "data-tg-dataset-name")) {
                    var datasetName = el.attr("data-tg-dataset-name");
                    return that.dataModel.getReadableDatasetName(datasetName);
                } else if(tg.dom.hasAttr(el, "data-tg-analysis-name")) {
                    var analysisName = el.attr("data-tg-analysis-name");
                    return that.dataModel.getReadableAnalysisNameInContext(anlaysisName);
                } else if(tg.dom.hasAttr(el, "data-tg-topic-number")) {
                    var topicNumber = el.attr("data-tg-topic-number");
                    return that.dataModel.getReadableTopicName(topicNumber);
                } else if(tg.dom.hasAttr(el, "data-tg-document-name")) {
                    var docName = el.attr("data-tg-document-name");
                    return docName;
                } else if(tg.dom.hasAttr(el, "data-tg-word-type")) {
                    var wordType = el.attr("data-tg-word-type");
                    return wordType;
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
        this.breadcrumbsView = new BreadcrumbsView(_.extend({ el: $("#tg-breadcrumbs"), tgView: this }, this.models));
        this.breadcrumbsView.render();
    },
    
    renderHelpAsHtml: function() {
        return "<p>Hopefully you never see this...</p>";
    },
    
    cleanup: function() {
        this.navView.dispose();
    },
    
    events: {
        "click .tg-fav": "clickFavorite", // Create site wide favorites functionality.
        "click .tg-select": "clickSelect", // Create site wide selection functionality.
    },
    
    clickFavorite: function(e) {
        var el = e.currentTarget;
        var type = null;
        var clsName = null;
        var favsModel = this.favsModel;
        if(tg.dom.hasAttr(el, "data-tg-dataset-name")) {
            type = "datasets";
            clsName = "data-tg-dataset-name";
        } else if(tg.dom.hasAttr(el, "data-tg-analyis-name")) {
            type = "analyses";
            clsName = "data-tg-analyis-name";
        } else if(tg.dom.hasAttr(el, "data-tg-topic-number")) {
            type = "topics";
            clsName = "data-tg-topic-number";
        } else if(tg.dom.hasAttr(el, "data-tg-document-name")) {
            type = "documents";
            clsName = "data-tg-document-name";
        } else if(tg.dom.hasAttr(el, "data-tg-topic-name-scheme")) {
            type = "topicNames";
            clsName = "data-tg-topic-name-scheme";
        }
        if(clsName !== null) {
            el = d3.select(el);
            var value = el.attr(clsName).toString();
            var favs = {};
            favs[type] = value;
            if(favsModel.has(type, value)) {
                favsModel.remove(favs);
                el.classed({ "glyphicon-star": false, "glyphicon-star-empty": true });
            } else {
                favsModel.add(favs);
                el.classed({ "glyphicon-star": true, "glyphicon-star-empty": false });
            }
        }
        e.stopPropagation();
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
            this.currentView.render();
        } catch(err) {
            console.log("The following error occurred while trying to render the view: " + err);
            console.log(err.stack);
        }
        
        // Change page title.
        $("head").find("title").html("Topical Guide &mdash; "+this.currentView.readableName);
    },
    
    changeAvailableViews: function() {
        var currView = this.viewModel.get("currentView");
        // If the current view doesn't match the view the viewModel is set to 
        // and that view is registered with the viewModel.
        if(this.currentView.shortName !== currView && this.viewModel.hasViewClass(currView)) {
            this.changeCurrentView();
        }
    },
    
    changeTopicNamesView: function() {
        this.topicNamesView.dispose();
        
        var init = {};
        _.extend(init, this.models);
        
        var topicNamesViewClass = this.viewModel.getTopicNamesViewClass();
        this.topicNamesView = new topicNameViewClass(init);
        this.topicNamesView.render();
    },
    
    clickSelect: function(e) {
        var el = e.currentTarget;
        var selection = {};
        if(tg.dom.hasAttr(el, "data-tg-dataset-name")) {
            selection["dataset"] = $(el).attr("data-tg-dataset-name");
        } else if(tg.dom.hasAttr(el, "data-tg-analysis-name")) {
            selection["analysis"] = $(el).attr("data-tg-analysis-name");
        } else if(tg.dom.hasAttr(el, "data-tg-topic-number")) {
            selection["topic"] = $(el).attr("data-tg-topic-number");
        } else if(tg.dom.hasAttr(el, "data-tg-document-name")) {
            selection["document"] = $(el).attr("data-tg-document-name");
        } else if(tg.dom.hasAttr(el, "data-tg-topic-name-scheme")) {
            selection["topicNameScheme"] = $(el).attr("data-tg-topic-name-scheme");
        }
        this.selectionModel.set(selection);
    },
    
});

