
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
var CircleViewer = MainView.add(ZoomableView, {
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
	
	var nodes = this.circle.nodes(this.create_node_hierarchy(0));

    this.maing.select('*').remove();
	this.maing.append('g').classed('cnodes', true);

	this.node = this.maing.select('g.cnodes').selectAll('g.cnode').data(nodes);

	this.node.enter().append("g")
      	.attr("class", function(d) { return d.children ? "root cnode" : "leaf cnode"; })
		.attr("id", function(d) { return "cnode" + d.id; })
      	.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
		.attr('pointer-events', 'all')
		.on('click', function(d) { that.change_circles(d); });
		//.on('mouseover', function(d) { that.add_word_cloud(d); });

	this.node.append("title")
		.text(function(d) { return d.name; });

 	this.node.append('circle')
		.attr('r', function(d) { return d.r; })
		.attr('id', function(d) { return "circle" + d.id; });

 	this.node.filter(function(d) { return !d.children; }).append("text")
		.attr("dy", ".3em")
		.style("text-anchor", "middle")
		.text(function(d) { return d.name.substring(0, d.r / 3); })
		.attr('id', function(d) { return "text" + d.id; });
  },

  change_root: function (d, i) {
	if (d === this.node) {
		return;
	}
	
	var nodes = this.circle.nodes(this.create_node_hierarchy(this.data, i));
	var that = this;

	this.create_circles(nodes);
  },

  //TODO: Create transitions via the enter and exit sets
  change_circles: function (d) {
	var that = this;
	var nodes = this.circle.nodes(this.create_node_hierarchy(d.id));

    this.maing.select('*').remove();
	this.maing.append('g').classed('cnodes', true);
	
	this.node = this.maing.select('g.cnodes').selectAll('g.cnode').data(nodes);

	this.node.enter().append("g")
      	.attr("class", function(d) { return d.children ? "root cnode" : "leaf cnode"; })
		.attr("id", function(d) { return "cnode" + d.id; })
      	.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
		.attr('pointer-events', 'all')
		.on('click', function(d) { that.change_circles(d); });
		//.on('mouseover', function(d) { that.add_word_cloud(d); });

	this.node.append("title")
		.text(function(d) { return d.name; });

 	this.node.append('circle')
		.attr('r', function(d) { return d.r; })
		.attr('id', function(d) { return "circle" + d.id; });

 	this.node.filter(function(d) { return !d.children; }).append("text")
		.attr("dy", ".3em")
		.style("text-anchor", "middle")
		.text(function(d) { return d.name.substring(0, d.r / 3); })
		.attr('id', function(d) { return "text" + d.id; });
  },

  //TODO: Make this work, and add a remove_word_cloud() method
  add_word_cloud: function(d) {

	var words = d.words;
	if (typeof words === "undefined") {
		return;
	}
	
	var fill = d3.scale.category20();
  	d3.layout.cloud().size([d.r, d.r])
      .words(words)
      .rotate(function() { return ~~(Math.random() * 2) * 90; })
      .font("Impact")
      .fontSize(function(d) { return d.size; })
      .on("end", draw)
      .start();

  	function draw(words) {
		d3.select("#cnode" + d.id).append("g")
			.attr("width", d.r)
			.attr("height", d.r)
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

  create_node_hierarchy: function(root) {
	var that = this;
	var sizes = this.data.matrix[root].filter(function(d) { return d > 0; });
	var scaleSize = d3.scale.linear().domain([Math.min.apply(null, sizes), Math.max.apply(null, sizes)])

	return {
		name: this.data.topics[root].names[0],
		children: this.data.matrix[root].map(
			function(d, i) {
				var words = that.data.topics[i].words;
				var wordCounts = words.map(function(d) { return d.count; });
				var scaleWordCount = d3.scale.log().domain([Math.min.apply(null, wordCounts), Math.max.apply(null, wordCounts)]).range([10, 100]);
				return {
					name: that.data.topics[i].names[0],
					size: scaleSize(d),
					id: i,
					words: words.map(
						function(d, i) {
							return {
								text: d.type__type,
								size: scaleWordCount(d.count)
							};
						}
					)
				};
			}
		).filter(function(d, i) { return (i != root && d.size > 0); })
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
				...
		...
*/

