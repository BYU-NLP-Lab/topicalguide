/*
 * All of the following models are independent of the rest of the system.
 * Some of the models may depend upon eachother, but none should depend 
 * upon anything outside this file with the exception of libraries.
 */

var UserModel = Backbone.Model.extend({
    
    initialize: function() {
        this.set({ loggedIn: false });
    },
    
    submitQueryByHash: function(sendData, dataReadyCallback, errorCallback) {
        $.ajax({
                type: "POST",
                url: "http://"+window.location.host+"/user-api",
                data: sendData,
                dataType: "json",
                
            })
            .done(function(data, textStatus, jqXHR) {
                if("error" in data) {
                    errorCallback(data["error"]);
                } else {
                    dataReadyCallback(data);
                }
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                errorCallback(errorThrown);
            });
    },
});
globalUserModel = new UserModel();


DEBUG_DATA_MODEL = true;
/*
 * The DataModel is responsible for managing the dataset and analysis data locally.
 * The localStorage variable is used so other browser windows will have the same data available to them.
 * The data is stored as localStorage["data-"+requestUrl] = JSON.stringify(data).
 */
var DataModel = Backbone.Model.extend({
    
    // TODO the following requests are common enough that they should be be made convenient.
    // Maybe even pre-load the information.
    getDatasetsAndAnalyses: function() {
    },
    
    getDatasetNames: function() {
    },
    
    getAnalysisNames: function() {
    },
    
    getTopicNames: function() {
    },
    
    /*
     * Submit a query to the server, the request hash is turned into a normalized url to ensure that
     * requests look the same when submitted.
     * request - A hash containing the properties being requested.
     * dataReadyCallback - The function called upon success.
     * errorCallback - The function called if there is an error message in the returned data.
     */
    submitQueryByHash: function(request, dataReadyCallback, errorCallback) {
        var url = "api?" + hashToUrl(request);
        this.submitQueryByUrl(url, dataReadyCallback, errorCallback);
    },
    
    /*
     * Submit a query to the server for json formatted data.
     * url - The url where the data is found.
     * dataReadyCallback - The function called upon success.
     * errorCallback - The function called if there is an error message in the returned data.
     */
    submitQueryByUrl: function(url, dataReadyCallback, errorCallback) {
        if(DEBUG_DATA_MODEL) console.log(url);
        var storageKey = "data-"+url;
        if(hasLocalStorage() && storageKey in localStorage) {
            dataReadyCallback(JSON.parse(localStorage[storageKey]));
        } else {
            d3.json(url, function(error, data) {
                if(error !== null) {
                    errorCallback("Odds are you couldn't connect to your server. Here is some error info: "+JSON.stringify(error));
                } else if("error" in data) {
                    errorCallback(data["error"]);
                } else {
                    if(hasLocalStorage()) {
                        try {
                            localStorage[storageKey] = JSON.stringify(data);
                        } catch(e) {
                            deletePrefixFromHash("data-", localStorage);
                            try {
                                localStorage[storageKey] = JSON.stringify(data);
                            } catch(e) {}
                        }
                    }
                    dataReadyCallback(data);
                }
            });
        }
    },
});
var globalDataModel = new DataModel();

DEBUG_SELECITON_MODEL = false;
/*
 * The Selection Model is responsible for tracking which specific topic(s), document(s), or word(s) 
 * are selected. It is recommended that the setMany function is used when setting any attributes, 
 * this is so updating many attributes will trigger a single event ("multichange").
 */
var SelectionModel = Backbone.Model.extend({
    
    availableSelections: {
        "dataset": String, 
        "analysis": String, 
        "topic": String, 
        "document": String, 
        "word": String
    },
    
    initialize: function() {
        var hash = {};
        for(key in this.availableSelections) {
            hash[key] = "";
        }
        this.set(hash);
    },
    
    /*
     * This function will trigger a "multichange" event.
     * This is preferred for views and the router so multiple events aren't triggered with each
     * new attribute.
     */
    set: function(attr, options) {
        if(DEBUG_SELECITON_MODEL) console.log("SelectionModel.set before: " + hashToUrl(this.attributes));
        // Some items need to trigger events such as change:topic if the dataset or analysis changes.
        // This function helps trigger those changes in attributes.
        var resetHelper = function (toSet, itemsToTrigger) {
            for(i=0; i<itemsToTrigger.length; i++) {
                if(!(itemsToTrigger[i] in toSet)) {
                    toSet[itemsToTrigger[i]] = "";
                    if(this.attributes[itemsToTrigger[i]] === "") {
                        delete this.attributes[itemsToTrigger[i]];
                    }
                }
            }
        }.bind(this);
        
        var toSet = {};
        var signalTrigger = false;
        for(key in attr) {
            if(key in this.availableSelections && attr[key] !== this.get(key)) {
                signalTrigger = true;
                toSet[key] = attr[key];
            }
        }
        
        if(signalTrigger) {
            if("dataset" in toSet) {
                resetHelper(toSet, ["analysis", "topic", "document", "word"]);
            } else if("analysis" in toSet) {
                 resetHelper(toSet, ["topic"]);
            }
            if(DEBUG_SELECITON_MODEL) console.log("SelectionModel.set middle: " + hashToUrl(this.attributes));
            Backbone.Model.prototype.set.call(this, toSet, options);
            this.trigger("multichange");
            if(DEBUG_SELECITON_MODEL) console.log("SelectionModel.set after: " + hashToUrl(this.attributes));
        }
    },
    
    /*
     * Ensure that the given items are non-empty strings.
     * Return true if they are non-empty; false otherwise.
     */
    nonEmpty: function(list) {
        for(i=0; i<list.length; i++) {
            if(this.get(list[i]) === "") {
                return false;
            }
        }
        return true;
    },
    
    /*
     * Pass in a list of items to get, if the item exists it will be returned in the hash.
     */
    getListed: function(list) {
        var hash = {};
        for(i=0; i<list.length; i++) {
            if(this.has(list[i])) {
                hash[list[i]] = this.get(list[i]);
            }
        }
        return hash;
    },
});
var globalSelectionModel = new SelectionModel();

/*
 * The Favorites Model allows the user to select favorites.
 * The events "addedFavorites" and "removedFavorites" are triggered 
 * when favorites are added or removed, respectively. Also, the "multichange" is triggered any time
 * something has changed, but if several items are changed in one call "multichange" is triggered once.
 * This depends upon the SelectionModel to make sure that the correct favorites are loaded.
 */
var FavoritesModel = Backbone.Model.extend({
    
    // The schema for this model.
    availableFavorites: {
        "datasets": true,
        "analyses": true,
        "topics": true,
        "documents": true,
        "words": true,
    },
    
    initialize: function() {
        this.listenTo(globalSelectionModel, "multichange", this.selectionChanged);
        this.loadFromLocalStorage();
    },
    
    dispose: function() {
        this.remove();
    },
    
    /* 
     * Generates a list of keys to properly save and load items.
     */
    generateKeys: function() {
        var dataset = globalSelectionModel.get("dataset");
        var analysis = globalSelectionModel.get("analysis");
        var result = {
            "datasets": "datasets",
            "analyses": "dataset-"+dataset+"-analyses",
            "topics": "dataset-"+dataset+"-analysis-"+analysis+"-topics",
            "documents": "dataset-"+dataset+"-analysis-"+analysis+"-documents",
            "words": "dataset-"+dataset+"-analysis-"+analysis+"-words",
        };
        return result;
    },
    
    /*
     * Save items in their context:
     * datasets is stored in favs-datasets
     * analyses is stored in favs-dataset-<dataset name>-analyses
     * topics is stored in favs-dataset-<dataset name>-analysis-<analysis name>-topics
     * documents and words are the same as topics
     */
    saveToLocalStorage: function() {
        if(hasLocalStorage()) {
            var keys = this.generateKeys();
            for(key in keys) {
                localStorage["favs-"+keys[key]] = JSON.stringify(this.attributes[key]);
            }
        }
    },
    
    // Reverse of saving.
    loadFromLocalStorage: function() {
        if(hasLocalStorage()) {
            var toSet = {};
            var keys = this.generateKeys();
            for(key in keys) {
                var localKey = "favs-"+keys[key];
                if(localKey in localStorage) {
                    toSet[key] = JSON.parse(localStorage[localKey]);
                } else {
                    toSet[key] = {};
                }
            }
            this.set(toSet);
        }
    },
    
    /*
     * Remove all locally stored favorites.
     * Return nothing.
     */
    deleteAllLocalStorage: function() {
        if(hasLocalStorage()) {
            for(key in localStorage) {
                if(key.slice(0,5) === "favs-") {
                    delete localStorage[key];
                }
            }
        }
    },
    
    selectionChanged: function() {
        this.loadFromLocalStorage();
        this.trigger("change");
        this.trigger("multichange");
    },
    
    add: function(attr) {
        var toSet = {};
        var isChanged = false;
        for(key in attr) {
            // Only pay attention to valid attributes.
            if(key in this.availableFavorites) {
                var attribute = this.get(key);
                if(key in toSet) {
                    attribute = toSet[key];
                }
                // Don't add duplicates.
                if(!(attr[key] in attribute)) {
                    attribute[attr[key]] = true;
                    toSet[key] = attribute;
                    isChanged = true;
                }
            }
        }
        // Trigger events.
        if(isChanged) {
            this.set(toSet);
            this.saveToLocalStorage();
            this.trigger("addedFavorites");
            this.trigger("multichange");
        }
    },
    
    remove: function(attr) {
        var toSet = {};
        var isChanged = false;
        for(key in attr) {
            // Only pay attention to valid attributes.
            if(key in this.availableFavorites) {
                var attribute = this.get(key);
                if(key in toSet) {
                    attribute = toSet[key];
                }
                // Don't add duplicates.
                if(attr[key] in attribute) {
                    delete attribute[attr[key]];
                    toSet[key] = attribute;
                    isChanged = true;
                }
            }
        }
        // Trigger events.
        if(isChanged) {
            this.set(toSet);
            this.saveToLocalStorage();
            this.trigger("removedFavorites");
            this.trigger("multichange");
        }
    },
    
    /*
     * Return true if value is a favorite; false otherwise.
     * key - One of datasets, analyses, etc.
     * value - The dataset, analysis, etc., in question.
     */
    has: function(key, value) {
        if(key in this.attributes) {
            if(value in this.attributes[key]) {
                return true;
            }
        }
        return false;
    },
    
    /*
     * If the value is not in the selected key, add the value; otherwise remove the value.
     * Trigger appropriate changes.
     */
    toggle: function(key, value) {
        if(key in this.attributes) {
            var attribute = this.get(key);
            if(value in attribute) {
                delete attribute[value];
            } else {
                attribute[value] = true;
            }
            this.saveToLocalStorage();
            this.trigger("change:"+key);
            this.trigger("change");
        }
    },
    
});
var globalFavoritesModel = new FavoritesModel();


var SettingsModel = Backbone.Model.extend({
    
    selectionModel: null,
    viewPath: null,
    
    setSelectionModel: function(selectionModel) {
        this.selectionModel = selectionModel;
    },
    
    setViewPath: function(viewPath) {
        this.viewPath = viewPath;
    },
    
    generateKey: function() {
        if(this.selectionModel && this.viewPath) {
            return "settings-"+this.selectionModel.get("dataset")+"-"+
                   this.selectionModel.get("analysis")+"-"+this.viewPath;
        } else {
            return null;
        }
    },
    
    load: function() {
        var settingsKey = this.generateKey();
        if(hasLocalStorage() && settingsKey && settingsKey in localStorage) {
            var savedSettings = JSON.parse(localStorage[settingsKey]);
            this.set(_.extend({}, this.attributes, savedSettings));
        }
    },
    
    save: function() {
        var settingsKey = this.generateKey();
        if(hasLocalStorage() && settingsKey) {
            localStorage[settingsKey] = JSON.stringify(this.attributes);
        }
    },
    
    set: function(attr, options) {
        Backbone.Model.prototype.set.call(this, attr, options);
        this.save();
    },
});
