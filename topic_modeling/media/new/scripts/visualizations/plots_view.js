/*
 * Create the Loading View, this is displayed while waiting for data to load from the server.
 */

var PlotView = LoadingView.extend({
    name: "chord",
    readableName: "2D Plot"
});

globalViewModel.addViewClass(["Visualizations"], PlotView);
