"use strict";

var TreemapView = DefaultView.extend({

/******************************************************************************
 *                             STATIC VARIABLES
 ******************************************************************************/

    readableName: 'Treemap',
    shortName: 'treemap',
    
    redirectTemplate:
'<div class="text-center">'+
'   <button class="treemap-redirect btn btn-default">'+
'       <span class="glyphicon glyphicon-chevron-left pewter"></span> Datasets'+
'   </button>'+
'   <span> You need to select a dataset and analysis before using this view. </span>'+
'</div>',

    baseTemplate:
'<div class="row">'+
'   <div class="treemap-container col-xs-12">'+
'   </div>'+
'</div>',

/******************************************************************************
 *                            INHERITED METHODS
 ******************************************************************************/

    initialize: function initialize() {
        this.listenTo(this.selectionModel, "change", this.render);
        this.model = new Backbone.Model();
    },
    
    cleanup: function cleanup() {},
    
    render: function render() {
        if(!this.selectionModel.nonEmpty(['dataset', 'analysis'])) {
            this.$el.html(this.redirectTemplate);
        } else {
            this.$el.html(this.baseTemplate);
            if(this.selectionModel.nonEmpty(['document'])) {
                if(this.selectionModel.nonEmpty(['topic'])) {
                    this.renderTopicSimilarity();
                } else {
                    this.selectionModel.set({ topic: '0' });
                }
            } else {
                this.renderDocuments();
            }
        }
    },

/******************************************************************************
 *                            HELPER METHODS
 ******************************************************************************/

    renderDocuments: function renderDocuments() {
        var $treemapContainer = this.$el.find('.treemap-container');
        $treemapContainer.html(this.loadingTemplate);
        
        var datasetName = this.selectionModel.get('dataset');
        var analysisName = this.selectionModel.get('analysis');
        var request = this.getDocumentsRequestObject(datasetName, analysisName);
        
        this.dataModel.submitQueryByHash(
            request,
            function callback(data) {
                $treemapContainer.html('');
                var documentData = data.datasets[datasetName].analyses[analysisName].documents;
                this.model.set({ documentData: documentData });
                
                var formattedData = this.formattedDocumentData(documentData, ['metrics', 'Token Count']);
                this.createTreemap(
                    $treemapContainer.get(0), 
                    {
                        data: formattedData,
                        leafNodeFunction: function leafNodeFunction(d, i) {
                            d3.select(this)
                                .attr('data-tg-document-name', d.name)
                                .classed('tg-select pointer', true);
                        },
                    }
                );
            }.bind(this),
            function errorCallback(msg) {
            }.bind(this)
        );
    },
    
    renderTopicSimilarity: function renderTopicSimilarity() {
        var that = this;
        var $treemapContainer = this.$el.find('.treemap-container');
        $treemapContainer.html(this.loadingTemplate);
        
        var datasetName = this.selectionModel.get('dataset');
        var analysisName = this.selectionModel.get('analysis');
        var documentName = this.selectionModel.get('document');
        var topicNumber = this.selectionModel.get('topic');
        var topicsRequest = this.getDocumentTopicsRequestObject(datasetName, analysisName, documentName, topicNumber);
        
        this.dataModel.submitQueryByHash(
            topicsRequest,
            function callback(data) {
                $treemapContainer.html('');
                var analysis = data.datasets[datasetName].analyses[analysisName];
                var topicData = analysis.documents[documentName]['topics'];
                var pairwiseData = analysis.topics[topicNumber].pairwise;
                this.model.set({ topicData: topicData });
                
                var formattedData = this.formattedTopicData(topicData);
                var pairwiseWordData = pairwiseData['Word Correlation'];
                var pairMin = _.min(pairwiseWordData);
                console.log(pairMin);
                console.log(formattedData);
                var colorScale = d3.scale.linear().domain([pairMin, 1]).range(['#FFEEEE', '#FF0000']);
                //~ var colorScale = d3.scale.pow().exponent(0.7).domain([pairMin, 1]).range(['#FFEEEE', '#FF0000']);
                
                this.createTreemap(
                    $treemapContainer.get(0),
                    {
                        data: formattedData,
                        leafNodeFunction: function leafNodeFunction(d, i) {
                            d3.select(this)
                                .attr('data-tg-topic-number', d.name)
                                .classed('tg-select pointer tg-topic-name-auto-update', true);
                        },
                        leafNodeNamingFunction: function leftNodeNamingFunction(d, i) {
                            return that.dataModel.getTopicName(d.name);
                        },
                        childColorScale: function childColorScale(d) {
                            var correlation = pairwiseWordData[parseInt(d)];
                            console.log(correlation);
                            return colorScale(correlation);
                        },
                    }
                );
            }.bind(this),
            function errorCallback(msg) {
                this.renderError(msg);
            }.bind(this)
        );
    },
    
    getDocumentsRequestObject: function getDocumentsRequestObject(datasetName, analysisName) {
        var result = {
            datasets: datasetName,
            analyses: analysisName,
            documents: '*',
            document_attr: ['metadata', 'metrics'],
            document_continue: 0,
            document_limit: 1000,
        };
        return result;
    },
    
    getDocumentTopicsRequestObject: function getDocumentTopicsRequestObject(datasetName, analysisName, documentName, topicNumber) {
        var result = {
            datasets: datasetName,
            analyses: analysisName,
            documents: documentName,
            document_attr: ['top_n_topics'],
            topics: topicNumber,
            topic_attr: ['pairwise'],
        };
        return result;
    },
    
    
    
/******************************************************************************
 *                             PURE FUNCTIONS
 ******************************************************************************/
    
    /**
     * Puts the documents into the format needed for the createTreemap method.
     */
    formattedDocumentData: function formatedDocumentData(documents, dataAccessList) {
        var result = {
            'name': 'documents',
        };
        
        var children = [];
        
        for(var docName in documents) {
            var obj = {};
            obj['name'] = docName;
            var size = documents[docName];
            for(var index in dataAccessList) {
                var accessor = dataAccessList[index];
                size = size[accessor];
            }
            obj['size'] = size;
            children.push(obj);
        }
        result['children'] = children;
        
        return result;
    },
    
    /**
     * Puts the topics into the format needed for the createTreemap method.
     */
    formattedTopicData: function formatedTopicData(topics) {
        var result = {
            'name': 'topics',
        };
        
        var children = [];
        
        for(var num in topics) {
            var obj = {};
            obj['name'] = num;
            var size = topics[num];
            obj['size'] = size;
            children.push(obj);
        }
        result['children'] = children;
        
        return result;
    },
    
    /**
     * el -- the element to render the svg in
     * options -- contains the following:
     * data -- data in the format of { name: name, children: [..], size: optional }
     *         where children is an object like the parent
     *         leaf nodes must have the "size" attribute
     * margin -- { top: 40, right: 10, bottom: 10, left: 10 }
     * width -- number
     * height -- number
     */
    createTreemap: function createTreemap(el, options) {
        var defaults = {
            data: {},
            margin: { top: 0, right: 0, bottom: 0, left: 0 },
            width: 960,
            height: 500,
            parentColorScale: d3.scale.category20c(),
            childColorScale: d3.scale.category20c(),
            leafNodeFunction: function() {},
            leafNodeNamingFunction: function(d) { return d.name; },
        };
        var options = _.extend({}, defaults, options);
        console.log('Options:');
        console.log(options);
        
        var d3El = d3.select(el);
        var treemap = d3.layout.treemap()
            .size([options.width, options.height])
            .sticky(true)
            .value(function (d) { return d.size; });
        
        var div = d3El.append('div')
            .classed('.treemap-div', true)
            .style('position', 'relative')
            .style("width", (options.width + options.margin.left + options.margin.right) + "px")
            .style("height", (options.height + options.margin.top + options.margin.bottom) + "px")
            .style("left", options.margin.left + "px")
            .style("top", options.margin.top + "px");
        
        var node = div.datum(options.data)
            .selectAll('.node')
            .data(treemap.nodes)
            .enter()
            .append('div')
            .classed('node', true)
            .each(function(d, i) {
                d.children ? null : options.leafNodeFunction.call(this, d, i);
            })
            .style({ 
                'border': 'solid 1px white', 
                'font': '10px sans-serif', 
                'line-height': '12px',
                'overflow': 'hidden',
                'position': 'absolute',
                'text-indent': '2px',
            })
            .call(position)
            .style('background', function(d) { return d.children ? options.parentColorScale(d.name) : options.childColorScale(d.name); })
            .text(function(d) { return d.children ? null : options.leafNodeNamingFunction(d); });
        
        function position() {
            this.style("left", function(d) { return d.x + "px"; })
                .style("top", function(d) { return d.y + "px"; })
                .style("width", function(d) { return Math.max(0, d.dx - 1) + "px"; })
                .style("height", function(d) { return Math.max(0, d.dy - 1) + "px"; });
        }
    },
    
/******************************************************************************
 *                           EVENT HANDLERS
 ******************************************************************************/
    
    events: {
        'click .treemap-redirect': 'clickRedirect',
    },
    
    clickRedirect: function clickRedirect() {
        this.viewModel.set({ currentView: 'datasets' });
    },
    
});

addViewClass(['Visualizations'], TreemapView);
