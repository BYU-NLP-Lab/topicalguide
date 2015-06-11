"use strict";


var SingleTopicView = DefaultView.extend({
    
    readableName: "Single Topic",
    shortName: "single_topic",
    
    redirectTemplate:
'<div class="text-center">'+
'   <button class="single-topic-redirect btn btn-default">'+
'       <span class="glyphicon glyphicon-chevron-left pewter"></span> All Topics'+
'   </button>'+
'   <span> You need to select a topic to see any specific information. </span>'+
'</div>',
    
    mainTemplate: 
'<div id="single-topic-title" class="row">'+
'	<h3>Topic Number: <span class="single-topic-number"></span></h3>'+
'	<h3>Topic Name: <span class="single-topic-name"></span></h3>'+
'	<h3>Top 10 Words: <span class="single-topic-top-ten-words"></span></h3>'+
'</div>'+
'<div id="single-topic-info" class="row"></div>',
    
    wordStatTemplate: 
'<div id="word-stat-table" class="col-xs-8"></div>'+
'<div id="word-stat-pie" class="col-xs-4"></div>',

    pieChartTemplate:
'<div id="single-topic-pie-chart" class="row">'+
'</div>'+
'<h4 class="text-center">Word Types</h4>'+
'<p class="text-center">(sorted by token count)</p>'+
'<div id="single-topic-pie-chart-word-type-selector" class="row">'+
'</div>'+
'<p class="text-center"><span>Showing <span id="single-topic-showing-n-word-types">__</span> of <span id="single-topic-total-word-types">__</span></span></p>'+
'<div id="single-topic-pie-chart-legend" class="row">'+
'</div>',

	events: {
		'click .single-topic-redirect': 'clickRedirect',
	},
	
	clickRedirect: function clickRedirect() {
		this.viewModel.set({ currentView: 'all_topics' });
	},
    
    initialize: function() {
        this.listenTo(this.selectionModel, "change:topic", this.render);
        this.listenTo(this.settingsModel, "change:minWordTypeIndex", this.changeSelectedWordTypesRange);
        this.listenTo(this.settingsModel, "change:maxWordTypeIndex", this.changeSelectedWordTypesRange);
        this.listenTo(this.settingsModel, "change:minWordTypeIndex", this.updateSliderInfo);
        this.listenTo(this.settingsModel, "change:maxWordTypeIndex", this.updateSliderInfo);
        this.listenTo(this.settingsModel, "change:minWordTypeIndex", this.updatePieChartAndLegend);
        this.listenTo(this.settingsModel, "change:maxWordTypeIndex", this.updatePieChartAndLegend);
        
    },
    
    render: function() {
		if(this.selectionModel.nonEmpty(["dataset", "analysis", "topic"])) {
			this.$el.html(this.mainTemplate);
			this.renderTopicTitle();
			this.renderTabs();
		} else {
			this.$el.html(this.redirectTemplate);
		}
    },
    
    renderTabs: function renderTabs() {
		var tabs = {
            "Similar Topics": this.renderSimilarTopics.bind(this) ,
            "Top Documents": this.renderTopDocuments.bind(this) ,
            "Metadata and Metrics": this.renderMetadataAndMetrics.bind(this),
            "Words and Words in Context": this.renderWords.bind(this),
            "Word Statistics": this.renderWordStats.bind(this),
        };
        
        var tabOnClick = function(tab) {
            this.settingsModel.set({ selectedTab: tab });
        }.bind(this);
        
        tg.gen.createTabbedContent(this.$el.find("#single-topic-info").get(0), {
            tabs: tabs,
            selected: this.settingsModel.get("selectedTab"),
            tabOnClick: tabOnClick,
        });
	},

    renderTopicTitle: function() {
        var selections = this.selectionModel.attributes;
        var container = d3.select(this.el).select("#single-topic-title");
        container.html(this.loadingTemplate);
        // Make a request
        this.dataModel.submitQueryByHash({
            "datasets": selections["dataset"],
            "analyses": selections["analysis"],
            "topics": selections["topic"],
            "topic_attr": "top_n_words",
            "words": "*",
            "top_n_words": "10",
        }, function(data) {
            container.html("");
            var topic = extractTopics(data, this.selectionModel)[selections["topic"]];
            var words = [];
            for(var key in topic["words"]) words.push({ key: key, value: topic["words"][key]});
            words.sort(function(a, b) { return b.value.token_count - a.value.token_count; });
            words = _.map(words, function(entry) { return entry.key; });
            
            container.append("h2")
                .text("Topic Number: "+selections["topic"]);
            container.append("h3")
                .text(words.join(" "));
        }.bind(this), this.renderError.bind(this));
    },
    
    renderTopDocuments: function(tab, content) {
        content.html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        var datasetName = this.selectionModel.get("dataset");
        var analysisName = this.selectionModel.get("analysis");
        var topicNumber = this.selectionModel.get("topic");
        var queryHash = {
			"datasets": datasetName,
            "analyses": analysisName,
            "topics": topicNumber,
            "topic_attr": "metrics",
            "top_n_documents": 10,
		};
        this.dataModel.submitQueryByHash(queryHash, function topDocumentsCallback(data) {
            content.html("");
            var topicNumber = this.selectionModel.get("topic");
            var topic = extractTopics(data, this.selectionModel)[topicNumber];
            var topDocs = topic["top_n_documents"];
            var tokenCountTotal = parseFloat(topic.metrics["Token Count"]);
            
            var documentsList = _.reduce(topDocs, function extractDocumentNames(result, value, key) {
				result.push(key);
				return result;
			}, []);
            
            var docSnippetsRequest = {
				"datasets": datasetName,
				"analyses": analysisName,
				"documents": documentsList,
				"document_attr": ["intro_snippet"],
			};
            this.dataModel.submitQueryByHash(docSnippetsRequest, function finishTopDocumentsCallback(data2) {
				var that = this;
				var documentSnippets = data2.datasets[datasetName].analyses[analysisName].documents;
				
				var header = ["", "Document", "Preview", "Token Count", "% of Topic"];
				var sortable = [false, true, true, true, true];
				var sortBy = 4;
				var sortAscending = this.settingsModel.get("ascending");
				var tableData = _.map(topDocs, function createTableData(value, key) {
					return [key, key, documentSnippets[key]["intro_snippet"], value.token_count, value.token_count/tokenCountTotal];
				});
				var tokenCountMax = _.max(tableData, function findTokenCountMax(value) {
					return value[4];
				})[4];
				console.log(tokenCountMax);
				var dataFunctions = [
					function col0(d, i) {
						var el = d3.select(this)
							.append("span")
							.attr("data-tg-document-name", d)
							.classed("tg-fav", true);
						tg.site.initFav(el[0][0], that.favsModel);
					},
					false,
					function col2(snippet, i) {
						d3.select(this)
							.append('div')
							.style({ "float": "left" , "text-align": "left", "max-width": "400px" })
							.text(snippet);
					},
					false,
					function col4(d, i) {
						console.log(d);
						console.log(tokenCountMax);
						d3.select(this)
							.html(tg.gen.createPercentageBar(d, tokenCountMax) + " " + d.toFixed(4) + "%");
					},
				];
				var tableRowFunction = function tableRowFunction(rowData, index) {
					d3.select(this)
						.attr("data-tg-document-name", rowData[1])
						.classed("tg-select pointer", true)
						.classed("all-docs-update-document-highlight all-docs-document-popover", true)
						.classed("success", function isRowHighlighted(d, i) {
							if(d3.select(this).attr("data-tg-document-name") === that.selectionModel.get("document")) {
								return true;
							} else {
								return false;
							}
						});
				};
				
				tg.gen.createSortableTable(content[0][0], {
					header: header, 
					sortable: sortable,
					sortBy: sortBy,
					sortAscending: sortAscending,
					data: tableData,
					dataFunctions: dataFunctions,
					tableRowFunction: tableRowFunction,
				});
			}.bind(this), this.renderError.bind(this));
        }.bind(this), this.renderError.bind(this));
    },
    
    renderWordStats: function(tab, content) {
        content.html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "topics": selection["topic"],
            "topic_attr": ["top_n_words", "metrics"],
            "words": "*",
            "top_n_words": 100, // TODO: need to get all words
        }, function(data) {
            content.html(this.wordStatTemplate);
            var topicNumber = this.selectionModel.get("topic");
            var topic = extractTopics(data, this.selectionModel)[topicNumber];
            this.renderPieChartContent(content.select("#word-stat-pie"), topic);
            //console.log(topic);
            var topWords = topic["words"];
            //console.log(topWords);
            var tokenCount = parseFloat(topic.metrics["Token Count"]);
            var words = d3.entries(topWords).map(function(entry) {
                //~ return [entry];
                return [entry.key, entry.value.token_count, (entry.value.token_count/tokenCount)*100];
            });
            //console.log(words);
            var table = content.select("#word-stat-table").append("table")
                .classed("table table-hover table-condensed", true);
            //~ TODO: go to word view some day
            //~ var onClick = function(d, i) {
                //~ this.selectionModel.set({ "document": d[0] });
                //~ window.location.href = "#documents";
            //~ }.bind(this);
            createSortableTable(table, {
                header: ["Word", "Token Count", "% of Topic"], 
                data: words, 
                //~ onClick: { "1": onClick }, 
                bars: [2], 
                percentages: [2],
                //~ favicon: [0, "documents", this],
                sortBy: 2,
                sortAscending: false,
            });
        }.bind(this), this.renderError.bind(this));
    },
    
    renderPieChartContent: function(container, topic) {
        // Extract the needed data.
        var topWordTypes = topic["words"];
        this.selectedWordTypes = {};

        this.sortedTokenCounts = [];
        for(var wordType in topWordTypes) {
            this.sortedTokenCounts.push({
                wordType: wordType,
                tokenCount: topWordTypes[wordType].token_count,
            });
        }
        
        // Sort descending by token counts.
        this.sortedTokenCounts = _.sortBy(this.sortedTokenCounts, function(d) {
            return -d.tokenCount;
        });
        
        // Create base containers.
        container.html(this.pieChartTemplate);
        
        // Set number of word types
        d3.select("#single-topic-total-word-types").text(this.sortedTokenCounts.length);
        
        // Default indices
        var low = 0;
        var high = Math.min(7, this.sortedTokenCounts.length - 1);
        
        // Create the color scale.
        // Space word types far enough apart that they won't be confused.
        var wordTypeNames = [];
        var tempStripeLength = colorPalettes.pastels.length;
        for(var i = 0; i < colorPalettes.pastels.length; i++) {
            for(var j = i; j < this.sortedTokenCounts.length; j += tempStripeLength) {
                wordTypeNames.push(this.sortedTokenCounts[j].wordType.toString());
            }
        }
        this.wordTypeColorScale = colorPalettes.getDiscreteColorScale(wordTypeNames, colorPalettes.pastels);
        
        // Render initial pie chart framework.
        var wordTypePieContainer = d3.select("#single-topic-pie-chart");
        
        var width = wordTypePieContainer[0][0].clientWidth;
        var buffer = 6;
        var pieChartSVG = wordTypePieContainer.append("svg")
            .attr("width", width + buffer)
            .attr("height", width + buffer)
            .classed({ "single-word-type-pie-chart": true });
            //~ .attr("id", "test-id");
        
        var x = width/2 + buffer/2;
        var y = x;
        var radius = width/2;
        this.pieChartRadius = radius;
        this.pieGroup = pieChartSVG.append("g")
            .classed("topic-pie-chart", true)
            .attr("transform", "translate("+x+","+y+")");
        
        // Create convenience reference for legend.
        this.legendGroup = d3.select("#single-topic-pie-chart-legend");
        
        // Render the slider and set slider events.
        this.$el.find("#single-topic-pie-chart-word-type-selector").slider({
            range: true,
            min: 0,
            max: this.sortedTokenCounts.length,
            step: 1,
            values: [low, high],
            slide: function(event, ui) {
                this.settingsModel.set({
                    minWordTypeIndex: ui.values[0],
                    maxWordTypeIndex: ui.values[1],
                });
            }.bind(this),
            change: function(event, ui) {
                this.settingsModel.set({
                    minWordTypeIndex: ui.values[0],
                    maxWordTypeIndex: ui.values[1],
                });
            }.bind(this),
        });
        this.settingsModel.set({
            minWordTypeIndex: low,
            maxWordTypeIndex: high,
        });
        
        
        
        this.changeSelectedWordTypeRange(); // Update which word types are visible.
        this.updateSliderInfo();
        this.updatePieChartAndLegend();
    },
    
    /**
     * When the word type range changes, then the selected word types must be updated.
     */
    changeSelectedWordTypeRange: function() {
        var wordTypes = this.getWordTypesInSliderRange();
        wordTypes = _.reduce(wordTypes, function(result, wordTypeObject) {
            result[wordTypeObject] = true;
            return result;
        }, {});
        for(var wordType in this.selectedWordTypes) {
            if(wordType in wordTypes) {
                this.selectedWordTypes[wordType] = true;
            } else {
                this.selectedWordTypes[wordType] = false;
            }
        }
    },
    
    /**
     * Change the number of word types shown.
     */
    updateSliderInfo: function() {
        var low = this.settingsModel.get("minWordTypeIndex");
        var high = this.settingsModel.get("maxWordTypeIndex");
        d3.select("#single-topic-showing-n-word-types").text(high - low);
    },
    
    /**
     * Currently nukes the current display and redraws it.
     */
    updatePieChartAndLegend: function() {
        var data = this.getWordTypesInSliderRange();
        //console.log(data);
        var dataWordTypeNames = [];
        for(var i in data) {
            dataWordTypeNames.push(data[i].wordType.toString());
        }
        var colorScale = colorPalettes.getDiscreteColorScale(dataWordTypeNames, colorPalettes.pastels);
        
        var outerRadius = this.pieChartRadius;
        var innerRadius = outerRadius * (1/10);
        var bufferRadius = outerRadius * (1/10);
        var allocatedAngleBuffer = (0.03)*2*Math.PI;
        var padAngle = allocatedAngleBuffer*(1/data.length)
        
        var arc = d3.svg.arc()
            .padRadius(outerRadius)
            .innerRadius(innerRadius);
        var pie = d3.layout.pie()
            .padAngle(padAngle)
            .sort(null)
            .value(function(d) { return d.tokenCount; });
        
        var that = this;
        
        // Update the pie chart.
        this.pieGroup.selectAll("path").remove();
        var arcs = this.pieGroup.selectAll("path");
        arcs.data(pie(data.reverse()))
            .enter().append("path")
            .each(function(d) { d.outerRadius = outerRadius - bufferRadius; }) // Modify the outer radius manually to be 1/10th of the full radius.
            .style("stroke", function(d, i) {
                return d3.rgb(that.wordTypeColorScale(d.data.wordType)).darker(2);
            })
            .style("stroke-width", "1.5px")
            .style("fill", function(d, i) {
                return that.wordTypeColorScale(d.data.wordType);
            })
            .attr("d", arc)
            .classed({
                "single-topic-word-type": true,
                //~ "single-topic-word-type-pie-slice": true,
                "tg-word-type-tooltip": true,
                "pointer": true,
            })
            .attr("data-original-title", function(d, i) { // Tool tip text.
                return d.data.wordType;
            });
        
        data.reverse(); // List was reversed for the pie chart, resetting it.
        
        // Update the legend.
        this.legendGroup.selectAll(".single-topic-word-type-in-legend").remove();
        var wordTypes = this.legendGroup.selectAll(".single-topic-word-type-in-legend");
        var legendEntries = wordTypes.data(data)
            .enter().append("div")
            .classed({ "row": true, "single-topic-word-type-in-legend": true })
            .classed("pointer", true);
        
        legendEntries.append("span") // Add a color swatch.
            .html("&nbsp;")
            .style("display", "inline-block")
            .style("width", "1em")
            .style("background-color", function(d, i) {
                return that.wordTypeColorScale(d.wordType);
            })
            .classed("single-topic-word-type", true)
            .attr("data-word-type-number", function(d, i) { return d.wordType; });
        legendEntries.append("span") // Add a space between color swatch and text.
            .html("&nbsp;&nbsp;");
        legendEntries.append("span")
            .text(function(d, i) {
                return d.wordType;
            })
            .attr("id", function(d, i) { // Label the span for hover effects.
                return "single-topic-legend-word-type-"+d.wordType;
            })
            .classed({ "single-topic-word-type": true })
            .attr("data-word-type-number", function(d, i) {
                return d.wordType;
            });
        
        // Store the "tween" function for mouseover/out events.
        this.mouseoverArcTween = function() {
            d3.select(this).transition().attrTween("d", function(d) {
                var i = d3.interpolate(d.outerRadius, outerRadius);
                return function(t) { d.outerRadius = i(t); return arc(d); }
            });
        };
        this.mouseoutArcTween = function() {
            d3.select(this).transition().attrTween("d", function(d) {
                var i = d3.interpolate(d.outerRadius, outerRadius-bufferRadius);
                return function(t) { d.outerRadius = i(t); return arc(d); }
            });
        };
    },
    
    
    /**
     * Return a sorted list of word type objects of the form:
     *     { wordType: string, tokenCount: # }.
     */
    getWordTypesInSliderRange: function() {
        var low = this.settingsModel.get("minWordTypeIndex");
        var high = this.settingsModel.get("maxWordTypeIndex");
        return this.sortedTokenCounts.slice(low, high + 1);
    },
    
    renderSimilarTopics: function(tab, content) {
        var that = this;
        content.html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selections["dataset"],
                "analyses": selections["analysis"],
                "topics": selections["topic"],
                "topic_attr": ["metrics","names","pairwise"],
        }, function(data) {
			
            this.dataModel.submitQueryByHash({
                "datasets": selections["dataset"],
                "analyses": selections["analysis"],
                "topics": "*",
                "topic_attr": "names",
            },function(allTopicsData) {
                content.html("");
                var allTopics = extractTopics(allTopicsData, this.selectionModel);
                var currentTopic = that.selectionModel.get("topic");
                var topic = extractTopics(data, this.selectionModel)[currentTopic];
                var header = ["", "#", "Topic Name"];
                var updateHeader = true;
                var percentageColumns = [];
                var finalData = d3.entries(allTopics)
                    .filter(function(entry) {
                        return entry.key != currentTopic;
                    })
                    .map(function(entry) {
                        var result = [entry.key, entry.key, that.dataModel.getTopicNameRaw(entry.key)];
                        var index = parseFloat(entry.key);
                        var pairwise = topic["pairwise"];
                        for(var key in pairwise) {
                            result.push(pairwise[key][index]*100);
                            if(updateHeader) {
                                header.push(key);
                                percentageColumns.push(header.length-1);
                            }
                        }
                        updateHeader = false;
                        return result;
                    });
                
                var table = content.append("table")
                    .classed("table table-hover table-condensed", true);
                var onClick = function(d, i) {
                    this.selectionModel.set({ "topic": d[0] });
                }.bind(this);
                
                createSortableTable(table, {
                    header: header, 
                    data: finalData, 
                    onClick: { "1": onClick, "2": onClick }, 
                    bars: percentageColumns, 
                    percentages: percentageColumns,
                    favicon: [0, "topics", this],
                    sortBy: header.length-1,
                    sortAscending: false,
                });
            }.bind(this), this.renderError.bind(this));
        }.bind(this), this.renderError.bind(this));
    },
    
    renderMetadataAndMetrics: function(tab, content) {
        var that = this;
        content.html(this.loadingTemplate);
        var selections = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selections["dataset"],
                "analyses": selections["analysis"],
                "topics": selections["topic"],
                "topic_attr": ["metrics","metadata"],
        }, function(data) {
            content.html("<div id=\"single-topic-metadata\" class=\"row container-fluid\"></div><div id=\"single-topic-metrics\" class=\"row container-fluid\"></div>");
            var topic = extractTopics(data, this.selectionModel)[selections["topic"]];
            createTableFromHash(content.select("#single-topic-metadata"), topic.metadata, ["Key", "Value"], "metadata");
            createTableFromHash(content.select("#single-topic-metrics"), topic.metrics, ["Metric", "Value"]), "metrics";
        }.bind(this), this.renderError.bind(this));
    },
    
    renderWords: function(tab, content) {
        var that = this;
        content.html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "topics": selection["topic"],
            "topic_attr": "top_n_words",
            "words": "*",
            "top_n_words": 100,
        }, function(data) {
            // Containers.
            content.html("");
            content.append("h3")
                .text("Word Cloud");
            var cloud = content.append("div")
                .classed("word-cloud container-fluid", true);
            content.append("h3")
                .text("Words in Context");
            var context = content.append("div")
                .classed("word-in-context container-fluid", true);
            
            
            // Data extraction.
            var topic = extractTopics(data, this.selectionModel)[selection.topic];
            var words = _.reduce(topic.words, function(result, value, key) {
                result[key] = value["token_count"];
                return result;
            }, {});
            
            // Select top 5 words.
            var top5 = d3.entries(words).sort(function sortWords(a, b) {
                return parseInt(b.value) - parseInt(a.value);
            }).slice(0, 5);
            
            // Set up words in context.
            this.wordsInContext = {};
            for(var i = 0; i < top5.length; i++) {
                var w = top5[i].key;
                this.wordsInContext[w] = true;
                this.renderWordInContext(context.append("div"), w);
            }
            
            // Allow more words in context.
            var wordOnClick = function wordOnClick(word) { 
                this.selectionModel.set({ word: word });
                if(!(word in this.wordsInContext)) {
                    this.wordsInContext[word] = true;
                    this.renderWordInContext(context.append("div"), word);
                }
            }.bind(this);
            
            // Render word cloud.
            createWordCloud(cloud, {
                words: words,
                wordOnClick: wordOnClick,
            });
        }.bind(this), this.renderError.bind(this));
    },
    
    /*
     * Helper function to renderWords.
     * container - The container to render the words document context in.
     * word - The word to find all contexts of.
     * Return nothing.
     */
    renderWordInContext: function(container, word) {
        container.text("Loading...");
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "topics": selection["topic"],
            "topic_attr": "word_tokens",
            "words": [word],
        }, function(data) {
            var tokens = extractTopics(data, this.selectionModel)[selection["topic"]].word_tokens[word];
            var index = 0;
            container.html(icons.document+"<span> </span>"+icons.previous+"<span> </span>"+icons.next+"<span class=\"document-text\"></span>");
            container.select(".document")
                .style("cursor", "pointer")
                .attr("title", tokens[index][0])
                .on("click", function onDocumentClick() {
                    this.selectionModel.set({ document: tokens[index][0] });
                    window.location.href = "#documents";
                }.bind(this));
            container.select(".previous")
                .style("cursor", "pointer")
                .attr("title", "Previous Context")
                .on("click", function onLeftClick() {
                    index = (index - 1 + tokens.length)%tokens.length;
                    this.renderContextText(container.select(".document-text"), tokens[index]);
                }.bind(this));
            container.select(".next")
                .style("cursor", "pointer")
                .attr("title", "Next Context")
                .on("click", function onRightClick() {
                    index = (index + 1)%tokens.length;
                    this.renderContextText(container.select(".document-text"), tokens[index]);
                }.bind(this));
            this.renderContextText(container.select(".document-text"), tokens[index]);
        }.bind(this), this.renderError.bind(this));
    },
    
    /*
     * Helper function to renderWordInContext.
     * container - D3 text container to put the text into.
     * tokenInfo - The document and the token index as a 2-tuple e.g. [doc, index].
     * Return nothing.
     */
    renderContextText: function(container, tokenInfo) {
        container.text("Loading...");
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "documents": tokenInfo[0],
            "document_attr": "kwic",
            "token_indices": tokenInfo[1],
        }, function(data) {
            var textInfo = extractDocuments(data, this.selectionModel)[tokenInfo[0]].kwic[tokenInfo[1]];
            container.html("");
            container.append("span")
                .text(textInfo[0]);
            container.append("span")
                .style("cursor", "pointer")
                .style("background-color", "yellow")
                .text(textInfo[1])
                .on("click", function onWordClick() {
                    this.selectionModel.set({ word: textInfo[3] });
                }.bind(this))
                .on("mouseenter", function() {
                    d3.select(this).style("color", "blue");
                })
                .on("mouseleave", function() {
                    d3.select(this).style("color", "black");
                });
            container.append("span")
                .text(textInfo[2]);
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return "";
    },
});

var SingleTopicSubView = DefaultView.extend({
    
    mainTemplate: "<div id=\"all-topic-container\" class=\"col-xs-3\"></div>"+
                  "<div id=\"topic-info\" class=\"col-xs-9\"></div>",
    
    dropdownTemplate: "<div class=\"btn-group\">"+
                          "<button type=\"button\" class=\"btn btn-primary\">Sort By</button>"+
                          "<button type=\"button\" class=\"btn btn-primary dropdown-toggle\" data-toggle=\"dropdown\">"+
                            "<span class=\"caret\"></span>"+
                            "<span class=\"sr-only\">Toggle Dropdown</span>"+
                          "</button>"+
                          "<ul id=\"sort-by\" class=\"dropdown-menu\" role=\"menu\"></ul>"+
                      "</div>",
    
    initialize: function() {},
    
    cleanup: function() {
        if(this.info !== undefined) {
            this.info.dispose();
        }
    },
    
    render: function() {
        this.$el.html(this.mainTemplate);
        this.renderAllTopicsSideBar();
        this.renderTopicInfo();
    },
    
    renderTopicInfo: function() {
        if(this.info !== undefined) {
            this.info.cleanup();
        }
        this.info = new SingleTopicView(_.extend({ el: $("#topic-info") }, this.getAllModels()));
        this.info.render();
    },
    
    renderAllTopicsSideBar: function() {
        var selections = this.selectionModel.attributes;
        var container = d3.select("#all-topic-container");
        container.append("button")
            .classed("btn btn-default", true)
            .attr("type", "button")
            .html("<span class=\"glyphicon glyphicon-chevron-left pewter\"></span> Back to All Topics")
            .on("click", function() {
                this.selectionModel.set({ "topic": "" });
            }.bind(this));
        container.append("hr");
        container = container.append("div");
        container.html(this.loadingTemplate);
        
        // Make a request
        this.dataModel.submitQueryByHash({
            "datasets": selections["dataset"],
            "analyses": selections["analysis"],
            "topics": '*',
            "topic_attr": ["metrics","names"],
            "analysis_attr": "metrics",
        }, function(data) { // Render the content
            container.html(this.dropdownTemplate);
            
            var sortList = [];
            var topics = extractTopics(data, this.selectionModel);
            topics = d3.entries(topics).map(function(d) {
                
                var items = {};
                for(var key in d.value.names) {
                    items[key] = d.value.names[key];
                }
                for(var key in d.value.metrics) {
                    items[key] = d.value.metrics[key];
                }
                items["Number"] = d.key;
                if(d.key === "0") {
                    for(var key in items) sortList.push(key);
                }
                return [d.key, d.value.names.Top3, items];
            });
            var tableHeader = ['Topics'];
            var ascending = true;
            var sortBy = 'Number';
            
            
            var list = d3.select("#all-topic-container").append("ul")
                .classed("list-unstyled", true);
            var items = list.selectAll(".all-topic-sidebar-items")
                .data(topics)
                .enter()
                .append("li")
                .classed(".all-topic-sidebar-items", true)
                .classed("list-group-item", true)
                .text(function(d) {
                    return d[0] + ": " +d[1];
                })
                .on("click", function(d) {
                    this.selectionModel.set({ "topic": d[0] });
                }.bind(this));
            
            var sort = d3.select("#sort-by").selectAll("li")
                .data(sortList)
                .enter()
                .append("li")
                .append("a")
                .text(function(d) { return d; })
                .on("click", function(d) {
                    var ascendingSort = function(a, b) {
                        if($.isNumeric(a[2][d]) && $.isNumeric(b[2][d])) return parseFloat(a[2][d]) - parseFloat(b[2][d]);
                        else return a[2][d].localeCompare(b[2][d]);
                    };
                    var descendingSort = function(a, b) {
                        return ascendingSort(b,a);
                    };
                    
                    if(d !== sortBy) ascending = true;
                    sortBy = d;
                    if(ascending) {
                        d3.selectAll(".all-topic-sidebar-items").sort(ascendingSort);
                        ascending = false;
                    } else {
                        d3.selectAll(".all-topic-sidebar-items").items.sort(descendingSort);
                        ascending = true;
                    }
                });
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        var subViewHtml = "";
        if(this.info !== undefined) {
            subViewHtml = this.info.renderHelpAsHtml();
        }
        return "<h4>All Topics</h4>"+
               "<p>Use the 'Sort By' dropdown menu to choose how to sort the topics on the sidebar.  "+
               "The topics will be sorted in ascending order, to reverse the order select the sort by option again.</p>"+
               subViewHtml;
    },
});

var SingleTopicViewSidebar = DefaultView.extend({
    readableName: "Document Information",
    shortName: "single_topic_sidebar",
    
    baseTemplate:
'<div class="single-topic-sidebar-select-container"></div>'+
'<div class="single-topic-sidebar-topics-list">'+
'</div>',
    
    initialize: function initialize() {
    },
    
    render: function render() {
        this.$el.html(this.baseTemplate);
        
    },
    
    cleanup: function cleanup() {
    },
    
    renderHelpAsHtml: function renderHelpAsHtml() {
        return '';
    },
});

/**
 * Simple manager to combine two views.
 * leftView -- the side bar
 * rightView -- the single topic
 */
var SingleTopicViewManager = DefaultView.extend({
    readableName: "Document Information",
    shortName: "single_topic",
    
    baseTemplate:
'<div class="row">'+
'    <div class="single-topic-manager-left-container col-xs-3">'+
'    </div>'+
'    <div class="single-topic-manager-right-container col-xs-9">'+
'    </div>'+
'</div>',
    
    initialize: function initialize() {
        this.leftView = new DefaultView();
        this.rightView = new DefaultView();
    },
    
    render: function render() {
        this.cleanup();
        this.$el.html(this.baseTemplate);
        this.leftView = new SingleTopicViewSidebar();
        this.leftView.render();
        this.rightView = new SingleTopicView();
        this.rightView.render();
    },
    
    cleanup: function cleanup() {
        this.leftView.dispose();
        this.rightView.dispose();
    },
    
    renderHelpAsHtml: function renderHelpAsHtml() {
        return this.rightView.renderHelpAsHtml();
    },
});

// Add the Topic View to the top level menu
addViewClass(["Topic"], SingleTopicViewManager);
