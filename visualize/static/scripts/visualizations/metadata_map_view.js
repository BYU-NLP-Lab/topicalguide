/**
 * update methods read the model (respond to model updates) and update the display accordingly
 * change/click methods respond to user interaction and change the models triggering the appropriate events
 * render methods that create the visualization based on whatever settings and data are available
 */
var MetadataMapView = DefaultView.extend({
    
    readableName: "Metadata Map",
    shortName: "metadata_map",

    initialize: function() {
        var defaults = {
            
        };
        this.selectionModel.on("change:analysis", this.render, this);
        this.model = new Backbone.Model(); // Used to store document data.
        this.model.set({
            // The document data.
            documents: [], // Array of objects { doc: "docname", metadata: { labeled: {}, unlabeled: {}, userLabeled: {} } }
            documentNames: {}, // Object acting as a set of document names
            metadataTypes: {}, // Object mapping metadata names to metadata types
            
            
            // Dimensions of svg viewBox.
            dimensions: {
                width: 800,
                height: 800,
            },
            
            // Dimensions of the circles.
            documentHeight: 20,
            documentWidth: 20,
            pieChartRadius: 60,
            
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
        });
        this.settingsModel.set({
            name: "",
            type: "",
        });
        this.settingsModel.on("change", this.updateMetadataSelection, this);
        this.settingsModel.on("change", this.updateDocumentSelection, this);
        this.settingsModel.on("change", this.updateMap, this);
        this.selectionModel.on("change:document", this.updateDocumentSelection, this);
        this.model.on("change:metadataTypes", this.updateMetadataOptions, this);
        this.model.on("change:documents", this.renderDocuments, this);
        this.model.on("change", this.updateMap, this);
    },
    
    cleanup: function() {
    },
    
    //++++++++++++++++++++++++++++++++++++++++++++++++++    TEMPLATES    ++++++++++++++++++++++++++++++++++++++++++++++++++\\
    
    mainTemplate: 
"<div id=\"metadata-map-view2\" class=\"col-xs-9\" style=\"display: inline; float: left;\">"+
"<div id=\"metadata-map-view\" class=\"container-fluid\"></div>"+
"<div id=\"document-info-view-container\" class=\"container-fluid\"></div>"+
"</div>"+
"<div id=\"metadata-map-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",
    
    controlsTemplate:
"<h4><b>Selected Document</b></h4>"+
"<hr />"+
"<div>"+
"    <label for=\"selected-document\">Document:</label><br />"+
"    <span id=\"selected-document\"></span>"+
"</div>"+
"<div>"+
"    <label for=\"document-value-control\">Value:</label>"+
"    <input id=\"document-value-control\" type=\"text\" class=\"form-control\" name=\"Value\" placeholder=\"Enter value\"></select>"+
"</div>"+
"<hr />"+
"<h4><b>Server Requests</b></h4>"+
"<hr />"+
"<div>"+
"    <button id=\"save-changes\" class=\"btn btn-default\">Save Changes</button>"+
"    <br/><br/>"+
"    <button id=\"get-documents\" class=\"btn btn-default\">Get Documents</button>"+
"</div>",
    
    helpHtml:
"<div id=\"metadata-map-help\"><p>Documentation coming soon.</p></div>",
    
    //++++++++++++++++++++++++++++++++++++++++++++++++++    RENDER    ++++++++++++++++++++++++++++++++++++++++++++++++++\\
    
    /**
     * Entry point to start visualization.
     */
    render: function() {
        this.$el.empty();
        this.settingsModel.set({ metadataName: "" });
        return;
        if(!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<p>You should select a <a href=\"#\">dataset and analysis</a> before proceeding.</p>");
            return;
        } else {
            this.renderMetadataOptions();
        }
    },
    
    
    
    
    /**
     * Return html of help message to user.
     */
    renderHelpAsHtml: function() {
        return this.helpHtml;
    },
    
    /**
     * Populate the controls panel.
     */
    renderControls: function() {
        var controls = d3.select(this.el).select("#metadata-map-controls");
        controls.html(this.controlsTemplate);
        this.updateMetadataOptions();
        this.updateMetadataSelection();
        this.updateDocumentSelection();
    },
    
    /**
     * Create the svg component, axis component, and any other needed components.
     */
    renderMap: function() {
        console.log("Rendering the map.");
        // Dimensions.
        var dim = this.model.attributes.dimensions;
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
        
        // Create scales and axes.
        var xScale = this.xScale = d3.scale.linear()
            .domain([0, 1])
            .range([0, dim.width]);
        var xAxis = d3.svg.axis().scale(xScale).orient("bottom");
        
        // Render the scatter plot.
        var view = d3.select(this.el).select("#metadata-map-view").html("");
        
        var svg = this.svg = view.append("svg")
            .attr("width", "100%")
            .attr("height", windowHeight)
            .attr("viewBox", "0, 0, "+dim.width+", "+dim.height/2)
            .attr("preserveAspectRatio", "xMidYMin meet")
            .append("g");
            
        this.bufferedPane = svg.append("g")
            .attr("id", "metadata-map-buffered-pane");
        
        // Render xAxis.
        this.xAxisGroup = this.bufferedPane.append("g")
            .attr("id", "x-axis")
            .attr("transform", "translate(0,"+dim.height+")")
            .style({ "fill": "none", "stroke": "black", "stroke-width": "1.5px", "shape-rendering": "crispedges" });
        this.xAxisText = this.xAxisGroup.append("text");
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
    
    /**
     */
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
    
    //++++++++++++++++++++++++++++++++++++++++++++++++++    DATA    ++++++++++++++++++++++++++++++++++++++++++++++++++\\
    
    // TODO unused, initial query item
    getQueryHash: function() {
        var selections = this.selectionModel.attributes;
        return {
            "datasets": selections.dataset,
            "analyses": selections.analysis,
        };
    },
    
    // TODO this is a dummy function used to create ficticious data for the use of developement
    /**
     * Retrieve the metadata types available from the server.
     * Store the metadata in this.model.
     */
    loadData: function() {
        var data = {
            "documents": {
                "George_W._Bush_5.txt": {
                    "labeled": {
                        "year": 2015,
                    },
                    "unlabeled": {
                        "time_of_day": [0, 0.7, 1],
                    },
                    "topics": {
                        "0": 1000, 
                        "1": 143, 
                        "2": 5, 
                        "3": 30, 
                        "4": 62, 
                        "5": 85, 
                    }
                }, 
                "Lyndon_Baines_Johnson_1.txt": {
                    "labeled": {
                    },
                    "unlabeled": {
                        "time_of_day": [0, 0.2, 0.4],
                        "year": [2000, 2002, 2003],
                    },
                    "topics": {
                        "0": 52, 
                        "1": 500, 
                        "2": 5, 
                        "3": 30, 
                        "4": 100, 
                        "5": 85, 
                    }
                }, 
                "George_Washington_6.txt": {
                    "labeled": {
                    },
                    "unlabeled": {
                        "time_of_day": [0, 0.5, 0.9],
                        "year": [1980, 2002, 2015],
                    },
                    "topics": {
                        "0": 52, 
                        "1": 300, 
                        "2": 5, 
                        "3": 30, 
                        "4": 62, 
                        "5": 300, 
                    }
                }, 
                "Jimmy_Carter_4.txt": {
                    "labeled": {
                    },
                    "unlabeled": {
                        "time_of_day": [0, 0.5, 1],
                        "year": [2005, 2006, 2010],
                    },
                    "topics": {
                        "0": 52, 
                        "1": 143, 
                        "2": 1000, 
                        "3": 30, 
                        "4": 62, 
                        "5": 85, 
                    }
                }, 
                "John_Adams_1.txt": {
                    "labeled": {
                    },
                    "unlabeled": {
                        "time_of_day": [0, 0.5, 1],
                        "year": [2000, 2000, 2001],
                    },
                    "topics": {
                        "0": 52, 
                        "1": 143, 
                        "2": 5, 
                        "3": 800, 
                        "4": 62, 
                        "5": 85, 
                    }
                }, 
                "Andrew_Johnson_3.txt": {
                    "labeled": {
                    },
                    "unlabeled": {
                        "time_of_day": [0, 0.5, 1],
                        "year": [1996, 1999, 2001],
                    },
                    "topics": {
                        "0": 52, 
                        "1": 143, 
                        "2": 5, 
                        "3": 30, 
                        "4": 600, 
                        "5": 85, 
                    }
                }, 
                "Theodore_Roosevelt_3.txt": {
                    "labeled": {
                        "year": 2000,
                    },
                    "unlabeled": {
                        "time_of_day": [0.6, 0.8, 0.9],
                    },
                    "topics": {
                        "0": 52, 
                        "1": 143, 
                        "2": 5, 
                        "3": 500, 
                        "4": 500, 
                        "5": 85, 
                    }
                }, 
                "Grover_Cleveland_8.txt": {
                    "labeled": {
                        "time_of_day": 0.33456,
                    },
                    "unlabeled": {
                        "year": [1994, 1996, 1997],
                    },
                    "topics": {
                        "0": 100, 
                        "1": 143, 
                        "5": 100, 
                    }
                }, 
                "George_W._Bush_6.txt": {
                    "labeled": {
                    },
                    "unlabeled": {
                        "time_of_day": [0, 0.7, 0.8],
                        "year": [2000, 2006, 2010],
                    },
                    "topics": {
                        "0": 52, 
                        "1": 143, 
                        "2": 5, 
                        "3": 30, 
                        "4": 62, 
                        "5": 350, 
                    }
                }, 
                "Abraham_Lincoln_3.txt": {
                    "labeled": {
                    },
                    "unlabeled": {
                        "time_of_day": [0, 0.1, 0.2],
                        "year": [2001, 2002, 2003],
                    },
                    "topics": {
                        "0": 52, 
                        "1": 143, 
                        "2": 222, 
                        "3": 30, 
                    }
                }, 
                "Grover_Cleveland_1.txt": {
                    "labeled": {
                        "time_of_day": 0.21156,
                    },
                    "unlabeled": {
                        "year": [1997, 1997, 1997],
                    },
                    "topics": {
                        "0": 143, 
                        "18": 200, 
                    }
                }, 
            },
            "metadataTypes": {
                "year": "int",
                "time_of_day": "float",
            },
        };
        var docs = [];
        var docNames = {};
        for(key in data.documents) {
            var metadata = data.documents[key];
            metadata["userLabeled"] = {};
            var element = {
                "doc": key,
                "metadata": metadata,
            };
            docs.push(element);
            docNames[key] = metadata;
        }
        data.documents = docs;
        data.documentNames = docNames;
        var name = "";
        var type = "";
        for(n in data.metadataTypes) {
            name = n;
            type = data.metadataTypes[n];
        }
        this.model.set(data);
        this.settingsModel.set({ name: name, type: type });
    },
    
    //++++++++++++++++++++++++++++++++++++++++++++++++++    UPDATE VISUALIZATION    ++++++++++++++++++++++++++++++++++++++++++++++++++\\
    
    /**
     * Move the plot and axis into place.
     */
    updateMap: function() {
        // Basic data needed to determine axis information.
        var type = this.settingsModel.get("type");
        var name = this.settingsModel.get("name");
        
        if(name === "" || type === "") {
            return;
        }
        
        // Split documents so we can see how many unlabeled documents we'll have room for.
        var documents = this.model.get("documents");
        var numberOfUnlabeled = this.getNumberOfUnlabeledDocuments();
        
        // Gather data.
        var width = this.model.get("dimensions").width;
        var height = this.model.get("dimensions").height;
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
        console.log("Start: "+labeledBoxHeight);
        
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
            type.text(globalTypes[selectedType]);
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
        if(this.settingsModel.get("name") === "" || this.settingsModel.get("type") === "") {
            return;
        }
        
        var that = this;
        
        var xScale = this.xScale;
        var name = this.settingsModel.get("name"); // Metadata name
        var type = this.settingsModel.get("type"); // Metadata type
        var documentHeight = this.model.get("documentHeight");
        var radius = documentHeight/2;
        var buffer = radius;
        var numberOfUnlabeledsToShow = this.model.get("unlabeledDocumentCount");
        var labeledY = this.model.get("labeledYCoord");
        var unlabeledY = this.model.get("unlabeledYCoord");
        var documentQueueOrder = this.model.get("unlabeledDocumentOrder");
        
        function getUnlabeledDocumentY(docName) {
            return unlabeledY + documentQueueOrder[docName]*documentHeight+documentHeight/2;
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
                if(that.isLabeled(d, name, false)) {
                    if(that.isUserLabeled(d, name)) {
                        return "red";
                    } else {
                        return "blue"
                    }
                } else {
                    if(that.isUserLabeled(d, name)) {
                        return "green";
                    } else {
                        return "black";
                    }
                }
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
    
    //++++++++++++++++++++++++++++++++++++++++++++++++++    EVENTS    ++++++++++++++++++++++++++++++++++++++++++++++++++\\
    
    events: {
        "change #metadata-name-control": "changeMetadataType",
        "change #document-value-control": "changeDocumentValue",
        "click .document": "clickDocument",
        "dblclick .document": "doubleClickDocument",
        "click #save-changes": "clickSaveChanges",
        "click #get-documents": "clickGetDocuments",
        "mouseover .document": "mouseoverDocument",
        "mouseout .document": "mouseoutDocument",
        "mousedown .document": "mousedownDocument",
    },
    
    /**
     * Update the settings model.
     */
    changeMetadataType: function(e) {
        var metadataType = e["target"]["value"];
        this.settingsModel.set({
            "name": metadataType,
            "type": this.model.get("metadataTypes")[metadataType],
        });
    },
    
    /**
     * Check the user input for valid input type. Update the settings model.
     */
    changeDocumentValue: function(e) {
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
     * Save any updates to document metadata from the user to the server.
     */
    clickSaveChanges: function(e) {
        alert("Saving not yet enabled.");
    },
    
    /**
     * Get documents from the server.
     */
    clickGetDocuments: function(e) {
        this.loadData();
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
        console.log(topics);
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
