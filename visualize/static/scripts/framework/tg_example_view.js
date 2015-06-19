"use strict";

/****** How to make a view in the TopicalGuide ******
 * 
 * Step 1:
 * Copy and rename this file.
 * 
 * Step 2:
 * Change the readableName to the name as you want it displayed to the user.
 * Then change the shortName to be a url friendly name with no spaces,
 * no special characters ('_' is okay), and all lowercase; this is the name other 
 * views can reference your view by for navigation purposes. This name 
 * must be unique.
 * 
 * Step 3:
 * Change the class name from ExampleView to a class name you pick that doesn't 
 * conflict with any others in the project.
 * 
 * Step 4:
 * Determine where on the navigation bar your view is put.
 * [] will put your view name directly on the menu bar
 * ["Menu"] will put your view under a menu named "Menu"
 * ["Menu", "SubMenu", "SubSubMenu"] will nest your view accordingly
 * 
 * Step 5:
 * Add the javascript file to the views list in visualize/templates/root.html.
 * 
 * Step 6:
 * By now your view should be fully incorporated into the site.
 * Add custom functionality, and learn about provided functionality below.
 */
 
 
/**
 * Remember that your view automatically comes with the following models:
 * 
 * this.dataModel
 * Use the submitQueryByHash method to get data from the server.
 * 
 * this.selectionModel
 * Bind to this to be notified of different topics, documents, etc. 
 * that the user has selected.
 * 
 * this.favsModel
 * Use this to be notified of any changed favorites.
 * 
 * this.settingsModel
 * This is where any settings necessary to recreate what the user sees
 * should be stored. ONLY put the minimal needed items in here. The 
 * router and other things may set your settings to what they previously
 * were so the user doesn't have to reset them every time.
 * 
 * this.viewModel
 * Use this to navigate to other views. Set the "currentView"
 * to be the "shortName" of the view you want to navigate to.
 * 
 * Failure to use the above models may make your view less user-friendly
 * and result in odd behaviors.
 * 
 * 
 * 
 * Other built-in functionality:
 * 
 * this.el
 * Your view's root DOM element.
 * 
 * this.$el
 * Your view's root element wrapped by jquery.
 * 
 * 
 * 
 * Function naming conventions:
 * Use "render" to indicate that the view is being built from scratch, over-writing
 * the existing content.
 * Use "update" to indicate that content already on the screen is being updated.
 * Use "click", "change", etc. to indicate that the function is responding to events.
 */
var ExampleView = DefaultView.extend({
    
    /**
     * The name the user can see.
     */
    readableName: "Example",
    /**
     * The name other views and the navigation will use.
     * This must be a unique identifier.
     */
    shortName: "example",
    
    /**
     * Essentially this is a contructor.
     * 
     * Bind to models or do other preparatory stuff.
     * Using this.listenTo(someModel, "change", this.someMethod) is recommended 
     * as the event bindings will automatically be cleaned up when your view 
     * is disposed.
     */
    initialize: function initialize() {
    },
    
    /**
     * This function is called when the framework wants you to create your view.
     * Make sure your entire view stays in the given element (this.el or this.$el).
     * this.el is a DOM element
     * this.$el is a query element
     */
    render: function render() {
        this.$el.html("<p>This is just an example view.</p>");
    },
    
    /**
     * This is used to get help information for the user.
     * Click the help icon to see.
     */
    renderHelpAsHtml: function renderHelpAsHtml() {
        return "<p>This is just an example view.</p>";
    },
    
    /**
     * Your view is being torn down at this point cleanup anything that may cause 
     * inconsistencies or memory leaks.
     * If you have any sub-views call .dispose() on them to clean them up.
     * Note that there is a function "dispose" that will try to clean things up 
     * for you, but only if you used the listenTo method.
     * Also, note that the .dispose() method will call cleanup for you.
     * Also, note that the .dispose() method will remove the view's element
     * from the DOM tree.
     */
    cleanup: function cleanup() {
    },
});

/**
 * Add strings to the list (below) to nest this view under menus.
 * Leave it empty to put the view on the menu bar.
 */
addViewClass(["Menu 1", "Sub Menu 2", "Sub Menu 3"], ExampleView);

/**
 * Site wide functionality available to you.
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
 * 
 * Topic Name Schemes:
 * Set the class "tg-topic-name-auto-update" and set the 
 * "data-tg-topic-number" data attribute.
 * When a topic name scheme changes it is useful to have the topic names change
 * as well. This will do it automatically.
 * 
 * Navigation:
 * Allows the user to double click on the element and get redirected to the
 * single topic or single document view.
 * Set the class "tg-explore" and set either "data-tg-topic-number" or
 * "data-tg-document-name".
 */
 
/**
 * Other Hints:
 * 1. Use the global library tg which contains a collection of sub-modules for your convenience.
 */
