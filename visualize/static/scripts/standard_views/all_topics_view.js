"use strict";

/*
 * Displays all topics in a table format that can be sorted.
 */
var AllTopicsView = DefaultView.extend({

/******************************************************************************
 *                             STATIC VARIABLES
 ******************************************************************************/

    readableName: "All Topics",
    shortName: "all_topics",
    
    redirectTemplate:
'<div class="text-center">'+
'   <button class="all-topics-redirect btn btn-default">'+
'       <span class="glyphicon glyphicon-chevron-left pewter"></span> Datasets'+
'   </button>'+
'   <span> You need to select a dataset and analysis before using this view. </span>'+
'</div>',
    
    baseTemplate:
'<div class="all-topics-header text-center">'+
'   <h2>All Topics</h2>'+
'</div>'+
'<div class="all-topics-form-container row container-fluid"></div>'+
'<div class="all-topics-table-container row container-fluid"></div>',
    
/******************************************************************************
 *                             BASIC METHODS
 ******************************************************************************/
    
    initialize: function() {
        var defaultSettings = _.extend({ "sortBy": 1, "sortAscending": true }, this.settingsModel.attributes)
        this.settingsModel.set(defaultSettings);
        this.listenTo(this.selectionModel, "change:analysis", this.render);
        this.listenTo(this.selectionModel, "change:topicNameScheme", this.render);
        this.listenTo(this.selectionModel, "change:topic", this.changeTopic);
    },
    
    cleanup: function(topics) {},
    
    render: function() {
        if(this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html(this.baseTemplate);
            this.renderTopicsTable();
        } else {
            this.$el.html(this.redirectTemplate);
        }
    },
    
    renderTopicsTable: function() {
        var container = d3.select(this.el).select(".all-topics-table-container").html(this.loadingTemplate);
        var datasetName = this.selectionModel.get("dataset");
        var analysisName = this.selectionModel.get("analysis");
        // Make a request
        this.dataModel.submitQueryByHash({
            "datasets": datasetName,
            "analyses": analysisName,
            "topics": "*",
            "topic_attr": ["metrics"],
            "analysis_attr": ["metrics"],
        }, function(data) {
            var that = this;
            
            container.html("");
            
            // Extract basic data.
            var analysis = data.datasets[datasetName].analyses[analysisName];
            var topics = analysis.topics;
            var maxTokens = analysis.metrics["Token Count"];
            var metrics = null; // Used to determine the presence of "Temperature"
            for(var t in topics) {
                metrics = topics[t].metrics;
            }
            
            // Find mins and maxes.
            var tokenMaxPercentage = _.max(topics, function findMaxTokenPercentage(value, key) {
                return value.metrics["Token Count"];
            }).metrics["Token Count"]/maxTokens;
            var wordEntropyMax = _.max(topics, function findWordEntropyMax(value, key) {
                return value.metrics["Word Entropy"];
            }).metrics["Word Entropy"];
            var documentEntropyMax = _.max(topics, function findDocumentEntropyMax(value, key) {
                return value.metrics["Document Entropy"];
            }).metrics["Document Entropy"];
            var temperatureMax = null;
            var temperatureMin = null;
            if("Temperature" in metrics) {
                temperatureMax = _.max(topics, function findDocumentEntropyMax(value, key) {
                    return value.metrics["Temperature"];
                }).metrics["Temperature"];
                temperatureMin = _.min(topics, function findDocumentEntropyMin(value, key) {
                    return value.metrics["Temperature"];
                }).metrics["Temperature"];
            }
            
            // Define table data.
            var header = ["", "#", "Name", "% of Corpus", "Word Entropy", "Document Entropy"];
            var sortable = [false, true, true, true, true, true];
            var sortBy = this.settingsModel.get("sortBy");
            var sortAscending = this.settingsModel.get("sortAscending");
            var onSortFunction = function onSortFunction(index, ascending) {
                var toSet = { sortBy: index };
                if(index == this.settingsModel.get("sortBy")) {
                    toSet.sortAscending = !this.settingsModel.get("sortAscending");
                }
                this.settingsModel.set(toSet);
            }.bind(this);
            var tableData = _.map(topics, function createTableData(value, key) {
                var result = [
                    key, 
                    key, 
                    that.dataModel.getTopicNameRaw(key), 
                    value.metrics["Token Count"]/maxTokens, 
                    value.metrics["Word Entropy"], 
                    value.metrics["Document Entropy"]
                ];
                if("Temperature" in metrics) {
                    result.push(value.metrics["Temperature"]);
                }
                result.push(key);
                return result;
            });
            var dataFunctions = [
                function col0(d, i) {
                    var el = d3.select(this)
                        .append("span")
                        .attr("data-tg-topic-number", d)
                        .classed("tg-fav", true);
                    tg.site.initFav(el[0][0], that.favsModel);
                },
                false,
                false,
                function col3(d, i) {
                    d3.select(this).html(tg.gen.createPercentageBar(d, tokenMaxPercentage) + "&nbsp;" + (d*100).toFixed(2) + "%");
                },
                function col4(d, i) {
                    d3.select(this).html(tg.gen.createPercentageBar(d, wordEntropyMax) + "&nbsp;" + d.toFixed(2));
                },
                function col5(d, i) {
                    d3.select(this).html(tg.gen.createPercentageBar(d, documentEntropyMax) + "&nbsp;" + d.toFixed(2));
                },
            ];
            var tableRowFunction = function tableRowFunction(rowData, index) {
                // Set select topic functionality and row highlight functionality.
                d3.select(this)
                    .attr("data-tg-topic-number", rowData[1])
                    .classed("tg-select tg-explore pointer", true)
                    .classed("all-topics-update-document-highlight", true)
                    .classed("success", function isRowHighlighted(d, i) {
                        if(d3.select(this).attr("data-tg-topic-number") === that.selectionModel.get("topic")) {
                            return true;
                        } else {
                            return false;
                        }
                    });
            };
            if("Temperature" in metrics) {
                header.push("Temperature");
                sortable.push(true);
                dataFunctions.push(function col6(d, i) {
                    d3.select(this).html(tg.gen.createTemperatureBar(d, temperatureMin, temperatureMax) + "&nbsp;" + d.toFixed(4));
                });
            }
            
            // Add "Explore!" button last.
            header.push("");
            sortable.push(false);
            dataFunctions.push(function col7(d, i) {
                d3.select(this).append("button")
                    .attr("data-tg-topic-number", d)
                    .classed("btn btn-success tg-select all-topics-explore", true)
                    .style("padding", "1px 4px")
                    .text("Explore!");
            });
            
            tg.gen.createSortableTable(container[0][0], {
                header: header, 
                sortable: sortable,
                sortBy: sortBy,
                sortAscending: sortAscending,
                onSortFunction: onSortFunction,
                data: tableData,
                dataFunctions: dataFunctions,
                tableRowFunction: tableRowFunction,
            });
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return "This page recently changed. Documentation coming soon.";
    },
    
/******************************************************************************
 *                                EVENTS
 ******************************************************************************/

    events: {
        "click .all-topics-redirect": "clickRedirect",
        "click .all-topics-explore": "clickExplore",
    },
    
    clickRedirect: function clickRedirect(e) {
        this.viewModel.set({ currentView: "datasets" });
    },
    
    clickExplore: function clickExplore(e) {
        setTimeout(function delayRedirect() {
            this.viewModel.set({ currentView: "single_topic" });
        }.bind(this), 100);
    },
    
    changeTopic: function changeTopic() {
        var that = this;
        d3.select(this.el).selectAll(".all-topics-update-document-highlight")
            .classed("success", function isRowHighlighted(d, i) {
                if(d3.select(this).attr("data-tg-topic-number") === that.selectionModel.get("topic")) {
                    return true;
                } else {
                    return false;
                }
            });
    },

});

// Add the Topic View to the top level menu
addViewClass(["Topic"], AllTopicsView);
