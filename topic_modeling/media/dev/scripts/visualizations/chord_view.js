

var ChordView = DefaultView.extend({
    readableName: "Chord Diagram",
    
    mainTemplate:
"<div id=\"chord-diagram-container\" class=\"row\"></div>"+
"<div id=\"topic-info-container\" class=\"row container-fluid\"></div>",
    
    chordDiagramTemplate:
"<div id=\"chord-view\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>"+
"<div id=\"chord-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",

    controlsTemplate:   
"<h3><b>Controls</b></h3>"+
"<hr />"+
"<div><label>Link Threshold</label></div>"+
"<label id=\"chords-slider-min\" style=\"display: block; float: left;\">0.0%</label><label id=\"chords-slider-max\" style=\"display: block; float: right;\">100.0%</label>"+
"<div id=\"chords-slider\" style=\"clear: both;\"></div>"+
"<hr />"+
"<div><label>Correlation Color Legend</label></div>"+
"<div class=\"col-xs-4\" style=\"text-align: left; padding-left: 2px; padding-right: 2px;\"><b>Low</b></div>"+
"<div class=\"col-xs-4\" style=\"text-align: center; padding-left: 2px; padding-right: 2px;\"><b>Average</b></div>"+
"<div class=\"col-xs-4\" style=\"text-align: right; padding-left: 2px; padding-right: 2px;\"><b>High</b></div>"+
"<div id=\"palette\" style=\"clear: both; height: 1.4em; display: block; padding: 2px; margin: 2px; border: 1px solid black;\"></div>"+
"<hr />"+
"<label>Select Correlation Metric</label>"+
"<p><select id=\"metric-options\"></select></p>",

    initialize: function() {
        this.selectionModel.on("change:analysis", this.render, this);
        this.model = new Backbone.Model(); // For storing settings and data.
    },
    
    cleanup: function() {
        if(this.topicInfo !== undefined) {
            this.topicInfo.cleanup();
        }
        this.selectionModel.off(null, null, this);
    },
    
    render: function() {
        if(!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<p>You should select a <a href=\"#\">dataset and analysis</a> before proceeding.</p>");
            return;
        }
        this.$el.html(this.mainTemplate);
        this.renderChordDiagram();
        this.renderTopicInfo();
    },
    
    renderChordDiagram: function() {
        var container = d3.select(this.el).select("#chord-diagram-container");
        container.html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selections.dataset,
            "analyses": selections.analysis,
            "topics": "*",
            "topic_attr": ["pairwise", "names"],
        }, function(data) {
            // Create top level containers.
            container.html(this.chordDiagramTemplate);
            
            // The color picker.
            this.fill = d3.scale.linear()
                .domain([0, 0.5, 1])
                .range(["#2166AC", "snow", "#AF182B"]); // Dark blue to dark red.
            
            // Extract and store data in this.model.
            var topics = extractTopics(data);
            var topicCount = _.size(topics);
            metricOptions = [];
            for(key in topics[0].pairwise) {
                metricOptions.push(key);
            }
            metricOptions.sort();
            var names = {};
            for(i=0; i<topicCount; i++) { // Extract names.
                names[i] = topics[i].names.Top3;
            }
            var metric = metricOptions[0];
            var matrices = {};
            var extremes = {};
            for(i=0; i<metricOptions.length; i++) { // Store pairwise info as matrix and find extremes.
                var m = metricOptions[i];
                extremes[m] = {};
                var max = 0;
                var min = 1;
                var matrix = matrices[m] = [];
                for(j=0; j<topicCount; j++) {
                    matrix.push(_.map(topics[j].pairwise[m], function(value, index, array) {
                        if(value > max && index !== j) max = value;
                        if(value < min && value !== 0) min = value;
                        if(index === j) return 0;
                        else return value;
                    }));
                }
                extremes[m].min = min;
                extremes[m].max = max;
            }
            this.model.set({
                topicCount: topicCount,
                metric: metric,
                metricOptions: metricOptions,
                names: names,
                extremes: extremes,
                matrices: matrices,
            });
            
            // Ready to render.
            this.renderControls();
            this.model.on("change:metric", this.renderControls, this);
            this.renderChords();
            this.model.on("change", this.renderChords, this);
        }.bind(this), this.renderError.bind(this));
    },
    

    
    renderControls: function() {
        var controls = d3.select("#chord-controls");
        controls.html(this.controlsTemplate);
        
        var metric = this.model.attributes.metric;
        var min = this.model.attributes.extremes[metric].min;
        var max = this.model.attributes.extremes[metric].max;
        var linkMin = max*0.75;
        var linkMax = max;
        this.model.set({ linkMin: linkMin, linkMax: linkMax }, { silent: true });
        var step = 1000;
        // Render the slider.
        this.$el.find("#chords-slider").slider({
            range: true,
            min: min,
            max: max,
            step: (max-min)/step,
            values: [linkMin, linkMax],
            slide: function(event, ui) {
                controls.select("#chords-slider-min").text((ui.values[0]*100).toFixed(1)+"%");
                controls.select("#chords-slider-max").text((ui.values[1]*100).toFixed(1)+"%");
            }.bind(this),
            change: function(event, ui) {
                this.model.set({ linkMin: ui.values[0], linkMax: ui.values[1] });
            }.bind(this),
        });
        controls.select("#chords-slider-min").text((linkMin*100).toFixed(1)+"%");
        controls.select("#chords-slider-max").text((linkMax*100).toFixed(1)+"%");
        
        // Render the color palette.
        var palette = controls.select("#palette");
        var colors = [];
        var numColorSwatches = 40;
        for(i=0; i<(numColorSwatches-1); i++) {
            colors.push(i/(numColorSwatches-1));
        }
        colors.push(1);
        
        palette.selectAll("span")
            .data(colors)
            .enter()
            .append("span")
            .style("float", "left")
            .style("background-color", this.fill)
            .style("height", "1em")
            .style("width", function(d) { return (100/numColorSwatches)+"%"; });
        
        // Render the metric options.
        var metric = this.model.get("metric");
        controls.select("#metric-options")
            .on("change", function(e) {
                this.model.set({ metric: controls.select("#metric-options").property("value") });
            }.bind(this))
            .selectAll("option")
            .data(this.model.attributes.metricOptions)
            .enter()
            .append("option")
            .text(function(d) { return d; })
            .each(function(d) {
                var el = d3.select(this);
                if(metric === d) {
                    el.attr("selected", "selected");
                }
            });
    },

    // Helper function to create a matrix specifying relationships in the chord diagram.
    // A one specifies there exists a relationship; a zero specifies no relationship.
    // Also the average and groups with no relationships are returned.
    // Return [average, linkMatrix, emptyGroups];
    createLinkMatrix: function(min, max, inMatrix) {
        var outMatrix = [];
        var total = 0;
        var count = 0;
        var emptyGroups = {};
        for(i=0; i<inMatrix.length; i++) {
            var inRow = inMatrix[i];
            outMatrix.push([]);
            var outRow = outMatrix[i];
            var empty = true;
            for(j=0; j<inRow.length; j++) {
                if(inRow[j] < min || inRow[j] > max) {
                    outRow.push(0);
                } else {
                    empty = false;
                    outRow.push(1);
                    count++;
                    total += inRow[j];
                }
            }
            if(empty) {
                emptyGroups[i] = true;
            }
        }
        return [(total/count), outMatrix, emptyGroups];
    },

    renderChords: function() {
        var that = this;
        
        var container = d3.select(this.el).select("#chord-view");
        container.html("");
        
        // Create needed variables
        var width = 500;
        var height = width;
        var outerPadding = 15;
        var innerPadding = 20;
        var outerRadius = Math.min(width, height)/2 - outerPadding;
        var innerRadius = outerRadius - innerPadding;
        // Get needed data.
        var metric = this.model.get("metric");
        var matrix = this.model.get("matrices")[metric];
        var names = this.model.get("names");
        var topicCount = this.model.get("topicCount");
        var linkMin = this.model.attributes.linkMin;
        var linkMax = this.model.attributes.linkMax;
        var results = this.createLinkMatrix(linkMin, linkMax, matrix);
        var linkAvg = results[0];
        var linkMatrix = results[1];
        var emptyGroups = results[2];
        
        var chord = d3.layout.chord()
            .padding(0.5/topicCount) // Set angular padding between groups in radians.
            .sortSubgroups(d3.descending)
            .matrix(linkMatrix);
        var controlBoxDimensions = $("#chord-controls").get(0).getBoundingClientRect(); // Use the controls element to set height of the svg element.
        var svg = container.append("svg")
            .attr("width", "100%")
            .attr("height", controlBoxDimensions.height*2)
            .attr("viewBox", "0, 0, "+width+", "+height)
            .attr("preserveAspectRatio", "xMidYMin meet")
            .append("g")
            .attr("transform", "translate(" + width/2 + "," + height/2 + ")");
        
        var arc = d3.svg.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius);
        
        // Scale to fit color/fill input domain.
        var scale = d3.scale.linear()
            .domain([linkMin, linkAvg, linkMax])
            .range([0, 0.5, 1]);
        
        // Render chords.
        var chords = svg.append("g")
            .selectAll("path")
            .data(chord.chords)
            .enter()
            .append("path")
            .style("stroke", "black")
            .style("stroke-opacity", 0)
            .classed("chord", true)
            .attr("d", d3.svg.chord().radius(innerRadius))
            .style("fill", function(d, i) {
                return that.fill(scale(matrix[d.source.index][d.target.index]));
            })
            .style("opacity", 0.8);
        
        // Render arcs.
        var topicGroups = svg.append("g")
            .classed("all-groups", true)
            .selectAll("g")
            .data(chord.groups)
            .enter()
            .append("g")
            .classed("group", true)
            .append("path")
            .style("fill", "lightgrey")
            .style("stroke", "lightgrey")
            .attr("d", arc)
            .on("mouseover", showRelations(true))
            .on("mouseout", showRelations(false))
            .on("click", function(g, i) { that.selectionModel.set({ topic: i.toString() }); });
        
        // Hide unused groups.
        topicGroups.filter(function(g, i) { return i in emptyGroups; })
            .style("display", "none");
        
        var titles = svg.selectAll(".group")
            .each(function(d, i) {
                var b = this.getBBox();
                var el = d3.select(this);
                var text = el.append("text")
                    .attr("transform", "translate("+parseInt(b.x+b.width/2)+","+parseInt(b.y+b.height/2)+")")
                    .style("font-weight", "bold")
                    .style("display", "none")
                    .style("text-anchor", "middle");
                var parts = names[i].split(' ');
                for (var j=0; j<parts.length; j++) {
                    text.append('tspan')
                        .style("stroke", "white")
                        .style("stroke-width", 4)
                        .attr('class', 'back')
                        .text(parts[j])
                        .attr('y', (j*1.15)+"em")
                        .attr('x', 0);
                }
                for (var j=0; j<parts.length; j++) {
                    text.append('tspan')
                        .text(parts[j])
                        .attr('y', (j*1.15)+"em")
                        .attr('x', 0);
                }
                text.on("mouseover", function() { showRelations(true)(d, i); })
                    .on("mouseout", function() { showRelations(false)(d, i); })
                    .on("click", function() { console.log('text '+i); that.selectionModel.set({ topic: i.toString() }); });
            });
        
        // Returns an event handler for fading a given chord group.
        // Show determines which topic names to display.
        function showRelations(show) {
            return function(g, i) {
                // Show text.
                var text = titles.selectAll("text");
                if(show) { 
                    // Show selected text.
                    text.filter(function(d) { 
                            return linkMatrix[g.index][d.index] || g.index === d.index; 
                        })
                        .style("display", "block");
                    
                    // Show selected chords better.
                    chords.filter(function(d) { 
                            return d.source.index === i || d.target.index === i;
                        })
                        .transition()
                        .duration(600)
                        .style("opacity", 1)
                        .style("stroke-opacity", 1);
                    
                    var groupsWithLinks = {};
                    // Fade non-selected chords.
                    chords.filter(function(d) {
                            if(d.source.index === i || d.target.index === i) { // Collect involved groups.
                                groupsWithLinks[d.source.index] = true;
                                groupsWithLinks[d.target.index] = true;
                            }
                            return d.source.index !== i && d.target.index !== i;
                        })
                        .transition()
                        .duration(600)
                        .style("opacity", 0.02);
                    
                    // Fade uninvolved groups.
                    topicGroups.filter(function(group) {
                            return !(group.index in groupsWithLinks);
                        })
                        .transition()
                        .duration(600)
                        .style("stroke-opacity", 0.02)
                        .style("opacity", 0.02);
                } else { // Hide text re-show groups and chords.
                    text.style("display", "none");
                    chords.transition()
                        .duration(600)
                        .style("stroke-opacity", 0)
                        .style("opacity", 0.8);
                    topicGroups.transition()
                        .duration(600)
                        .style("stroke-opacity", 1)
                        .style("opacity", 1);
                }
            };
        }
    },
    
    renderTopicInfo: function() {
        if(this.topicInfo === undefined) {
            this.topicInfo = new SingleTopicView({ el: $("#topic-info-container") });
            this.topicInfo.render();
        }
    },
    
    renderHelpAsHtml: function() {
        return "<h4>Link Threshold</h4>"+
               "<p>This adjusts which relationships you see by selecting a range of percentages. These percentages refer to how strongly the topics relate according to the selected metric.</p>"+
               "<h4>Correlation Color Legend</h4>"+
               "<p>The more red the chord is the more similar the topics are, and vice versa with the color blue. "+
               "Note that red colors indicate that the relationship is above average for the selection and blue colors are below average for the selection.</p>"+
               "<h4>Select Correlation Metric</h4>"+
               "<p>This is the metric that will adjust how the topics are correlated.</p>";
    },
});

globalViewModel.addViewClass(["Visualizations"], ChordView);
