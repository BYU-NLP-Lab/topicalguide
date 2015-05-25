"use strict";

// Execution begins once the page is loaded.
// The views need some page elements that must be loaded in order to work.
var router;
var navView;
var globalTopicalGuideView = null;
$(function startApplication() {
    // Show the page.
    globalTopicalGuideView = new TopicalGuideView({ el: $("#tg-all-content") });
    // Cleanup local data.
    deletePrefixFromHash("settings-", localStorage);
    
    // Render the Topical Guide View ... show time!
    globalTopicalGuideView.render();
    
    // Add special sub views to help manage favorites, help content, and other items.
    globalTopicalGuideView.viewModel.addSettingsClass(LoginView);
});


/**
 * Add a new view class. This is a convenience function to aid forwards
 * compatibility.
 * nesting -- a list specifying how to nest the view
 *      eg: [] will put the view on the menu bar
 *          ["menu", "submenu"] will put the view under menu>submenu>your_view
 * cls -- the view class, which must be a Backbone View
 */
function addViewClass(nesting, cls) {
    $(function startApplication() {
        try{
            globalTopicalGuideView.viewModel.addViewClass(nesting, cls);
        } catch(e) {
        }
    });
}
