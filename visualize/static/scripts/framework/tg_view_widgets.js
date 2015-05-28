"use strict";

/**
 * Manages the input of metadata values and ranges.
 */
var MetadataValueView = DefaultView.extend({
    
    readableName: "Metadata Value",
    shortName: "metadata_value",
    
    rangeTemplate:
'<div class="metadata-range-control-container input-group">'+
'    <div class="input-group-addon">From</div>'+
'    <input type="number" class="metadata-range-from form-control" placeholder="From">'+
'    <div class="input-group-addon">To</div>'+
'    <input type="number" class="metadata-range-to form-control" placeholder="To">'+
'</div>',

    valueTemplate:
'<div class="metadata-value-control-container">'+
'    <input class="metadata-value-control form-control" type="text" />'+
'</div>',

    disabledValueTemplate:
'<div class="metadata-value-control-container">'+
'    <input class="metadata-value-control form-control" disabled />'+
'</div>',
    
    initialize: function initialize() {
        var modelDefaults = {
            metadataTypes: {},
        };
        this.model = new Backbone.Model();
        this.model.set(modelDefaults);
    },
    
    cleanup: function cleanup() {},
    
    render: function render() {
        this.$el.html("");
        var sm = this.selectionModel;
        var datasetName = sm.get("dataset");
        var analysisName = sm.get("analysis");
        this.dataModel.submitQueryByHash({
            "datasets": datasetName,
            "analyses": analysisName,
            "dataset_attr": ["document_metadata_types"],
        }, function(data) {
            var types = data.datasets[datasetName].document_metadata_types;
            this.model.set({ metadataTypes: types });
            this.listenTo(this.selectionModel, "change:metadataName", this.updateForm);
            this.listenTo(this.selectionModel, "change:metadataValue", this.updateValueField);
            this.listenTo(this.selectionModel, "change:metadataRange", this.updateRangeField);
            this.updateForm();
        }.bind(this), this.renderError.bind(this));
    },
    
    updateForm: function updateForm() {
        if(this.isMetadataNameSet()) {
            if(this.isRangeType()) {
                this.$el.html(this.rangeTemplate);
                this.updateRangeField();
            } else {
                this.$el.html(this.valueTemplate);
                this.updateValueField();
            }
        } else {
            this.$el.html(this.disabledValueTemplate);
        }
    },
    
    updateValueField: function updateValueField() {
        var value = this.selectionModel.get("metadataValue");
        if(!this.isRangeType()) {
            this.$el.find(".metadata-value-control").val(value);
        }
    },
    
    updateRangeField: function updateRangeField() {
        var range = this.selectionModel.get("metadataRange");
        if(this.isRangeType() && range !== "") {
            var nums = range.split(",");
            this.$el.find(".metadata-range-from").val(nums[0]);
            this.$el.find(".metadata-range-to").val(nums[1]);
            this.$el.find(".metadata-range-control-container").removeClass("has-error");
        }
    },
    
    /**
     * Return true if the metadata name is valid.
     */
    isMetadataNameSet: function isMetadataNameSet() {
        var metadataName = this.selectionModel.get("metadataName");
        var types = this.model.get("metadataTypes");
        return metadataName in types;
    },
    
    /**
     * Return true if the metadataName is associated with a range type.
     */
    isRangeType: function isRangeType() {
        var rangeTypes = {
            "int": true,
            "float": true,
        };
        var metadataName = this.selectionModel.get("metadataName");
        var types = this.model.get("metadataTypes");
        var metadataType = null;
        if(metadataName in types) {
            metadataType = types[metadataName];
        }
        return metadataType in rangeTypes;
    },
    
    events: {
        "change .metadata-value-control": "changeValue",
        "change .metadata-range-from": "changeRange",
        "change .metadata-range-to": "changeRange",
        //~ "focusout .metadata-value-control": "changeValue",
        //~ "focusout .metadata-range-control": "changeRange",
    },
    
    changeValue: function changeValue() {
        var value = this.$el.find(".metadata-value-control").val();
        this.selectionModel.setMetadataValue(value);
    },
    
    changeRange: function changeRange() {
        var from = this.$el.find(".metadata-range-from").val();
        var to = this.$el.find(".metadata-range-to").val();
        if(tg.js.isNumber(from) && tg.js.isNumber(to)) {
            if(Number(to) < Number(from)) { // Display error.
                this.$el.find(".metadata-range-control-container").addClass("has-error");
            } else { // Okay.
                this.selectionModel.setMetadataRange(from, to);
                this.$el.find(".metadata-range-control-container").removeClass("has-error");
            }
        }
    },
    
});
