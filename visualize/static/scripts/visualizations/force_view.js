

var ForceView = DefaultView.extend({
    readableName: "Force Diagram",
    
    visualizationTemplate:
"<div id=\"force-view\" class=\"col-xs-9\" style=\"display: inline; float: left;\"></div>"+
"<div id=\"force-controls\" class=\"col-xs-3 text-center\" style=\"display: inline; float: left;\"></div>",

    controlsTemplate:   
"<h3><b>Controls</b></h3>"+
"<hr />"+
"<div><label>Link Threshold</label></div>"+
"<label id=\"force-link-slider-min\" style=\"display: block; float: left;\"></label><label id=\"force-link-slider-max\" style=\"display: block; float: right;\"></label>"+
"<div id=\"force-link-slider\" style=\"clear: both;\"></div>"+
"<hr />"+
"<div><label>Topic Size Threshold</label></div>"+
"<label id=\"force-size-slider-min\" style=\"display: block; float: left;\"></label><label id=\"force-size-slider-max\" style=\"display: block; float: right;\"></label>"+
"<div id=\"force-size-slider\" style=\"clear: both;\"></div>"+
"<hr />"+
"<label>Select Correlation Metric</label>"+
"<p><select id=\"force-metric-options\"></select></p>",

    initialize: function() {
        this.selectionModel.on("change:analysis", this.render, this);
        this.model = new Backbone.Model(); // For storing settings and data.
    },
    
    cleanup: function() {},
    
    render: function() {
        this.$el.empty();
        
        // Check for selected dataset and analysis.
        if(!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<p>You should select a <a href=\"#datasets\">dataset and analysis</a> before proceeding.</p>");
            return;
        }
        
        // Retreive needed data.
        var container = d3.select(this.el);
        container.html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selections.dataset,
            "analyses": selections.analysis,
            "topics": "*",
            "topic_attr": ["pairwise", "names", "metrics"],
        }, function(data) {
            // Create top level containers.
            container.html(this.visualizationTemplate);
            
            // Extract and store data for this.model.
            var topics = extractTopics(data);
            var aTopic = null;
            for(key in topics) {
                aTopic = key;
                break;
            }
            var topicCount = _.size(topics);
            metricOptions = [];
            for(key in topics[aTopic].pairwise) {
                metricOptions.push(key);
            }
            metricOptions.sort();
            var metric = metricOptions[0];
            var names = {};
            for(i=0; i<topicCount; i++) { // Extract names.
                names[i] = topics[i].names.Top3;
            }
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
            var minTopicSize = topics[aTopic].metrics["Number of tokens"];
            var maxTopicSize = topics[aTopic].metrics["Number of tokens"];
            var topicTokenCounts = {};
            for(topic in topics) {
                var count = topics[topic].metrics["Number of tokens"];
                topicTokenCounts[topic] = count;
                if(count < minTopicSize) minTopicSize = count;
                if(count > maxTopicSize) maxTopicSize = count;
            }
            this.model.set({
                topicCount: topicCount,
                metricOptions: metricOptions,
                names: names,
                extremes: extremes,
                matrices: matrices,
                minTopicSize: minTopicSize,
                maxTopicSize: maxTopicSize,
                topicTokenCounts: topicTokenCounts,
            });
            this.settingsModel.set({ metric: metric });
            
            // Ready to render.
            this.renderControls();
            this.listenTo(this.settingsModel, "change:metric", this.renderControls);
            this.listenTo(this.model, "change", this.renderControls);
            this.renderForceDiagram();
            this.listenTo(this.settingsModel, "change:metric", this.renderForceDiagram);
            this.listenTo(this.model, "change", this.renderForceDiagram);
        }.bind(this), this.renderError.bind(this));
    },
    
    renderControls: function() {
        var that = this;
        
        var controls = d3.select("#force-controls");
        controls.html(this.controlsTemplate);
        
        var metric = this.settingsModel.attributes.metric;
        var min = this.model.attributes.extremes[metric].min;
        var max = this.model.attributes.extremes[metric].max;
        var linkMin = max*0.75;
        var linkMax = max;
        this.settingsModel.set({ link: { min: linkMin, max: linkMax } }, { silent: true });
        var step = 1000;
        // Render the link slider.
        this.$el.find("#force-link-slider").slider({
            range: true,
            min: min,
            max: max,
            step: (max-min)/step,
            values: [linkMin, linkMax],
            slide: function(event, ui) {
                controls.select("#force-link-slider-min").text((ui.values[0]*100).toFixed(1)+"%");
                controls.select("#force-link-slider-max").text((ui.values[1]*100).toFixed(1)+"%");
            }.bind(this),
            change: function(event, ui) {
                this.settingsModel.set({ link: { min: ui.values[0], max: ui.values[1] } });
            }.bind(this),
        });
        controls.select("#force-link-slider-min").text((linkMin*100).toFixed(1)+"%");
        controls.select("#force-link-slider-max").text((linkMax*100).toFixed(1)+"%");
        
        var minTopicSize = this.model.attributes.minTopicSize;
        var maxTopicSize = this.model.attributes.maxTopicSize;
        this.settingsModel.set({ size: { min: minTopicSize, max: maxTopicSize } }, { silent: true });
        // Render the size slider.
        this.$el.find("#force-size-slider").slider({
            range: true,
            min: minTopicSize,
            max: maxTopicSize,
            step: 1,
            values: [minTopicSize, maxTopicSize],
            slide: function(event, ui) {
                controls.select("#force-size-slider-min").text(ui.values[0]);
                controls.select("#force-size-slider-max").text(ui.values[1]);
            }.bind(this),
            change: function(event, ui) {
                this.settingsModel.set({ size: { min: ui.values[0], max: ui.values[1] } });
            }.bind(this),
        });
        controls.select("#force-size-slider-min").text(minTopicSize);
        controls.select("#force-size-slider-max").text(maxTopicSize);
        
        // Render the metric options.
        var metric = this.settingsModel.get("metric");
        controls.select("#force-metric-options")
            .on("change", function(e) {
                that.settingsModel.set({ metric: d3.select(this).property("value") });
            })
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
    
    /*
     * Return a hash with the topics with valid links from the topicSource.
     */
    computeLink: function(topicSource) {
        var topics = this.model.attributes.topicTokenCounts;
        var metric = this.settingsModel.attributes.metric;
        var matrix = this.model.attributes.matrices[metric];
        var size = this.settingsModel.attributes.size;
        var link = this.settingsModel.attributes.link;
        var displayedNodes = _.reduce(topics, function(result, value, key) {
            if(value >= size.min && value <= size.max) {
                result[key] = true;
            }
            return result;
        }, {});
        var row = matrix[topicSource];
        var result = {};
        for(topicTarget in displayedNodes) {
            var value = row[topicTarget];
            if(value >= link.min && value <= link.max) {
                result[topicTarget] = true;
            }
        }
        return result;
    },
    
    /*
     * Return a list of objects specifying relations by index.
     */
    computeLinks: function() {
        var topics = this.model.attributes.topicTokenCounts;
        var metric = this.settingsModel.attributes.metric;
        var matrix = this.model.attributes.matrices[metric];
        var size = this.settingsModel.attributes.size;
        var link = this.settingsModel.attributes.link;
        var displayedNodes = _.reduce(topics, function(result, value, key) {
            if(value >= size.min && value <= size.max) {
                result[key] = true;
            }
            return result;
        }, {});
        var links = [];
        for(topicSource in displayedNodes) {
            var row = matrix[topicSource];
            for(topicTarget in displayedNodes) {
                var value = row[topicTarget];
                if(value >= link.min && value <= link.max) {
                    links.push({ source: parseInt(topicSource), target: parseInt(topicTarget), value: value });
                }
            }
        }
        return links;
    },

    renderForceDiagram: function() {
        var that = this;
        
        // Create needed variables
        var width = 500;
        var height = width;
        var circleMin = 10;
        var circleMax = 50;
        
        // Data.
        var topics = this.model.attributes.topicTokenCounts;
        var topicNames = this.model.attributes.names;
        var minTopicSize = this.model.attributes.minTopicSize;
        var maxTopicSize = this.model.attributes.maxTopicSize;
        var nodes = d3.entries(topics).sort(function(a, b) { return parseFloat(b.key) - parseFloat(a.key); });
        var links = this.computeLinks();
        
        // Scale to transform from topic token count to radius.
        var radiusScale = d3.scale.linear().domain([minTopicSize, maxTopicSize])
            .range([circleMin, circleMax]);
        
        // Render force diagram.
        var force = d3.layout.force()
            .size([width, height])
            .charge(charge)
            .linkDistance(100)
            .nodes(nodes)
            .links(links)
            .start();
        
        var container = d3.select(this.el).select("#force-view");
        container.html("");
        
        var svg = container.append("svg")
            .attr("width", "100%")
            .attr("height", "90%")
            .attr("viewBox", "0, 0, "+width+", "+height)
            .attr("preserveAspectRatio", "xMidYMin meet")
            .append("g");
        
        var link = svg.selectAll(".link")
            .data(links)
            .enter()
            .append("line")
            .attr("class", "link")
            .style("stroke-width", linkWidth)
            .style("stroke", "black");
        
        var node = svg.selectAll(".node")
            .data(nodes)
            .enter()
            .append("g")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("class", "node")
            .on("mouseenter", onHover)
            .on("mouseleave", offHover)
            .call(force.drag);
        
        node.append("circle")
            .attr("r", function circleRadius(d) {
                return radiusScale(d.value);
            })
            .style("fill", "white")
            .style("stroke", "lightblue")
            .on("click", onClick);
        
        node.append("text")
            .each(function insertText(d, i) {
                var text = d3.select(this)
                    .style("font-weight", "bold")
                    .style("text-anchor", "middle")
                    .attr("transform", "scale(0.5, 0.5)")
                    .on("click", onClick);
                
                var parts = topicNames[d.key].split(' ');
                var yOffset = 0.65;
                for (var j=0; j<parts.length; j++) {
                    text.append('tspan')
                        .style("stroke", "white")
                        .style("stroke-width", 4)
                        .attr('class', 'back')
                        .text(parts[j])
                        .attr('y', (j*1.15 - yOffset)+"em")
                        .attr('x', 0);
                }
                for (var j=0; j<parts.length; j++) {
                    text.append('tspan')
                        .text(parts[j])
                        .attr('y', (j*1.15 - yOffset)+"em")
                        .attr('x', 0);
                }
            });
        
        force.on("tick", function forceTick() {
            link.attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });

            node.attr("transform", function(d) { return "translate("+d.x+","+d.y+")"; });
        });
        
        function linkWidth(d) {
            console.log(d.value);
            return d.value;
        };
        
        function charge(d, i) {
            var size = that.settingsModel.attributes.size;
            if(d.value >= size.min && d.value <= size.max) {
                return -(radiusScale(d.value) * 10);
            } else {
                return 0;
            }
        };
        
        function onHover(d, i) {
            d3.select(this)
                .select("text")
                .attr("transform", "scale(1,1)");
        };
        
        function offHover(d, i) {
            d3.select(this)
                .select("text")
                .attr("transform", "scale(0.5,0.5)");
        };
        
        function onClick(d, i) {
            that.selectionModel.set({ topic: d.key });
            var singleLink = that.computeLink(d.key);
            node.selectAll("circle")
                .style("fill", function(d2, i) { 
                    if(d2.key === d.key) {
                        return "blue";
                    } else {
                        return "white";
                    }
                })
                .style("stroke", function(d2, i) {
                    if(d2.key === d.key) {
                        return "blue";
                    } else if (d2.key in singleLink) {
                        return "blue";
                    } else {
                        return "lightblue";
                    }
                });
        };
        
        function linkThresholdChange() {
            
        };
        
        function sizeThresholdChange() {
            node.style("display", function changeNodeDisplay(d, i) {
                var size = that.settingsModel.attributes.size;
                if(d.value >= size.min && d.value <= size.max) {
                    return "block";
                } else {
                    return "none";
                }
            });
        };
        
        linkThresholdChange();
        sizeThresholdChange();
        
        this.listenTo(this.settingsModel, "change:link", linkThresholdChange);
        this.listenTo(this.settingsModel, "change:size", sizeThresholdChange);
    },
    
    renderHelpAsHtml: function() {
        return "<h4>Link Threshold</h4>"+
               "<p>This decides which links between topics are visible/created. The threshold values are pulled from Document Correlation or Word Correlation (or any other pairwise topic metrics that are available).</p>"+
               "<h4>Topic Size Threshold</h4>"+
               "<p>The topic size is based off of word token or word instance counts. This will effect which topics, the circles, are displayed.</p>"+
               "<h4>Select Correlation Metric</h4>"+
               "<p>This is the metric that will adjust how the topics are correlated. Word Correlation is based of of how many words (word types) the topics share. Document Correlation is based off of how many documents the topics share.</p>";
    },
});

addViewClass(["Visualizations"], ForceView);

