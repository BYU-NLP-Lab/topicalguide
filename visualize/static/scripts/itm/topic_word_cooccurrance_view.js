"use strict";

var UpdateTopicsWordCooccurrance = DefaultView.extend({
    
    readableName: "Topic Word Co-Occurrance",
    shortName: "topic_word_cooccurrance",
    
    messageToUserTemplate:
'Hello, enter the words in pairs that should co-occur together.',
    
    wordsFormTemplate:
'<div class="word-cooc-form-container input-group">'+
'    <div class="input-group-addon">Words</div>'+
'    <input type="text" class="word-cooc-words form-control" placeholder="Comma separated words...">'+
'</div>',

	submitButtonTemplate:
'<button class="word-cooc-submit btn btn-primary">Submit</button>',
    
    initialize: function() {
    },
    
    render: function() {
        this.$el.html(this.messageToUserTemplate + this.wordsFormTemplate + this.submitButtonTemplate);
    },
    
    renderHelpAsHtml: function() {
        return "<p>This is just an example view.</p>";
    },
    
    cleanup: function() {
    },
    
/******************************************************************************
 *                        EVENT HANDLERS
 ******************************************************************************/

	events: {
		'click .word-cooc-submit': 'clickSubmit',
	},
	
	clickSubmit: function clickSubmit(e) {
		var datasetName = this.selectionModel.get('dataset');
		var analysisName = this.selectionModel.get('analysis');
		var constraints = $(this.el).find('.word-cooc-words').val();
		
		var queryHash = {
			datasets: datasetName,
			analyses: analysisName,
			constraints: constraints,
		};
		
		this.dataModel.submitQueryByHash(
			queryHash,
			function callback(data) {
				alert("hurray, done");
				console.log(data);
			}.bind(this),
			this.renderError.bind(this)
		);
	},

});

addViewClass(["ITM"], UpdateTopicsWordCooccurrance);

