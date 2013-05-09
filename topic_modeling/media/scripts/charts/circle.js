function transform(x, y, s) {
	var transform = "translate(" + x + "," + y + ")";
	
	if (s) {
		transform += " scale(" + s + ")";
	}
	
	return transform;
}

function filterByType() {
	var args = arguments;
	return function(d) {		
		for (var i = 0; i < args.length; i++) {
			if (d.type == args[i]) {
				return true;
			}
		}
		
		return false;
	};
}

var CircleMenu = Backbone.View.extend({
	initialize: function (options) {
		var parent = this.parent = options.parent;
		this.$('button[name=unfreeze]').click(function () {
			if ($(this).hasClass('active')) {
				parent.stop_ticking();
			} else {
				parent.start_ticking();
			}
		});
		this.$('li[name=metric] button[name=Words]').click(function () {
			if (parent.main.loading) return false;
			parent.options.pairwise = 'word correlation';
			parent.reload();
		});
		this.$('li[name=metric] button[name=Documents]').click(function () {
			if (parent.main.loading) return false;
			parent.options.pairwise = 'document correlation';
			parent.reload();
		});
	},
	show: function () {
		this.$el.show();
	},
	hide: function () {
		this.$el.hide();
	}
});

var CircleInfo = InfoView.extend({
	initialize: function () {
		this.clear();
	},

	clear: function () {
		this.remove_topic();
		this.remove_document();
		this.remove_word();
	},

	load_topic: function (topic) {
		this.$('#circle-topic-name').text("Topic: " + topic.name);
		
		var details_url = location.href.split('/').slice(0,-1).join('/') + '/topics/' + topic.topicID;
                this.preload_popover(details_url);
		
		this.load_word_cloud(topic);
		
		this.$('#circle-document-name').show();
		this.$('#circle-document-info').show();
	},

	remove_topic: function() {
		this.$('#circle-topic-name').text("Click a Topic");
		this.$('.view-topic-details-btn').hide();
		this.$('#circle-topic-info').empty();
		
		this.$('#circle-document-name').hide();
		this.$('#circle-document-info').hide();
	},
	
	load_document: function(document) {
		this.$('#circle-document-name').text("Document: " + document.name);
		
		var details_url = location.href.split('/').slice(0,-1).join('/') + '/documents/' + document.documentID;
		this.$('.view-document-details-btn').show()
			.attr('href', details_url)
			.click(function (e) {
				e.preventDefault();
				$('#iframe-modal iframe.theframe')[0].contentDocument.body.innerHTML=$('script#iframe-loading')[0].innerHTML;
				$('#iframe-modal iframe.theframe').attr('src', details_url);
				$('#iframe-modal').modal('show');
				return false;
			});
			
		this.$('#circle-word-name').show();
		this.$('#circle-word-info').show();
	},
	
	remove_document: function() {
		this.$('#circle-document-name').text("Click a Document");
		this.$('.view-document-details-btn').hide();
		this.$('#circle-document-info').empty();
	
		this.$('#circle-word-name').hide();
		this.$('#circle-word-info').hide();
	},
	
	load_word: function(word) {
		this.$('#circle-word-name').text("Word: " + word.name);
		
		var details_url = location.href.split('/').slice(0,-1).join('/') + '/words/' + word.name;
		this.$('.view-word-details-btn').show()
			.attr('href', details_url)
			.click(function (e) {
				e.preventDefault();
				$('#iframe-modal iframe.theframe')[0].contentDocument.body.innerHTML=$('script#iframe-loading')[0].innerHTML;
				$('#iframe-modal iframe.theframe').attr('src', details_url);
				$('#iframe-modal').modal('show');
				return false;
			});
		
		this.load_contexts(word);
	},
	
	remove_word: function(word) {
		this.$('#circle-word-name').text("Click a Word");
		this.$('.view-word-details-btn').hide();
		this.$('#circle-word-info').empty();
	},

	load_word_cloud: function(topic) {
		var infoDiv = d3.select('#circle-topic-info');
		var wordCloud = infoDiv.append('svg')
			.attr("height", 200);

		var words = topic.words;

		var fill = d3.scale.category20();
		d3.layout.cloud().size([200, 200])
			.words(words)
			.timeInterval(5000)
			.rotate(function() { return 0;/*~~(Math.random() * 5) * 30;*/ })
			.font("Impact")
			.fontSize(function(d) { return d.size; })
			.on("end", draw_word_cloud)
			.start();

		function draw_word_cloud(words) {
			var g = wordCloud.append("g");

			g.selectAll("text")
				.data(words)
				.enter().append("text")
				.style("font-size", function(d) { return d.size + "px"; })
				.style("font-family", "Impact")
				.style("fill", function(d, i) { return fill(i); })
				.attr("text-anchor", "middle")
				.attr("transform", function(d) {
					return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
				})
				.text(function(d) { return d.text; });
			
			g.attr("transform", transform(145, 105));
		}
	},
	
	load_contexts: function(word) {
		var wordInfoDiv = d3.select('#circle-word-info')
		wordInfoDiv.append('h5')
			.text('Words in Context');
		
		var contextsDiv = wordInfoDiv.append('div')
			.attr('id', '#circle-word-contexts');
		
		contextsDiv.append('p')
			.html('<i>Loading contexts...</i>');
			
		var link = "/feeds/word-in-contexts-in-document";
				link += "/documents/" + word.documentID;
				link += "/words/" + word.name;
		
		d3.json(link, function (data) {
			if (!data) return;
			
			var wordContexts = data;
			
			contextsDiv.selectAll('*').remove();
			contextsDiv.append('ul')
				.selectAll('li')
				.data(wordContexts)
				.enter().append('li')
				.html(function(d) { return d['left_context'] + " <b>" + d['word'] + "</b> " + d['right_context']; });
		});			
	},
	

	show: function () {
		this.$el.show();
	},
	hide: function () {
		this.$el.hide();
	}
});

var CircleControls = Backbone.View.extend({
	initialize: function (options) {
		var parent = this.parent = options.parent;
		var t = parent.options.circle_threshold;
		this.$('#circle-topics-slider').slider({
			range: true,
			min: 0,
			max: 1,
			values: parent.options.circle_threshold,
			step: (t[1] - t[0]) / 20,
			stop: function ( event, ui ) {
				parent.set_threshhold(ui.values);
			}
		});
	},

	show: function () {
		this.$el.show();
	},

	hide: function () {
		this.$el.hide();
	}
});

/**
 * This is a Circle visualization
 */
var CircleViewer = MainView.add({
	name: 'circle-topics',
	title: 'Circle Diagram',
	menu_class: CircleMenu,
	info_class: CircleInfo,
	controls_class: CircleControls,

	defaults: {
		circle_r: 20,
		circle_min: 50,
		charge: -50,
		link_distance: 50,
		max_link_strength: .1,
		line_width: 3,
		full_scale: 3,
		circle_threshold: [0.7, 1],
		pairwise: 'document correlation'
	},

	initialize: function () {
		VisualizationView.prototype.initialize.apply(this, arguments);
		this.ticking = false;
	},

	url: function () {
		return URLS['pairwise topics'][this.options.pairwise];
	},

	setup_d3: function () {
		this.circle = d3.layout.pack()
			.size([this.options.width, this.options.height])
			.value(function(d) { return d.size; });
	},

	set_threshhold: function (threshhold) {
		this.options.circle_threshold = threshhold;
		this.reload();
	},

	load: function (data) {
		var that = this;
		this.data = data;
		
		this.maing.selectAll("*").remove();
		this.info.clear();

		var nodeHierarchy = this.create_node_hierarchy();
		var topicNodes = this.circle.nodes(nodeHierarchy);

		this.create_topic_layer(topicNodes);
		this.create_text_layer(topicNodes, 'topic');
		this.create_event_layer(topicNodes, 'topic', function(d) { return that.create_document_layer(d); });
	},

	create_node_hierarchy: function() {
		var that = this;
		var sizes = this.data.topics.map(function(d) { return d.metrics["Number of tokens"]; });
		var scaleSize = d3.scale.linear().domain([Math.min.apply(null, sizes), Math.max.apply(null, sizes)])

		return {
			name: "Topics",
			class: "root-node",
			id: "root",
			type: "root",
			children: this.data.topics.map(
				function(d, topicIndex) {
					var words = d.words;
					var wordCounts = words.map(function(d) { return d.count; });
					var scaleWordCount = d3.scale.log().domain([Math.min.apply(null, wordCounts), Math.max.apply(null, wordCounts)]).range([15, 40]);

					var documents = d.documents;
					var documentCounts = documents.map(function(d) { return d.count; });
					var scaleDocumentCount = d3.scale.log().domain([Math.min.apply(null, documentCounts), Math.max.apply(null, documentCounts)]).range([15, 50]);
					return {
						name: d.names[0],
						tokenCount: scaleSize(d.metrics["Number of tokens"]),
						class: "circle-node topic-node",
						id: "topic" + topicIndex,
						topicID: topicIndex,
						type: "topic",
						children: d.documents.map(
							function(d, documentIndex) { 
								return {
									name: d.document__filename.substr(0, d.document__filename.lastIndexOf('.')).replace(/_/g, " "), 
									size: d.count, 
									class: "leaf-node document-node", 
									id: "topic" + topicIndex + "-document" + documentIndex,
									topicID: topicIndex,
									documentID: d.document__id,
									type: "document",
									children: null
								}; 
							}
						),
						words: d.words.map(
							function(d) {
								return {
									text: d.type__type,
									size: scaleWordCount(d.count)
								};
							}
						)
					};
				}
			).filter(function(d) {return d.tokenCount > that.options.circle_threshold[0] && d.tokenCount < that.options.circle_threshold[1]; })
		};
	},

	create_topic_layer: function (nodes) {
		var that = this;

		this.maing.selectAll('*').remove();
		this.maing.append('g').classed('topic-layer-nodes', true);

		var circles = this.maing.select('g.topic-layer-nodes').selectAll('g.topic-node').data(nodes);

		circles.enter().append("g")
			.attr("class", function(d) { return d.class; })
			.attr("id", function(d) { return d.id; })
			.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
			.attr('pointer-events', 'all');

		circles.append('circle')
			.attr('r', function(d) { return d.r; })
			.attr('id', function(d) { return "c_circle_" + d.id; });
	},

	remove_text_layer: function(layer) {
		var layerName = layer + '-layer-texts';
		d3.select('.' + layerName).remove();
	},
   
	create_text_layer: function (nodes, layer) {
		nodes = nodes.filter(filterByType(layer));
		var scaleText = d3.scale.linear().domain([1, 100]).range([3, 20]);
		var textSize = 23 - scaleText(nodes.length);
		
		var layerName = layer + '-layer-texts';
		
		var textLayer = d3.select('.' + layerName);
		if (textLayer.empty()) {
			textLayer = this.maing.append('g')
				.classed(layerName, true).selectAll('g.text')
				.data(nodes)
				.enter().append('g')
				.attr('pointer-events', 'none')
				.attr('class', 'text');
		}
			
		textLayer.append('text')
			.attr('id', function (d) { return 'text-' + d.id; })
			.each(function (d, index) {
		
				var node = d3.select(this);
				var parts = d.name.split(' ');

				for (var i = 0; i < parts.length; i++) {
					node.append('tspan')
						.attr('class', 'back')
						.text(parts[i])
						.style("font-size", textSize + "px")
						.attr('y', i * textSize)
						.attr('x', 0);
				}

				for (i = 0; i < parts.length; i++) {
					node.append('tspan')
					.text(parts[i])
					.style("font-size", textSize + "px")
					.attr('y', i * textSize)
					.attr('x', 0);
				}
			})
			.attr("transform", function(d) { return "translate(" + d.x + "," + (d.y - (textSize / 2)) + ")"; });
	},
	
	remove_event_layer: function(layer) {
		var layerName = layer + '-layer-events';
		d3.select('.' + layerName).remove();
	},

	create_event_layer: function(nodes, layer, eventHandler) {
		nodes = nodes.filter(filterByType(layer));
		var that = this;
		var layerName = layer + '-layer-events';
		
		var eventLayer = d3.select('.' + layerName);
		if (eventLayer.empty()) {
			eventLayer = this.maing.append('g').classed(layerName, true);
		}
      
		eventLayer.selectAll('svg.handler')
			.data(nodes)
			.enter().append('g')
			.attr('pointer-events', 'all')
			.attr('class', 'event-handler')
			.attr('width', function(d) { return d.r })
			.attr('height', function(d) { return d.r })
			.on('mouseover', function(d) {
				d3.select("#text-" + d.id).transition()
					.attr('transform', 'translate(' + d.x + ',' + (d.y - 10) + ') scale(2)');
			})
			.on('mouseout', function(d) {
				d3.select("#text-" + d.id).transition()
					.attr('transform', 'translate(' + d.x + ',' + (d.y - 10) + ') scale(1)');
			})
			.on('click', function(d) {
				eventHandler(d);
			})
			.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
			.append('circle')
			.attr('r', function(d) { return d.r; })
			.attr('id', function(d) { return "c_circle_" + d.id; })
			.attr('visibility', 'hidden');
	},
  
	create_document_layer: function(topic) {
		var that = this;
		var root = d3.select("#root");

		var topic_copy = $.extend({}, topic);
		var root_x = root.datum().x;
		var root_y = root.datum().y;
		var scale = root.datum().r / topic.r;

		var topic_x = topic.x - topic.r;
		var topic_y = topic.y - topic.r;
		var documentNodes = this.circle.nodes(topic_copy).filter(filterByType('topic', 'document'));

		var documentLayer = this.maing.append('g').classed('document-layer-nodes', true);

		var documentCircles = documentLayer
			.attr("transform", transform(topic_x, topic_y, 1 / scale)) 
			.selectAll('g.document-node').data(documentNodes);

		documentCircles.enter().append("g")
			.attr("class", function(d) { return d.class; })
			.attr("id", function(d) { return d.id + "-copy"; })
			.attr("transform", function(d) { return transform(d.x, d.y); })
			.attr('pointer-events', 'all');

		documentCircles.append('circle')
			.attr('r', function(d) { return d.r; })
			.attr('id', function(d) { return "c_circle_" + d.id; });      

		documentLayer.transition()
			.attr("transform", "")
			.each("end", function() {
				that.create_text_layer(documentNodes, 'document');
				documentCircles.filter(filterByType("document"))
					.each(function (d) { that.preview_word_circles(d)});
			});
		
		d3.select("#" + topic.id + "-copy")
			.on('click', function(d) {
				that.remove_text_layer('document');
				that.remove_event_layer('document');
				
				documentLayer.transition()
					.attr("transform", transform(topic_x, topic_y, 1 / scale))
					.each("end", function() { 
						documentLayer.remove();
						that.info.remove_topic();
					});
			});
		
		
		this.info.load_topic(topic);
		this.create_event_layer(documentNodes, 'document', function(d) { return that.create_word_layer(d); });

		return documentNodes;
	},
	
	preview_word_circles: function(document) {
		var that = this;
		
		var create_word_circle_previews = function() {
			var document_copy = $.extend({}, document);
			
			var circleLayout = d3.layout.pack()
				.size([2 * document.r, 2 * document.r])
				.value(function(d) { return d.size; });
				
			var wordNodes = circleLayout(document_copy).filter(filterByType('word'));
				
			var wordCircles = d3.select("#" + document.id + "-copy")
				.selectAll('g').data(wordNodes);
			
			wordCircles.enter().append("g")
				.attr("class", function(d) { return d.class; })
				.attr("transform", function(d) {
					return transform(d.x - document_copy.r, d.y - document_copy.r); 
				});

			wordCircles.append('circle')
				.attr('r', function(d) { return d.r; });
		}
		
		if (!document.children) {
			var link = "/feeds/words-in-document-given-topic/datasets/state_of_the_union";
				link += "/analyses/" + "lda100topics";
				link += "/documents/" + document.documentID;
				link += "/topics/" + document.topicID;
			
			d3.json(link, function (data) {
				if (!data) return;
				
				document.children = data.map(function(d, i) {
					return {
						name: d.type__type,
						size: d.count,
						class: 'leaf-node word-node',
						id: document.id + '-word' + i,
						documentID: document.documentID,
						type: 'word'
					};
				});

				create_word_circle_previews();
			});
			
		} else {
			create_word_circle_previews();
		}
	},

	create_word_layer: function(document) {
		if (!document.children) {
			return;
		}
		
		var that = this;
		var root = d3.select("#root");

		var document_copy = $.extend({}, document);
		var root_x = root.datum().x;
		var root_y = root.datum().y;
		var scale = root.datum().r / document.r;

		var document_x = document.x - document.r;
		var document_y = document.y - document.r;
		var wordNodes = this.circle.nodes(document_copy);

		var wordLayer = this.maing.append('g').classed('word-layer-nodes', true);

		var circles = wordLayer
			.attr("transform", transform(document_x, document_y, 1 / scale)) 
			.selectAll('g.word-node').data(wordNodes);

		circles.enter().append("g")
			.attr("class", function(d) { return d.class + " copy"; })
			.attr("id", function(d) { return d.id + "-word-copy"; })
			.attr("transform", function(d) { return transform(d.x, d.y); })
			.attr('pointer-events', 'all');

		circles.append('circle')
			.attr('r', function(d) { return d.r; });   

		wordLayer.transition()
			.attr("transform", "")
			.each("end", function() { 
				that.create_text_layer(wordNodes, 'word');
			});
		
		d3.select("#" + document.id + "-word-copy")
			.on('click', function(d) {
				that.remove_text_layer('word');
				that.remove_event_layer('word');
				
				wordLayer.transition()
					.attr("transform", transform(document_x, document_y, 1 / scale))
					.each("end", function() { 
						wordLayer.remove();
						that.info.remove_word();
						that.info.remove_document();
					});
			});
		
		this.info.remove_document();
		this.info.load_document(document);
		this.create_event_layer(wordNodes, 'word', function(d) { that.info.remove_word(); that.info.load_word(d); });

		return wordNodes;
	}
});
