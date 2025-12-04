/*
 * Dataset Metadata View
 *
 * Displays metadata and metrics for the currently selected dataset.
 */

var DatasetMetadataView = DefaultView.extend({

    readableName: "Dataset Info",

    template:
        '<div class="container-fluid">' +
        '  <div class="row">' +
        '    <div class="col-xs-12">' +
        '      <h2 id="dataset-title"></h2>' +
        '      <p id="dataset-description"></p>' +
        '    </div>' +
        '  </div>' +
        '  <div class="row">' +
        '    <div class="col-xs-6">' +
        '      <h3>Metadata</h3>' +
        '      <div id="dataset-metadata-table"></div>' +
        '    </div>' +
        '    <div class="col-xs-6">' +
        '      <h3>Metrics</h3>' +
        '      <div id="dataset-metrics-table"></div>' +
        '    </div>' +
        '  </div>' +
        '  <div class="row" style="margin-top: 20px;">' +
        '    <div class="col-xs-12">' +
        '      <h3>Available Analyses</h3>' +
        '      <div id="analyses-list"></div>' +
        '    </div>' +
        '  </div>' +
        '</div>',

    initialize: function() {
        this.listenTo(this.selectionModel, "change:dataset", this.render);
    },

    render: function() {
        if (!this.selectionModel.nonEmpty(["dataset"])) {
            this.$el.html("<p>Please select a dataset to view its information.</p>");
            return this;
        }

        this.$el.html(this.loadingTemplate);

        var dataset = this.selectionModel.get("dataset");

        this.dataModel.submitQueryByHash({
            "datasets": dataset,
            "analyses": "*",
            "dataset_attr": ["metadata", "metrics"],
            "analysis_attr": ["metadata", "metrics", "topic_count"],
        }, this.renderDataset.bind(this), this.renderError.bind(this));

        return this;
    },

    renderDataset: function(data) {
        this.$el.html(this.template);

        var datasetName = this.selectionModel.get("dataset");
        var dataset = data.datasets[datasetName];

        if (!dataset) {
            this.$el.html("<p>Dataset not found.</p>");
            return;
        }

        // Set title
        var readableName = dataset.readable_name ||
                          (dataset.metadata && dataset.metadata.readable_name) ||
                          datasetName.replace(/_/g, " ").toUpperCase();
        d3.select("#dataset-title").text(readableName);

        // Set description
        var description = (dataset.metadata && dataset.metadata.description) ||
                         "No description available.";
        d3.select("#dataset-description").text(description);

        // Render metadata table
        var metadata = dataset.metadata || {};
        var metadataContainer = d3.select("#dataset-metadata-table");
        if (_.size(metadata) === 0) {
            metadataContainer.html("<p>No metadata available.</p>");
        } else {
            // Filter out readable_name and description as they're shown above
            var filteredMetadata = {};
            for (var key in metadata) {
                if (key !== "readable_name" && key !== "description") {
                    filteredMetadata[key] = metadata[key];
                }
            }
            if (_.size(filteredMetadata) === 0) {
                metadataContainer.html("<p>No additional metadata available.</p>");
            } else {
                createTableFromHash(metadataContainer, filteredMetadata, ["Key", "Value"], "metadata");
            }
        }

        // Render metrics table
        var metrics = dataset.metrics || {};
        var metricsContainer = d3.select("#dataset-metrics-table");
        if (_.size(metrics) === 0) {
            metricsContainer.html("<p>No metrics available.</p>");
        } else {
            createTableFromHash(metricsContainer, metrics, ["Metric", "Value"], "metrics");
        }

        // Render analyses list
        this.renderAnalysesList(dataset.analyses || {});
    },

    renderAnalysesList: function(analyses) {
        var that = this;
        var container = d3.select("#analyses-list");

        if (_.size(analyses) === 0) {
            container.html("<p>No analyses available for this dataset.</p>");
            return;
        }

        // Create a table for analyses
        var table = container.append("table")
            .classed("table table-hover table-condensed", true);

        var thead = table.append("thead").append("tr");
        thead.append("th").text("Analysis Name");
        thead.append("th").text("Description");
        thead.append("th").text("Topics");
        thead.append("th").text("Actions");

        var tbody = table.append("tbody");

        var analysisEntries = d3.entries(analyses);
        analysisEntries.forEach(function(entry) {
            var analysisName = entry.key;
            var analysis = entry.value;

            var readableName = analysis.readable_name ||
                              (analysis.metadata && analysis.metadata.readable_name) ||
                              analysisName.replace(/_/g, " ").toUpperCase();

            var description = (analysis.metadata && analysis.metadata.description) ||
                             "No description";

            var topicCount = analysis.topic_count || "N/A";

            var row = tbody.append("tr");
            row.append("td").text(readableName);
            row.append("td").text(description);
            row.append("td").text(topicCount);

            var actionsCell = row.append("td");
            actionsCell.append("button")
                .classed("btn btn-sm btn-primary", true)
                .text("View Topics")
                .on("click", function() {
                    that.selectionModel.set({ analysis: analysisName });
                    router.navigate("topics", { trigger: true });
                });
        });
    },

    renderHelpAsHtml: function() {
        return "<h4>Dataset Information</h4>" +
               "<p>This page displays metadata and metrics for the currently selected dataset. " +
               "Use the dropdown selectors at the top of the page to switch between datasets.</p>" +
               "<p>The 'Available Analyses' section shows all topic model analyses that have been " +
               "run on this dataset. Click 'View Topics' to explore the topics for a particular analysis.</p>";
    },
});

// Add the Dataset Metadata View to the top level menu
globalViewModel.addViewClass([], DatasetMetadataView);
