

var DatasetView = LoadingView.extend({
    
    readableName: "Datasets",
    
    compiledTemplate: _.template($("#datasets-template").html()),
    compiledDatasetTemplate: _.template($("#dataset-template").html()),
    
    mainQuery: "api?datasets=*&analyses=*&dataset_attr=metadata,metrics&analysis_attr=metadata,metrics",
    
    renderLoaded: function(data) {
        var datasets = data["datasets"];
        this.modifyMetadata(datasets);
        
        // Create basic outline
        this.$el.html(this.compiledTemplate({ "hasDatasets": (_.size(datasets) !== 0) }));
        var accordion = this.$el.find("#accordion");
        
        // Append panels for each dataset
        for(key in datasets) {
            datasets[key]["identifier"] = key;
            accordion.append(this.compiledDatasetTemplate(datasets[key]));
        }
    },
    
    modifyMetadata: function(datasets) {
        for(key in datasets) {
            var dataset = datasets[key];
            extractMetadata(dataset, dataset["metadata"], {
                "readable_name": key.replace("_", " ").toUpperCase(),
                "description": "No description available"
            });
            var analyses = dataset["analyses"];
            for(key2 in analyses) {
                var analysis = analyses[key2];
                extractMetadata(analysis, analysis["metadata"], {
                    "readable_name": key2.replace("_", " ").toUpperCase(),
                    "description": "No description available"
                });
            }
        }
    },
});

// Add the Datasets View as the root view
globalViewModel.setRootViewClass(DatasetView);
