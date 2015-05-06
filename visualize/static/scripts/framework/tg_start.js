"use strict";

// Execution begins once the page is loaded.
// The views need some page elements that must be loaded in order to work.
var router;
var navView;
var globalTopicalGuideView = null;
$(function startApplication() {
    try {
        // Show the page.
        globalTopicalGuideView = new TopicalGuideView({ el: $("#tg-all-content") });
        // Cleanup local data.
        deletePrefixFromHash("settings-", localStorage);
        
        // Render the Topical Guide View ... show time!
        globalTopicalGuideView.render();
        
        // Add special sub views to help manage favorites, help content, and other items.
        globalTopicalGuideView.viewModel.addSettingsClass(LoginView);
    } catch(err) {
        console.log(err.stack);
    }
});
