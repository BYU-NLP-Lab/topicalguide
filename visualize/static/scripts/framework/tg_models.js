/*
 * All of the following models are independent of the rest of the system.
 * Some of the models may depend upon eachother, but none should depend 
 * upon anything outside this file with the exception of libraries.
 */



DEBUG_SELECTION_MODEL = false;
/*
 * The Selection Model is responsible for tracking which specific topic(s), document(s), or word(s) 
 * are selected. It is recommended that the setMany function is used when setting any attributes, 
 * this is so updating many attributes will trigger a single event ("multichange").
 */
var SelectionModel = Backbone.Model.extend({
    
    // This is mostly for reference and convenience, this object doesn't change.
    availableSelections: {
        "dataset": String, 
        "analysis": String, 
        "topic": String, 
        "document": String, 
        "topicNameScheme": String,
    },
    
    initialize: function() {
        var hash = {};
        for(key in this.availableSelections) {
            hash[key] = "";
        }
        this.set(hash);
    },
    
    /**
     * Must be set before use.
     * The data model and selection model reference eachother for certain tasks.
     */
    setDataModel: function(dm) {
        this.dataModel = dm;
    },
    
    /**
     * This function will trigger a "multichange" event.
     * This is preferred for views and the router so multiple events aren't 
     * triggered with each new attribute.
     */
    set: function(attr, options) {
        if(DEBUG_SELECTION_MODEL) console.log("SelectionModel.set before: " + hashToUrl(this.attributes));
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
                resetHelper(toSet, ["analysis", "topic", "document", "topicNameScheme"]);
            } else if("analysis" in toSet) {
                 resetHelper(toSet, ["topic", "topicNameScheme"]);
            }
            if(DEBUG_SELECTION_MODEL) console.log("SelectionModel.set middle: " + hashToUrl(this.attributes));
            Backbone.Model.prototype.set.call(this, toSet, options);
            this.trigger("multichange");
            if(DEBUG_SELECTION_MODEL) console.log("SelectionModel.set after: " + hashToUrl(this.attributes));
        }
    },
    
    /**
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
    
    /**
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
    
    /**
     * Auto select a dataset, analysis, and topic name scheme.
     */
    selectRandom: function() {
        var dataset = "";
        var analysis = "";
        var topicNameScheme = "";
        
        var gdm = this.dataModel;
        var datasets = gdm.getDatasetNames();
        if(datasets.length > 0) {
            dataset = datasets[getRandomIntegerInRange(0, datasets.length)];
            var analyses = gdm.getAnalysisNames(dataset);
            if(analyses.length > 0) {
                analysis = analyses[getRandomIntegerInRange(0, analyses.length)];
            }
        }
        
        this.set({
            dataset: dataset,
            analysis: analysis,
            topicNameScheme: topicNameScheme,
        });
    },
    
    /**
     * Select the first dataset, analysis, and topic name scheme available.
     */
    selectFirst: function(allowOverride) {
        if(!allowOverride && this.get("dataset") !== "") {
            return;
        }
        var dataset = "";
        var analysis = "";
        var topicNameScheme = "";
        
        var gdm = this.dataModel;
        var datasets = gdm.getDatasetNames();
        for(d in datasets) {
            dataset = datasets[d];
            var analyses = gdm.getAnalysisNames(dataset);
            for(a in analyses) {
                analysis = analyses[a];
                break;
            }
            break;
        }
        
        this.set({
            dataset: dataset,
            analysis: analysis,
            topicNameScheme: topicNameScheme,
        });
    },
});


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
        "topicNameScheme": true,
    },
    
    /**
     * models -- must contain the selectionModel, used for storing favorites in local storage
     */
    initialize: function(models) {
        this.selectionModel = models.selectionModel;
        this.listenTo(this.selectionModel, "multichange", this.selectionChanged);
        this.loadFromLocalStorage();
    },
    
    dispose: function() {
        this.remove();
    },
    
    /* 
     * Generates a list of keys to properly save and load items.
     */
    generateKeys: function() {
        var dataset = this.selectionModel.get("dataset");
        var analysis = this.selectionModel.get("analysis");
        var result = {
            "datasets": "datasets",
            "analyses": "dataset-"+dataset+"-analyses",
            "topics": "dataset-"+dataset+"-analysis-"+analysis+"-topics",
            "documents": "dataset-"+dataset+"-analysis-"+analysis+"-documents",
            "topicNameSchemes": "dataset-"+dataset+"-analysis-"+analysis+"-topicNameScheme",
        };
        return result;
    },
    
    /*
     * Save items in their context:
     * datasets is stored in favs-datasets
     * analyses is stored in favs-dataset-<dataset name>-analyses
     * topics is stored in favs-dataset-<dataset name>-analysis-<analysis name>-topics
     * documents and topicNameSchemes are the same as topics
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

/**
 * Used to store view specific settings per page visit.
 */
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

/**
 * The DataModel is responsible for managing data requests and providing convenience functions.
 * Note that the DataModel listens to the selection model so topic names can
 * be pre-loaded and used throughout the site.
 * Most of the pre-loaded data is stored in an HTML script tag on page load and is
 * parsed and stored for quick access.
 * This way refreshing the site ensures the latest datasets and analyses, and 
 * eliminates the need to perform synchronous calls to the web server.
 */
DEBUG_DATA_MODEL = true; // Used to display the api request to the console.
var DataModel = Backbone.Model.extend({
    
    serverInfo: {},
    datasetsAndAnalyses: {},
    analysisTopicNameSchemes: {},
    
    /**
     * models -- the must contain the selectionModel to listen to, used to preload topic names
     */
    initialize: function(models) {
        this.selectionModel = models.selectionModel;
        this.listenTo(this.selectionModel, "change:analysis", this.changeAnalysis);
        
        // Make sure that dataset and analyses data is available.
        var defaultData = JSON.parse($("#global-dataset-and-analyses-info").html());
        this.datasetsAndAnalyses = defaultData['datasets'];
        this.serverInfo = defaultData['server'];
    },
    
    /**
     * Return an object with basic server information.
     */
    getServerInfo: function() {
        return this.serverInfo;
    },
    
    /**
     * Return an object with all of the datasets and analyses, as well as 
     * metadata, metrics, and other information.
     */
    getDatasetsAndAnalyses: function() {
        return this.datasetsAndAnalyses;
    },
    
    /**
     * Synchronous method to get dataset names.
     * Return list of available datasets; empty list if none or error.
     */
    getDatasetNames: function() {
        var result = [];
        for(key in this.datasetsAndAnalyses) {
            result.push(key);
        }
        return result;
    },
    
    /**
     * Synchronous method to get number of documents in the dataset.
     * datasetName -- the name of a dataset
     * Return number of documents in datasetName; 0 if the dataset doesn't exist.
     */
    getDatasetDocumentCount: function(datasetName) {
        result = this.datasetsAndAnalyses[datasetName].metrics["Document Count"];
        return result;
    },
    
    /**
     * Synchronous method to get analysis names.
     * Return list of available analyses; empty list if none or error.
     */
    getAnalysisNames: function(datasetName) {
        result = [];
        for(key in this.datasetsAndAnalyses[datasetName].analyses) {
            result.push(key);
        }
        return result;
    },
    
    /**
     * Synchronous method to get analysis name schemes.
     * Return list of analysis name schemes available; empty if none.
     */
    getTopicNameSchemes: function(datasetName, analysisName) {
        result = [];
        if(datasetName !== "" && analysisName !== "") {
            result = this.datasetsAndAnalyses[datasetName].analyses[analysisName].topic_name_schemes;
        }
        return result;
    },
    
    getDatasetReadableName: function(datasetName) {
        return "name";
    },
    
    /**
     * topicNumber -- the number of the topic
     * Return the name of a topic according to the currently selected dataset, 
     * analysis, and topic name scheme; the "Top3" name if the selected namer 
     * isn't available; the topicNumber as a string otherwise.
     */
    getTopicNameRaw: function(topicNumber) {
        var topicNumberString = topicNumber.toString();
        var nameScheme = this.selectionModel.get("topicNameScheme");
        // Select a default name scheme if none is selected.
        if(nameScheme === "" || nameScheme === undefined || nameScheme === null) {
            nameScheme = "Top3";
        }
        
        var result = topicNumberString;
        try {
            result = this.analysisTopicNameSchemes[topicNumberString][nameScheme];
        } catch(e) {}
        
        if(result === undefined || result === null) {
            result = topicNumberString;
        }
        
        return result;
    },
    
    /**
     * topicNumber -- the number of the topic
     * Return a human readable name.
     */
    getTopicName: function(topicNumber) {
        var name = this.getTopicNameRaw(topicNumber);
        if(name === topicNumber.toString()) {
            return "Topic #" + name;
        } else {
            return name + " (#" + topicNumber + ")";
        }
    },
    
    
    
    /**
     * Synchronous method to get topic names upon a change in analysis.
     */
    changeAnalysis: function() {
        var s = this.selectionModel;
        if(s.get("analysis") !== "") {
            var data = this.synchronousQueryByHash({
                datasets: s.get("dataset"),
                analyses: s.get("analysis"),
                topics: "*",
                topic_attr: ["names"],
            });
            if(data) {
                var temp = {};
                var topics = extractTopics(data, this.selectionModel);
                for(topicNumber in topics) {
                    temp[topicNumber] = topics[topicNumber].names;
                }
                this.analysisTopicNameSchemes = temp;
            } else {
                this.analysisTopicNameSchemes = {};
            }
        }
    },
    
    /**
     * Return the request data if there was no error; null otherwise.
     */
    synchronousQueryByHash: function(request) {
        var result = null;
        this.submitQueryByHash(request, function(data) {
            result = data;
        }, function() {}, false);
        return result;
    },
    
    /**
     * Submit a query to the server, the request hash is turned into a normalized url to ensure that
     * requests look the same when submitted.
     * request - A hash containing the properties being requested.
     * dataReadyCallback - The function called upon success.
     * errorCallback - The function called if there is an error message in the returned data.
     */
    submitQueryByHash: function(request, dataReadyCallback, errorCallback, async) {
        var url = "api?" + hashToUrl(request);
        if(async === undefined || async === null) async = true;
        this.submitQueryByUrl(url, dataReadyCallback, errorCallback, async);
    },
    
    /**
     * Submit a query to the server for json formatted data.
     * url -- The url where the data is found.
     * dataReadyCallback -- The function called upon success.
     * errorCallback -- The function called if there is an error message in the returned data.
     * async -- perform the call asynchronously if true
     * Return nothing.
     */
    submitQueryByUrl: function(url, dataReadyCallback, errorCallback, async) {
        if(DEBUG_DATA_MODEL) console.log(url);
        if(async) {
            d3.json(url, function(error, data) {
                if(error !== null) {
                    errorCallback("Odds are you couldn't connect to your server. Here is some error info: "+JSON.stringify(error));
                } else if("error" in data) {
                    errorCallback(data["error"]);
                } else {
                    dataReadyCallback(data);
                }
            });
        } else {
            var jsonData;
            jQuery.ajax({
                dataType: "json",
                url: url,
                async: async,
                success: dataReadyCallback,
                error: errorCallback,
            });
        }
    },
});

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

var DEBUG_VIEWMODEL = false;
/*
 * The ViewModel is responsible for tracking which view is selected.
 * Bindable events include:
 *      change:rootView -- note that availableViews gets triggered with this one
 *      change:currentView
 *      change:availableViews
 *      change:helpView
 *      change:favsView
 *      change:topicNamesView
 *      change:settingsViews
 */
var ViewModel = Backbone.Model.extend({
    
    initialize: function() {
        var defaults = {
            "rootView": "",
            "currentView": "", 
            "availableViews": "", 
            "helpView": "", 
            "favsView": "", 
            "topicNamesView": "",
            "settingsViews": "",
        };
        this.set(defaults);
    },
    
    availableViewClasses: {},
    availableViewClassPaths: {}, // Used for building the navigation bar.
    helpViewClass: null,
    favsViewClass: null,
    topicNamesViewClass: null,
    settingsViewClasses: {},
    
    /**
     * Add a view. Will not override another existing view.
     * menus - an array with human readable names that will be used to create the 
     *         route and update the navigation bar; null means that the view
     *         does not appear on the navigation bar
     * view - a view class inheriting from DefaultView
     */
    addViewClass: function(menus, viewClass) {
        var shortName = viewClass.prototype.shortName;
        if(shortName in this.availableViewClasses) {
            console.log("View class with short name \""+shortName+"\" already exists.");
            return;
        }
        
        if(menus !== null) {
            this.availableViewClassPaths[shortName] = menus;
        }
        
        this.availableViewClasses[shortName] = viewClass;
        this.set({ "availableViews": this._hashKeysToList(this.availableViewClasses) });
    },
    
    getCurrentViewClass: function() {
        return this.availableViewClasses[this.get("currentView")];
    },
    
    getReadableViewName: function(name) {
        var result = null;
        if(name in this.availableViewClasses) {
            result = this.availableViewClasses[name].prototype.readableName;
        }
        return result;
    },
    
    _hashKeysToList: function(hash) {
        var arr = _.reduce(hash, function(result, val, key) {
            result.push(key);
            return result;
        }, []);
        arr.sort();
        return arr.join(",");
    },
    
    getAvailableViewClassPaths: function() {
        return this.availableViewClassPaths;
    },
    
    /**
     * Used by the router to create part of the URL.
     */
    getCurrentPath: function() {
        return this.get("currentView");
    },
    
    /*
     * Change the view to the one specified. No-op if the name doesn't exist.
     * path - url path to view as string
     */
    changeView: function(path) {
        if(DEBUG_VIEWMODEL) console.log("ViewModel.changeView path=\""+path+"\" settings=\""+hashToUrl(settings)+"\"");
        
        var pathParts = path.split("/")
        var currentView = pathParts[pathParts.length - 1];
        
        if(currentView === "") {
            currentView = this.get("rootView");
        }
        console.log(path);
        this.set({ "currentView": currentView });
    },
    
    hasViewClass: function(name) {
        return name in this.availableViewClasses;
    },
    
    /**
     * attrKey -- one of the attribute keys
     * name -- a name under one of them
     * Return true if name is in the list attrKey; false otherwise.
     */
    _has: function(attrKey, name) {
        var attr = this.attributes[attrKey];
        if(attr === "") {
            return false;
        }
        var uniqueDict = _.reduce(attr.split[","], function(result, n) {
            result[n] = true;
            return result;
        }, {});
        return name in uniqueDict;
    },
    
    /**
     * Set the root view to the given class.
     * Return nothing.
     */
    setRootViewClass: function(rootClass) {
        var shortName = rootClass.prototype.shortName;
        if(shortName in this.availableViewClasses) {
            console.log("Cannot set \""+shortName+"\" as the root view because a view with that name already exists.");
            return;
        }
        this.set({ "rootView": shortName });
        this.addViewClass(null, rootClass);
    },
    
    /**
     * Add a settings view.
     * settingsClass - A class inheriting from default.
     */
    addSettingsClass: function(settingsClass) {
        var shortName = settingsClass.prototype.shortName;
        if(shortName in this.settingsViewClasses) {
            console.log("Settings class with short name \""+shortName+"\" already exists.");
            return;
        }
        
        this.settingsViewClasses[shortName] = settingsClass;
        this.set({ "settingsViews": this._hashKeysToList(this.settingsViewClasses) });
    },
    
    /**
     * Set the help view class. 
     * Warning: only set after the DOM is loaded.
     */
    setHelpViewClass: function(helpViewClass) {
        this.helpViewClass = helpViewClass;
        this.set({ "helpView": helpViewClass.prototype.shortName });
    },
    
    getHelpViewClass: function() {
        return this.helpViewClass;
    },
    
    /**
     * Set the favorites quick select view class.
     * Warning: only set after the DOM is loaded.
     */
    setFavoritesViewClass: function(favsViewClass) {
        this.favsViewClass = favsViewClass;
        this.set({ "favsView": favsViewClass.prototype.shortName });
    },
    
    getFavoritesViewClass: function() {
        return this.favsViewClass;
    },
    
    setTopicNamesViewClass: function(topicNamesViewClass) {
        this.topicNamesViewClass = topicNamesViewClass;
        this.set({ "topicNamesView": topicNamesViewClass.prototype.shortName });
    },
    
    getTopicNamesViewClass: function() {
        this.topicNamesViewClass;
    },
});
