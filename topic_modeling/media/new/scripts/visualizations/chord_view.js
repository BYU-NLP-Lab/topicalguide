/*
 * Create the Loading View, this is displayed while waiting for data to load from the server.
 */

var ChordView = LoadingView.extend({
    name: "chord",
    readableName: "Chord Diagram"
});

globalViewModel.addViewClass(["Visualizations"], ChordView);
