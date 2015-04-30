
// Execution begins once the page is loaded.
// The views need some page elements that must be loaded in order to work.
var router;
var navView;
$(function startApplication() {
    // Make sure that dataset and analyses data is available.
    defaultData = JSON.parse($("#global-dataset-and-analyses-info").html());
    globalDataModel.datasetsAndAnalyses = defaultData['datasets'];
    globalDataModel.serverInfo = defaultData['server'];
    // Cleanup local data
    deletePrefixFromHash("settings-", localStorage);
    // Start the router
    navView = new NavigationView({ el: $("#main-nav") });
    navView.render();
    router = new Router();
    Backbone.history.start({ pushState: false });
    // Create a Topical Guide View
    
});
