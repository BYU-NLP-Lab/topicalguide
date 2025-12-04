
var PlotView = DefaultView.extend({
    
    mainTemplate:
"<div id=\"plot-view\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>"+
"<div id=\"plot-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",

    controlsTemplate:
"<h3><b>Controls</b></h3>"+
"<hr />"+
"<div>"+
"    <label for=\"document-picker-control\">Select Document</label>"+
"    <select id=\"document-picker-control\" type=\"selection\" class=\"form-control\" name=\"Document\">"+
"        <option value=\"\">(Click a point or select here)</option>"+
"    </select>"+
"</div>"+
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
"</div>"+
"<hr />"+
"<div id=\"plot-remove-documents\" class=\"btn btn-default\">Remove Documents</div>"+
"<div id=\"plot-add-all-removed-documents\" class=\"btn btn-default\">Add Removed Documents</div>"+
"<hr />"+
"<div>"+
"    <a id=\"plot-save-svg\" class=\"btn btn-default\">Download as SVG</a>"+
"</div>",

    readableName: "2D Plots",
    
    initialize: function() {
        this.selectionModel.on("change:dataset", this.render, this);
        this.selectionModel.on("change:analysis", this.render, this);
        this.selectionModel.on("change:topic_name_scheme", this.render, this);
        this.selectionModel.on("change:document", this.updateDocumentPicker, this);
        this.model = new Backbone.Model(); // Used to store document data.
    },
    
    cleanup: function() {
        this.selectionModel.off(null, null, this);
    },
    
    getQueryHash: function() {
        var selections = this.selectionModel.attributes;
        return {
            "datasets": selections.dataset,
            "analyses": selections.analysis,
            "topics": "*",
            "topic_attr": "names",
            "documents": "*",
            "document_attr": ["metadata", "metrics", "top_n_topics"],
            "document_continue": 0,
            "document_limit": 1000,
        };
    },
    
    render: function() {
        this.$el.empty();
        
        if(!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<p>You should select a <a href=\"#\">dataset and analysis</a> before proceeding.</p>");
            return;
        }
        
        d3.select(this.el).html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash(this.getQueryHash(), function(data) {
            this.$el.html(this.mainTemplate);
            
            var processedData = this.processData(data);
            this.model.set(processedData);
            this.model.set({
                // Dimensions of svg viewBox.
                dimensions: {
                    width: 800,
                    height: 800,
                },
                // Dimensions of the circles.
                radii: {
                    min: 7,
                    max: 20,
                },
                
                // Duration of the transitions.
                duration: 800, // 8/10 of a second
                
                textHeight: 16,
            });
            this.xInfo = {
                min: 0,
                max: 1,
                type: "float",
                title: "x-axis",
                text: [],
                rangeMax: 800,
                noData: {},
            };
            this.yInfo = {
                min: 0,
                max: 1,
                type: "float",
                title: "y-axis",
                text: [],
                rangeMax: 800,
                noData: {},
            };
            this.radiusInfo = {
                min: 0,
                max: 1,
                type: "float",
                title: "radial-axis",
                text: [],
                noData: {},
            };
            this.colorInfo = {
                min: 0,
                max: 1,
                type: "float",
                title: "color-axis",
                text: [],
                noData: {},
            };
            this.removedDocuments = {};
            
            this.renderControls();
            this.renderPlot();
            this.model.on("change", this.transition, this);
        }.bind(this), this.renderError.bind(this));
    },
    
    /*
     * Put data in the form of several hashes. All groups must exist in the hashes but not all 
     * values need to exist.  A group is like "metrics" a value is like "Token Count" (a metric).
     * data - Contains the raw data. The group and value items should index this value.
     *        e.g. data[group][value] -> Text or numeric value.
     * groupNames - Maps a group name to the readable group name.
     *              e.g. groupNames[group] -> readableName
     * valueNames - Maps to group to a value to a readable name.
     *              e.g. valuesNames[group][value] -> readableName
     * valueTypes - Maps to group to a value to a type. Must contain all possible values.
     *              e.g. valuesTypes[group][value] -> readableName
     * Return a hash with the above hashes.
     */
    processData: function(data) {
        var selections = this.selectionModel.attributes;
        var analysis = data.datasets[selections["dataset"]].analyses[selections["analysis"]];
        
        var groupNames = {};
        var valueNames = {};
        var valueTypes = {};
        
        // Put data into the correct format.
        var documents = analysis.documents;
        // Make sure that topic relations are in percentage forms.
        for(docKey in documents) {
            var doc = documents[docKey];
            var totalTokens = 0;
            var topics = doc.topics;
            for(key in topics) {
                totalTokens += topics[key];
            }
            for(key in topics) {
                topics[key] = topics[key]/totalTokens;
            }
            // Add uniform property.
            doc.other = {};
            doc.other.uniform = 0;
            
            for(key in doc) {
                groupNames[key] = toTitleCase(key.replace(/_/g, " "));
                if(!(key in valueNames)) {
                    valueNames[key] = {};
                    valueTypes[key] = {};
                }
                var group = doc[key];
                for(valKey in group){
                    if(!(valKey in valueNames[key])) {
                        valueNames[key][valKey] = toTitleCase(valKey.replace(/_/g, " "));
                        valueTypes[key][valKey] = this.getType(group[valKey]);
                    }
                }
            }
        }
        
        // Make sure the topic's readable name is set.
        var allTopics = analysis.topics;
        var selectedScheme = this.selectionModel.get("topic_name_scheme") || "Top3";
        console.log(valueNames);
        if("topics" in valueNames) {
            var valueTopics = valueNames.topics;
            for(topKey in valueTopics) {
                // Skip topics that don't exist (e.g., BERTopic outlier topic -1)
                if(allTopics[topKey] && allTopics[topKey].names) {
                    valueTopics[topKey] = toTitleCase(allTopics[topKey].names[selectedScheme] || allTopics[topKey].names.Top3);
                }
            }
        }
        
        return {
            data: documents,
            groupNames: groupNames,
            valueNames: valueNames,
            valueTypes: valueTypes,
        };
    },
    
    updateDocumentPicker: function() {
        var documentPicker = d3.select(this.el).select("#document-picker-control");
        if(!documentPicker.empty()) {
            var selectedDoc = this.selectionModel.get("document");
            if(selectedDoc && selectedDoc !== "") {
                documentPicker.property("value", selectedDoc);
            } else {
                documentPicker.property("value", "");
            }
        }
    },

    renderControls: function() {
        var that = this;
        var controls = d3.select(this.el).select("#plot-controls");
        controls.html(this.controlsTemplate);
        
        // Get selects to be populated.
        var xAxis = this.xAxisSelect = controls.select("#x-axis-control");
        var yAxis = this.yAxisSelect = controls.select("#y-axis-control");
        var radius = this.radiusSelect = controls.select("#radius-control");
        var color = this.colorSelect = controls.select("#color-control");
        var selects = [xAxis, yAxis, color, radius]; // Radius is last as the options differ.
        
        // Find the initial group and value.
        var group = false;
        var value = false;
        
        var groupNames = this.model.attributes.groupNames;
        groupNames = d3.entries(groupNames).sort(function(a, b) { return a.value.localeCompare(b.value); });
        
        var valueNames = this.model.attributes.valueNames;
        // Build the selects.
        for(var i = 0; i < selects.length; i++) {
            var select = selects[i];
            var optgroups = select.selectAll("optgroup")
                .data(groupNames)
                .enter()
                .append("optgroup")
                .attr("value", function(d, i) { 
                    if(!group) group = d.key;
                    return d.key;
                })
                .attr("label", function(d) { return d.value; });
            var options = optgroups.selectAll("option")
                .data(function(d) { 
                    var names = valueNames[d.key];
                    names = d3.entries(names).sort(function(a, b) { return a.value.localeCompare(b.value); });
                    return names;
                })
                .enter()
                .append("option")
                .attr("value", function(d) { 
                    if(!value) value = d.key;
                    return d.key;
                })
                .text(function(d) { return d.value; });
            if(select === radius) {
                select.property("value", "uniform"); // Set to uniform option.
            }
        }
        if(this.settingsModel.has("xSelection")) {
            xAxis.property("value", this.settingsModel.get("xSelection").value);
        }
        if(this.settingsModel.has("ySelection")) {
            yAxis.property("value", this.settingsModel.get("ySelection").value);
        }
        if(this.settingsModel.has("radiusSelection")) {
            radius.property("value", this.settingsModel.get("radiusSelection").value);
        }
        if(this.settingsModel.has("colorSelection")) {
            color.property("value", this.settingsModel.get("colorSelection").value);
        }
        
        // Populate document picker.
        var documentPicker = controls.select("#document-picker-control");
        var data = this.model.attributes.data;
        var documentIds = d3.keys(data).sort();
        documentPicker.selectAll("option.doc-option")
            .data(documentIds)
            .enter()
            .append("option")
            .classed("doc-option", true)
            .attr("value", function(d) { return d; })
            .text(function(d) { return d; });

        // Set document picker to current selection if any.
        if(this.selectionModel.has("document") && this.selectionModel.get("document") !== "") {
            documentPicker.property("value", this.selectionModel.get("document"));
        }

        // Set control listeners.
        documentPicker.on("change", function documentPickerChange() {
            var value = documentPicker.property("value");
            that.selectionModel.set({ document: value });
        });

        xAxis.on("change", function xAxisChange() {
            var group = $(this).find(":selected").parent().attr("value");
            var value = xAxis.property("value");
            that.settingsModel.set({ xSelection: { group: group, value: value } });
        });
        yAxis.on("change", function yAxisChange() {
            var group = $(this).find(":selected").parent().attr("value");
            var value = yAxis.property("value");
            that.settingsModel.set({ ySelection: { group: group, value: value } });
        });
        radius.on("change", function radiusAxisChange() {
            var group = $(this).find(":selected").parent().attr("value");
            var value = radius.property("value");
            that.settingsModel.set({ radiusSelection: { group: group, value: value } });
        });
        color.on("change", function colorAxisChange() {
            var group = $(this).find(":selected").parent().attr("value");
            var value = color.property("value");
            that.settingsModel.set({ colorSelection: { group: group, value: value } });
        });
        
        // Set initial groups and values for selections.
        var defaultSettings = {
            xSelection: { group: group, value: value },
            ySelection: { group: group, value: value },
            radiusSelection: { group: "other", value: "uniform" },
            colorSelection: { group: group, value: value },
            removing: false,
        };
        this.settingsModel.set(_.extend({}, defaultSettings, this.settingsModel.attributes));
        
        // Give the remove documents buttons functionality.
        d3.select(this.el).select("#plot-remove-documents")
            .on("click", function onRemoveDocumentsClick() {
                var removing = that.settingsModel.attributes.removing;
                if(removing) {
                    d3.select(this).text("Remove Documents");
                    that.calculateXAxis();
                    that.calculateYAxis();
                    that.calculateRadiusAxis();
                } else {
                    d3.select(this).text("Stop Removing Documents");
                }
                that.settingsModel.set({ removing: (!removing) });
            });
        d3.select(this.el).select("#plot-add-all-removed-documents")
            .on("click", function onAddAllDocumentsClick() {
                that.removedDocuments = {};
                that.calculateXAxis();
                that.calculateYAxis();
                that.calculateRadiusAxis();
            });
        
        // Give save buttons functionality.
        d3.select(this.el).select("#plot-save-svg")
            .on("mouseenter", function createSVGText() {
                var svg = d3.select(that.el).select("#plot-view");
                d3.select(this)
                    .attr("href", "data:application/octet-stream;utf8,"+encodeURIComponent(svg.html()))
                    .attr("download", "graph.svg");
            })
            .on("mouseleave", function removeSVGText() {
                d3.select(this)
                    .attr("href", "");
            });
    },
    
    renderPlot: function() {
        var that = this;
        
        // Data variables.
        var data = this.model.attributes.data;
        var topics = this.model.attributes.topics;
        // Dimensions.
        var dim = this.model.attributes.dimensions;
        var textHeight = this.model.attributes.textHeight;
        var duration = this.model.attributes.duration;
        
        // Create scales and axes.
        var xScale = d3.scale.linear()
            .domain([0, 1])
            .range([0, dim.width]);
        var yScale = d3.scale.linear()
            .domain([0, 1])
            .range([dim.height, 0]);
        var xAxis = d3.svg.axis().scale(xScale).orient("bottom");
        var yAxis = d3.svg.axis().scale(yScale).orient("left");
        
        // Render the scatter plot.
        var view = d3.select(this.el).select("#plot-view").html("");
        
        var svg = this.svg = view.append("svg")
            .attr("width", "100%")
            .attr("height", "90%")
            .attr("viewBox", "0, 0, "+dim.width+", "+dim.height)
            .attr("preserveAspectRatio", "xMidYMin meet")
            .append("g");
        // Hidden group to render the axis before making transitions so everything appears correctly.
        this.xAxisHidden = svg.append("g")
            .attr("id", "x-hidden")
            .attr("transform", "translate(0,"+dim.height+")")
            .style({ "opacity": "0", "fill": "none", "stroke": "white", "shape-rendering": "crispedges" });
        this.yAxisHidden = svg.append("g")
            .attr("id", "y-hidden")
            .attr("transform", "translate(0,0)")
            .style({ "opacity": "0", "fill": "none", "stroke": "white", "shape-rendering": "crispedges" });
        // Render xAxis.
        this.xAxisGroup = svg.append("g")
            .attr("id", "x-axis")
            .attr("transform", "translate(0,"+dim.height+")")
            .style({ "fill": "none", "stroke": "black", "shape-rendering": "crispedges" });
        this.xAxisText = this.xAxisGroup.append("text");
        this.yAxisGroup = svg.append("g")
            .attr("id", "y-axis")
            .attr("transform", "translate(0,0)")
            .style({ "fill": "none", "stroke": "black", "shape-rendering": "crispedges" });
        this.yAxisText = this.yAxisGroup.append("text");
        // Render scatter plot container.
        this.plot = svg.append("g")
            .attr("id", "scatter-plot");
        this.circles = this.plot.selectAll("circle")
            .data(d3.entries(data))
            .enter()
            .append("circle")
            .attr("r", 3)
            .attr("cx", 0)
            .attr("cy", 0)
            .style("cursor", "pointer")
            .on("click", onDocumentClick);
        // Render the node count.
        this.nodeCount = svg.append("g")
            .attr("transform", "translate("+dim.width/2+",0)")
            .append("text")
            .style({ "text-anchor": "middle", "dominant-baseline": "hanging" });
        
        // Funcionality for document click.
        function onDocumentClick(d, i) {
            if(that.settingsModel.attributes.removing) {
                that.removedDocuments[d.key] = true;
                d3.select(this).transition()
                    .duration(duration)
                    .attr("r", 0);
            } else {
                that.selectionModel.set({ document: d.key });
            }
        };
        
        // Create listeners.
        this.settingsModel.on("change:xSelection", this.calculateXAxis, this);
        this.settingsModel.on("change:ySelection", this.calculateYAxis, this);
        this.settingsModel.on("change:radiusSelection", this.calculateRadiusAxis, this);
        this.settingsModel.on("change:colorSelection", this.calculateColorAxis, this);
        
        this.calculateAll();
    },
    
    getType: function(value) {
        var type = "text";
        if($.isNumeric(value) && !(value instanceof String)) {
            if(Math.floor(value) === value) {
                type = "int";
            } else {
                type = "float";
            }
        }
        return type;
    },
    
    getNoData: function(group, value) {
        var data = this.model.attributes.data;
        var noData = {};
        for(key in data) {
            var val = data[key][group][value];
            if(val === undefined || val === null) {
                noData[key] = true;
            }
        }
        
        return {
            noData: noData,
        };
    },
    
    calculateAll: function() {
        this.calculateXAxis(false);
        this.calculateYAxis(false);
        this.calculateRadiusAxis(false);
        this.calculateColorAxis();
    },
    
    calculateXAxis: function(transition) {
        var selection = this.settingsModel.attributes.xSelection;
        this.xInfo = _.extend(this.xInfo, this.getNoData(selection.group, selection.value));
        if(transition !== false) this.transition();
    },
    calculateYAxis: function(transition) {
        var selection = this.settingsModel.attributes.ySelection;
        this.yInfo = _.extend(this.yInfo, this.getNoData(selection.group, selection.value));
        if(transition !== false) this.transition();
    },
    calculateRadiusAxis: function(transition) {
        var selection = this.settingsModel.attributes.radiusSelection;
        this.radiusInfo = _.extend(this.radiusInfo, this.getNoData(selection.group, selection.value));
        if(transition !== false) this.transition();
    },
    calculateColorAxis: function(transition) {
        var selection = this.settingsModel.attributes.colorSelection;
        this.colorInfo = _.extend(this.colorInfo, this.getNoData(selection.group, selection.value));
        if(transition !== false) this.transition();
    },
    
    getFormat: function(type) {
        if(type === "float") {
            return d3.format(",.2f");
        } else if (type === "int") {
            return d3.format(".0f");
        } else {
            return function(s) { 
                if(s === undefined) return "undefined";
                else return s.slice(0, 20); 
            };
        }
    },
    
    // Find the min, max, type, title, and text for the given selection.
    getSelectionInfo: function(group, value, excluded) {
        var data = this.model.attributes.data;
        var groupNames = this.model.attributes.groupNames;
        var valueNames = this.model.attributes.valueNames;
        var min = Number.MAX_VALUE;
        var max = -Number.MAX_VALUE;
        var avg = 0;
        var total = 0;
        var count = 0;
        var text = {}; // Used if the type is determined to be text.
        var type = false;
        for(key in data) {
            if(key in excluded) continue;
            var val = data[key][group][value];
            
            if(!type) { // Set the type.
                type = this.getType(val);
                if(type === "text") {
                    min = 0;
                    max = 0;
                } else {
                    min = val;
                    max = val;
                }
            }
            
            if(type !== "text") {
                val = parseFloat(val);
                if(val < min) min = val;
                if(val > max) max = val;
                total += val;
                count++;
            } else {
                text[val] = true;
            }
        }
        
        if(type === "text") {
            var domain = [];
            for(k in text) domain.push(k);
            domain.sort();
            text = domain;
        }
        
        if(min === Number.MAX_VALUE && max === -Number.MAX_VALUE) {
            min = 0;
            max = 0;
        }
        
        if(count > 0) {
            avg = total/count;
        }
        
        return {
            min: min, 
            max: max, 
            avg: avg,
            type: type, 
            text: text, 
            title: groupNames[group]+": "+valueNames[group][value],
        };
    },
    
    getScale: function(info, range) {
        var scale = d3.scale.linear().domain([info.min, info.max]).range(range);
        if(info.type === "text") {
            scale = d3.scale.ordinal().domain(info.text).rangePoints(range);
        }
        return scale;
    },
    
    getInfo: function(group, value) {
    },
    
    transition: function() {
        // Collect needed information.
        var model = this.model.attributes;
        var dim = model.dimensions;
        var radii = model.radii;
        var transitionDuration = model.duration;
        var xSel = this.settingsModel.attributes.xSelection;
        var ySel = this.settingsModel.attributes.ySelection;
        var rSel = this.settingsModel.attributes.radiusSelection;
        var cSel = this.settingsModel.attributes.colorSelection;
        var xExclude = this.xInfo.noData;
        var yExclude = this.yInfo.noData;
        var radiusExclude = this.radiusInfo.noData;
        var colorExclude = this.colorInfo.noData;
        var docExclude = this.removedDocuments;
        var allExclude = _.extend({}, xExclude, yExclude, radiusExclude, docExclude);
        var xInfo = this.xInfo = _.extend(this.xInfo, this.getSelectionInfo(xSel.group, xSel.value, allExclude));
        var yInfo = this.yInfo = _.extend(this.yInfo, this.getSelectionInfo(ySel.group, ySel.value, allExclude));
        var radiusInfo = this.radiusInfo = _.extend(this.radiusInfo, this.getSelectionInfo(rSel.group, rSel.value, allExclude));
        var colorInfo = this.colorInfo = _.extend(this.colorInfo, this.getSelectionInfo(cSel.group, cSel.value, _.extend({}, allExclude, colorExclude)));
        
        var textHeight = model.textHeight;
        
        // Set axes at a starting point.
        var yScale = this.getScale(yInfo, [yInfo.rangeMax, 0]);
        var yFormat = this.getFormat(yInfo.type);
        var yAxis = d3.svg.axis().scale(yScale).orient("left").tickFormat(yFormat);
        this.yAxisHidden.call(yAxis);
        var yAxisDim = this.yAxisHidden[0][0].getBBox();
        
        var xScale = this.getScale(xInfo, [0, xInfo.rangeMax]);
        var xFormat = this.getFormat(xInfo.type);
        var xAxis = d3.svg.axis().scale(xScale).orient("bottom").tickFormat(xFormat);
        this.xAxisHidden.call(xAxis);
        this.xAxisHidden.selectAll("g").selectAll("text")
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", ".15em")
            .attr("transform", "rotate(-65)");
        var xAxisDim = this.xAxisHidden[0][0].getBBox();
        
        // Move the hidden axes.
        var yAxisX = textHeight + yAxisDim.width;
        var yAxisY = Math.max(radii.max, textHeight/2);
        var yAxisLength = yInfo.rangeMax = dim.height - textHeight - yAxisY - radii.max - xAxisDim.height;
        yScale = this.getScale(yInfo, [yInfo.rangeMax, 0]);
        yAxis = d3.svg.axis().scale(yScale).orient("left").tickFormat(yFormat);
        this.yAxisHidden.attr("transform", "translate("+yAxisX+","+yAxisY+")")
            .call(yAxis);
        yAxisDim = this.yAxisHidden[0][0].getBBox();
        var yAxisBar = this.yAxisHidden.select(".domain")[0][0].getBBox();
        
        var xAxisX = yAxisX + radii.max;
        var xAxisY = yAxisY + radii.max + yAxisBar.height;
        var xAxisLength = xInfo.rangeMax = dim.width - xAxisX - Math.max(radii.max, textHeight/2)
        xScale = this.getScale(xInfo, [0, xInfo.rangeMax]);
        xAxis = d3.svg.axis().scale(xScale).orient("bottom").tickFormat(xFormat);
        this.xAxisHidden.attr("transform", "translate("+xAxisX+","+xAxisY+")")
            .call(xAxis)
            .selectAll("g").selectAll("text")
                .style("text-anchor", "end")
                .attr("dx", "-.8em")
                .attr("dy", ".15em")
                .attr("transform", "rotate(-65)");
        xAxisDim = this.xAxisHidden[0][0].getBBox();
        
        // Transition the visible axes to final spot.
        yAxisX = textHeight + yAxisDim.width;
        yAxisY = Math.max(radii.max, textHeight/2);
        yAxisLength = yInfo.rangeMax = dim.height - textHeight - yAxisY - radii.max - xAxisDim.height;
        yScale = this.getScale(yInfo, [yInfo.rangeMax, 0]);
        yAxis = d3.svg.axis().scale(yScale).orient("left").tickFormat(yFormat);
        this.yAxisGroup.transition()
            .duration(transitionDuration)
            .attr("transform", "translate("+yAxisX+","+yAxisY+")")
            .call(yAxis);
        this.yAxisText.transition()
            .duration(transitionDuration)
            .attr("transform", "rotate(-90)")
            .attr("x", -yAxisLength/2)
            .attr("y", -yAxisDim.width - 4)
            .style("text-anchor", "middle")
            .text(yInfo.title);
        
        xAxisX = yAxisX + radii.max;
        xAxisY = yAxisY + radii.max + yAxisBar.height;
        xAxisLength = xInfo.rangeMax = dim.width - xAxisX - Math.max(radii.max, textHeight/2)
        xScale = this.getScale(xInfo, [0, xInfo.rangeMax]);
        xAxis = d3.svg.axis().scale(xScale).orient("bottom").tickFormat(xFormat);
        this.xAxisGroup.transition()
            .duration(transitionDuration)
            .attr("transform", "translate("+xAxisX+","+xAxisY+")")
            .call(xAxis)
            .selectAll("g").selectAll("text")
                .style("text-anchor", "end")
                .attr("dx", "-.8em")
                .attr("dy", ".15em")
                .attr("transform", "rotate(-65)");
        this.xAxisText.transition()
            .duration(transitionDuration)
            .attr("x", xAxisLength/2)
            .attr("y", xAxisDim.height)
            .style({ "text-anchor": "middle", "dominant-baseline": "hanging" })
            .text(xInfo.title);
        
        // Transition scatter plot.
        this.plot.transition()
            .duration(transitionDuration)
            .attr("transform", "translate("+xAxisX+","+yAxisY+")");
        
        // Transition circles.
        var radiusScale = this.getScale(radiusInfo, [radii.min, radii.max]);
        var colorScale = null;
        if(colorInfo.type === "text") {
            // All this allows us to map onto a spectrum of colors.
            var colors = ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a", 
                          "#d62728", "#ff9896", "#9467bd", "#c5b0d5", "#8c564b", "#c49c94", 
                          "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7", "#bcbd22", "#dbdb8d", 
                          "#17becf", "#9edae5"];
            var colorDomain = d3.scale.ordinal().domain(colors).rangePoints([0, 1], 0).range();
            var ordinalRange = d3.scale.ordinal().domain(colorInfo.text).rangePoints([0, 1], 0).range();
            var ordToNum = d3.scale.ordinal().domain(colorInfo.text).range(ordinalRange);
            var numToColor = d3.scale.linear().domain(colorDomain).range(colors);
            colorScale = function ordinalColorScale(val) { return numToColor(ordToNum(val)); };
        } else if(cSel.group === "other" && cSel.value === "uniform") {
            colorScale = function blackColorScale() { return "#000000"; };
        } else {
            colorScale = d3.scale.linear().domain([colorInfo.min, colorInfo.avg, colorInfo.max]).range(["blue", "#F0EAD6", "red"]);
        }
        
        this.circles.transition()
            .duration(transitionDuration)
            .attr("cx", function circleX(d, i) {
                if(d.key in allExclude) {
                    return 0;
                } else {
                    var v = d.value[xSel.group][xSel.value];
                    return xScale(v);
                }
            })
            .attr("cy", function circleY(d, i) {
                if(d.key in allExclude) {
                    return yAxisLength;
                } else {
                    var v = d.value[ySel.group][ySel.value];
                    return yScale(v);
                }
            })
            .attr("r", function circleRadius(d, i) {
                if(d.key in allExclude) {
                    return 0;
                } else {
                    var v = d.value[rSel.group][rSel.value];
                    return radiusScale(v);
                }
            })
            .attr("fill", function circleFill(d, i) {
                if(d.key in colorExclude) {
                    return "#000000";
                } else {
                    var v = d.value[cSel.group][cSel.value];
                    return colorScale(v);
                }
            });
        
        var totalDocuments = _.size(model.data);
        var totalDisplayed = totalDocuments - _.size(allExclude);
        this.nodeCount.text("Showing "+totalDisplayed+" of "+totalDocuments + " Documents");
    },
    
    renderHelpAsHtml: function() {
        return "<p>Note that with all the selections (except Color) a document is dropped if that document doesn't have the selected datum.</p>"+
               "<h4>X and Y Axes</h4>"+
               "<p>Select the data to sort the documents according to the data along the specified axis.</p>"+
               "<h4>Radius</h4>"+
               "<p>With text data that smaller the radius the earlier in the alphabet the text occurs.</p>"+
               "<h4>Color</h4>"+
               "<p>With text data the color is chosen from a spectrum of colors. With numeric data the color "+
               "is between blue, off-white, and red. Off-white is average, blue is below average and red is above average. "+
               "Note that documents without the selected data value will be displayed as black.</p>";
    },
    
});

var PlotViewManager = DefaultView.extend({
    
    readableName: "2D Plots",
    
    mainTemplate: 
"<div id=\"plot-view-container\" class=\"container-fluid\"></div>"+
"<div id=\"document-info-view-container\" class=\"container-fluid\"></div>",
    
    initialize: function() {
        this.plotView = new PlotView({ selectionModel: this.selectionModel, settingsModel: this.settingsModel });
        this.documentInfoView = new DocumentInfoView({ selectionModel: this.selectionModel, settingsModel: this.settingsModel });
    },
    
    cleanup: function() {
        this.plotView.dispose();
        this.documentInfoView.dispose();
    },
    
    render: function() {
        this.$el.html(this.mainTemplate);
        this.plotView.setElement(this.$el.find("#plot-view-container"));
        this.documentInfoView.setElement(this.$el.find("#document-info-view-container"));
        this.plotView.render();
        this.documentInfoView.render();
    },
    
    renderHelpAsHtml: function() {
        return this.plotView.renderHelpAsHtml();
    },
});

globalViewModel.addViewClass([], PlotViewManager);
