"use strict";

var AnalysisWordConstraints = DefaultView.extend({
    
/******************************************************************************
 *                        STATIC VARIABLES
 ******************************************************************************/
    
    readableName: "Analysis Word Constraints",
    shortName: "analysis_word_constraints",
    
    instructionsTemplate:
'<span>'+
'Enter comma separated lists of words into each text box.'+
'</span>',
    
    baseTemplate:
'<div class="row">'+
'   <div class="col-xs-6">'+
'       <h3 class="text-center">Merge Constraints</h3>'+
'       <div class="word-constraints-merge-container">'+
'       </div>'+
'   </div>'+
'   <div class="col-xs-6">'+
'       <h3 class="text-center">Split Constraints</h3>'+
'       <div class="word-constraints-split-container">'+
'       </div>'+
'   </div>'+
'</div>'+
'<div class="row text-center">'+
'   <button class="word-constraints-submit btn btn-primary">'+
'       <span>Submit Constraints</span>'+
'   </button>'+
'</div>'+
'<div class="row">'+
'   <div class="col-xs-6">'+
'       <h3 class="text-center">Existing Merge Constraints</h3>'+
'       <div class="existing-word-constraints-merge-container row text-center">'+
'       </div>'+
'   </div>'+
'   <div class="col-xs-6">'+
'       <h3 class="text-center">Existing Split Constraints</h3>'+
'       <div class="existing-word-constraints-split-container row">'+
'       </div>'+
'   </div>'+
'</div>',
    
    
/******************************************************************************
 *                        INHERITED METHODS
 ******************************************************************************/
    
    initialize: function initialize() {
    },
    
    cleanup: function cleanup() {
    },
    
    render: function render() {
        this.$el.html(this.baseTemplate);
        this.renderConstraintInputs();
        this.renderPreviousConstraints();
    },
    
    renderHelpAsHtml: function renderHelpAsHtml() {
        return "<p>Coming soon...</p>";
    },
    
/******************************************************************************
 *                               HELPER METHODS
 ******************************************************************************/
    
    renderConstraintInputs: function renderConstraintInputs() {
        this.renderMergeInputs(this.$el.find('.word-constraints-merge-container').get(0));
        this.renderSplitInputs(this.$el.find('.word-constraints-split-container').get(0));
    },
    
    renderPreviousConstraints: function renderPreviousConstraints() {
        var existingMergeEl = this.$el.find('.existing-word-constraints-merge-container');
        existingMergeEl.html('<span>Loading...</span>');
        var existingSplitEl = this.$el.find('.existing-word-constraints-split-container');
        existingSplitEl.html('<span>Loading...</span>');
        var datasetName = this.selectionModel.get('dataset');
        var analysisName = this.selectionModel.get('analysis');
        var request = this.getRequest(datasetName, analysisName);
        this.dataModel.submitQueryByHash(
            request,
            function previousConstraintsCallback(data) {
                var mergeData = this.getMergeData(data, datasetName, analysisName);
                var splitData = this.getSplitData(data, datasetName, analysisName);
                this.renderExistingMergeConstraints(existingMergeEl.get(0), mergeData);
                this.renderExistingSplitConstraints(existingSplitEl.get(0), splitData);
            }.bind(this),
            this.renderError.bind(this)
        );
    },
    
    /**
     * selector -- specifies how to find the textboxes to extract words from
     * Return [['word1', 'word2', ...] ...]
     */
    getListsOfListsOfWords: function getListsOfListsOfWords(selector) {
        var that = this;
        var result = [];
        d3.select(this.el).selectAll(selector)
            .each(function() {
                var words = that.csvToList($(this).val());
                if(words.length >= 2) {
                    result.push(words);
                }
            });
        return result;
    },
    
    getMergeConstraints: function getMergeConstraints() {
        return this.getListsOfListsOfWords('.merge-constraint-input');
    },
    
    getSplitConstraints: function getSplitConstraints() {
        return this.getListsOfListsOfWords('.split-constraint-input');
    },
    
/******************************************************************************
 *                              PURE FUNCTIONS
 *          (no this context used except to call other pure functions)
 ******************************************************************************/
    
    getRequest: function getRequest(datasetName, analysisName) {
        return {
            datasets: datasetName,
            analyses: analysisName,
            analysis_attr: ['word_constraints'],
        };
    },
    
    /**
     * Return a list of words with no duplicates or empty strings.
     */
    csvToList: function csvToList(csv) {
        var words = csv.split(',');
        var uniqueWords = _.reduce(
            words, 
            function sanitizeInputs(result, value) {
                result[value.trim().toLowerCase()] = true;
                return result;
            },
            {}
        );
        if('' in uniqueWords) {
            delete uniqueWords[''];
        }
        var filteredWords = _.reduce(
            uniqueWords,
            function filterWords(result, value, key) {
                result.push(key);
                return result;
            },
            []
        );
        return filteredWords;
    },
    
    getMergeData: function getMergeData(data, datasetName, analysisName) {
        return data.datasets[datasetName].analyses[analysisName].word_constraints['merge'];
    },
    
    getSplitData: function getSplitData(data, datasetName, analysisName) {
        return data.datasets[datasetName].analyses[analysisName].word_constraints['split'];
    },
    
    getTextFieldGenerator: function getTextFieldGenerator(classes) {
        var generator = function generator() {
            return '<input class="form-control '+classes+'" type="text"></input>';
        };
        return generator;
    },
    
    renderMergeInputs: function renderMergeInputs(el) {
        var textFieldGenerator = this.getTextFieldGenerator('merge-constraint-input');
        tg.gen.createExtensibleForm(el, textFieldGenerator);
    },
    
    renderSplitInputs: function renderSplitInputs(el) {
        var textFieldGenerator = this.getTextFieldGenerator('split-constraint-input');
        tg.gen.createExtensibleForm(el, textFieldGenerator);
    },
    
    renderExistingMergeConstraints: function renderExistingMergeConstraints(el, data) {
        var $el = $(el);
        if(data.length === 0) {
            $el.addClass('text-center');
            $el.html('<span>No existing merge constraints applied to this analysis.</span>');
        } else {
            this.renderListOfListsOfWords(el, data);
        }
    },
    
    renderExistingSplitConstraints: function renderExistingSplitConstraints(el, data) {
        var $el = $(el);
        if(data.length === 0) {
            $el.addClass('text-center');
            $el.html('<span>No existing split constraints applied to this analysis.</span>');
        } else {
            this.renderListOfListsOfWords(el, data);
        }
    },
    
    /**
     * el -- dom el to operate within
     * lolow -- list of lists of words
     * Return nothing.
     */
    renderListOfListsOfWords: function renderListOfListsOfWords(el, lolow) {
        d3.select(el)
            .data(lolow)
            .enter()
            .append('div')
            .classed('row', true)
            .append('span')
            .text(function(d) {
                return d.join(', ');
            });
    },
    
/******************************************************************************
 *                        EVENT HANDLERS
 ******************************************************************************/

	events: {
		'click .word-constraints-submit': 'clickSubmitConstraints',
	},
	
	clickSubmitConstraints: function clickSubmitConstraints(e) {
		var datasetName = this.selectionModel.get('dataset');
		var analysisName = this.selectionModel.get('analysis');
        console.log('add');
        var merge = this.getMergeConstraints();
        var split = this.getSplitConstraints();
        console.log(merge);
        console.log(split);
		//~ var constraints = $(this.el).find('.word-cooc-words').val();
		//~ 
		//~ var queryHash = {
			//~ datasets: datasetName,
			//~ analyses: analysisName,
			//~ constraints: constraints,
		//~ };
		//~ 
		//~ this.dataModel.submitQueryByHash(
			//~ queryHash,
			//~ function callback(data) {
				//~ alert("hurray, done");
				//~ console.log(data);
			//~ }.bind(this),
			//~ this.renderError.bind(this)
		//~ );
	},

});

addViewClass(["ITM"], AnalysisWordConstraints);

