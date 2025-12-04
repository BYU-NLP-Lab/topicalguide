/*
 * BERTopic Native Visualizations
 *
 * Displays BERTopic's built-in Plotly visualizations for topic analysis.
 * Only available for BERTopic analyses.
 */

var TopicEmbeddingsView = DefaultView.extend({

    readableName: "Topic Space",

    template:
        '<div id="embeddings-container" class="row">' +
        '  <div id="embeddings-info" class="col-xs-12">' +
        '    <p>Select a visualization type:</p>' +
        '    <div class="btn-group" role="group" style="margin-bottom: 10px;">' +
        '      <button type="button" class="btn btn-primary" data-viz="topics">Topics Map</button>' +
        '      <button type="button" class="btn btn-default" data-viz="documents">Documents Map</button>' +
        '      <button type="button" class="btn btn-default" data-viz="heatmap">Similarity Heatmap</button>' +
        '      <button type="button" class="btn btn-default" data-viz="hierarchy">Topic Hierarchy</button>' +
        '      <button type="button" class="btn btn-default" data-viz="barchart">Top Words</button>' +
        '    </div>' +
        '    <div class="btn-group" role="group">' +
        '      <button type="button" class="btn btn-default" data-viz="term_rank">Term Rank</button>' +
        '      <button type="button" class="btn btn-default" data-viz="topics_over_time">Topics Over Time</button>' +
        '      <button type="button" class="btn btn-default" data-viz="topics_per_class">Topics Per Class</button>' +
        '      <button type="button" class="btn btn-default" data-viz="hierarchical_documents">Hierarchical Documents</button>' +
        '    </div>' +
        '  </div>' +
        '  <div id="embeddings-plot" class="col-xs-12" style="margin-top: 20px;">' +
        '  </div>' +
        '</div>',

    initialize: function() {
        this.listenTo(this.selectionModel, "change:analysis", this.render);
        this.currentVizType = 'topics';  // Default visualization
    },

    render: function() {
        var that = this;
        this.$el.html(this.template);

        if (!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            d3.select("#embeddings-plot").html(
                "<p class=\"alert alert-info\">Please select a dataset and analysis to view visualizations.</p>"
            );
            return this;
        }

        var analysis = this.selectionModel.get("analysis");

        // Check if this is a BERTopic analysis
        if (!analysis.startsWith('bertopic')) {
            d3.select("#embeddings-plot").html(
                "<div class=\"alert alert-info\">" +
                "<strong>Info:</strong> These visualizations are only available for BERTopic analyses. " +
                "The current analysis (" + analysis + ") does not support this feature." +
                "</div>"
            );
            return this;
        }

        // Set up button click handlers
        d3.selectAll(".btn-group button").on("click", function() {
            // Update button states
            d3.selectAll(".btn-group button").classed("btn-primary", false).classed("btn-default", true);
            d3.select(this).classed("btn-primary", true).classed("btn-default", false);

            // Load the selected visualization
            that.currentVizType = d3.select(this).attr("data-viz");
            that.loadVisualization();
        });

        // Load default visualization
        this.loadVisualization();
        return this;
    },

    loadVisualization: function() {
        var selections = this.selectionModel.attributes;
        var dataset = selections["dataset"];
        var analysis = selections["analysis"];
        var vizType = this.currentVizType;

        // Build URL for the visualization endpoint
        var url = "/bertopic-viz/" + dataset + "/" + analysis + "/" + vizType + "/";

        // Show loading message and iframe container
        var container = d3.select("#embeddings-plot");
        container.html(
            "<div style=\"text-align: center; padding: 20px; color: #666;\">" +
            "<p><i class=\"glyphicon glyphicon-refresh glyphicon-spin\"></i> Loading " + vizType + " visualization...</p>" +
            "<p><small>This may take a moment for large visualizations.</small></p>" +
            "</div>" +
            "<iframe id=\"bertopic-viz-iframe\" " +
            "width=\"100%\" height=\"700px\" frameborder=\"0\" " +
            "style=\"border: 1px solid #ddd; border-radius: 4px; display: none;\">" +
            "</iframe>"
        );

        // Get the iframe element and set up load handlers
        var iframe = document.getElementById("bertopic-viz-iframe");

        iframe.onload = function() {
            // Hide loading message and show iframe
            container.select("div").remove();
            d3.select(iframe).style("display", "block");
        };

        iframe.onerror = function() {
            container.html(
                "<div class=\"alert alert-danger\">" +
                "<strong>Error:</strong> Failed to load visualization. " +
                "The endpoint may not be responding. Check the server logs for details." +
                "</div>"
            );
        };

        // Set the src to trigger loading
        iframe.src = url;
    },

    renderHelpAsHtml: function() {
        return "<h4>BERTopic Visualizations</h4>" +
            "<p>This view provides interactive visualizations of BERTopic topic models:</p>" +
            "<ul>" +
            "<li><strong>Topics Map:</strong> 2D scatter plot showing topics in embedding space. " +
            "Closer topics are more semantically similar.</li>" +
            "<li><strong>Documents Map:</strong> 2D visualization of individual documents colored by their topics. " +
            "Helps identify document clusters and outliers.</li>" +
            "<li><strong>Similarity Heatmap:</strong> Matrix showing pairwise similarity between all topics.</li>" +
            "<li><strong>Topic Hierarchy:</strong> Hierarchical clustering showing relationships between topics.</li>" +
            "<li><strong>Top Words:</strong> Bar charts showing the most representative words for each topic.</li>" +
            "<li><strong>Term Rank:</strong> Shows how c-TF-IDF scores decline as more terms are added. " +
            "Useful for determining optimal number of words per topic.</li>" +
            "<li><strong>Topics Over Time:</strong> Track how topic frequencies change over time (requires temporal data).</li>" +
            "<li><strong>Topics Per Class:</strong> Compare topic representations across document classes (requires class labels).</li>" +
            "<li><strong>Hierarchical Documents:</strong> View documents across different levels of the topic hierarchy.</li>" +
            "</ul>" +
            "<p>All visualizations are interactive - hover over elements for details, zoom, and pan.</p>" +
            "<p><em>Note:</em> These visualizations are only available for BERTopic analyses. Some visualizations require " +
            "specific data (timestamps, class labels) and may show errors if that data is not available.</p>";
    },
});

// Topic Space view disabled - keep BERTopic analyses but hide visualizations tab
// globalViewModel.addViewClass([], TopicEmbeddingsView);
