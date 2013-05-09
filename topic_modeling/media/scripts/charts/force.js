
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

function translate_node(d) {
  return 'translate(' + d.x + ',' + d.y + ')'; 
}

function twofloat(n) {
  return parseInt(n * 100)/100.0;
}

/**
 * Calculate the max and min values of a matrix.
 *
 * Arguments:
 *  matrix: a list of lists of floats
 *
 * Returns [min, max];
 */
function get_matrixminmax(matrix) {
  var min, max;
  min = max = matrix[0][0];
  for (var x=0; x<matrix.length; x++) {
    for (var y=0; y<matrix[x].length; y++) {
      if (matrix[x][y] > max) max = matrix[x][y];
      if (matrix[x][y] < min) min = matrix[x][y];
    }
  }
  return [min, max];
}

function get_topicsminmax(topics) {
  var min, max;
  min = max = topics[0].metrics['Number of tokens'];
  for (var i=0; i<topics.length; i++) {
    if (topics[i].metrics['Number of tokens'] > max)
      max = topics[i].metrics['Number of tokens'];
    if (topics[i].metrics['Number of tokens'] < min)
      min = topics[i].metrics['Number of tokens'];
  }
  
  return [min, max];
}

function force_links(nodes, matrix, threshhold) {
  /** create links for the force layout **/ 
  var links = [], target;
  for (var i=0; i<nodes.length; i++) {
    for (var j=0; j<nodes[i].topics.length; j++) {
      target = nodes[i].topics[j];
      if (matrix[i][target] <= threshhold[1] && matrix[i][target] >= threshhold[0])
        links.push({source: i, target: target, weight: matrix[i][target]});
    }
  }
  return links;
}

function make_rel(minmax) {
  var rng = minmax[1] - minmax[0];
  return function (x) {
    return (x - minmax[0]) / rng;
  };
}

var ForceMenu = Backbone.View.extend({
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

var ForceInfo = InfoView.extend({
  initialize: function () {
    this.$el.hide();
  },

  clear: function () {
    this.$('tbody').empty();
    this.$el.hide();
  },

  load_topic: function (id, info, metrics) {
    this.$el.hide();
    // get the popoverrolling
    var details_url = location.href.split('/').slice(0,-1).join('/') + '/topics/' + id;
    this.preload_popover(details_url);

    // populate
    this.$('.topic-name').text(info.names[0]);
    var mtable = this.$('table.metrics tbody');
    mtable.empty();
    _.forOwn(info.metrics, function (value, key) {
        mtable.append('<tr><td>' + key + '</td><td>' + twofloat(value) + '</td><td>' + twofloat(metrics[key].min) + '</td><td>' + twofloat(metrics[key].max) + '</td></tr>');
    });
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
    this.$el.show();
  },
  show: function () {
    // this.$el.show();
  },
  hide: function () {
    this.$el.hide();
  }
});

var ForceControls = Backbone.View.extend({
  initialize: function (options) {
    var parent = this.parent = options.parent;
    var t = parent.options.force_threshold;
    this.$('.threshhold').slider({
      range: true,
      min: 0,
      max: 1,
      values: parent.options.force_threshold,
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
 * This is a Force visualization
 */
var ForceViewer = MainView.add(ZoomableView, {
  name: 'force-topics',
  title: 'Force Diagram',
  menu_class: ForceMenu,
  info_class: ForceInfo,
  controls_class: ForceControls,

  defaults: {
    circle_r: 20,
    circle_min: 2,
    charge: -30,
    link_distance: 50,
    max_link_strength: .1,
    line_width: 3,
    full_scale: 3,
    force_threshold: [0.7, 1],
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
    this.force = d3.layout.force()
      .charge(this.options.charge)
      .linkDistance(this.options.link_distance)
      .size([this.options.width, this.options.height]);
  },

  load: function (data) {
    this.data = data;
    var nodes = data.topics;
    var links = force_links(nodes, data.matrix, this.options.force_threshold);
    var minmax = get_matrixminmax(data.matrix);
    var tminmax = get_topicsminmax(data.topics);
    var rel = make_rel(minmax);
    var trel = make_rel(tminmax);
    var that = this;
    this.info.clear();
    // populate the force layout
    this.force.nodes(nodes).links(links)
              .linkStrength(function (d) {
                return that.options.max_link_strength * rel(d.weight);
              }).start();
    // this.calc_layout();

    this.maing.selectAll('*').remove();
    this.maing.append('g').classed('all-links', true);
    this.maing.append('g').classed('all-nodes', true);
    // create links first so they're behind everything
    this.create_links(links, rel);
    this.create_nodes(nodes, data, trel);
    // update the positions of all the created nodes
    // this.update_positions();
    this.start_ticking();
  },

  create_links: function (links, rel) {
    var that = this;
    this.link = this.maing.select('g.all-links').selectAll('line.link')
      .data(links).enter().append('line')
      .attr('class', 'link').attr('name', function (d) {
        return 'link-' + d.source.index + '-' + d.target.index;
      }).style('stroke-width', function (d) {
        return that.options.line_width * rel(d.weight);
      });
  },

  remove_links: function () {
    this.link.remove();
  },

  set_threshhold: function (threshhold) {
    var data = this.data;
    this.options.force_threshold = threshhold;
    var minmax = get_matrixminmax(data.matrix);
    if (minmax[0] < threshhold[0]) minmax[0] = threshhold[0];
    if (minmax[1] > threshhold[1]) minmax[1] = threshhold[1];
    var rel = make_rel(minmax);
    this.remove_links();
    var links = force_links(data.topics, data.matrix, this.options.force_threshold);
    this.create_links(links, rel);
    if (this.ticking) {
      this.force.stop()
      this.force.links(links);
      this.force.start();
    } else {
      this.force.links(links);
      this.calc_layout();
      this.update_positions();
    }
  },

  create_nodes: function (nodes, data, trel) {
    var that = this;
    this.node = this.maing.select('g.all-nodes').selectAll("g.node")
        .data(nodes)
      .enter().append('g')
        .attr('class', function (d, i) { return 'node node-' + i; })
        .attr('pointer-events', 'all')
        .on('click', function (d, i) {
          that.node_click(d, this, data.topics[d.index]);
        }).call(this.force.drag)
        .on('mouseover', function (d, i) {
          d3.select('text.node-text-' + i)
            .transition().attr('transform', 'translate(0, -3) scale(3)');
        }).on('mouseout', function (d, i) {
          d3.select('text.node-text-' + i)
            .transition().attr('transform', 'translate(0, -3) scale(1)');
        });
    this.create_circles(trel);
    this.create_texts(nodes);
  },

  create_circles: function (trel) {
    var that = this;
    this.node.append("circle")
        .attr("class", "node")
        .attr("r", function (d) {
          var ret = that.options.circle_min + that.options.circle_r * trel(d.metrics['Number of tokens']);
          return parseInt(ret, 10);
        });
  },

  /* texts for the circles need to be above the circles */
  create_texts: function (nodes) {
    this.texts = this.maing.append('g')
      .classed('all-texts', true).selectAll('g.text')
        .data(nodes)
      .enter().append('svg:g')
        .attr('pointer-events', 'none')
        .attr('class', 'text');
    // add the lines of text
    this.texts.append('svg:text')
        .attr('class', function (d, i) { return 'node-text-' + i; })
        .attr('transform', 'translate(0, -3)')
        .each(function (d, index) {
          var node = d3.select(this);
          var parts = d.names[0].split(' ');
          for (var i=0; i<parts.length; i++) {
            node.append('tspan')
              .attr('class', 'back')
              .text(parts[i])
              .attr('y', i*4)
              .attr('x', 0);
          }
          for (i=0; i<parts.length; i++) {
            node.append('tspan')
              .text(parts[i])
              .attr('y', i*4)
              .attr('x', 0);
          }
        });
  },

  /* click callback for the nodes */
  node_click: function (data, node, topic) {
    this.info.load_topic(data.index, topic, this.data.metrics);
    var s = this.options.full_scale;
    this.zoom.translate([-s*data.x + this.options.width/2,
                        -s*data.y + this.options.height/2]).scale(s);
    this.redraw_smooth();
    d3.selectAll('g.node.highlighted').classed('highlighted', false);
    d3.selectAll('g.node.highlighted-main').classed('highlighted-main', false);
    var close = topic.topics;
    d3.select(node).classed('highlighted-main', true);
    var circle, line;
    for (var i=0; i<close.length; i++) {
      d3.select('g.node-' + close[i]).classed('highlighted', true);
    }
  },

  /* run 1000 ticks so that the layout settles down, then freeze it */
  calc_layout: function () {
    this.force.start();
    for (var i = 0; i < 1000; ++i) this.force.tick();
    this.force.stop();
  },

  /* update the positions to match the force layout */
  update_positions: function () {
    this.link.attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });
    this.node.attr('transform', translate_node);
    this.texts.attr('transform', translate_node);
  },

  start_ticking: function () {
    /* start the simulation going */
    if (this.ticking) return;
    this.ticking = true;
    var that = this;
    this.force.on("tick", function() {
      that.link.attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });

      that.node.attr("transform", translate_node);
      that.texts.attr('transform', translate_node);
    });
    this.force.start();
  },

  stop_ticking: function () {
    /* disable the simulation */
    if (!this.ticking) return;
    this.ticking = false;
    this.force.on('tick', null);
    this.force.stop();
  }
});

