
var PlotView = DefaultView.extend({
    
    mainTemplate:
"<div id=\"plot-view\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>"+
"<div id=\"plot-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",

    controlsTemplate:
"<h3><b>Controls</b></h3>"+
"<hr />"+
"<div>"+
"    <label for=\"x-axis-control\">X Axis</label>"+
"    <select id=\"x-axis-control\" type=\"selection\" class=\"form-control\" name=\"X Axis\"></select>"+
"</div>"+
"<div>"+
"    <label for=\"y-axis-control\">Y Axis</label>"+
"    <select id=\"y-axis-control\" type=\"selection\" class=\"form-control\" name=\"Y Axis\"></select>"+
"</div>"+
"<div>"+
"    <label for=\"radius-control\">Radius</label>"+
"    <select id=\"radius-control\" type=\"selection\" class=\"form-control\" name=\"Radius\"></select>"+
"</div>"+
"<div>"+
"    <label for=\"color-control\">Color</label>"+
"    <select id=\"color-control\" type=\"selection\" class=\"form-control\" name=\"Color\"></select>"+
"</div>",
//~ "<hr />"+
//~ "<div>"+
//~ "    <label for=\"aggregate-control\">Aggregate Documents</label>"+
//~ "    <select id=\"aggregate-control\" type=\"selection\" class=\"form-control\" name=\"Aggregate\"></select>"+
//~ "</div>"+
//~ "<hr />"+
//~ "<div>"+
//~ "    <label for=\"add-remove-control\">Add/Remove Documents</label>"+
//~ "    <select id=\"add-remove-control\" type=\"selection\" class=\"form-control\" name=\"Add/Remove\"></select>"+
//~ "</div>",

    readableName: "2D Plots",
    
    initialize: function() {
        this.model = new Backbone.Model();
    },
    
    cleanup: function() {
    },
    
    render: function() {
        d3.select(this.el).html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selections["dataset"],
            "analyses": selections.analysis,
            "topics": "*",
            "topic_attr": "names",
            "documents": "*",
            "document_attr": ["metadata", "metrics", "top_n_topics"],
            "document_continue": 0,
            "document_limit": 100,
        }, function(data) {
            this.$el.html(this.mainTemplate);
            
            var selections = this.selectionModel.attributes;
            var analysis = data.datasets[selections["dataset"]].analyses[selections["analysis"]];
            var documents = analysis.documents;
            var topics = analysis.topics;
            var topicCount = _.size(topics);
            this.model.set({ documents: documents, topicCount: topicCount, topics: topics });
            this.model.set({
                dimensions: {
                    // Dimensions of svg element.
                    width: 800,
                    height: 800,
                },
                
                radii: {
                    // Dimensions of document circles.
                    min: 3,
                    max: 10,
                },
                
                // Duration of the transitions.
                duration: 800, // 8/10 seconds
                
                // Set default values for the axes, radius, and colors.
                xAxis: {
                    min: 0,
                    max: 1,
                    type: "int",
                    title: "x-axis",
                    scale: d3.scale.linear().domain([0, 1]),
                },
                yAxis: {
                    min: 0,
                    max: 1,
                    type: "int",
                    title: "y-axis",
                    scale: d3.scale.linear().domain([0, 1]),
                },
                radius: {
                    min: 0,
                    max: 1,
                },
                color: {
                    min: 0,
                    max: 1,
                },
            });
            
            this.renderControls();
            this.renderPlot();
            this.model.on("change:dimensions", this.renderPlot, this);
        }.bind(this), this.renderError.bind(this));
    },
    
    renderControls: function() {
        var that = this;
        var controls = d3.select(this.el).select("#plot-controls");
        controls.html(this.controlsTemplate);
        
        // Find selects to be populated.
        var xAxis = this.xAxisSelect = controls.select("#x-axis-control");
        var yAxis = this.yAxisSelect = controls.select("#y-axis-control");
        var radius = this.radiusSelect = controls.select("#radius-control");
        var color = this.colorSelect = controls.select("#color-control");
        var selects = [xAxis, yAxis, color, radius]; // Radius is last as the options differ.
        
        var documents = this.model.attributes.documents;
        var topics = this.model.attributes.topics;
        var data = {};
        // Get metadata and metric information.
        for(key in documents) {
            for(key2 in documents[key]) {
                data[key2] = $.extend({}, documents[key][key2]);
            }
            break;
        }
        // Remove topics from data used for building the selects.
        delete data.topics;
        // Change the stuff we copied.
        for(key in data) {
            var groupItem = data[key];
            for(key2 in groupItem) {
                groupItem[key2] = key2;
            }
        }
        // Add topic names.
        data.topics = {};
        for(key in topics) {
            var name = topics[key].names.Top3;
            data.topics[name] = key;
        }
        // Turn hashes to arrays and sort in alphabetical order.
        // Also, make sure the documents hash keys are stored in the select for retrieval.
        var groupNames = [];
        for(key in data) {
            groupNames.push(key);
            var readableNames = [];
            var hashKeys = [];
            var subData = data[key];
            for(item in subData) readableNames.push(item);
            readableNames.sort();
            for(var i = 0; i < readableNames.length; i++) {
                hashKeys.push({ key: readableNames[i], value: subData[readableNames[i]] });
            }
            data[key] = hashKeys;
        }
        groupNames.sort();
        // Find the initial group and value.
        var group = false;
        var value = false;
        
        // Build the selects.
        for(var i = 0; i < selects.length; i++) {
            var select = selects[i];
            if(select === radius) {
                groupNames.push("other"); // Add uniform option.
                data["other"] = [{ key: "uniform", value: "uniform" }];
            }
            var optgroups = select.selectAll("optgroup")
                .data(groupNames)
                .enter()
                .append("optgroup")
                .attr("value", function(d, i) { 
                    if(!group) group = d;
                    return d;
                })
                .attr("label", function(d) { return toTitleCase(d.replace(/_/g, " ")); });
            var options = optgroups.selectAll("option")
                .data(function(d) { return data[d]; })
                .enter()
                .append("option")
                .attr("value", function(d) { 
                    if(!value) value = d.value;
                    return d.value;
                })
                .text(function(d) { return toTitleCase(d.key.replace(/_/g, " ")); });
            if(select === radius) {
                select.property("value", "uniform"); // Set to uniform option.
            }
        }
        
        // Set listeners.
        xAxis.on("change", function() {
            var group = $(this).find(":selected").parent().attr("value");
            var value = xAxis.property("value");
            that.model.set({ xSelection: { group: group, value: value } });
        });
        yAxis.on("change", function() {
            var group = $(this).find(":selected").parent().attr("value");
            var value = yAxis.property("value");
            that.model.set({ ySelection: { group: group, value: value } });
        });
        radius.on("change", function() {
            var group = $(this).find(":selected").parent().attr("value");
            var value = radius.property("value");
            that.model.set({ radiusSelection: { group: group, value: value } });
        });
        color.on("change", function() {
            var group = $(this).find(":selected").parent().attr("value");
            var value = color.property("value");
            that.model.set({ colorSelection: { group: group, value: value } });
        });
        
        // Set initial groups and values for selections.
        this.model.set({
            xSelection: { group: group, value: value },
            ySelection: { group: group, value: value },
            radiusSelection: { group: "other", value: "uniform" },
            colorSelection: { group: group, value: value },
        });
    },
    
    renderPlot: function() {
        // Data variables.
        var documents = this.model.attributes.documents;
        var topics = this.model.attributes.topics;
        // Dimensions.
        var dim = this.model.attributes.dimensions;
        
        // Create scales and axes.
        var xScale = this.xScale = d3.scale.linear()
            .domain([0, 1])
            .range([0, dim.width]);
        var yScale = this.yScale = d3.scale.linear()
            .domain([0, 1])
            .range([dim.height, 0]);
        var xAxis = this.xAxis = d3.svg.axis().scale(xScale).orient("bottom");
        var yAxis = this.yAxis = d3.svg.axis().scale(yScale).orient("left");
        
        // Render the scatter plot.
        var view = d3.select(this.el).select("#plot-view").html("");
        
        var svg = this.svg = view.append("svg")
            .attr("width", "100%")
            .attr("height", "90%")
            .attr("viewBox", "0, 0, "+dim.width+", "+dim.height)
            .attr("preserveAspectRatio", "xMidYMin meet")
            .append("g");
        // Hidden group to render text and get the size in pixels.
        this.hiddenTextGroup = svg.append("g")
            .attr("transform", "translate("+dim.width/2+","+dim.height/2+")")
            .style({ "fill": "none", "stroke": "white" });
        this.hiddenText = this.hiddenTextGroup.append("text");
        // Render xAxis.
        var xAxisGroup = this.xAxisGroup = svg.append("g")
            .attr("id", "x-axis");
        this.xAxisText = this.xAxisGroup.append("text");
        var yAxisGroup = this.yAxisGroup = svg.append("g")
            .attr("id", "y-axis");
        this.yAxisText = this.yAxisGroup.append("text");
        // Render scatter plot container.
        this.plot = svg.append("g")
            .attr("id", "scatter-plot");
        this.circles = this.plot.selectAll("circle")
            .data(d3.entries(documents))
            .enter()
            .append("circle")
            .attr("r", 3)
            .attr("cx", 0)
            .attr("cy", 0);
        
        // Create listeners.
        this.model.on("change:xSelection", this.calculateXAxis, this);
        this.model.on("change:ySelection", this.calculateYAxis, this);
        this.model.on("change:xAxis change:yAxis", this.transitionAxes, this);
        this.model.on("change:radii", this.transitionAxes, this); // If the radii change, the padding the axes get changes.
        this.model.on("change:xScale", this.transitionXCoordinates, this);
        this.model.on("change:yScale", this.transitionYCoordinates, this);
        
        this.model.on("change:radiusSelection", this.transitionRadii, this);
        this.model.on("change:colorSelection", this.transitionColors, this);
        this.model.on("change:radii", this.transitionRadii, this);
        
        this.calculateXAxis();
        this.calculateYAxis();
    },
    
    // Find the min, max, type, and scale for the given selection.
    getSelectionInfo: function(group, value) {
        var documents = this.model.attributes.documents;
        console.log(group);
        console.log(value);
        console.log(JSON.stringify(documents));
        var min = Number.MAX_VALUE;
        var max = -Number.MAX_VALUE;
        var text = {}; // Used if the type is determined to be text.
        var type = false;
        for(key in documents) {
            var docValue = documents[key][group][value];
            if(docValue === undefined) continue;
            if(!type) { // Set the type.
                console.log("Value: "+docValue);
                if($.isNumeric(docValue) && !(docValue instanceof String)) {
                    if(Math.floor(docValue) === docValue) {
                        type = "int";
                    } else {
                        type = "float";
                    }
                    min = Number.MAX_VALUE;
                    max = -Number.MAX_VALUE;
                } else {
                    type = "text";
                    min = "";
                    max = "DDDDDDDDDDD";// only ten characters can be displayed.
                }
                console.log("Type: "+type);
            }
            
            if(type !== "text") {
                if(docValue < min) min = docValue;
                if(docValue > max) max = docValue;
            } else {
                text[docValue] = true;
            }
        }
        
        console.log(JSON.stringify(text));
        console.log(JSON.stringify([min, max]));
        var scale = false;
        if(type === "text") {
            var domain = [];
            for(k in text) domain.push(k);
            domain.sort();
            scale = d3.scale.ordinal().domain(domain);
        } else {
            scale = d3.scale.linear().domain([min, max]);
        }
        return {
            min: min, 
            max: max, 
            type: type, 
            scale: scale,
            title: toTitleCase(group.replace(/_/g, " "))+": "+toTitleCase(value.replace(/_/g, " ")),
        };
    },
    
    calculateXAxis: function() {
        // Get basic information about the group.
        var group = this.model.attributes.xSelection.group;
        var value = this.model.attributes.xSelection.value;
        this.model.set({ xAxis: this.getSelectionInfo(group, value) });
    },
    
    calculateYAxis: function() {
        // Get basic information about the group.
        var group = this.model.attributes.ySelection.group;
        var value = this.model.attributes.ySelection.value;
        this.model.set({ yAxis: this.getSelectionInfo(group, value) });
    },
    
    getFormat: function(type) {
        if(type === "float") {
            return d3.format(".2f");
        } else if (type === "int") {
            return d3.format(".0f");
        } else {
            return function(s) { return s.slice(0, 10); };
        }
    },
    
    // Any time the axes min/max change the axes will transition to where they should be.
    transitionAxes: function() {
        var transitionDuration = this.model.attributes.duration;
        var dim = this.model.attributes.dimensions;
        var radii = this.model.attributes.radii;
        var xAxisInfo = this.model.attributes.xAxis;
        var yAxisInfo = this.model.attributes.yAxis;
        var xFormat = this.getFormat(xAxisInfo.type);
        var yFormat = this.getFormat(yAxisInfo.type);
        
        var barThickness = 11;
        this.hiddenText.text(xFormat(xAxisInfo.min)); 
        var xAxisLeft = this.hiddenTextGroup[0][0].getBBox().width/2;
        this.hiddenText.text(xFormat(xAxisInfo.max));
        var xAxisRight = this.hiddenTextGroup[0][0].getBBox().width/2;
        var xAxisHeight = this.hiddenTextGroup[0][0].getBBox().height + barThickness;
        this.hiddenText.text(yFormat(yAxisInfo.max));
        var yAxisTextLen = this.hiddenTextGroup[0][0].getBBox().width;
        var textHeight = this.hiddenTextGroup[0][0].getBBox().height;
        
        // Calculate axes offsets.
        var yAxisX = textHeight + yAxisTextLen + barThickness;
        var yAxisY = radii.max;
        var yAxisHeight = dim.height - 2*textHeight - 2*radii.max - barThickness;
        var xAxisX = Math.max(yAxisX + radii.max, xAxisLeft);
        var xAxisY = yAxisHeight + 2*radii.max;
        var xAxisWidth = dim.width -  xAxisX - Math.max(xAxisRight, radii.max);
        
        // Transition x-axis.
        if(xAxisInfo.type === "text")
            xAxisInfo.scale.rangeBands([0, xAxisWidth]);
        else
            xAxisInfo.scale.range([0, xAxisWidth]);
        this.xAxis.scale(xAxisInfo.scale)
            .tickFormat(xFormat);
        this.xAxisGroup.transition()
            .duration(transitionDuration)
            .style({ "fill": "none", "stroke": "black", "shape-rendering": "crispedges" })
            .attr("transform", "translate("+xAxisX+","+xAxisY+")")
            .call(this.xAxis);
        this.xAxisText.transition()
            .duration(transitionDuration)
            .attr("x", xAxisWidth/2)
            .attr("y", barThickness + textHeight)
            .style({ "text-anchor": "middle", "dominant-baseline": "hanging" })
            .text(xAxisInfo.title);
        
        // Transition y-axis.
        if(yAxisInfo.type === "text")
            yAxisInfo.scale.rangeBands([yAxisHeight, 0]);
        else
            yAxisInfo.scale.range([yAxisHeight, 0]);
        this.yAxis.scale(yAxisInfo.scale)
            .tickFormat(yFormat);
        this.yAxisGroup.transition()
            .duration(transitionDuration)
            .style({ "fill": "none", "stroke": "black", "shape-rendering": "crispedges" })
            .attr("transform", "translate("+yAxisX+","+yAxisY+")")
            .call(this.yAxis);
        this.yAxisText.transition()
            .duration(transitionDuration)
            .attr("transform", "rotate(-90)")
            .attr("x", -yAxisHeight/2)
            .attr("y", -(yAxisTextLen + barThickness))
            .style("text-anchor", "middle")
            .text(yAxisInfo.title);
        
        this.plot.attr("transform", "translate("+xAxisX+","+yAxisY+")");
        
        this.transitionCircles(xAxisInfo.scale, yAxisInfo.scale);
    },
    
    transitionCircles: function(xScale, yScale) {
        console.log("xcoord");
        var transitionDuration = this.model.attributes.duration;
        var xGroup = this.model.attributes.xSelection.group;
        var xValue = this.model.attributes.xSelection.value;
        var xType = this.model.attributes.xAxis.type;
        var yGroup = this.model.attributes.ySelection.group;
        var yValue = this.model.attributes.ySelection.value;
        var yType = this.model.attributes.yAxis.type;
        var newXScale = null;
        var newYScale = null;
        
        var indicesToHide = {};
        // Modify the scale to account for text data and remove add index to remove if values are undefined.
        if(xType !== "text") {
            newXScale = function(v, i) { 
                if(v === undefined) {
                    indicesToHide[i] = true;
                    return 0;
                } else {
                    return xScale(v);
                }
            };
        } else {
            var xWidth = xScale.rangeBand()/2;
            newXScale = function(s, i) {
                if(s === undefined) {
                    indicesToHide[i] = true;
                    return 0;
                } else {
                    return xScale(s) + xWidth;
                }
            };
        }
        if(yType !== "text") {
            newYScale = function(v, i) { 
                if(v === undefined) {
                    indicesToHide[i] = true;
                    return 0;
                } else {
                    return yScale(v);
                }
            };
        } else {
            var yWidth = yScale.rangeBand()/2;
            newYScale = function(s, i) {
                if(s === undefined) {
                    indicesToHide[i] = true;
                    return 0;
                } else {
                    return yScale(s) + yWidth;
                }
            };
        }
        
        // Transition the circles.
        this.circles.transition()
            .duration(transitionDuration)
            .attr("cx", function(d, i) {
                return newXScale(d.value[xGroup][xValue], i);
            })
            .attr("cy", function(d, i) {
                return newYScale(d.value[yGroup][yValue], i);
            })
            .each("end", function(d, i) {
                var opacity = 1;
                if(i in indicesToHide) {
                    opacity = 0;
                }
                d3.select(this)
                    .transition()
                    .duration(transitionDuration)
                    .attr("opacity", opacity);
            });
        
        
    },
    
    transitionColors: function() {
    },
    
    transitionRadii: function() {
    },
    
    renderHelpAsHtml: function() {
        return "<p>Plots help coming soon.</p>";
    },
    
});

globalViewModel.addViewClass([], PlotView);
