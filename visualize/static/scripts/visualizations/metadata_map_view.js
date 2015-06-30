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
'       <input id="document-value-control" type="text" class="form-control" name="Value" placeholder="Enter value"></select>'+
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
                    this.changeDocumentSelection();
                    
                    var documents = data.datasets[datasetName].analyses[analysisName].documents;
                    var formattedDocData = this.formatDocumentData(documents, metadataName);
                    var metadataType = data.datasets[datasetName].document_metadata_types[metadataName];
                    this.model.set({ metadataName: metadataName, metadataType: metadataType });
                    this.model.set({ documents: formattedDocData.documents, documentNames: formattedDocData.documentNames });
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
        
        var boxThickness = 1.5;
        var extraBuffering = 1.5;
        var docWidth = 20;
        var docHeight = 20;
        var sideBuffer = boxThickness + extraBuffering + docWidth/2;
        var xAxisWidth = width - 2*sideBuffer;
        var transitionDuration = 600;
        var xScale = this.createAxisScale(metadataName, metadataType, xAxisWidth);
        console.log(xScale.domain());
        
        var xAxisLabel = this.model.get('metadataName');
        
        var componentBuffer = 5;
        var distH = 200;
        var labeledH = boxThickness + extraBuffering + docHeight;
        var distY = 0;
        var labeledY = distH + componentBuffer + labeledH/2;
        var xAxisY = labeledY + componentBuffer + labeledH/2;
        
        var distData = that.getTopicDistributionData();
        console.log(distData);
        var distDataNameKeys = _.reduce(distData, function (r, v, k) { r.push(k); return r; }, []);
        var distColorScale = tg.color.getDiscreteColorScale(distDataNameKeys, tg.color.pastels);
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
            colorScale: distColorScale,
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
            duration: transitionDuration - 200,
            label: xAxisLabel,
            doneTransitioningCallback: function() {
                console.log('Done transitioning xaxis.');
                var xAxisH = that.getXAxisHeight(xaxis.get(0));
                var docQueueY = xAxisY + xAxisH + componentBuffer;
                documents.attr('transform', 'translate('+sideBuffer+','+docQueueY+')');
                that.createDocuments(documents.get(0), {
                    
                });
            },
        });
        
    },
    
    getTopicDistributionData: function getTopicDistributionData() {
        var that = this;
        var selectedTopic = '0';
        var metadataName = this.model.get('metadataName');
        var rawData = this.model.get('documentNames');
        var result = [
            { name: selectedTopic, points: [] },
        ];
        for(var docName in rawData) {
            var docData = rawData[docName]
            var topics = docData.topics;
            for(var index in result) {
                var obj = result[index];
                // TODO change this back to using labeled data only
                if(topics[obj.name] !== undefined && metadataName in docData.unlabeled) {
                    obj.points.push([docData.unlabeled[metadataName][1], topics[obj.name]]);
                }
            }
        }
        _.forEach(result, function(val) {
            this.sortPoints(val.points);
        }, this);
        
        var pts = result[0].points;
        var sum = _.reduce(pts, function(r, v) { r += v[1]; return r; }, 0);
        pts = _.map(pts, function(v) { return [v[0], v[1]/sum]; });
        result[0].points = that.kernelDensityEstimation(pts, [pts[0][0],pts[pts.length-1][0],100], that.getH(pts), that.epanechnikovKernel);
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
    
    /**
     * Choosing the right bandwidth is the hardest part of kernel density estimation.
     * See "Practical estimation of the bandwidth"
     * at https://en.wikipedia.org/wiki/Kernel_density_estimation
     */
    getH: function getH(pts) {
        var n = pts.length;
        var mean = _.reduce(pts, function(r, p) { return r + p[0]; }, 0)/n;
        var o = Math.sqrt(_.reduce(pts, function(r, p) { 
            var val = p[0] - mean;
            return r + val*val;
        }, 0)/n);
        return 1.06*o*Math.pow(n, -1/5);
    },
    
    /**
     * See https://en.wikipedia.org/wiki/Kernel_(statistics)#Kernel_functions_in_common_use
     */
    epanechnikovKernel: function epanechnikovKernel(u) {
        return Math.abs(u) <= 1? 0.75*(1 - u*u): 0;
    },
    
    /**
     * See https://en.wikipedia.org/wiki/Kernel_density_estimation
     * 
     * points -- your list of [x, y] pairs
     * lhs -- [low, high, stepCount]; specifies how many points to generate
     *          low -- the low end of the range
     *          high -- the high end of the range
     *          stepCount -- the number of points you want to generate
     * h -- h > 0; smoothing parameter (bandwidth)
     * K -- the kernel function K(x)
     * Return new list of points.
     */
    kernelDensityEstimation: function kernelDensityEstimation(points, lhs, h, K) {
        var n = points.length;
        var inv_nh = 1/(n*h);
        function f_h(x) {
            return inv_nh*_.reduce(points, function(result, xy) {
                result += K((x-xy[0])/h);
                //~ console.log(result);
                return result;
            }, 0);
        }
        var newPoints = [];
        var newX = lhs[0];
        var step = (lhs[1]-lhs[0])/(lhs[2]-1);
        while(newX < lhs[1]) {
            newY = f_h(newX);
            newPoints.push([newX, newY]);
            newX += step;
        }
        return newPoints;
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
    
    formatDocumentData: function formatDocumentData(documents, metadataName) {
        var formatted = _.reduce(documents, function reducer(result, value, key) {
            var temp = {};
            temp['labeled'] = {};
            var unlabeled = {};
            unlabeled[metadataName] = value.metadata_predictions[metadataName];
            temp['unlabeled'] = unlabeled;
            temp['userLabeled'] = {};
            temp['topics'] = value.topics;
            var docElement = {
                doc: key,
                metadata: temp,
            };
            result['documents'].push(docElement);
            result['documentNames'][key] = temp;
            return result;
        }, { documents: [], documentNames: {} });
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
            .data([o])
            .enter()
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
            var xAxisHeight = xAxisGroup.selectAll('.tick')[0][0].getBBox().height;
            transitionAxisLabel(xAxisHeight);
        }
        
        function transitionAxisLabel(height) {
            xAxisLabel.transition()
                .duration(o.duration/2)
                .call(endAll, o.doneTransitioningCallback)
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
            xScale: d3.scale.linear().domain([0, 1]),
            data: [], // documents, both labeled and unlabeled
            show: function(d, i) { return true; },
            isLabeled: function(d, i) { return true; },
        };
        
        var group = d3.select(g);
        
        var groupsData = ['red-line-group', 'documents-only-group'];
        var documents = group.selectAll('g')
            .data(groupsData)
            .enter()
            .append('g')
            .classed(function(d) { return d; }, true)
            .each(function(d) {
                if(d === groupsData[0]) { // Make sure the red line stuff is setup the first time.
                    var grp = d3.select(this);
                    grp.attr("id", "red-line-group")
                        .style({ "display": "none" })
                    grp.append('line')
                        .attr("id", "red-line")
                        .style({ "fill": "none", "stroke": "red", "stroke-width": "1.5px", "shape-rendering": "crispedges" })
                        .attr("x1", 0)
                        .attr("y1", 0)
                        .attr("x2", 0)
                        .attr("y2", 0);
                    grp.append("circle")
                        .attr("id", "red-dot")
                        .attr("r", 2)
                        .attr("cx", 0)
                        .attr("cy", 0)
                        .style({ "fill": "red" });
                }
            });
        
        var redLineGroup = group.select('.'+groupsData[0]);
        var documentsGroup = group.select('.'+groupsData[1]);
        
        
        
    },
    
    /**
     * Create the svg component, axis component, and any other needed components.
     */
    renderMap: function() {
        console.log("Rendering the map.");
        // Dimensions.
        var width = this.model.get('width');
        var height = this.model.get('height');
        var textHeight = this.model.attributes.textHeight;
        var duration = this.model.attributes.duration;
        var windowWidth = window.innerWidth*.9*0.75;
        var windowHeight = window.innerHeight*.9;
        var windowHeight = document.getElementById("metadata-map-controls").offsetHeight;
        if(windowHeight > windowWidth) {
            windowHeight = windowWidth;
        }
        
        this.svgMaxHeight = windowHeight;
        
        windowHeight = windowHeight/2;
        
        // Render the scatter plot.
        this.bufferedPane = svg.append("g")
            .attr("id", "metadata-map-buffered-pane");
        
        // Render document queue container.
        // The queue container will also chart labeled documents.
        this.docQueue = this.bufferedPane.append("g")
            .attr("id", "metadata-map-queue");
        this.labeledOuterRect = this.docQueue.append("rect");
        this.labeledInnerRect = this.docQueue.append("rect");
        
        // Add group for red line during user drag operation.
        this.redLineGroup = this.docQueue.append("g")
            .attr("id", "red-line-group")
            .style({ "display": "none" });
        this.redLineGroup.append("line")
            .attr("id", "red-line")
            .style({ "fill": "none", "stroke": "red", "stroke-width": "1.5px", "shape-rendering": "crispedges" })
            .attr("x1", 0)
            .attr("y1", 0)
            .attr("x2", 0)
            .attr("y2", 0);
        this.redLineGroup.append("circle")
            .attr("id", "red-dot")
            .attr("r", 2)
            .attr("cx", 0)
            .attr("cy", 0)
            .style({ "fill": "red" });
        
        // Sync with any settings.
        this.updateMap();
    },
    
    renderDocuments: function() {
        var documents = this.model.get("documents");
        
        // Create whisker lines
        this.docQueue.selectAll(".whisker-lines").remove();
        this.whiskerLines = this.docQueue.selectAll(".whisker-lines")
            .data(documents);
        this.whiskerLines.exit().remove();
        this.whiskerLines.enter()
            .append("line")
            .classed("whisker-lines", true);
        
        // Create left whisker lines
        this.docQueue.selectAll(".left-whisker-lines").remove();
        this.leftWhiskerLines = this.docQueue.selectAll(".left-whisker-lines")
            .data(documents);
        this.leftWhiskerLines.exit().remove();
        // Add needed.
        this.leftWhiskerLines.enter()
            .append("line")
            .classed("left-whisker-lines", true);
        
        // Create left whisker lines
        this.docQueue.selectAll(".right-whisker-lines").remove();
        this.rightWhiskerLines = this.docQueue.selectAll(".right-whisker-lines")
            .data(documents);
        this.rightWhiskerLines.exit().remove();
        // Add needed.
        this.rightWhiskerLines.enter()
            .append("line")
            .classed("right-whisker-lines", true);
        
        // Create circle elements
        this.docQueue.selectAll(".document").remove();
        this.circles = this.docQueue.selectAll(".document")
            .data(documents);
        this.circles.enter()
            .append("circle")
            .classed("document", true)
            .attr("fill", "none")
            .style("cursor", "pointer")
            .attr("data-document-name", function(datum) {
                return datum.doc;
            });
        
        this.updateDocuments();
    },
    
    //++++++++++++++++++++++++++++++++++++++++++++++++++    UPDATE VISUALIZATION    ++++++++++++++++++++++++++++++++++++++++++++++++++\\
    
    /**
     * Move the plot and axis into place.
     */
    updateMap: function() {
        // Basic data needed to determine axis information.
        var name = this.model.get('metadataName');
        var type = this.model.get('metadataType');
        if(name === "" || type === "") {
            return;
        }
        
        // Split documents so we can see how many unlabeled documents we'll have room for.
        var documents = this.model.get("documents");
        var numberOfUnlabeled = this.getNumberOfUnlabeledDocuments();
        
        // Gather data.
        var width = this.model.get('width');
        var height = this.model.get('height');
        var queueHeight = 600;
        
        var documentHeight = this.model.get("documentHeight");
        var documentWidth = this.model.get("documentWidth");
        var buffer = Math.max(documentHeight, documentWidth)/2; // buffer around visual components
        var textBufferLeft = 10;
        
        var numberOfUnlabeledDocs = Math.min(Math.floor(queueHeight/documentHeight), numberOfUnlabeled);
        
        var labeledBoxThickness = 2; // 2 px
        var labeledBoxBuffer = 2; // 2 px
        var labeledBoxHeight = 2*labeledBoxThickness + 2*labeledBoxBuffer + documentHeight;
        var labeledInnerBoxHeight = labeledBoxHeight - 2*labeledBoxThickness;
        //~ var unlabeledHeight = numberOfUnlabeledDocs*documentHeight;
        //~ var labeledY = unlabeledHeight + labeledBoxHeight/2 + buffer;
        var labeledY = labeledBoxHeight/2 + buffer;
        var unlabeledHeight = labeledY*2;
        var unlabeledY = labeledBoxHeight;
        var labeledBoxX = -labeledBoxThickness - buffer - labeledBoxBuffer;
        var labeledBoxY = labeledY - labeledBoxThickness - labeledBoxBuffer - buffer;
        
        var leftBuffer = buffer + textBufferLeft + labeledBoxThickness
        var xAxisLength = width - leftBuffer - buffer - 2*labeledBoxThickness;
        
        var xScale = this.xScale = this.createAxisScale(name, type, xAxisLength);
        var xFormat = this.createAxisFormat(type);
        var xAxis = d3.svg.axis().scale(xScale).orient("bottom").tickFormat(xFormat);
        var transitionDuration = this.model.get("duration");
        var fastTransitionDuration = transitionDuration/4;
        queueHeight = unlabeledHeight + labeledBoxHeight + buffer;
        
        // Set the outer buffers.
        this.bufferedPane.attr("transform", "translate(" + leftBuffer + "," + buffer + ")");
        
        // Move the labeled area box.
        this.labeledOuterRect
            .transition()
            .duration(transitionDuration)
            .attr("x", labeledBoxX)
            .attr("y", labeledBoxY)
            .attr("width", xAxisLength + 2*labeledBoxThickness + 2*labeledBoxBuffer + documentWidth)
            .attr("height", labeledBoxHeight)
            .attr("rx", buffer)
            .attr("ry", buffer)
            .attr("fill", "black");
        this.labeledInnerRect
            .transition()
            .duration(transitionDuration)
            .attr("x", labeledBoxX + labeledBoxThickness)
            .attr("y", labeledBoxY + labeledBoxThickness)
            .attr("width", xAxisLength + 2*labeledBoxBuffer + documentWidth)
            .attr("height", labeledInnerBoxHeight)
            .attr("rx", buffer)
            .attr("ry", buffer)
            .attr("fill", "white");
        
        // Move the map.
        this.docQueue.transition()
            .duration(transitionDuration)
            .attr("transform", "translate(0,0)"); // May need to move it later.
        
        // Move the axis.
        var heightOfOtherComponents = labeledBoxHeight + buffer;
        var xAxisY = heightOfOtherComponents + buffer;
        this.xAxisGroup.transition()
            .duration(transitionDuration)
            .attr("transform", "translate(0,"+xAxisY+")");
        
        // Transform the axis.
        this.xAxisGroup.transition()
            .duration(fastTransitionDuration)
            .attr("transform", "translate(0,"+xAxisY+")")
            .call(xAxis)
            .call(endAll, transitionAxisLabelCallback)
            .selectAll("g")
            .selectAll("text")
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", ".15em")
            .attr("transform", "rotate(-65)");
        
        this.xAxisText.text(toTitleCase(name.replace(/_/g, " ")));
        
        function endAll(transition, callback) {
            var counter = 0;
            transition
                .each(function() { ++counter; })
                .each("end", function() { if (!--counter) callback.apply(this, arguments); }); 
        }
        
        var that = this;
        
        function transitionAxisLabelCallback() {
            var xAxisHeight = that.xAxisGroup.selectAll(".tick")[0][0].getBBox().height;
            transitionAxisLabel(xAxisHeight);
        }
        
        function transitionAxisLabel(height) {
            that.xAxisText.transition()
                .duration(fastTransitionDuration)
                .call(endAll, transitionDocumentsCallback)
                .attr("x", xAxisLength/2)
                .attr("y", height)
                .style({ "text-anchor": "middle", "dominant-baseline": "hanging" });
            console.log("Done axis");
        }
        
        function transitionDocumentsCallback() {
            console.log("Done label");
            var xAxisHeight = that.xAxisGroup.selectAll("#x-axis")[0].parentNode.getBBox().height;
            unlabeledY = labeledBoxHeight + buffer + xAxisHeight + buffer;
            
            that.model.set({
                xScale: xScale,
                labeledYCoord: labeledY, // y coordinate offset for the labeled area
                unlabeledYCoord: unlabeledY,
                unlabeledDocumentCount: numberOfUnlabeledDocs, // The number of unlabeled docs to show in the queue
                unlabeledDocumentOrder: that.createUnlabeledDocumentOrder(name, type, numberOfUnlabeledDocs), // Object specifying the document order.
                xAxisLength: xAxisLength,
            }, { silent: true});// prevent triggering this function again
            
            that.updateDocuments();
        }
    },
    
    /**
     * Create the list of metadata items allowed.
     */
    updateMetadataOptions: function() {
        var nameSelect = d3.select(this.el).select("#metadata-name-control");
        var options = nameSelect.selectAll("option")
            .data(Object.keys(this.model.get("metadataTypes")));
        options.exit().remove();
        options.enter()
            .append("option")
            .attr("value", function(d) {
                return d;
            })
            .text(function(d) { return toTitleCase(d.replace(/_/g, " ")); });
        this.updateMetadataSelection();
    },
    
    /**
     * Update the controls display.
     */
    updateMetadataSelection: function() {
        var controls = d3.select(this.el).select("#metadata-map-controls");
        var name = controls.select("#metadata-name-control");
        var type = controls.select("#metadata-type-control");
        var selectedName = this.settingsModel.get("name");
        var selectedType = this.settingsModel.get("type");
        name.property("value", selectedName);
        if(selectedType === "") {
            type.text("N/A");
        } else {
            type.text(tg.site.readableTypes[selectedType]);
        }
    },
    
    /**
     * Update the document display and its value.
     */
    updateDocumentSelection: function() {
        var selectedDocument = this.selectionModel.get("document");
        var docName = selectedDocument;
        var value = "";
        var placeholder = "Enter value";
        var document = this.getDocumentByName(selectedDocument);
        if(document) {
            var metadata = document.metadata;
            var metadataName = this.settingsModel.get("name");
            if(metadataName in metadata.userLabeled) {
                value = metadata.userLabeled[metadataName];
            } else if(metadataName in metadata.labeled) {
                value = metadata.labeled[metadataName];
            } else if(metadataName in metadata.unlabeled){
                placeholder = "Suggestion: "+metadata.unlabeled[metadataName][1];
            }
        } else {
            docName = "Click on a document";
        }
        d3.select(this.el).select("#selected-document").text(docName);
        d3.select(this.el).select("#document-value-control")
            .property("value", value.toString())
            .property("placeholder", placeholder);
    },
    
    /**
     * Update the documents according to any changes in the documents to be charted.
     */
    updateDocuments: function() {
        var name = this.model.get("metadataName"); // Metadata name
        var type = this.model.get("metadataType"); // Metadata type
        if(name === '' || type === '') {
            return;
        }
        
        var that = this;
        
        var xScale = this.xScale;
        
        var documentHeight = this.model.get("documentHeight");
        var radius = documentHeight/2;
        var buffer = radius;
        var numberOfUnlabeledsToShow = this.model.get("unlabeledDocumentCount");
        var labeledY = this.model.get("labeledYCoord");
        var unlabeledY = this.model.get("unlabeledYCoord");
        var documentQueueOrder = this.model.get("unlabeledDocumentOrder");
        
        function getUnlabeledDocumentY(docName) {
            if(docName in documentQueueOrder) {
                return unlabeledY + documentQueueOrder[docName]*documentHeight+documentHeight/2;
            } else {
                return 0;
            }
        }
        
        function getDocumentFill(docObj) {
            if(that.isLabeled(docObj, name, false)) {
                if(that.isUserLabeled(docObj, name)) {
                    return "red";
                } else {
                    return "blue"
                }
            } else {
                if(that.isUserLabeled(docObj, name)) {
                    return "green";
                } else {
                    return "black";
                }
            }
        }
        
        function showDocument(docObj) {
            if((docObj.doc in documentQueueOrder) || that.isUserLabeled(docObj, name)) {
                return true;
            } else {
                return false;
            }
        }
        
        // Move circles
        this.circles.transition()
            .duration(400)
            .attr("r", radius)
            .attr("cx", function(datum) {
                var value = that.getValue(datum, name);
                return xScale(value);
            })
            .attr("cy", function(datum, i) {
                var y = 0;
                if(name in datum.metadata.userLabeled || name in datum.metadata.labeled) {
                    y = labeledY;
                } else {
                    y = getUnlabeledDocumentY(datum.doc);
                }
                return y;
            })
            .attr("fill", function(d, i) {
                return getDocumentFill(d);
            })
            .style('display', function(d, i) {
                return showDocument(d)? null: 'none';
            });
        
        var inLabeledArea = function(d3Circle) {
            var y = parseFloat(d3Circle.attr("cy"));
            if(y < labeledY + buffer && y > labeledY - buffer) {
                return true;
            } else {
                return false;
            }
        }
        
        // Add circle drag behavior // TODO this could probably be assigned once
        var circleDrag = d3.behavior.drag()
            .on("dragstart", function(d, i) {
                d3.event.sourceEvent.stopPropagation();
                
                // Remove pie chart
                that.removePieCharts();
                
                // Get circle location
                var circle = d3.select(this);
                var x = circle.attr("cx");
                var y = circle.attr("cy");
                
                // Reset dragging indicator
                that.draggingDocument = false;
                
                // Treat as a click event and set the document appropriately
                var documentName = d3.select(this).attr("data-document-name");
                if(documentName) {
                    that.selectionModel.set({ document: documentName });
                }
            })
            .on("drag", function(d, i) {
                // Indicate that a circle is being dragged
                that.draggingDocument = true;
                
                // Remove pie chart // TODO not needed?
                if(!that.draggingDocument) {
                    
                    //~ that.startedInLabeledArea = inLabeledArea(circle); 
                }
                
                // Move circle
                var circle = d3.select(this);
                var dx = d3.event.dx;
                var dy = d3.event.dy;
                var x = Math.max(parseFloat(circle.attr("cx")) + dx, 0);
                var y = Math.max(parseFloat(circle.attr("cy")) + dy, 0);
                var x = Math.min(x, that.model.get("xAxisLength"));
                var y = Math.min(y, unlabeledY+documentHeight*numberOfUnlabeledsToShow);
                circle.attr("cx", x)
                    .attr("cy", y);
                
                // Set value and update "Selected Document" content
                var newValue = xScale.invert(x);
                if(type === "int") {
                    newValue = Math.round(newValue);
                }
                d.metadata.userLabeled[name] = newValue;
                
                // Initialize the red line
                that.redLineGroup.style({ "display": null });
                that.updateRedLineGroup(x, y, x, labeledY);
                that.updateDocumentSelection();
            })
            .on("dragend", function(d, i) {
                d3.event.sourceEvent.stopPropagation();
                
                
                // Snap circle to a location
                if(that.draggingDocument) {
                    var circle = d3.select(this);
                    var x = parseFloat(circle.attr("cx"));
                    var y = labeledY;
                    var newValue = xScale.invert(x);
                    if(type === "int") {
                        newValue = Math.round(newValue);
                    }
                    d.metadata.userLabeled[name] = newValue;
                    that.updateMap();
                }
                
                
                // Hide the red line group
                that.redLineGroup.style({ "display": "none" });
                
                // Cause any necessary updates with regards to "Selected Document" area
                that.updateDocumentSelection();
                
                // Indicate that dragging has finished
                that.draggingDocument = false;
            })
            .origin(function(d) { return d; });
        this.circles.call(circleDrag);
        
        // Move whisker lines
        this.whiskerLines
            .transition()
            .duration(400)
            .attr("x1", function(datum) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return xScale(datum.metadata.unlabeled[name][0]);
                }
            })
            .attr("y1", function(datum, i) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return getUnlabeledDocumentY(datum.doc);
                }
            })
            .attr("x2", function(datum) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return xScale(datum.metadata.unlabeled[name][2]);
                }
            })
            .attr("y2", function(datum, i) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return getUnlabeledDocumentY(datum.doc);
                }
            })
            .style('display', function(d, i) {
                return showDocument(d)? null: 'none';
            })
            .attr("style", "stroke: rgb(0,0,0); stroke-width:2");
        
        // Move left whisker lines
        this.leftWhiskerLines
            .transition()
            .duration(400)
            .attr("x1", function(datum) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return xScale(datum.metadata.unlabeled[name][0]);
                }
            })
            .attr("y1", function(datum, i) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return getUnlabeledDocumentY(datum.doc) + Math.ceil(documentHeight/4);
                }
            })
            .attr("x2", function(datum) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return xScale(datum.metadata.unlabeled[name][0]);
                }
            })
            .attr("y2", function(datum, i) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return getUnlabeledDocumentY(datum.doc) - Math.ceil(documentHeight/4);
                }
            })
            .style('display', function(d, i) {
                return showDocument(d)? null: 'none';
            })
            .attr("style", "stroke: rgb(0,0,0); stroke-width:2");
            
        // Move right whisker lines
        this.rightWhiskerLines
            .transition()
            .duration(400)
            .attr("x1", function(datum) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return xScale(datum.metadata.unlabeled[name][2]);
                }
            })
            .attr("y1", function(datum, i) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return getUnlabeledDocumentY(datum.doc) + Math.ceil(documentHeight/4);
                }
            })
            .attr("x2", function(datum) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return xScale(datum.metadata.unlabeled[name][2]);
                }
            })
            .attr("y2", function(datum, i) {
                if(that.isLabeled(datum, name, true)) {
                    return 0;
                } else {
                    return getUnlabeledDocumentY(datum.doc) - Math.ceil(documentHeight/4);
                }
            })
            .style('display', function(d, i) {
                return showDocument(d)? null: 'none';
            })
            .attr("style", "stroke: rgb(0,0,0); stroke-width:2");
    },
    
    // Update the coordinates of the group members
    updateRedLineGroup: function(x1, y1, x2, y2) {
        var redLine = this.redLineGroup.select("#red-line");
        var redCircle = this.redLineGroup.select("#red-dot");
        redLine.attr("x1", x1)
            .attr("y1", y1)
            .attr("x2", x2)
            .attr("y2", y2);
        redCircle.attr("cx", x2)
            .attr("cy", y2);
    },
    
/******************************************************************************
 *                           EVENT HANDLERS (DOM/Window)
 ******************************************************************************/
    
    events: {
        'click .metadata-map-redirect': 'clickRedirect',
        
        'change #document-value-control': 'changeDocumentValue',
        
        'click #save-changes': 'clickSaveChanges',
        
        'click .document': 'clickDocument',
        'dblclick .document': 'doubleClickDocument',
        
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
     * Check the user input for valid input type. Update the settings model.
     */
    changeDocumentValue: function changeDocumentValue(e) {
        var docName = d3.select(this.el).select("#selected-document").text();
        var document = this.getDocumentByName(docName);
        if(document) {
            var meta = document.metadata;
            var name = this.settingsModel.get("name");
            var value = parseFloat(d3.select(this.el).select("#document-value-control").property("value"));
            if(!isNaN(value)) {
                meta.userLabeled[name] = value;
            }
            
            this.updateDocumentSelection();
            this.updateMap();
        }
    },
    
    /**
     * Update the document selection.
     */
    clickDocument: function(e) {
        var docName = this.getDocumentNameFromEvent(e);
        if(docName in this.model.get("documentNames")) {
            this.selectionModel.set({ document: docName });
        }
    },
    
    /**
     * Label the document according to the location it is at.
     */
    doubleClickDocument: function(e) {
        var docName = this.getDocumentNameFromEvent(e);
        var document = this.model.get("documentNames")[docName];
        var name = this.settingsModel.get("name");
        
        // Remove user set label
        if (this.isUserLabeled(docName, name)) {
            this.removeUserLabel(docName, name);
            this.updateDocumentSelection();
            this.updateMap();
        } else if(this.isUnlabeled(docName, name)) {
            document.userLabeled[name] = this.getADocumentLabel(docName, name);
            this.updateDocumentSelection();
            this.updateMap();
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
        //~ console.log(topics);
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
        return e.currentTarget.attributes["data-document-name"].value;
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
