/**
 * Display the metadata options for the user to select from.
 * Also, allows the user to create a new metadata attribute.
 */
var MetadataView = DefaultView.extend({
    
    readableName: "Metadata",
    shortName: "metadata",
    
    selectMetadataTemplate:
'<div class="container-fluid row">'+
'   <div class="col-xs-2">'+
'   </div>'+
'   <div class="col-xs-4">'+
'       <div class="choose-metadata"></div>'+
'   </div>'+
'   <div class="col-xs-4">'+
'       <div class="add-metadata"></div>'+
'   </div>'+
'   <div class="col-xs-2">'+
'   </div>'+
'</div>',

    metadataOptionsTemplate:
'<h4><b>Metadata Selection</b></h4>'+
'<hr />'+
'<div>'+
'    <label>Name:</label><br />'+
'    <select class="metadata-name-control form-control" type="selection"></select>'+
'</div>'+
'<div>'+
'    <label>Type:</label><br />'+
'    <span class="metadata-type-control"></span>'+
'</div>'+
'<div>'+
'    <label>Meaning:</label><br />'+
'    <span class="metadata-meaning-control"></span>'+
'</div>'+
'<div class="metadata-value-control-container">'+
'    <label>Set Value:</label><br />'+
'    <input class="metadata-value-control form-control" type="text" />'+
'</div>'+
'<div>'+
'   <button class="metadata-clear-selection-button btn btn-danger form-control">Clear Metadata Selection</button>'+
'</div>'+
'<div>'+
'   <button class="metadata-goto-metadata-map-button btn btn-success form-control" style="display: none;">Go to the Metadata Map</button>'+
'</div>',

    addMetadataTemplate:
'<h4><b>Add New Metadata</b></h4>'+
'<hr />'+
'<div>'+
'   <label>Name:</label><br />'+
'   <input class="metadata-add-name-control form-control" type="text" />'+
'</div>'+
'<div>'+
'    <label>Type:</label><br />'+
'    <select class="metadata-add-type-control form-control" name="Name" type="selection">'+
'       <option value="text">Text</option>'+
'       <option value="bool">Boolean</option>'+
'       <option value="int">Integer</option>'+
'       <option value="float">Float</option>'+
'       <option value="datetime">Date/Time</option>'+
'    </select>'+
'</div>'+
'<div>'+
'   <button class="metadata-add-submit btn btn-primary form-control">Add Metadata</button>'+
'</div>'+
'<div class="metadata-add-messages">'+
'</div>',
    

    initialize: function initialize() {
        var defaultModelAttr = {
            metadataTypes: {}, // The keys are the names used.
            metadataMeanings: {},
            metadataOrdinals: {},
        };
        this.model = new Backbone.Model(defaultModelAttr);
    },
    
    cleanup: function cleanup() {
    },
    
    /**
     * Show the loading icon.
     * Request the data.
     * Drop in the template for the forms to use.
     * Bind needed listeners for updating.
     */
    render: function render() {
        this.$el.html(this.loadingTemplate);
        
        var dataset = this.selectionModel.get("dataset");
        this.dataModel.submitQueryByHash({
            datasets: dataset,
            dataset_attr: ["document_metadata_types", "document_metadata_meanings", "document_metadata_ordinals"],
        }, function(data) {
            this.$el.html(this.selectMetadataTemplate);
            
            // Extract data.
            var metadataOrdinals = data.datasets[dataset].document_metatdata_ordinals;
            var metadataMeanings = data.datasets[dataset].document_metadata_meanings;
            var metadataTypes = data.datasets[dataset].document_metadata_types;
            this.model.set({
                "metadataTypes": metadataTypes,
                "metadataMeanings": metadataMeanings,
                "metadataOrdinals": metadataOrdinals,
            });
            
            // Bind to events.
            this.listenTo(this.selectionModel, "change:metadataName", this.updateMetadataSelection);
            this.listenTo(this.selectionModel, "change:metadataName", this.updateGoToMetadataMapButton);
            this.listenTo(this.model, "change:metadataTypes", this.updateMetadataOptions);
            this.listenTo(this.model, "change:metadataMeanings", this.updateMetadataSelection);
            this.listenTo(this.model, "change:metadataOrdinals", this.updateMetadataSelection);
            this.updateMetadataOptions();
            this.updateMetadataSelection();
            this.updateGoToMetadataMapButton();
            
            this.listenTo(this.userModel, "change:loggedIn", this.updateMetadataOptions);
            this.updateAddMetadata();
        }.bind(this), this.renderError.bind(this));
    },
    
    /**
     * Update the selected metadata type information and make sure the selected 
     * type is set correctly (it can be set from elsewhere).
     * Update the metadata meaning.
     */
    updateMetadataSelection: function updateMetadataSelection() {
        var controls = d3.select(this.el).select(".choose-metadata");
        var metadataTypes = this.model.get("metadataTypes");
        
        var nameControl = controls.select(".metadata-name-control");
        var typeControl = controls.select(".metadata-type-control");
        var meaningControl = controls.select(".metadata-meaning-control");
        var valueControl = controls.select(".metadata-value-control");
        
        var metadataName = this.selectionModel.get("metadataName");
        nameControl.property("value", metadataName);
        
        var metadataType = metadataTypes[metadataName];
        var typeNames = this.dataModel.getServerInfo().metadata_types;
        typeControl.text(typeNames[metadataType]);
        
        var metadataMeanings = this.model.get("metadataMeanings");
        var meaningNames = this.dataModel.getServerInfo().metadata_meanings;
        meaningControl.text(meaningNames[metadataMeanings[metadataName]]);
        
        var metadataValue = this.selectionModel.get("metadataValue");
        valueControl.property("value", metadataValue);
    },
    
    /**
     * Update the metadata names available, show the data type, and render the button.
     */
    updateMetadataOptions: function updateMetadataOptions() {
        var container = d3.select(this.el).select(".choose-metadata");
        var metadataTypes = this.model.get("metadataTypes");
        if(_.size(metadataTypes) === 0) {
            container.html("<h4>No document metadata is available.</h4>");
        } else {
            container.html(this.metadataOptionsTemplate);
            var nameSelect = d3.select(this.el).select(".metadata-name-control");
            var options = nameSelect.selectAll("option")
                .data(Object.keys(metadataTypes));
            options.exit().remove();
            options.enter()
                .append("option")
                .property("value", function(d) {
                    return d;
                })
                .text(function(d) {
                    return tg.str.toTitleCase(d.replace(/_/g, " "));
                });
            
            // Auto select for the user if no metadata option has been chosen.
            if(this.selectionModel.get("metadataName") === "") {
                var metadataMeanings = this.model.get("metadataMeanings");
                var preferredMeaning = "time";
                var preferredName = _.reduce(metadataMeanings, function(result, value, key) {
                    if(value === preferredMeaning) {
                        return key;
                    }
                    return result;
                }, null);
                
                if(preferredName in metadataTypes) {
                    this.selectionModel.set({ "metadataName": preferredName });
                } else {
                    var first = null;
                    for(first in metadataTypes) {
                        break;
                    }
                    this.selectionModel.set({ "metadataName": first });
                }
            }
        }
    },
    
    updateGoToMetadataMapButton: function updateGoToMetadataMapButton() {
        var allowedTypes = { 'int': true, 'float': true };
        var button = d3.select(this.el).select(".metadata-goto-metadata-map-button");
        var metadataName = this.selectionModel.get("metadataName");
        var metadataTypes = this.model.get("metadataTypes");
        if(metadataName in metadataTypes && metadataTypes[metadataName] in allowedTypes) {
            button.style("display", null);
        } else {
            button.style("display", "none");
        }
    },
    
    /**
     * Update whether the user can use the add metadata capabilities (must be
     * logged in).
     */
    updateAddMetadata: function updateAddMetadata() {
        var container = d3.select(this.el).select(".add-metadata");
        if(this.userModel.get("loggedIn") || true) {// TODO make it so the user's logged in status is checked.
            container.html(this.addMetadataTemplate);
        } else {
            container.html("<h4>You must be logged in to add a metadata attribute.</h4>");
        }
    },
    
    events: {
        "change .metadata-name-control": "changeMetadataName",
        "change .metadata-value-control": "changeMetadataValue",
        "click .metadata-clear-selection-button": "clickClearMetadataSelection",
        "click .metadata-goto-metadata-map-button": "clickGoToMetadataMap",
        
        "change .metadata-add-type-control": "changeAddType",
        "click .metadata-add-submit": "clickAddMetadata",
    },
    
    /**
     * Change the selected metadata name.
     */
    changeMetadataName: function changeMetadataName(e) {
        var metadataName = e["target"]["value"];
        this.selectionModel.set({
            "metadataName": metadataName,
        });
    },
    
    /**
     * Change the selected metadata value.
     */
    changeMetadataValue: function changeMetadataValue(e) {
        var metadataValue = e["target"]["value"];
        this.selectionModel.set({
            "metadataValue": metadataValue,
        });
    },
    
    /**
     * Set "metadataName" and let the parent view handle switching views.
     */
    clickClearMetadataSelection: function clickClearMetadataSelection(e) {
        this.selectionModel.set({
            metadataName: "",
            metadataValue: "",
        });
    },
    
    /**
     * Set "metadataName" and let the parent view handle switching views.
     */
    clickGoToMetadataMap: function clickGoToMetadataMap(e) {
        this.viewModel.set({ currentView: "metadata_map" });
    },
    
    getAddMetadataNameFromInput: function getAddMetadataNameFromInput() {
        return d3.select(this.el).select(".metadata-add-name-control").property("value");
    },
    
    getAddMetadataTypeFromSelect: function getAddMetadataTypeFromSelect() {
        var selection = this.$el.find(".metadata-add-type-control").find(":selected");
        return selection.attr("value");
    },
    
    /**
     * The type has been changed.
     */
    changeAddType: function changeAddType(e) {
        // TODO add ability to create ordinal values with the type
    },
    
    /**
     * Verify that the name is not empty.
     * Normalize the name (replace spaces with "_" and put it in lowercase.
     * Submit the query to the server.
     */
    clickAddMetadata: function clickAddMetadata(e) {
        var inputName = this.getAddMetadataNameFromInput();
        var type = this.getAddMetadataTypeFromSelect();
        var name = inputName.replace(/ /g, "_").toLowerCase();
        
        console.log(type);
        
        // TODO if the type is ordinals then require that they be specified in advance
        
        if(name === "") {
            alert("That is an invalid name.");
            return;
        }
        
        var container = d3.select(this.el).select(".metadata-add-messages");
        container.html("");
        var messageToUser = container.append("h4")
            .text("Your request to add "+inputName+"("+tg.site.readableTypes[type]+") is pending...");
        var datasetName = this.selectionModel.get("dataset");
        this.userModel.submitQueryByHash({
            dataset: datasetName,
            dataset_add: ['document_metadata_type'],
            metadata_type: { name: name, datatype: type },
        }, function(data) {
            this.model.get("metadataTypes")[name] = type;
            this.updateMetadataOptions();
            container.html("");
            container.append("h4")
                .text("You successfully added "+inputName+" ("+tg.site.readableTypes[type]+").");
        }.bind(this), function(error) {
            container.html("");
            container.append("h4")
                .text("There was an error adding the new metadata item.");
            console.log(error);
        }.bind(this));
    },
    
    renderHelpAsHtml: function renderHelpAsHtml() {
        return ''+
        '<h4>Metadata Selection</h4>'+
        '<p>Select a metadata attribute by name from the drop down list and click the "Get Started" button to begin labeling documents.</p>'+
        '<h4>Add New Metadata</h4>'+
        '<p>You must be logged in to add a metadata item. Type in the name and select the datatype of the item. Then click "Add Metadata" to send the request to the server. You\'ll be notified once the item has been added.</p>';
    },
    
});

addViewClass([], MetadataView);
