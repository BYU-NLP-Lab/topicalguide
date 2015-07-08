'use strict';

/**
 * update methods read the model (respond to model updates) and update the display accordingly
 * change/click methods respond to user interaction and change the models triggering the appropriate events
 * render methods that create the visualization based on whatever settings and data are available
 */
var MetadataMapView = DefaultView.extend({

/******************************************************************************
 *                             STATIC VARIABLES
 ******************************************************************************/

    readableName: "Metadata Map",
    shortName: "metadata_map",
    
    redirectTemplate:
'<div class="text-center">'+
'   <button class="metadata-map-redirect btn btn-default">'+
'       <span class="glyphicon glyphicon-chevron-left pewter"></span> Metadata'+
'   </button>'+
'   <span> You need to select a metadata item before using this view. </span>'+
'</div>',
    
    mainTemplate: 
'<div id="metadata-map-view-container" class="col-xs-9" style="display: inline; float: left;">'+
'	<div id="metadata-map-view" class="container-fluid">'+
'       <svg width="720" height="720" viewBox="0, 0, 800, 800" preserveAspectRatio="xMidYMin meet">'+
'           <g id="metadata-map-distribution"></g>'+
'           <g id="metadata-map-labeled"></g>'+
'           <g id="metadata-map-xaxis"></g>'+
'           <g id="metadata-map-documents"></g>'+
'       </svg>'+
'   </div>'+
'	<div id="document-info-view-container" class="container-fluid"></div>'+
'</div>'+
'<div id="metadata-map-controls" class="col-xs-3 text-center" style="display: inline; float: left;">'+
'   <h4><b>Selected Document</b></h4>'+
'   <hr />'+
'   <div>'+
'       <label for="selected-document">Document:</label><br />'+
'       <span id="selected-document"></span>'+
'   </div>'+
'   <div>'+
'       <label for="document-value-control">Value:</label>'+
'       <input id="document-value-control" type="text" class="form-control" name="Value" placeholder="Enter value"></input>'+
'   </div>'+
'   <hr />'+
'   <h4><b>Server Requests</b></h4>'+
'   <hr />'+
'   <div>'+
'       <button id="save-changes" class="btn btn-default">Save Changes</button>'+
//~ '       <br/><br/>'+
//~ '       <button id="get-documents" class="btn btn-default">Get Documents</button>'+
'   </div>'+
'</div>',
    
    helpHtml:
'<div><p>Documentation coming soon.</p></div>',

/******************************************************************************
 *                           INHERITED METHODS
 ******************************************************************************/

    initialize: function initialize() {
        var defaults = {
            
        };
        this.selectionModel.on("change:analysis", this.render, this);
        this.model = new Backbone.Model(); // Used to store document data.
        this.model.set({
            // The document data.
            documents: [], // Array of objects { doc: "docname", metadata: { labeled: {}, unlabeled: {}, userLabeled: {} } }
            documentNames: {}, // Map document names to their information
            metadataName: '',
            metadataType: '',
            
            // For all topics
            topicColorScale: tg.color.getDiscreteColorScale(['0', '1', '2'], tg.color.pastels),
            
            // Dimensions of svg element
            svgWidth: 800,
            svgHeight: 800,
            
            // Dimensions of svg viewBox.
            width: 800,
            height: 800,
            
            // Dimensions of the circles.
            documentHeight: 20,
            documentWidth: 20,
            //~ pieChartRadius: 60, // Not used.
            
            // Duration of the transitions.
            duration: 400, // 4/10 of a second
            
            textHeight: 16,
            
            // Needed attributes for the document transitions and document events
            xScale: d3.scale.linear().domain([0, 0]).range([0, 0]),
            labeledYCoord: 0, // y coordinate offset for the labeled area
            unlabeledYCoord: 0,
            unlabeledDocumentCount: 0, // The number of unlabeled docs to show in the queue
            unlabeledDocumentOrder: {}, // Object specifying the document order.
            xAxisLength: 1,
            
            currentDocumentValue: 0,
        });
        
        // Event bindings.
        this.listenTo(this.selectionModel, 'change:document', this.changeDocumentSelection);
        this.listenTo(this.selectionModel, 'change:analysis', this.render);
        this.listenTo(this.selectionModel, 'change:metadataName', this.render);
        this.listenTo(this.selectionModel, 'change:topic', this.renderGroupHierarchy);
        
        this.listenTo(this.model, 'change:documents', this.renderGroupHierarchy);
        this.listenTo(this.model, 'change:metadataTypes', this.updateMetadataOptions);
        this.listenTo(this.model, 'change:svgWidth', this.changeSVGWidth);
        this.listenTo(this.model, 'change:svgHeight', this.changeSVGHeight);
        //~ this.listenTo(this.model, 'change', this.updateMap);
        
        $(window).on('resize', this.resizeWindowEvent.bind(this));
    },
    
    cleanup: function cleanup() {
        $(window).off('resize', this.resizeWindowEvent.bind(this));
    },
    
    /**
     * Entry point to start visualization.
     */
    render: function render() {
        this.$el.empty();
        if(this.selectionModel.nonEmpty(['dataset', 'analysis', 'metadataName'])) {
            this.$el.html(this.loadingTemplate);
            
            var datasetName = this.selectionModel.get('dataset');
            var analysisName = this.selectionModel.get('analysis');
            var metadataName = this.selectionModel.get('metadataName');
            var request = this.getRequestHash(datasetName, analysisName, metadataName);
            
            this.dataModel.submitQueryByHash(
                request,
                function callback(data) {
                    this.$el.html(this.mainTemplate);
                    
                    // Make sure the dimensions of the svg element are correct.
                    this.resizeWindowEvent(null);
                    this.updateDocumentSelection();
                    
                    var documents = data.datasets[datasetName].analyses[analysisName].documents;
                    var formattedData = this.formatData(documents, metadataName);
                    var metadataType = data.datasets[datasetName].document_metadata_types[metadataName];
                    this.model.set({ metadataName: metadataName, metadataType: metadataType });
                    this.model.set({ documents: formattedData.documents, documentNames: formattedData.documentNames, topicColorScale: formattedData.topicColorScale });
                }.bind(this),
                function errorCallback(msg) {
                    this.renderError(msg);
                }.bind(this)
            );
        } else {
			this.$el.html(this.redirectTemplate);
        }
    },
    
    /**
     * Return html of help message to user.
     */
    renderHelpAsHtml: function renderHelpAsHtml() {
        return this.helpHtml;
    },

/******************************************************************************
 *                           HELPER METHODS
 ******************************************************************************/

    /**
     * Gathers all of the data to render each component of the metadata map.
     * Can be called at any time to transition everything to its place based on the
     * data.
     * WARNING: The only time this shouldn't be called is when the user is 
     * dragging a document as there will be a conflict between the user's events
     * and the transition events.
     */
    renderGroupHierarchy: function renderGroupHierarchy() {
        var that = this;
        
        var distribution = this.$el.find('#metadata-map-distribution');
        var labeled = this.$el.find('#metadata-map-labeled');
        var xaxis = this.$el.find('#metadata-map-xaxis');
        var documents = this.$el.find('#metadata-map-documents');
        
        var width = this.model.get('width');
        var height = this.model.get('height');
        var metadataName = this.model.get('metadataName');
        var metadataType = this.model.get('metadataType');
        var documentData = this.model.get('documents');
        var topicColorScale = this.model.get('topicColorScale');
        var selectedDocument = this.selectionModel.get('document');
        
        var boxThickness = 1.5;
        var extraBuffering = 1.5;
        var docWidth = 20;
        var docHeight = 20;
        var sideBuffer = boxThickness + extraBuffering + docWidth/2;
        var xAxisWidth = width - 2*sideBuffer;
        var transitionDuration = 600;
        var xScale = this.createAxisScale(metadataName, metadataType, xAxisWidth);
        
        var xAxisLabel = tg.str.toTitleCase(this.model.get('metadataName').replace(/_/g, ' '));
        
        var componentBuffer = 5;
        var distH = 200;
        var labeledH = boxThickness + extraBuffering + docHeight;
        var distY = 0;
        var labeledY = distH + componentBuffer + labeledH/2;
        var xAxisY = labeledY + componentBuffer + labeledH/2;
        
        var distData = that.getTopicDistributionData(xScale.domain());
        var distYScale = d3.scale.linear().domain([distData.min, distData.max]);
        
        distribution.attr('transform', 'translate('+sideBuffer+','+distY+')');
        labeled.attr('transform', 'translate('+sideBuffer+','+labeledY+')');
        xaxis.attr('transform', 'translate('+sideBuffer+','+xAxisY+')');
        
        tg.gen.createLineGraph(distribution.get(0), {
            interpolate: 'linear', 
            height: distH,
            width: xAxisWidth,
            xScale: xScale,
            yScale: distYScale,
            data: distData.lines,
            colorScale: topicColorScale,
            lineFunction: function(d, i) {
                d3.select(this)
                    .attr('data-tg-topic-number', d.name)
                    .classed('tg-tooltip', true);
            },
            transitionDuration: transitionDuration,
        });
        this.createLabeledArea(labeled.get(0), {
            width: xAxisWidth,
            docWidth: docWidth,
            docHeight: docHeight,
            boxThickness: boxThickness,
            extraBuffering: extraBuffering,
            duration: transitionDuration,
        });
        this.createXAxis(xaxis.get(0), {
            width: xAxisWidth,
            xScale: xScale,
            duration: transitionDuration/4,
            label: xAxisLabel,
            doneTransitioningCallback: function() {
                var xAxisH = that.getXAxisHeight(xaxis.get(0));
                var docQueueY = xAxisY + xAxisH + componentBuffer;
                documents.attr('transform', 'translate('+sideBuffer+','+docQueueY+')');
                that.createDocuments(documents.get(0), {
                    labeledY: labeledY - docQueueY,
                    width: xAxisWidth,
                    docWidth: docWidth,
                    docHeight: docHeight,
                    selectedDocument: selectedDocument,
                    maxQueueLength: 20,
                    xScale: xScale,
                    metadataName: metadataName,
                    metadataType: metadataType,
                    data: documentData,
                    updatedDocumentValue: function(d, i) {
                        that.redrawDistribution();
                        that.updateDocumentSelection();
                    },
                    doneDragging: function() {
                        that.renderGroupHierarchy();
                    },
                    selectedDocumentFunction: function(d, i) {
                        that.selectionModel.set({ document: d.name });
                    },
                    getDocumentColor: function(d, i) { // Requires that topTopic is attached to each document object.
                        return topicColorScale(d.topTopic);
                    },
                });
            },
        });
    },
    
    /**
     * Quickly redraws the distribution.
     */
    redrawDistribution: function redrawDistribution() {
        var distribution = this.$el.find('#metadata-map-distribution');
        
        var that = this;
        
        var metadataName = this.model.get('metadataName');
        var metadataType = this.model.get('metadataType');
        var topicColorScale = this.model.get('topicColorScale');
        
        var xScale = this.createAxisScale(metadataName, metadataType, xAxisWidth);
        var distH = 200;
        var width = this.model.get('width');
        var boxThickness = 1.5;
        var extraBuffering = 1.5;
        var docWidth = 20;
        var sideBuffer = boxThickness + extraBuffering + docWidth/2;
        var xAxisWidth = width - 2*sideBuffer;
        var distData = that.getTopicDistributionData(xScale.domain());
        var distYScale = d3.scale.linear().domain([distData.min, distData.max]);
        console.log(distData.lines);
        tg.gen.createLineGraph(distribution.get(0), {
            interpolate: 'linear', 
            height: distH,
            width: xAxisWidth,
            xScale: xScale,
            yScale: distYScale,
            data: distData.lines,
            colorScale: topicColorScale,
            lineFunction: function(d, i) {
                d3.select(this)
                    .attr('data-tg-topic-number', d.name)
                    .classed('tg-tooltip', true);
            },
            transitionDuration: 50,
        });
    },
    
    getTopicDistributionData: function getTopicDistributionData(xDomain) {
        var that = this;
        var selectedTopic = this.selectionModel.get('topic');
        var metadataName = this.model.get('metadataName');
        var rawData = this.model.get('documentNames');
        if(selectedTopic === '') {
            var zeros = [];
            for(var i = 0; i < 100; i++) { zeros.push(0); }
            return { lines: { name: '', points: zeros }, min: 0, max: 1 };
        }
        var result = [
            { name: selectedTopic, points: [] },
            //~ { name: '1', points: [] },
            //~ { name: '2', points: [] },
            //~ { name: '3', points: [] },
            //~ { name: '4', points: [] },
            //~ { name: '5', points: [] },
            //~ { name: '6', points: [] },
            //~ { name: '7', points: [] },
        ];
        for(var docName in rawData) {
            var docData = rawData[docName]
            var topics = docData.topics;
            for(var index in result) {
                var obj = result[index];
                if(topics[obj.name] !== undefined) {
                    if(metadataName in docData.userLabeled) {
                        obj.points.push([docData.userLabeled[metadataName], topics[obj.name]]);
                    } else if(metadataName in docData.labeled) {
                        obj.points.push([docData.labeled[metadataName], topics[obj.name]]);
                    }
                }
            }
        }
        _.forEach(result, function(val) {
            this.sortPoints(val.points);
            var pts = val.points;
            var tokenTotal = _.reduce(pts, function(r, v) { r += v[1]; return r; }, 0); // Count tokens (y values).
            pts = _.map(pts, function(v) { return [v[0], v[1]/tokenTotal]; }); // Normalize y values.
            if(pts.length === 0) {
                val.points = [];
            } else {
                //~ val.points = tg.lines.kernelDensityEstimation(pts, [pts[0][0], pts[pts.length-1][0], 100], tg.lines.getH(pts), tg.lines.epanechnikovKernel);
                console.log(tg.lines.getH(pts)/3);
                val.points = tg.lines.kernelDensityEstimation(pts, [xDomain[0], xDomain[1], 100], tg.lines.getH(pts)/3, tg.lines.gaussianKernel);
                console.log(val.points);
            }
        }, this);
        
        var max = _.reduce(result, function(tempR, line) {
            var tempMax = _.reduce(line.points, function(r, val) { return r > val[1]? r: val[1]; }, 0);
            return tempR > tempMax? tempR: tempMax;
        }, 0);
        
        return {
            lines: result,
            min: 0,
            max: max,
        };
    },

/******************************************************************************
 *                             PURE FUNCTIONS
 ******************************************************************************/
    
    /**
     * Modifies the points array in place.
     */
    sortPoints: function sortPoints(points) {
        points.sort(function(a, b) { return a[0] - b[0]; });
    },
    
    getRequestHash: function getRequestHash(datasetName, analysisName, metadataName) {
        return {
            datasets: datasetName,
            dataset_attr: ['document_metadata_types'],
            analyses: analysisName,
            documents: '*',
            document_limit: 1000,
            document_continue: 0,
            document_attr: ['metadata_predictions', 'top_n_topics'],
            metadata_name: metadataName,
        };
    },
    
    formatData: function formatData(documents, metadataName) {
        var formatted = _.reduce(documents, function reducer(result, value, key) {
            var temp = {};
            temp['labeled'] = {};
            var unlabeled = {};
            unlabeled[metadataName] = value.metadata_predictions[metadataName];
            temp['unlabeled'] = unlabeled;
            temp['userLabeled'] = {};
            temp['topics'] = value.topics;
            var topTopic = _.max(value.topics, function(v, k) {
                return v;
            });
            var docElement = {
                name: key,
                metadata: temp,
                queuePos: 0,
                topTopic: topTopic,
            };
            result['documents'].push(docElement);
            result['documentNames'][key] = temp;
            return result;
        }, { documents: [], documentNames: {} });
        // Extract all topic numbers present and create a color scale for them.
        var topicNumbers = _.reduce(formatted.documents, function(result, docObj, index) {
            var topicKeys = docObj.metadata.topics;
            result = _.assign({}, result, topicKeys);
            return result;
        }, {});
        var allTopics = Object.keys(topicNumbers);
        allTopics.sort();
        formatted.topicColorScale = tg.color.getDiscreteColorScale(allTopics, tg.color.pastels);
        return formatted;
    },
    
    createLabeledArea: function createLabeledArea(g, options) {
        var defaults = {
            width: 800,
            docWidth: 20,
            docHeight: 20,
            boxThickness: 1.5,
            extraBuffering: 1.5,
            duration: 600,
        };
        
        var o = _.extend({}, defaults, options);
        
        
        var xbase = o.docWidth/2 + o.extraBuffering;
        var ybase = o.docHeight/2 + o.extraBuffering;
        var data = [
            { // Outer rect.
                x: -(xbase + o.boxThickness),
                y: -(ybase + o.boxThickness),
                dx: xbase*2 + o.boxThickness*2 + o.width,
                dy: ybase*2 + o.boxThickness*2,
                rx: xbase,
                ry: ybase,
                fill: 'black',
            },
            { // Inner rect.
                x: -(xbase),
                y: -(ybase),
                dx: xbase*2 + o.width,
                dy: ybase*2,
                rx: xbase - o.extraBuffering,
                ry: ybase - o.extraBuffering,
                fill: 'white',
            },
        ];
        
        var rects = d3.select(g).selectAll('rect')
            .data(data)
            .enter()
            .append('rect')
            .attr('x', 0)
            .attr('y', 0)
            .attr('width', 0)
            .attr('height', 0)
            .attr('rx', 0)
            .attr('ry', 0)
            .style('fill', 'white');
        
        rects.transition().duration(o.duration)
            .attr('x', function(d) { return d.x; })
            .attr('y', function(d) { return d.y; })
            .attr('width', function(d) { return d.dx; })
            .attr('height', function(d) { return d.dy; })
            .attr('rx', function(d) { return d.rx; })
            .attr('ry', function(d) { return d.ry; })
            .style('fill', function(d) { return d.fill; });
        
    },
    
    /**
     * Note that the label may transition after the axis.
     */
    createXAxis: function createXAxis(g, options) {
        var defaults = {
            width: 800,
            xScale: d3.scale.linear().domain([0, 1]),
            duration: 400,
            label: 'X Axis',
            doneTransitioningCallback: function() {},
        };
        
        var o = _.extend({}, defaults, options);
        o.xScale.range([0, o.width]);
        
        var xAxis = d3.svg.axis().scale(o.xScale).orient('bottom');
        
        
        
        // Create/select if needed.
        var xAxisGroup = d3.select(g)
            .style({ 'fill': 'none', 'stroke': 'black', 'stroke-width': '1.3px', 'shape-rendering': 'crispedges' });
        var xAxisLabel = xAxisGroup.selectAll('.xaxis-label')
            .data([o]);
        xAxisLabel.enter()
            .append('text')
            .classed('xaxis-label', true)
            .style({ 'fill': 'black', 'stroke': 'black', 'stroke-width': '0.5px' })
            .text(o.label);
        
        // Transition.
        xAxisGroup.transition()
            .duration(o.duration)
            .call(xAxis)
            .call(endAll, transitionAxisLabelCallback)
            .selectAll('g')
            .selectAll('text')
            .style({ 'text-anchor': 'end', 'fill': 'black', 'stroke': 'black', 'stroke-width': '0.5px' })
            .attr('dx', '-.8em')
            .attr('dy', '.15em')
            .attr('transform', 'rotate(-65)');
        
        function endAll(transition, callback) {
            var counter = 0;
            transition
                .each(function() { ++counter; })
                .each('end', function() { if (!--counter) callback.apply(this, arguments); }); 
        }
        
        var that = this;
        
        function transitionAxisLabelCallback() {
            var xAxisHeight = 100;
            try {
                xAxisHeight = xAxisGroup.selectAll('.tick')[0][0].getBBox().height;
            } catch(ex) {
                
            }
            transitionAxisLabel(xAxisHeight);
        }
        
        var fullyDoneTransitioning = function fullyDoneTransitioning() {
            o.doneTransitioningCallback();
        };
        
        function transitionAxisLabel(height) {
            xAxisLabel.transition()
                .duration(o.duration/2)
                .call(endAll, fullyDoneTransitioning)
                .attr('x', o.width/2)
                .attr('y', height)
                .style({ 'text-anchor': 'middle', 'dominant-baseline': 'hanging' });
        }
    },
    
    getXAxisHeight: function getXAxisHeight(g) {
        //~ var tickHeight = d3.select(g).selectAll('.domain')[0][0].getBBox().height;
        //~ var tickTextHeight = d3.select(g).selectAll('.tick').selectAll('text')[0][0].getBBox().height;
        //~ var labelHeight = d3.select(g).selectAll('.xaxis-label')[0][0].getBBox().height;
        //~ return tickHeight + tickTextHeight + labelHeight;
        return g.getBBox().height;
    },
    
    createDocuments: function createDocuments(g, options) {
        var defaults = {
            labeledY: -100,
            width: 600,
            docWidth: 10,
            docHeight: 10,
            maxQueueLength: 20,
            xScale: d3.scale.linear().domain([0, 1]),
            // documents, both labeled and unlabeled
            metadataName: '',
            metadataType: 'int',
            selectedDocument: 'some name',
            data: [
                {
                    name: 'some name', 
                    metadata: {
                        labeled: { 
                            //~ '': 0.50, // metadataName => value
                        },
                        unlabeled: {
                            '': [0.2, 0.4, 0.55],
                        },
                        userLabeled: {
                            //~ '': 0.6,
                        },
                    }, 
                    queuePos: 0, // Assigned by this method.
                }
            ], 
            updatedDocumentValue: function(d, i) {
            },
            doneDragging: function() {},
            selectedDocumentFunction: function(d, i) {},
            getDocumentColor: function(d, i) { return 'black'; },
            duration: 600,
        };
        
        var displayNum = function(n) {
            if(o.metadataType === 'int') {
                return Math.round(n).toString();
            } else {
                return n.toPrecision(2);
            }
        };
        
        var o = _.extend({}, defaults, options);
        o.xScale = o.xScale.range([0, o.width]);
        
        var isLabeled = function isLabeled(d, i) {
            return o.metadataName in d.metadata.labeled;
        };
        
        var isUserLabeled = function isUserLabeled(d, i) {
            return o.metadataName in d.metadata.userLabeled;
        };
        
        // Looser check than isLabeled as userLabeled is acceptable.
        var isLabeled2 = function isLabeled2(d, i) {
            return isLabeled(d, i) || isUserLabeled(d, i);
        };
        
        var getValue = function getValue(d, i) {
            if(isLabeled(d, i)) {
                return d.metadata.labeled[o.metadataName];
            } else {
                if(isUserLabeled(d, i)) {
                    return d.metadata.userLabeled[o.metadataName];
                } else {
                    return d.metadata.unlabeled[o.metadataName][1];
                }
            }
        };
        
        var show = function show(d, i) {
            if(isLabeled(d, i) || isUserLabeled(d, i)) {
                return true;
            } else if(d.queuePos < o.maxQueueLength) {
                return true;
            } else {
                return false;
            }
        };
        
        var getDocumentColor = function getDocumentColor(d, i) {
            return o.getDocumentColor(d, i);
        };
        
        var getDocumentOpacity = function getDocumentOpacity(d, i) {
            if(isLabeled2(d, i)) {
                return 1;
            } else if(d.queuePos < o.maxQueueLength) { // Scale to be between 0.2 and 0.8
                return 0.6 * (1/(o.maxQueueLength - d.queuePos)) + 0.2;
            } else {
                return 0;
            }
        };
        
        var documentOutlineColor = function documentOutlineColor(d, i) {
            if(d.name !== o.selectedDocument) {
                return null;
            } else {
                return 'red';
            }
        };
        
        var documentOutlineWidth = function documentOutlineColor(d, i) {
            if(d.name !== o.selectedDocument) {
                return 0;
            } else {
                return '1.5px';
            }
        };
        
        // Assign each document a queue position.
        var docsToAssignPosition = _.filter(o.data, function(d, i) { return !isLabeled2(d, i); });
        var sortedDocuments = _.sortBy(docsToAssignPosition, function(d, i) {
            var range = d.metadata.unlabeled[o.metadataName];
            return range[0] - range[2];
        });
        _.forEach(sortedDocuments, function(d, i) {
            d.queuePos = i;
        });
        
        var group = d3.select(g);
        
        var groupsData = ['red-line-group', 'documents-only-group'];
        var documents = group.selectAll('g')
            .data(groupsData)
            .enter()
            .append('g')
            .each(function(d) {
                if(d === groupsData[0]) { // Make sure the red line stuff is setup the first time.
                    var grp = d3.select(this);
                    grp.attr('id', 'red-line-group')
                        .style({ 'display': 'none' })
                    grp.append('line')
                        .attr('id', 'red-line')
                        .style({ 'fill': 'none', 'stroke': 'red', 'stroke-width': '1.5px', 'shape-rendering': 'crispedges' })
                        .attr('x1', 0)
                        .attr('y1', 0)
                        .attr('x2', 0)
                        .attr('y2', 0);
                    grp.append('circle')
                        .attr('id', 'red-dot')
                        .attr('r', 2)
                        .attr('cx', 0)
                        .attr('cy', 0)
                        .style({ 'fill': 'red' });
                    grp.append('text')
                        .attr('x', 0)
                        .attr('y', 0)
                        .style({ 'text-anchor': 'after-edge', 'stroke-width': '0px', 'stroke': 'red', 'fill': 'red' })
                        .text('');
                }
                d3.select(this)
                    .classed(d, true);
            });
        
        var redLineGroup = group.select('.'+groupsData[0]);
        var documentsGroup = group.select('.'+groupsData[1]);
        
        // Create whisker lines
        var singleDocGroups = documentsGroup.selectAll('.metadata-map-document')  
            .data(o.data);
        // Remove anything that doesn't belong
        singleDocGroups.exit().remove();
        // Initialize entering documents
        singleDocGroups.enter()
            .append('g')
            .classed('metadata-map-document', true)
            .style('display', 'none')
            .each(function(d) {
                var grp = d3.select(this);
                grp.attr('data-tg-document-name', d.name);
                grp.append('circle')
                    .classed('doc-circle', true)
                    .attr('r', o.docWidth/2)
                    .attr('cx', 0)
                    .attr('cy', 0)
                    .attr('data-tg-document-name', function(d) { return d.name; })
                    .classed('tg-tooltip tg-select pointer', true);
                grp.append('line')
                    .classed('whisker-line whisker', true)
                    .attr("x1", 0)
                    .attr("y1", 0)
                    .attr("x2", 0)
                    .attr("y2", 0)
                    .style({ 'stroke-width': '1.5px' });
                grp.append('line')
                    .classed('left-whisker-line whisker', true)
                    .attr("x1", 0)
                    .attr("y1", 0)
                    .attr("x2", 0)
                    .attr("y2", 0)
                    .style({ 'stroke-width': '1.5px' });
                grp.append('line')
                    .classed('right-whisker-line whisker', true)
                    .attr("x1", 0)
                    .attr("y1", 0)
                    .attr("x2", 0)
                    .attr("y2", 0)
                    .style({ 'stroke-width': '1.5px' });
            });
        
        // Transition documents to be where they should
        singleDocGroups.transition().duration(o.duration)
            .style('display', function(d, i) { 
                if(show(d, i)) {
                    return null;
                } else {
                    return 'none';
                }
            })
            .attr('transform', function(d, i) {
                var x = o.xScale(getValue(d, i));
                var y = 0;
                if(isLabeled2(d, i)) {
                    y = o.labeledY;
                } else {
                    y = o.docHeight/2 + d.queuePos*o.docHeight;
                }
                return 'translate('+x+','+y+')';
            })
            .style('fill', getDocumentColor)
            .style('stroke', getDocumentColor)
            .style('opacity', getDocumentOpacity);
        var docCircles = singleDocGroups.selectAll('.doc-circle');
        docCircles.transition().duration(o.duration)
            .attr('r', o.docWidth/2);
        
        var changeSelectedCircle = function changeSelectedCircle(allDocCircles) {
            allDocCircles.style('stroke-width', documentOutlineWidth)
                .style('stroke', documentOutlineColor);
        };
        
        changeSelectedCircle(docCircles);
        
        var updateRedLineGroup = function updateRedLineGroup(x, yUnlabeled, text) {
            redLineGroup.select('line')
                .attr("x1", x)
                .attr("y1", yUnlabeled)
                .attr("x2", x)
                .attr("y2", o.labeledY);
            redLineGroup.select('circle')
                .attr("cx", x)
                .attr("cy", o.labeledY);
            redLineGroup.select('text')
                .attr('y', o.labeledY)
                .attr('x', x + 4)
                .text(text);
            
        };
        
        var translateToXY = function(s) {
            return _.map(s.match(/[-]?[\d\.]+/g), function(v) { return parseFloat(v); });
        };
        
        var collapseWhiskers = function collapseWhiskers(grp) {
            grp.selectAll('.whisker')
                .transition().duration(o.duration)
                .attr('x1', 0)
                .attr('y1', 0)
                .attr('x2', 0)
                .attr('y2', 0);
        };
        
        // Dragging functionality
        var dragging = false;
        var circleDrag = d3.behavior.drag()
            .on('dragstart',  function(d, i) {
                d3.event.sourceEvent.stopPropagation();
                
                // Get coordinates of document group.
                var grp = d3.select(this);
                var xy = translateToXY(grp.attr('transform'));
                var x = xy[0];
                var y = xy[1];
                
                dragging = false; // Don't set dragging on start so the user can just click to select
                
                // Make sure that the document is selected.
                o.selectedDocumentFunction(d, i);
                o.selectedDocument = d.name;
                changeSelectedCircle(docCircles);
                
                collapseWhiskers(grp);
                
                var newValue = o.xScale.invert(x);
                d.metadata.userLabeled[o.metadataName] = newValue;
                
                // Initialize the red line
                redLineGroup.style({ "display": null });
                updateRedLineGroup(x, y, displayNum(newValue));
                
                o.updatedDocumentValue(d);
            })
            .on('drag', function(d, i) {
                //~ d3.event.sourceEvent.stopPropagation();
                // Move circle
                var grp = d3.select(this);
                var xy = translateToXY(grp.attr('transform'));
                var x = xy[0];
                var y = xy[1];
                var dx = d3.event.dx;
                var dy = d3.event.dy;
                x = Math.max(x + dx, 0);
                y = Math.max(y + dy, o.labeledY);
                x = Math.min(x, o.width);
                y = Math.min(y, o.docHeight*o.maxQueueLength);
                grp.attr('transform', 'translate('+x+','+y+')');
                dragging = true;
                // Set value and update 'Selected Document' content
                var newValue = o.xScale.invert(x);
                //~ if(type === 'int') {
                    //~ newValue = Math.round(newValue);
                //~ }
                d.metadata.userLabeled[o.metadataName] = newValue;
                
                // Update the red line
                redLineGroup.style({ 'display': null });
                updateRedLineGroup(x, y, displayNum(newValue));
                o.updatedDocumentValue(d);
            })
            .on('dragend', function(d, i) {
                d3.event.sourceEvent.stopPropagation();
                var grp = d3.select(this);
                var xy = translateToXY(grp.attr('transform'));
                var x = xy[0];
                var y = xy[1];
                
                // Snap circle to a location
                if(dragging) {
                    var newValue = o.xScale.invert(x);
                    //~ if(type === 'int') {
                        //~ newValue = Math.round(newValue);
                    //~ }
                    d.metadata.userLabeled[o.metadataName] = newValue;
                    o.updatedDocumentValue(d);
                } else {
                    if(Math.abs(y-o.labeledY) < 5) {
                        
                    } else {
                        if(o.metadataName in d.metadata.userLabeled) {
                            delete d.metadata.userLabeled[o.metadataName];
                        }
                    }
                }
                dragging = false;
                
                // Hide the red line group
                redLineGroup.style({ 'display': 'none' });
                
                // Cause any necessary updates with regards to "Selected Document" area
                o.doneDragging(d);
            })
            .origin(function(d) { return d; });
        singleDocGroups.call(circleDrag);
        
        var name = o.metadataName;
        // Move whisker lines
        singleDocGroups.selectAll('.whisker-line')
            .transition().duration(400)
            .attr("x1", function(datum, i) {
                if(isLabeled2(datum, i)) {
                    return 0;
                } else {
                    return o.xScale(datum.metadata.unlabeled[name][0]) - o.xScale(datum.metadata.unlabeled[name][1]);
                }
            })
            .attr("x2", function(datum, i) {
                if(isLabeled2(datum, i)) {
                    return 0;
                } else {
                    return o.xScale(datum.metadata.unlabeled[name][2]) - o.xScale(datum.metadata.unlabeled[name][1]);
                }
            })
            .style('display', function(d, i) {
                return show(d, i)? null: 'none';
            });
        
        // Move left whisker lines
        singleDocGroups.selectAll('.left-whisker-line')
            .transition()
            .duration(400)
            .attr("x1", function(datum, i) {
                if(isLabeled2(datum, i)) {
                    return 0;
                } else {
                    return o.xScale(datum.metadata.unlabeled[name][0]) - o.xScale(datum.metadata.unlabeled[name][1]);
                }
            })
            .attr("y1", function(datum, i) {
                if(isLabeled2(datum, i)) {
                    return 0;
                } else {
                    return Math.ceil(o.docHeight/4);
                }
            })
            .attr("x2", function(datum, i) {
                if(isLabeled2(datum, i)) {
                    return 0;
                } else {
                    return o.xScale(datum.metadata.unlabeled[name][0]) - o.xScale(datum.metadata.unlabeled[name][1]);
                }
            })
            .attr("y2", function(datum, i) {
                if(isLabeled2(datum, i)) {
                    return 0;
                } else {
                    return -Math.ceil(o.docHeight/4);
                }
            })
            .style('display', function(d, i) {
                return show(d, i)? null: 'none';
            });
            
        // Move right whisker lines
        singleDocGroups.selectAll('.right-whisker-line')
            .transition()
            .duration(400)
            .attr("x1", function(datum, i) {
                if(isLabeled2(datum, i)) {
                    return 0;
                } else {
                    return o.xScale(datum.metadata.unlabeled[name][2]) - o.xScale(datum.metadata.unlabeled[name][1]);
                }
            })
            .attr("y1", function(datum, i) {
                if(isLabeled2(datum, i)) {
                    return 0;
                } else {
                    return Math.ceil(o.docHeight/4);
                }
            })
            .attr("x2", function(datum, i) {
                if(isLabeled2(datum, i)) {
                    return 0;
                } else {
                    return o.xScale(datum.metadata.unlabeled[name][2]) - o.xScale(datum.metadata.unlabeled[name][1]);
                }
            })
            .attr("y2", function(datum, i) {
                if(isLabeled2(datum, i)) {
                    return 0;
                } else {
                    return -Math.ceil(o.docHeight/4);
                }
            })
            .style('display', function(d, i) {
                return show(d, i)? null: 'none';
            });
    },
    
    /**
     * Update the document display and its value.
     */
    updateDocumentSelection: function() {
        var docName = this.selectionModel.get('document');
        var name = docName;
        var value = '';
        var placeholder = 'Enter value';
        var docMetadata = this.model.get('documentNames')[docName];;
        if(docMetadata) {
            var metadataName = this.model.get('metadataName');
            if(metadataName in docMetadata.userLabeled) {
                value = docMetadata.userLabeled[metadataName];
            } else if(metadataName in docMetadata.labeled) {
                value = docMetadata.labeled[metadataName];
            } else if(metadataName in docMetadata.unlabeled){
                placeholder = 'Suggestion: '+docMetadata.unlabeled[metadataName][1];
            }
        } else {
            name = 'Click on a document';
        }
        this.changeDocumentValueAllowRerender = false;
        d3.select(this.el).select('#selected-document').text(name);
        d3.select(this.el).select('#document-value-control')
            .property('value', value.toString())
            .property('placeholder', placeholder);
        this.changeDocumentValueAllowRerender = true;
    },
    
/******************************************************************************
 *                           EVENT HANDLERS (DOM/Window)
 ******************************************************************************/
    
    events: {
        'click .metadata-map-redirect': 'clickRedirect',
        
        'change #document-value-control': 'changeDocumentValue',
        
        'click #save-changes': 'clickSaveChanges',
        
        'dblclick .doc-circle': 'doubleClickDocument',
        
        // Unused pie charts.
        //~ 'mouseover .document': 'mouseoverDocument',
        //~ 'mouseout .document': 'mouseoutDocument',
        //~ 'mousedown .document': 'mousedownDocument',
    },
    
    clickRedirect: function clickRedirect(e) {
        this.viewModel.set({ currentView: 'metadata' });
    },
    
    /**
     * Save any updates to document metadata from the user to the server.
     */
    clickSaveChanges: function(e) {
        alert("Saving not yet enabled.");
    },
    
    /**
     * Used to suppress the changeDocumentValue function from rerendering.
     * The only time we want rerendering is if the user directly changed the 
     * value.
     */
    changeDocumentValueAllowRerender: true,
    /**
     * Check the user input for valid input type. Update the settings model.
     */
    changeDocumentValue: function changeDocumentValue(e) {
        var docName = d3.select(this.el).select("#selected-document").text();
        var docMetadata = this.model.get('documentNames')[docName];
        if(docMetadata) {
            var metadataName = this.model.get('metadataName');
            var value = parseFloat(d3.select(this.el).select("#document-value-control").property("value"));
            if(!isNaN(value)) {
                docMetadata.userLabeled[metadataName] = value;
            }
            
            if(this.changeDocumentValueAllowRerender) {
                this.renderGroupHierarchy();
            }
        }
    },
    
    /**
     * Label the document according to the location it is at.
     */
    doubleClickDocument: function(e) {
        var docName = this.getDocumentNameFromEvent(e);
        var docMetadata = this.model.get("documentNames")[docName];
        var metadataName = this.model.get('metadataName');
        
        // Remove user set label
        if (metadataName in docMetadata.userLabeled) {
            delete docMetadata.userLabeled[metadataName];
            this.updateDocumentSelection();
            this.renderGroupHierarchy();
        } else if(!(metadataName in docMetadata.labeled)) {
            docMetadata.userLabeled[metadataName] = docMetadata.unlabeled[metadataName][1];
            this.updateDocumentSelection();
            this.renderGroupHierarchy();
        }
    },
    
    /**
     * When the mouse enters a document circle create a pie chart.
     */
    mouseoverDocument: function(e) {
        if(this.draggingDocument) {
            return;
        }
        
        var circle = d3.select(e.currentTarget);
        
        this.pieChartCircle = circle;
        
        var x = parseFloat(circle.attr("cx"));
        var y = parseFloat(circle.attr("cy"));
        
        var topics = this.getDocumentMetadata(this.getDocumentNameFromEvent(e)).topics;
        var pieGroup = this.docQueue.append("g")
            .classed("document-pie-chart", true)
            .attr("transform", "translate("+x+","+y+")")
            .attr("data-document-circle", circle)
            .style({ "pointer-events": "none" });
        
        var colors = ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a", 
                      "#d62728", "#ff9896", "#9467bd", "#c5b0d5", "#8c564b", "#c49c94", 
                      "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7", "#bcbd22", "#dbdb8d", 
                      "#17becf", "#9edae5"];
        var ordinals = [];
        var data = [];
        var index = 0;
        for(key in topics) {
            ordinals.push(index.toString());
            index += 1;
            data.push(topics[key]);
        }
        //~ var ordinals = ["0", "1", "2", "3", "4", "5"];
        var colorDomain = d3.scale.ordinal().domain(colors).rangePoints([0, 1], 0).range();
        var ordinalRange = d3.scale.ordinal().domain(ordinals).rangePoints([0, 1], 0).range();
        var ordToNum = d3.scale.ordinal().domain(ordinals).range(ordinalRange);
        var numToColor = d3.scale.linear().domain(colorDomain).range(colors);
        var colorScale = function ordinalColorScale(val) { return numToColor(ordToNum(val)); };
        
        //~ var data = [1, 1, 3, 8, 11, 13];
        
        var radius = this.model.get("pieChartRadius");
        
        var arc = d3.svg.arc()
            .outerRadius(radius)
            .innerRadius(0);
        
        var pie = d3.layout.pie()
            .sort(null)
            .value(function(d) { return d; });
        
        var arcs = pieGroup.selectAll("path")
            .data(pie(data))
            .enter().append("path")
            .style("fill", function(d, i) { return colorScale(i); })
            .style("opacity", 0.5)
            .attr("d", arc);
        
        // An invisible covering to make the mouseout event work properly
        var pieBackground = pieGroup.append("circle")
            .style({ "opacity": 0 })
            .attr("r", radius)
            .attr("cx", 0)
            .attr("cy", 0);
    },
    
    /**
     * When the mouse leaves the document circle destroy the pie chart.
     */
    mouseoutDocument: function(e) {
        this.removePieCharts();
    },
    
    /**
     * When the user clicks on a pie chart the drag functionality needs to engage.
     */
    mousedownDocument: function(e) {
        this.removePieCharts();
    },
    
    resizeWindowEvent: function resizeWindowEvent(e) {
		var plotContainer = this.$el.find('#metadata-map-view');
		var width = plotContainer.get(0).clientWidth;
		var height = window.innerHeight*0.8;
		var min = Math.min(width, height);
        this.model.set({ svgWidth: min, svgHeight: min });
	},

/******************************************************************************
 *                           EVENT HANDLERS (Model)
 ******************************************************************************/
    
    changeSVGWidth: function updateSVGWidth() {
        var svg = this.$el.find('#metadata-map-view').find('svg');
        svg.attr('width', this.model.get('svgWidth'));
    },
    
    changeSVGHeight: function updateSVGHeight() {
        var svg = this.$el.find('#metadata-map-view').find('svg');
        svg.attr('height', this.model.get('svgHeight'));
    },
    
    changeDocumentSelection: function changeDocumentSelection() {
        var docName = this.selectionModel.get("document");
        if(docName === '') {
            docName = 'No document selected.';
        }
        this.$el.find('#selected-document').text(docName);
        this.changeDocumentValueAllowRerender = false;
        this.changeDocumentValue();
        this.changeDocumentValueAllowRerender = true;
    },
    
    
    //++++++++++++++++++++++++++++++++++++++++++++++++++    GETTERS/SETTERS/HELPERS    ++++++++++++++++++++++++++++++++++++++++++++++++++\\
    
    
    removePieCharts: function() {
        this.docQueue.selectAll(".document-pie-chart").remove();
    },
    
    /**
     * Return the domain for the given metadata name and type.
     */
    getDataDomain: function(name, type) {
        if (type === "int" || type === "float") {
            var documents = this.model.get("documents");
            if(documents.length > 0) {
                var mapMin = function(doc) {
                    if(name in doc.metadata.userLabeled) {
                        return doc.metadata.userLabeled[name];
                    } else if(name in doc.metadata.labeled) {
                        return doc.metadata.labeled[name];
                    } else {
                        return doc.metadata.unlabeled[name][0];
                    }
                };
                var mapMax = function(doc) {
                    if(name in doc.metadata.userLabeled) {
                        return doc.metadata.userLabeled[name];
                    } else if(name in doc.metadata.labeled) {
                        return doc.metadata.labeled[name];
                    } else {
                        return doc.metadata.unlabeled[name][2];
                    }
                };
                var xValueMin = _.min(_.map(documents, mapMin));
                var xValueMax = _.max(_.map(documents, mapMax));
                return [xValueMin, xValueMax];
            } else {
                return [0, 0];
            }
        } else {
            return [0, 0];
        }
    },
    
    /**
     * Gets the value of the metadata item according to presence of userLabeled, 
     * labeled, or unlabeled information (in that order).
     */
    getValue: function(doc, name) {
        var value = 0;
        if(name in doc.metadata.userLabeled) { // Must go first to reflect user changes.
            value = doc.metadata.userLabeled[name];
        } else if(name in doc.metadata.labeled) {
            value = doc.metadata.labeled[name];
        } else {
            value = doc.metadata.unlabeled[name][1];
        }
        return value;
    },
    
    /**
     * Like getValue, but doesn't consider userLabeled.
     */
    getOriginalValue: function(doc, name) {
        var value = 0;
        if(name in doc.metadata.labeled) {
            value = doc.metadata.labeled[name];
        } else {
            value = doc.metadata.unlabeled[name][1];
        }
        return value;
    },
    
    
    /**
     * Returns the d3 scale to be used for the given datatype.
     */
    createAxisScale: function(name, type, axisLength) {
        var xRange = [0, axisLength];
        
        var scale = null;
        if (type === "int" || type === "float") {
            var xDomain = this.getDataDomain(name, type);
            scale = d3.scale.linear().domain(xDomain).range(xRange);
        } else {
            var xDomain = [0, 1];
            scale = d3.scale.linear().domain(xDomain).range(xRange);
        }
        return scale;
    },
    
    /**
     * Returns a d3 formating function for the axis.
     * Currently "float" is truncated at two decimal places and uses commas, 
     * "int" is displayed with no decimal places or commas, 
     * and anything else is just text which only allows up to 20 characters.
     */
    createAxisFormat: function(type) {
        if(type === "float") {
            return d3.format(",.2f");
        } else if (type === "int") {
            return d3.format(".0f");
        } else { // assume the format is just text
            return function(s) { 
                if(s === undefined) return "undefined";
                else return s.slice(0, 20); 
            };
        }
    },
    
    /**
     * Sorts the documents be the maximum difference of metadata values in the unlabeled category.
     */
    helperSortByMaxRange: function(unlabeled) {
        unlabeled.sort(function(a, b) {
            var aUnlabeledMeta = a.metadata.unlabeled;
            var bUnlabeledMeta = b.metadata.unlabeled;
            var aDiff = aUnlabeledMeta[2] - aUnlabeledMeta[0];
            var bDiff = bUnlabeledMeta[2] - bUnlabeledMeta[0];
            if(aDiff > bDiff) return -1;
            if(bDiff < aDiff) return 1;
            return 0;
        });
    },
    
    /**
     * Splits the array into two arrays.
     * documents -- the array of documents to split
     * name -- the metadata name used to perform the split
     * Return an Object { "labeled": [], "unlabeled": [] }.
     */
    helperSplitLabeledFromUnlabeled: function(documents, name) {
        var labeled = [];
        var unlabeled = [];
        
        var length = documents.length;
        for(var i = 0; i < length; i++) {
            var doc = documents[i];
            if(name in doc.metadata.labeled || name in doc.metadata.userLabeled) {
                labeled.push(doc);
            } else {
                unlabeled.push(doc);
            }
        }
        
        return {
            "labeled": labeled,
            "unlabeled": unlabeled,
        };
    },
    
    /**
     * TODO this should be called get variance, range implies something else
     * Return range of unlabeled value.
     */
    getRange: function(doc, name, type) {
        if(type === "int" || type === "float") {
            var meta = doc.metadata;
            if(name in meta.unlabeled) {
                var temp = meta.unlabeled[name];
                return temp[2] - temp[0];
            }
        }
        return 0;
    },
    
    /**
     * Return Object mapping document name to index in sorted order.
     */
    createUnlabeledDocumentOrder: function(name, type, maxDocuments) {
        var that = this;
        var documents = this.model.get("documents");
        
        documents.sort(function(a, b) {
            var aUnlabel = !that.isLabeled(a, name, true);
            var bUnlabel = !that.isLabeled(b, name, true);
            
            if(aUnlabel && bUnlabel) {
                var aRange = that.getRange(a, name, type);
                var bRange = that.getRange(b, name, type);
                if(aRange > bRange) return -1;
                else if(bRange > aRange) return 1;
                else return a.doc.localeCompare(b.doc);
            } else {
                if(aUnlabel) return -1;
                if(bUnlabel) return 1;
            }
            
            return 0;
        });
        
        var result = {};
        var minDocs = Math.min(documents.length, maxDocuments);
        
        for(var i = 0; i < minDocs; i++) {
            result[documents[i].doc] = i;
        }
        
        return result;
    },
    
    /**
     * Return document object if found; null otherwise.
     */
    getDocumentByName: function(docName) {
        var documents = this.model.get("documents");
        for(var i = 0; i < documents.length; i++) {
            if(docName === documents[i].doc) {
                return documents[i];
            }
        }
        return null;
    },
    
    /**
     * Counts the number of unlabeled documents.
     */
    getNumberOfUnlabeledDocuments: function() {
        var name = this.settingsModel.get("name");
        var documents = this.model.get("documents");
        var count = 0;
        for(var i = 0; i < documents.length; i++) {
            var meta = documents[i].metadata;
            if(!(name in meta.labeled || name in meta.userLabeled)) {
                count++;
            }
        }
        return count;
    },
    
    /** 
     * doc -- dictionary object representing document and metadata, or string representing document name
     * name -- metadata name value to check for
     * checkUser -- true if you want user labeled data to count as the document being labeled
     * Return true if document has labeled or user labeled value; false otherwise.
     */
    isLabeled: function(doc, name, checkUser) {
        var metadata = null;
        if(isString(doc)) {
            metadata = this.getDocumentMetadata(doc);
        } else {
            metadata = doc.metadata;
        }
        
        if(name in metadata.labeled || (checkUser && name in metadata.userLabeled)) {
            return true;
        }
        return false;
    },
    isUserLabeled: function(doc, name) {
        var metadata = null;
        if(isString(doc)) {
            metadata = this.getDocumentMetadata(doc);
        } else {
            metadata = doc.metadata;
        }
        
        if("userLabeled" in metadata && name in metadata.userLabeled) {
            return true;
        }
        return false;
    },
    isUnlabeled: function(doc, name) {
        var metadata = null;
        if(isString(doc)) {
            metadata = this.getDocumentMetadata(doc);
        } else {
            metadata = doc.metadata;
        }
        if("unlabeled" in metadata && name in metadata.unlabeled) {
            
            return true;
        }
        return false;
    },
    
    /**
     * e -- an event object that contains the document's name
     * Return the document name of the event object.
     */
    getDocumentNameFromEvent: function(e) {
        return e.currentTarget.attributes["data-tg-document-name"].value;
    },
    
    /**
     * docName -- the name of the document
     * name -- the name of the metadata attribute
     * Return either the labeled recommendation, user labeled value, or the unlabeled recommendation, in that order.
     */
    getADocumentLabel: function(docName, name) {
        var metadata = this.getDocumentMetadata(docName);
        if("labeled" in metadata && name in metadata.labeled) {
            return metadata.labeled[name];
        } else if("userLabeled" in metadata && name in metadata.userLabeled) {
            return metadata.userLabeled[name];
        } else {
            return metadata.unlabeled[name][1];
        }
    },
    
    removeUserLabel: function(docName, name) {
        var metadata = this.getDocumentMetadata(docName);
        if("userLabeled" in metadata && name in metadata.userLabeled) {
            
            delete metadata.userLabeled[name];
        }
    },
    
    getDocumentMetadata: function(docName) {
        return this.model.get("documentNames")[docName];
    },
    
    createTopicColorScale: function(numberOfTopics) {
    },
    
});

addViewClass(["Visualizations"], MetadataMapView);
