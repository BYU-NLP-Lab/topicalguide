/*
 * Global selectors for Dataset, Analysis, and Topic Name Scheme
 *
 * This module adds persistent dropdown selectors to the navigation bar that allow
 * users to quickly switch between datasets, analyses, and naming schemes without
 * navigating back to the home page.
 */

(function() {

    var DEBUG_SELECTORS = false;

    /*
     * Initialize global selectors in the navigation bar
     * This should be called after the navigation view is rendered
     */
    var GlobalSelectorsView = DefaultView.extend({

        template:
            '<div id="global-selectors-container" style="background-color: #f8f8f8; border-bottom: 1px solid #e7e7e7; padding: 10px 15px; margin-bottom: 0;">' +
            '  <div class="container-fluid">' +
            '    <div style="display: flex; align-items: center;">' +
            '      <div style="margin-right: 20px; flex-shrink: 0;">' +
            '        <a href="#" style="display: block; padding: 5px;">' +
            '          <svg width="140" height="50" viewBox="0, 0, 300, 70" preserveAspectRatio="xMinYMid meet">' +
            '            <g>' +
            '              <text style="font-size:14px;font-style:normal;font-weight:normal;line-height:125%;letter-spacing:0px;word-spacing:0px;fill:#000000;fill-opacity:1;stroke:none;font-family:Sans" x="50" y="14">' +
            '                <tspan>The</tspan>' +
            '              </text>' +
            '              <text style="font-size:40px;font-style:normal;font-weight:normal;line-height:125%;letter-spacing:-1px;word-spacing:0px;fill:#000000;fill-opacity:1;stroke:none;font-family:Sans" x="80" y="35">' +
            '                <tspan><tspan style="line-height:1000%;fill:#008000">Topic</tspan>al</tspan>' +
            '              </text>' +
            '              <text style="font-size:40px;font-style:normal;font-weight:normal;line-height:125%;letter-spacing:-1px;word-spacing:0px;fill:#000000;fill-opacity:1;stroke:none;font-family:Sans" x="185" y="67">' +
            '                <tspan>Guide</tspan>' +
            '              </text>' +
            '              <g>' +
            '                <rect style="fill:#000000;fill-opacity:1" width="50" height="70" x="0" y="0" ry="11" rx="11" />' +
            '                <rect style="fill:#ffffff;fill-opacity:1" width="40" height="60" x="5" y="5" rx="8" ry="8" />' +
            '                <rect style="fill:#0000cc;fill-opacity:1" width="30" height="6" x="10" y="15" rx="4" ry="4" />' +
            '                <rect style="fill:#00d000;fill-opacity:1" width="30" height="6" x="10" y="26" rx="4" ry="4" />' +
            '                <rect style="fill:#d30000;fill-opacity:1" width="30" height="6" x="10" y="37" rx="4" ry="4" />' +
            '                <rect style="fill:#ee7216;fill-opacity:1" width="30" height="6" x="10" y="48" rx="4" ry="4" />' +
            '              </g>' +
            '            </g>' +
            '          </svg>' +
            '        </a>' +
            '      </div>' +
            '      <div id="global-selectors" class="form-inline" style="flex: 1;">' +
            '        <div class="form-group">' +
            '          <label for="dataset-selector" style="margin-right: 5px; color: #555; font-weight: 600;">Dataset:</label>' +
            '          <select id="dataset-selector" class="form-control input-sm" style="min-width: 200px;"></select>' +
            '        </div>' +
            '        <div class="form-group" style="margin-left: 15px;">' +
            '          <label for="analysis-selector" style="margin-right: 5px; color: #555; font-weight: 600;">Analysis:</label>' +
            '          <select id="analysis-selector" class="form-control input-sm" style="min-width: 200px;"></select>' +
            '        </div>' +
            '        <div class="form-group" style="margin-left: 15px;">' +
            '          <label for="global-nameScheme-selector" style="margin-right: 5px; color: #555; font-weight: 600;">Topic Names:</label>' +
            '          <select id="global-nameScheme-selector" class="form-control input-sm" style="min-width: 180px;"></select>' +
            '        </div>' +
            '      </div>' +
            '    </div>' +
            '  </div>' +
            '</div>',

        initialize: function() {
            this.dataModel = globalDataModel;
            this.selectionModel = globalSelectionModel;
            this.datasets = {};
            this.analyses = {};
            this.nameSchemes = [];
            this.nameSchemesCache = {};  // Cache naming schemes by analysis

            // Listen for selection changes
            this.listenTo(this.selectionModel, "change:dataset", this.onDatasetChange);
            this.listenTo(this.selectionModel, "change:analysis", this.onAnalysisChange);
            this.listenTo(this.selectionModel, "change:topic_name_scheme", this.onNameSchemeChange);

            // Load initial data
            this.loadDatasetsAndAnalyses();
        },

        render: function() {
            // Inject selectors above the entire navigation bar
            // Need to re-inject every time because NavigationView.render() clears everything
            var mainNav = $("#main-nav");
            if (mainNav.length) {
                // Remove existing selectors if present
                $("#global-selectors-container").remove();

                // Always inject fresh selectors before the main nav
                mainNav.prepend(this.template);
                this.renderDatasetSelector();
                this.renderAnalysisSelector();
                this.renderNameSchemeSelector();
            }
            return this;
        },

        loadDatasetsAndAnalyses: function() {
            if(DEBUG_SELECTORS) console.log("Loading datasets and analyses...");
            this.dataModel.submitQueryByHash({
                "datasets": "*",
                "analyses": "*",
                "dataset_attr": ["metadata"],
                "analysis_attr": ["metadata"],
            }, this.onDataLoaded.bind(this), this.onError.bind(this));
        },

        onDataLoaded: function(data) {
            if(DEBUG_SELECTORS) console.log("Data loaded:", data);
            this.datasets = data.datasets || {};

            // Extract analyses grouped by dataset
            this.analyses = {};
            for (var datasetName in this.datasets) {
                var dataset = this.datasets[datasetName];
                this.analyses[datasetName] = dataset.analyses || {};

                // Set readable names
                if (dataset.metadata && dataset.metadata.readable_name) {
                    dataset.readable_name = dataset.metadata.readable_name;
                } else {
                    dataset.readable_name = datasetName.replace(/_/g, " ").toUpperCase();
                }

                // Set readable names for analyses
                for (var analysisName in this.analyses[datasetName]) {
                    var analysis = this.analyses[datasetName][analysisName];
                    if (analysis.metadata && analysis.metadata.readable_name) {
                        analysis.readable_name = analysis.metadata.readable_name;
                    } else {
                        analysis.readable_name = analysisName.replace(/_/g, " ").toUpperCase();
                    }
                }
            }

            this.render();
            this.autoSelectDefaults();
        },

        autoSelectDefaults: function() {
            // Auto-select first dataset/analysis if none selected
            var currentDataset = this.selectionModel.get("dataset");
            var currentAnalysis = this.selectionModel.get("analysis");

            if (!currentDataset || currentDataset === "") {
                var datasetNames = Object.keys(this.datasets);
                if (datasetNames.length > 0) {
                    currentDataset = datasetNames[0];
                    if(DEBUG_SELECTORS) console.log("Auto-selecting first dataset:", currentDataset);
                    this.selectionModel.set({ dataset: currentDataset });
                }
            }

            if (currentDataset && (!currentAnalysis || currentAnalysis === "")) {
                var analysisNames = Object.keys(this.analyses[currentDataset] || {});
                if (analysisNames.length > 0) {
                    currentAnalysis = analysisNames[0];
                    if(DEBUG_SELECTORS) console.log("Auto-selecting first analysis:", currentAnalysis);
                    this.selectionModel.set({ analysis: currentAnalysis });
                }
            }
        },

        renderDatasetSelector: function() {
            var dropdown = d3.select("#dataset-selector");
            var currentDataset = this.selectionModel.get("dataset");

            dropdown.html("");
            if (_.size(this.datasets) === 0) {
                dropdown.append("option").text("No datasets").attr("disabled", true);
                return;
            }

            var that = this;
            var datasetEntries = d3.entries(this.datasets);
            datasetEntries.forEach(function(entry) {
                dropdown.append("option")
                    .attr("value", entry.key)
                    .property("selected", entry.key === currentDataset)
                    .text(entry.value.readable_name || entry.key);
            });

            dropdown.on("change", function() {
                var newDataset = d3.select(this).property("value");
                if(DEBUG_SELECTORS) console.log("Dataset selector changed to:", newDataset);
                that.selectionModel.set({ dataset: newDataset });
            });
        },

        renderAnalysisSelector: function() {
            var dropdown = d3.select("#analysis-selector");
            var currentDataset = this.selectionModel.get("dataset");
            var currentAnalysis = this.selectionModel.get("analysis");

            dropdown.html("");

            if (!currentDataset || !(currentDataset in this.analyses)) {
                dropdown.append("option").text("Select dataset first").attr("disabled", true);
                return;
            }

            var datasetAnalyses = this.analyses[currentDataset];
            if (_.size(datasetAnalyses) === 0) {
                dropdown.append("option").text("No analyses").attr("disabled", true);
                return;
            }

            var that = this;
            var analysisEntries = d3.entries(datasetAnalyses);
            analysisEntries.forEach(function(entry) {
                dropdown.append("option")
                    .attr("value", entry.key)
                    .property("selected", entry.key === currentAnalysis)
                    .text(entry.value.readable_name || entry.key);
            });

            dropdown.on("change", function() {
                var newAnalysis = d3.select(this).property("value");
                if(DEBUG_SELECTORS) console.log("Analysis selector changed to:", newAnalysis);
                that.selectionModel.set({ analysis: newAnalysis });
            });
        },

        renderNameSchemeSelector: function() {
            var dropdown = d3.select("#global-nameScheme-selector");
            var currentDataset = this.selectionModel.get("dataset");
            var currentAnalysis = this.selectionModel.get("analysis");
            var currentScheme = this.selectionModel.get("topic_name_scheme");

            dropdown.html("");

            if (!currentDataset || !currentAnalysis) {
                dropdown.append("option").text("Select analysis first").attr("disabled", true);
                return;
            }

            var cacheKey = currentDataset + ":" + currentAnalysis;

            // Check cache first
            if (this.nameSchemesCache[cacheKey]) {
                if(DEBUG_SELECTORS) console.log("Using cached naming schemes for", cacheKey);
                this.populateNameSchemeDropdown(this.nameSchemesCache[cacheKey], currentScheme);
                return;
            }

            // Show loading state
            dropdown.append("option").text("Loading...").attr("disabled", true);

            // Fetch available naming schemes from a sample topic
            var that = this;
            this.dataModel.submitQueryByHash({
                "datasets": currentDataset,
                "analyses": currentAnalysis,
                "topics": "0",  // Just get topic 0 to see available naming schemes
                "topic_attr": "names",
            }, function(data) {
                if(DEBUG_SELECTORS) console.log("Name scheme data received:", data);
                var topics = extractTopics(data);
                if(DEBUG_SELECTORS) console.log("Extracted topics:", topics);
                var firstTopic = d3.entries(topics)[0];

                dropdown.html("");

                if (!firstTopic || !firstTopic.value.names) {
                    dropdown.append("option").text("No naming schemes").attr("disabled", true);
                    return;
                }

                var schemes = Object.keys(firstTopic.value.names);
                that.nameSchemes = schemes;

                // Cache the schemes
                that.nameSchemesCache[cacheKey] = schemes;

                // Populate the dropdown
                that.populateNameSchemeDropdown(schemes, currentScheme);
            }, this.onError.bind(this));
        },

        populateNameSchemeDropdown: function(schemes, currentScheme) {
            var that = this;
            var dropdown = d3.select("#global-nameScheme-selector");

            // Smart default: prefer LLM-10words, then BERTopic, then Top3
            if (!currentScheme || currentScheme === "") {
                if (schemes.indexOf("LLM-10words") !== -1) {
                    currentScheme = "LLM-10words";
                } else if (schemes.some(function(s) { return s.startsWith("BERTopic"); })) {
                    currentScheme = schemes.find(function(s) { return s.startsWith("BERTopic"); });
                } else {
                    currentScheme = "Top3";
                }
                that.selectionModel.set({ topic_name_scheme: currentScheme }, { silent: true });
            }

            dropdown.html("");
            schemes.forEach(function(scheme) {
                dropdown.append("option")
                    .attr("value", scheme)
                    .property("selected", scheme === currentScheme)
                    .text(scheme);
            });

            dropdown.on("change", function() {
                var newScheme = d3.select(this).property("value");
                if(DEBUG_SELECTORS) console.log("Name scheme changed to:", newScheme);
                that.selectionModel.set({ topic_name_scheme: newScheme });
            });
        },

        onDatasetChange: function() {
            if(DEBUG_SELECTORS) console.log("Dataset changed, re-rendering selectors");
            this.renderDatasetSelector();
            this.renderAnalysisSelector();
            this.renderNameSchemeSelector();

            // Auto-select first analysis in new dataset
            var currentDataset = this.selectionModel.get("dataset");
            if (currentDataset && currentDataset in this.analyses) {
                var analysisNames = Object.keys(this.analyses[currentDataset]);
                if (analysisNames.length > 0) {
                    this.selectionModel.set({ analysis: analysisNames[0] });
                }
            }
        },

        onAnalysisChange: function() {
            if(DEBUG_SELECTORS) console.log("Analysis changed, re-rendering analysis selector");
            this.renderAnalysisSelector();
            this.renderNameSchemeSelector();
        },

        onNameSchemeChange: function() {
            if(DEBUG_SELECTORS) console.log("Name scheme changed, re-rendering name scheme selector");
            var currentScheme = this.selectionModel.get("topic_name_scheme");
            d3.select("#global-nameScheme-selector").property("value", currentScheme);
        },

        onError: function(error) {
            console.error("Error loading data for selectors:", error);
        },
    });

    // Create global instance and attach to navigation view
    var globalSelectorsView = null;

    // Hook into NavigationView render to add selectors
    var originalNavViewRender = NavigationView.prototype.render;
    NavigationView.prototype.render = function() {
        var result = originalNavViewRender.call(this);

        // Initialize selectors after navigation is rendered
        if (!globalSelectorsView) {
            globalSelectorsView = new GlobalSelectorsView();
        }

        // Always re-render selectors to keep them persistent
        globalSelectorsView.render();

        return result;
    };

})();
