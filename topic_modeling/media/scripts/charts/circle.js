/**
 * Create a bootstrap button group
 *
 * Arguments:
 *  - items: [['name', callback], ...]
 *  - node : string or element to house it (will receive the class "btn-group"
 */
function create_button_group(items, node) {
  node = $(node).addClass('btn-group').attr('data-toggle', 'buttons-radio');
  node.empty();
  var buttons = [];
  for (var i=0; i<items.length; i++) {
    buttons.push($('<button type="button" class="btn btn-primary">' + items[i][0] + '</button>')
      .appendTo(node).click(items[i][1]));
  }
  return buttons;
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

var CircleInfo = Backbone.View.extend({
  initialize: function () {
  },

  clear: function () {
    this.$('tbody').empty();
  },

  load_topic: function (info) {
    this.$('.topic-name').text(info.names[0]);
    var mtable = this.$('table.metrics tbody');
    mtable.empty();
    var dtable = this.$('table.documents tbody');
    dtable.empty();
    _.each(info.documents, function (doc, i) {
      $('<tr><td>' + doc.document__filename + '</td><td>' + doc.count + '</td></tr>')
        .appendTo(dtable);
    });
    var wtable = this.$('table.words tbody');
    wtable.empty();
    _.each(info.words, function (word, i) {
      $('<tr><td>' + word.type__type + '</td><td>' + word.count + '</td></tr>')
        .appendTo(wtable);
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
    var t = parent.options.threshhold;
    this.$('.threshhold').slider({
      range: true,
      min: 0,
      max: 1,
      values: parent.options.threshhold,
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
    threshhold: [0.7, 1],
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

  load: function (data) {
    this.data = data;
	this.initialize_circles();
  },
	
  initialize_circles: function () {
	var that = this;
	var nodes = this.circle.nodes(this.create_node_hierarchy());
	
    this.maing.selectAll('*').remove();
	this.maing.append('g').classed('c_nodes', true);
	
	this.node = this.maing.select('g.c_nodes').selectAll('g.c_node').data(nodes);

	this.node.enter().append("g")
      	.attr("class", function(d) { return d.children ? "c_root c_node" : "c_leaf c_node"; })
		.attr("id", function(d) { return d.children ? "c_node_root" : "c_node_" + d.id; })
      	.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
		.attr('pointer-events', 'all')
		.on('mouseover', function(d) { 
			if (!d.children) {
				 d3.select("#c_text_" + d.id).transition()
				.attr('transform', 'translate(' + d.x + ',' + (d.y - 3) + ') scale(3)');
			}
		})
		.on('mouseout', function(d) {
			if (!d.children) {
				 d3.select("#c_text_" + d.id).transition()
				.attr('transform', 'translate(' + d.x + ',' + (d.y - 3) + ') scale(1)');
			}
		})
		.on('click', function(d) {
			var root = d3.select("#c_node_root");
			var x = root.datum().x;
			var y = root.datum().y;
			var scale = (root.datum().r - 10) / d.r;
			if (!d.children) {
				that.display_word_cloud(d);
			}
		});

 	this.node.append('circle')
		.attr('r', function(d) { return d.r; })
		.attr('id', function(d) { return "c_circle_" + d.id; });

	this.create_texts(nodes);
  },

  display_word_cloud: function(d) {
	var that = this;
	var root = d3.select("#c_node_root");
	var x = root.datum().x;
	var y = root.datum().y;
	var scale = (root.datum().r - 10) / d.r;
	var wordCloudLayer = this.maing.append('g').classed('word_cloud_layer', true);
	
	wordCloudLayer.append("g")
      	.attr("class", "cloned c_leaf c_node")
		.attr("id", "cloned-c_node_" + d.id)
      	.attr("transform", "translate(" + d.x + "," + d.y + ")")
		.on("click", function() {
			d3.select("#cloned-c_node_" + d.id).transition()
				.attr("transform", "translate(" + d.x + "," + d.y + ") scale(" + 1 / scale + ")");

			d3.select("#cloned-c_circle_" + d.id).transition()
				.style("fill", "#3BC600")
				.each("end", function() { that.maing.selectAll("g.word_cloud_layer").remove(); });
		});

	wordCloudLayer.select("#cloned-c_node_" + d.id).append("circle")
		.attr("r", d.r)
		.attr("id", "cloned-c_circle_" + d.id);

	d3.select("#cloned-c_node_" + d.id).transition()
		.attr("transform", "translate(" + x + "," + y + ") scale(" + scale + ")");

	d3.select("#cloned-c_circle_" + d.id).transition()
		.style("fill", "#0064cd")
		.each("end", function() { that.create_word_cloud(d); });
  },

  create_texts: function (nodes) {
	var scaleText = d3.scale.linear().domain([1, 100]).range([3, 10])
	var textSize = 13 - scaleText(nodes.length)

    this.texts = this.maing.append('g')
      .classed('all-texts', true).selectAll('g.text')
        .data(nodes.filter(function(d) { return !d.children; }))
      .enter().append('g')
        .attr('pointer-events', 'none')
        .attr('class', 'c_text');
    
	this.texts.append('text')
        .attr('id', function (d) { return 'c_text_' + d.id; })
        .each(function (d, index) {
          var node = d3.select(this);
          var parts = d.name.split(' ');
          for (var i=0; i<parts.length; i++) {
            node.append('tspan')
              .attr('class', 'back')
              .text(parts[i])
			  .style("font-size", textSize + "px")
              .attr('y', i * textSize)
              .attr('x', 0);
          }
          for (i=0; i<parts.length; i++) {
            node.append('tspan')
              .text(parts[i])
			  .style("font-size", textSize + "px")
              .attr('y', i * textSize)
              .attr('x', 0);
          }
        })
		.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
  },

  create_word_cloud: function(d) {
	var root = d3.select("#c_node_root");
	var wordCloudLayer = this.maing.append('g').classed('word_cloud_layer', true);

	var words = d.words;
	if (typeof words === "undefined") {
		return;
	}
	
	var fill = d3.scale.category20();
  	d3.layout.cloud().size([root.datum().r - 10, root.datum().r - 10])
      .words(words)
	  .timeInterval(5000)
      .rotate(function() { return 0;/*~~(Math.random() * 5) * 30;*/ })
      .font("Impact")
      .fontSize(function(d) { return d.size; })
      .on("end", draw)
      .start();

  	function draw(words) {
		wordCloudLayer.append("g")
			.attr("width", root.datum().r - 10)
			.attr("height", root.datum().r - 10)
			.attr("transform", "translate(" + [root.datum().x, root.datum().y] + ") scale(2)")
		  .selectAll("text")
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
 	 }
  },

  set_threshhold: function (threshhold) {
    this.options.threshhold = threshhold;
    this.reload();
  },

  create_node_hierarchy: function() {
	var that = this;
	var sizes = this.data.topics.map(function(d) { return d.metrics["Number of tokens"]; });
	var scaleSize = d3.scale.linear().domain([Math.min.apply(null, sizes), Math.max.apply(null, sizes)])

	return {
		name: "Topics",
		children: this.data.topics.map(
			function(d, i) {
				var words = d.words;
				var wordCounts = words.map(function(d) { return d.count; });
				var scaleWordCount = d3.scale.log().domain([Math.min.apply(null, wordCounts), Math.max.apply(null, wordCounts)]).range([15, 50]);
				return {
					name: d.names[0],
					size: scaleSize(d.metrics["Number of tokens"]),
					id: i,
					words: d.words.map(
						function(d, i) {
							return {
								text: d.type__type,
								size: scaleWordCount(d.count)
							};
						}
					)
				};
			}
		).filter(function(d) { return d.size > that.options.threshhold[0] && d.size < that.options.threshhold[1]; })
	};
  }
});

/*
data
	matrix: Array[100]
		0: Array[100]
		...
	metrics: Object
		Document Entropy: Object
			avg: fp
			max: fp
			min: fp
		Number of tokens: Object
			...
		Number of types: Object
			...
		Word Entropy: Object
			...
	topics: Array[100]
		0: Object
			documents: Array[10]
				0: Object
					count: int
					document__filename: str
					document__id: int
				...
			metrics: Object
				Document Entropy: fp
				Number of tokens: int
				Number of types: int
				Word Entropy: fp
			names: Array[1]
				0: str
			topics: Array[10]
				0: int
				...
			words: Array[10]
				0: Object
					count: int
					type__type: str
*/
