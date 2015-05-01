/* How to make a view in the TopicalGuide.
 * Step 1: Copy and rename this file.
 * Step 2: Change the readableName to the name as you want it displayed to the user.
 * Step 3: Change the class name from ExampleView to a class name you pick that doesn't 
 *         conflict with any others in the project.
 * Step 4: Determine where on the navigation bar your view is put.
 *         [] will put your view name directly on the menu bar
 *         ["Menu"] will put your view under a menu named "Menu"
 *         ["Menu", "SubMenu", "SubSubMenu"] will nest your view accordingly
 * Step 5: Add the javascript file to the views list in root.html.
 * Step 6: By now your view should be fully incorporated into the site.
 *         Add custom functionality, see method details below.
 */
var ExampleView = DefaultView.extend({
    readableName: "Example",
    
    /*
     * Remember that your view automatically comes with the following models:
     * this.dataModel - Use the submitQueryByHash method to get data from the server.
     * this.selectionModel - Bind to this to be notified of different topics, documents, etc. 
     *                       that the user has selected.
     * this.favsModel - Use this to be notified of any changed favorites.
     * this.settingsModel - This is where any settings necessary to recreate what the user sees
     *                      should be stored. ONLY put the minimal needed items in here. The 
     *                      router and other things may set your settings to what they previously
     *                      were so the user doesn't have to reset them every time.
     * 
     * Failure to use the above models may make your view less user-friendly.
     */
    
    initialize: function() {
        // Bind to models or do other preparatory stuff.
        // Using this.listenTo(someModel, "change", this.someMethod) is recommended as the event
        // bindings will automatically be cleaned up by the .dispose method.
    },
    
    render: function() {
        // This function is called when the framework wants you to create your view.
        // Make sure your entire view stays in the given element (this.el or this.$el).
        // this.el is a DOM element
        // this.$el is a query element
        this.$el.html("<p>This is just an example view.</p>");
    },
    
    renderHelpAsHtml: function() {
        // This is used to get help information for the user. Click the help icon to see.
        return "<p>This is just an example view.</p>";
    },
    
    cleanup: function() {
        // Your view is being torn down at this point cleanup anything that may cause 
        // inconsistencies or memory leaks.
        // If you have any sub-views call .dispose() on them to clean them up.
        // Note that there is a function "dispose" that will try to clean things up for you.
    },
    
    /*
     * Other Hints:
     * 1. Use the global variable icons (found in view_templates.js) where-ever possible.
     *    If an icon needs to be changed across the site it can be done painlessly.
     *    Of especial use is icons.loading which you can display while waiting on the server.
     * 2. Also there is a function this.renderError which you can use to have error information
     *    displayed automatically.
     */
});

/*
 * Add strings to the list (below) to nest this view under menus.
 */
addViewClass(["Menu 1", "Sub Menu 2", "Sub Menu 3"], ExampleView);
