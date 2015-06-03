"use strict";

var DatasetView = DefaultView.extend({
    
    readableName: "Datasets",
    shortName: "datasets",
    
    helpTemplate:
'<p class="text-center">Select a dataset by clicking on one of the bars below. Details of the dataset are shown when selected. '+
'Select an analysis by clicking on one. An analysis will turn blue when selected.</p>',
    
    datasetsTemplate:
'<h3 class="text-center">Datasets</h3>'+
'<p class="text-center">Select a dataset by clicking on one of the bars below. Details of the dataset are shown when selected. '+
'Select an analysis by clicking on one. An analysis will turn blue when selected.</p>'+
'<div class="datasets-accordion panel-group"></div>',
    
    noDatasetsTemplate:
'<div class=\"panel\"><p>No datasets yet. Import one using <code>python tg.py -h</code>.</p></div>',
    
    initialize: function() {
        this.initialized = 
        this.listenTo(this.selectionModel, "change:dataset", this.updateDataset);
        this.listenTo(this.selectionModel, "change:analysis", this.updateAnalysis);
    },
    
    render: function() {
        this.$el.html("");
        var datasets = this.dataModel.getDatasetsAndAnalyses();
        
        if(_.size(datasets) !== 0) {
            this.renderDatasets();
        } else {
            this.renderNoDatasets();
        }
    },
    
    renderDatasets: function() {
        var that = this;
        var datasets = this.dataModel.getDatasetsAndAnalyses();
        
        this.selectionModel.selectFirst(false);
        
        // Returns the defaultValue if the key isn't present.
        function getMetadataValue(object, key, defaultValue) {
            if(!(key in object)) {
                return defaultValue;
            } else {
                return object[key];
            }
        }
        
        // Create basic outline
        this.$el.html(this.datasetsTemplate);
        var accordion = d3.select(this.el).select(".datasets-accordion");
        
        // Create panels for each dataset.
        var panels = accordion.selectAll("div")
            .data(d3.entries(datasets))
            .enter()
            .append("div")
            .classed("panel panel-default", true);
        
        // Create the panel title.
        var bold = panels.append("div")
            .attr("data-tg-dataset-name", function(d, i) {
                return d.key;
            })
            .classed("panel-heading text-center tg-select pointer", true)
            .attr("data-toggle", "collapse")
            .attr("data-parent", ".datasets-accordion")
            .attr("href", function(d, i) { return "#collapse-"+d.key; })
            .append("h3")
            .classed("panel-title", true)
            .append("b");
        bold.append("a") // Add dataset name.
            .classed("nounderline black-text-blue-hover", true)
            .text(function(d, i) {
                return that.dataModel.getReadableDatasetName(d.key);
            });
        bold.append("span") // Add a space between the name and the favicon.
            .text(" ");
        bold.append("a") // Add favs icon.
            .html(icons.emptyStar)
            .select("span")
            .attr("data-tg-dataset-name", function(d, i) {
                return d.key;
            })
            .classed("tg-fav", true)
            .each(function(d, i) {
                tg.site.initFav(this, that.favsModel);
            });
        
        // Create div for dataset content.
        var panel = panels.append("div")
            .attr("id", function(d, i) { return "collapse-"+d.key; })
            .classed("panel-collapse collapse", true)
            .classed("in", function(d, i) {
                return d.key === that.selectionModel.get("dataset");
            })
            .append("div")
            .classed("panel-body", true)
            .append("div")
            .classed("container-fluid", true);
        var analyses = panel.append("div")
            .classed("col-xs-4", true);
        analyses.each(function(d, i) {
            var el = d3.select(this);
            var datasetName = d.key;
            if(_.size(d.value.analyses) === 0) {
                el.html("<p>No analyses available for this dataset. Import one using <code>python topicalguide.py -h</code>.</p>");
            } else {
                // Create analysis list.
                el.append("h4").text("Analyses");
                var ul = el.append("ul")
                    .classed("nav nav-pills nav-stacked", true);
                var li = ul.selectAll("li")
                    .data(d3.entries(d.value.analyses))
                    .enter()
                    .append("li")
                    .attr("data-tg-analysis-name", function(d, i) {
                        return d.key;
                    })
                    .classed("pointer tg-select", true)
                    .classed("datasets-analysis-active-element", true) // Used to reselect the selection and identify the popover.
                    .classed("active", function(d, i) {
                        return d.key === that.selectionModel.get("analysis");
                    });
                var a = li.append("a");
                // Create favs icons.
                a.append("span")
                    .attr("data-tg-analysis-name", function(d, i) {
                        return d.key;
                    })
                    .classed("tg-fav", true)
                    .each(function(d, i) {
                        createFavsIcon(d3.select(this), "analyses", d.key, that);
                    });
                // Create analysis text.
                a.append("span")
                    .text(" ");
                a.append("span")
                    .text(function(d, i) {
                        return that.dataModel.getReadableAnalysisName(datasetName, d.key);
                    })
                    .style("cursor", "pointer");
                a.append("button")
                    .attr("type", "button")
                    .classed("btn btn-success", true)
                    .attr("data-tg-analysis-name", function(d, i) {
                        return d.key;
                    })
                    .classed("tg-select datasets-explore", true)
                    .style({ "float": "right", "padding": "1px 4px" })
                    .text("Explore!");
            }
        });
        
        var body = panel.append("div")
            .classed("col-xs-8", true);
        // Create description.
        body.append("h4")
            .text("Description");
        body.append("p")
            .text(function(d, i) { return getMetadataValue(d.value.metadata, "description", "No description available."); });
        
        // Create metadata table.
        var metadata = body.append("div");
        metadata.each(function(d, i) {
            var el = d3.select(this);
            var datasetMetadata = _.reduce(d.value.metadata, function(result, value, key) {
                var newKey = tg.str.toTitleCase(key.replace(/_/g, " "));
                result[newKey] = value;
                return result;
            }, {});
            if(_.size(d.value.metadata) === 0) {
                el.html("<p>No metadata available for this dataset.</p>");
            } else {
                tg.gen.createTableFromHash(this, datasetMetadata, ["Metadata", "Value"], "No metadata available.");
            }
        });
        
        // Create metrics table.
        var metrics = body.append("div");
        metrics.each(function(d, i) {
            var el = d3.select(this);
            if(_.size(d.value.metrics) === 0) {
                el.html("<p>No metrics available for this dataset.</p>");
            } else {
                tg.gen.createTableFromHash(this, d.value.metrics, ["Metric", "Value"], "No metrics available.");
            }
        });
        
        // Create popover functionality for the analyses' metadata and metrics.
        this.$el.popover({
            container: this.$el.get(0),
            content: function() {
                // Construct the contents of the popover.
                var emptyElement = document.createElement("div");
                var datasetName = that.selectionModel.get("dataset");
                var analysisName = $(this).attr("data-tg-analysis-name");
                var metadata = that.dataModel.getAnalysisMetadata(datasetName, analysisName);
                metadata = _.reduce(metadata, function(result, value, key) {
                    result[tg.str.toTitleCase(key.replace(/_/g, " "))] = value;
                    return result;
                }, {});
                var metrics = that.dataModel.getAnalysisMetrics(datasetName, analysisName);
                tg.gen.createTableFromHash(emptyElement, metadata, ["Metadata", "Value"], "No metadata available.");
                tg.gen.createTableFromHash(emptyElement, metrics, ["Metric", "Value"], "No metrics available.");
                return $(emptyElement).html();
            },
            html: true,
            placement: "auto right",
            selector: ".datasets-analysis-active-element",
            template: '<div class="popover" role="tooltip" style="max-width: 100%; max-height: 100%;"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>',
            title: "Metadata and Metrics",
            trigger: "hover",
        });
    },
    
    renderNoDatasets: function() {
        this.$el.html(this.noDatasetsTemplate);
    },
    
    events: {
        "click .datasets-explore": "clickExplore",
    },
    
    /**
     * Redirect to the "topics" view.
     * The redirect is delayed to allow the analysis to be set by the 
     * topical guide view.
     */
    clickExplore: function(e) {
        // This is a way to allow the event to propagate before switching views.
        setTimeout(function() {
            this.viewModel.set({ "currentView": "all_topics" });
        }.bind(this), 100);
    },
    
    /**
     * Expand the dataset accordion on dataset change.
     */
    updateDataset: function() {
        var datasetName = this.selectionModel.get("dataset");
        this.$el.find(".collapse.in").collapse('hide');
        d3.select(this.el).selectAll(".collapse")
            .each(function(d, i) {
                if(d.key === datasetName) {
                    $(this).collapse('show');
                }
            });
    },
    
    /**
     * Highlight the analysis text box on analysis change.
     */
    updateAnalysis: function(msg) {
        var datasetName = this.selectionModel.get("dataset");
        var analysisName = this.selectionModel.get("analysis");
        if(datasetName !== "") {
            var panel = d3.select(this.el).selectAll(".panel").filter(function(d, i) {
                return d.key === datasetName;
            });
            
            panel.selectAll(".datasets-analysis-active-element")
                .classed("active", function(d, i) {
                    return d.key === analysisName;
                });
        }
    },
    
    renderHelpAsHtml: function() {
        return this.helpTemplate;
    },
});

// Add the Datasets View as the root view
addViewClass([], DatasetView);
