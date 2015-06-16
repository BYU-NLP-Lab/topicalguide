"use strict";

var AnalysisWordConstraints = DefaultView.extend({
    
/******************************************************************************
 *                        STATIC VARIABLES
 ******************************************************************************/
    
    readableName: "Analysis Word Constraints",
    shortName: "analysis_word_constraints",
    
    redirectTemplate:
'<div class="text-center">'+
'   <button class="word-constraints-redirect btn btn-default">'+
'       <span class="glyphicon glyphicon-chevron-left pewter"></span> Datasets'+
'   </button>'+
'   <span> You need to select a dataset and analysis before using this view. </span>'+
'</div>',
    
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
'<div class="row">'+
'   <div class="col-xs-6">'+
'       <h3 class="text-center">Existing Merge Constraints</h3>'+
'       <div class="existing-word-constraints-merge-container row text-center">'+
'       </div>'+
'   </div>'+
'   <div class="col-xs-6">'+
'       <h3 class="text-center">Existing Split Constraints</h3>'+
'       <div class="existing-word-constraints-split-container row text-center">'+
'       </div>'+
'   </div>'+
'</div>'+
'<div class="row text-center">'+
'   <button class="word-constraints-submit btn btn-primary">'+
'       <span>Submit Constraints</span>'+
'   </button>'+
'</div>',
    
    
/******************************************************************************
 *                        INHERITED METHODS
 ******************************************************************************/
    
    initialize: function initialize() {
        this.listenTo(this.selectionModel, 'change:analysis', this.render);
    },
    
    cleanup: function cleanup() {
    },
    
    render: function render() {
        if(this.selectionModel.nonEmpty(['dataset', 'analysis'])) {
            this.$el.html(this.baseTemplate);
            this.renderConstraintInputs();
            this.renderPreviousConstraints();
        } else {
            this.$el.html(this.redirectTemplate);
        }
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
    
    /**
     * selector -- specifies how to find the buttons to extract words from
     * Return [['word1', 'word2', ...] ...]
     */
    getListsOfListsOfWordsFromButtons: function getListsOfListsOfWordsFromButtons(selector, dataAttribute) {
        var that = this;
        var result = [];
        d3.select(this.el).selectAll(selector)
            .each(function() {
                var words = that.csvToList(d3.select(this).attr(dataAttribute));
                result.push(words);
            });
        return result;
    },
    
    getMergeConstraints: function getMergeConstraints() {
        var result = this.getListsOfListsOfWords('.merge-constraint-input');
        var result2 = this.getListsOfListsOfWordsFromButtons('.existing-merge-constraint.list-of-words-selected', 'data-list-of-words');
        return result.concat(result2);
    },
    
    getSplitConstraints: function getSplitConstraints() {
        var result = this.getListsOfListsOfWords('.split-constraint-input');
        var result2 = this.getListsOfListsOfWordsFromButtons('.existing-split-constraint.list-of-words-selected', 'data-list-of-words');
        return result.concat(result2);
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
            $el.html('<span>No existing merge constraints applied to this analysis.</span>');
        } else {
            this.renderListOfListsOfWords(el, data, 'existing-merge-constraint');
        }
    },
    
    renderExistingSplitConstraints: function renderExistingSplitConstraints(el, data) {
        var $el = $(el);
        if(data.length === 0) {
            $el.html('<span>No existing split constraints applied to this analysis.</span>');
        } else {
            this.renderListOfListsOfWords(el, data, 'existing-split-constraint');
        }
    },
    
    /**
     * Tag each element with the listClassTag. Each element
     * has the data-list-of-words set to the list of words associated with the 
     * element. Also, the 'list-of-words-selected' class is set if the list
     * of words is selected by the user. By default everything is selected to
     * start with.
     * el -- dom el to operate within
     * lolow -- list of lists of words
     * listClassTag -- the class tag to label each element with
     * Return nothing.
     */
    renderListOfListsOfWords: function renderListOfListsOfWords(el, lolow, listClassTag) {
        var d3El = d3.select(el).html('');
        console.log(lolow);
        var rows = d3El.selectAll('div')
            .data(lolow)
            .enter()
            .append('div')
            .classed('row', true);
        rows//.append('div')
            .append('span')
            .text(function(d) {
                return d.join(', ') + '  ';
            });
        rows//.append('div')
            .append('button')
            .classed('btn btn-danger', true)
            .style({ padding: '0px 6px' })
            .classed('list-of-words-selected', true)
            .classed(listClassTag, true)
            .attr('data-list-of-words', function(d) {
                return d.join(',');
            })
            .on('click', function(d, i) {
                var elem = d3.select(this);
                var icon = elem.select('span');
                var row = rows.filter(function(d2, i2) { return i2 == i; }).select('span');
                if(icon.classed('glyphicon-minus')) {
                    icon.classed('glyphicon-minus', false);
                    icon.classed('glyphicon-plus', true);
                    elem.classed('btn-danger list-of-words-selected', false);
                    elem.classed('btn-success', true);
                    row.style({ color: 'red' });
                } else {
                    icon.classed('glyphicon-plus', false);
                    icon.classed('glyphicon-minus', true);
                    elem.classed('btn-success', false);
                    elem.classed('btn-danger list-of-words-selected', true);
                    row.style({ color: 'black' });
                }
            })
            .append('span')
            .classed('glyphicon glyphicon-minus', true);
    },
    
/******************************************************************************
 *                        EVENT HANDLERS
 ******************************************************************************/

	events: {
        'click .word-constraints-redirect': 'clickRedirect',
		'click .word-constraints-submit': 'clickSubmitConstraints',
	},
    
    clickRedirect: function clickRedirect(e) {
        this.viewModel.set({ currentView: 'datasets' });
    },
	
	clickSubmitConstraints: function clickSubmitConstraints(e) {
		var datasetName = this.selectionModel.get('dataset');
		var analysisName = this.selectionModel.get('analysis');
        var merge = this.getMergeConstraints();
        var split = this.getSplitConstraints();
        var wordConstraints = {
            'merge': merge,
            'split': split,
        };
        console.log(wordConstraints);
        
		var queryHash = {
			datasets: datasetName,
			analyses: analysisName,
			word_constraints: JSON.stringify(wordConstraints),
		};
		
        this.$el.html(this.loadingTemplate);
		this.dataModel.submitQueryByHash(
			queryHash,
			function callback(data) {
				alert("hurray, done");
				console.log(data);
                var newAnalysisName = data.datasets[datasetName].analyses[analysisName]['modifications']['new_analysis_name'];
                console.log(newAnalysisName);
                this.dataModel.refresh();
                this.selectionModel.set({ analysis: newAnalysisName });
			}.bind(this),
            function onError(msg) {
                this.renderError(msg);
                this.render();
            }.bind(this)
		);
	},

});

addViewClass(["ITM"], AnalysisWordConstraints);

