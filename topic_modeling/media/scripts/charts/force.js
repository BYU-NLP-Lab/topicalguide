//TODO: You need to understand a lot more of whats going on here...

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

//performance fix
function twofloat(n) {
  //return parseInt(n * 100)/100.0;
  return Math.round(n * 100) / 100.0;
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

/* returns an array of link objects {source : <index>, target: <index>, weight: <float>}
    where the size of the source and target nodes are within the size threshold and
    the link weight is within the link threshold
*/
function force_links(nodes, matrix, lk_thresh, sz_thresh, scale) {
  /** create links for the force layout **/ 
  var links = [], target, target_node, src_node;
  for (var src=0; src<nodes.length; src++) {

    src_node = nodes[src];
    if(!in_range(src_node, scale, sz_thresh)) {
      continue;
    }

    for (var j=0; j<nodes[src].topics.length; j++) {
      target = nodes[src].topics[j];
      target_node = nodes[target];

      if (in_range(target_node, scale, sz_thresh) && 
          matrix[src][target] <= lk_thresh[1] &&
          matrix[src][target] >= lk_thresh[0]) {
            links.push({source: src_node, target: target_node, weight: matrix[src][target]});
            //console.log(src + " to " + target);
          }
    }
  }
  return links;
}

function in_range(node, scale, thresh) {
  var size = scale(node.metrics['Number of tokens']);
  return size <= thresh[1] && size >= thresh[0];
}

function make_scale(minmax) {
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
    console.log(id);
    console.log(info);
    console.log(metrics);
    this.$el.hide();
    // get the popoverrolling
    var details_url = location.href.split('/').slice(0,-1).join('/') + '/topics/' + id;
    this.preload_popover(details_url);

    // populate
    this.$('.topic-name').text(info.names[0]);
    var mtable = this.$('table.metrics tbody');
    mtable.empty();

    _.forOwn(info.metrics, function (value, key) {
        mtable.append('<tr><td>' + key + '</td><td>' +
                        twofloat(value) + '</td><td>' +
                        twofloat(metrics[key].min) + '</td><td>' +
                        twofloat(metrics[key].max) + '</td></tr>');
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
    var link_th = parent.options.link_threshold;
    this.$('#force-link-slider').slider({
      range: true,
      min: 0,
      max: 1,
      values: parent.options.link_threshold,
      step: (link_th[1] - link_th[0]) / 20,
      stop: function ( event, ui ) {
        parent.set_link_th(ui.values);
      }
    });

    var size_th = parent.options.size_threshold;
    this.$('#force-size-slider').slider({
      range: true,
      min: 0,
      max: 1,
      values: size_th,
      step: (size_th[1] - size_th[0]) / 20,
      stop: function ( event, ui ) {
        parent.set_size_th(ui.values);
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
    link_threshold: [0.7, 1],
    size_threshold: [0.4, 1],
    pairwise: 'document correlation'
  },

  first : true,

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

    this.all_nodes = data.topics;
    /* this loop assigns the absolute index (into data.topics) to each node, so when
        we filter and use a subset, we can properly populate the info panel.  d3.force uses
        node.index so we use node.abs_idx */
    for(var k = 0; k < this.all_nodes.length; k++) {
      this.all_nodes[k].abs_idx = k;
    }

    var tminmax = get_topicsminmax(this.all_nodes);
    this.node_scale = make_scale(tminmax);
    this.nodes = this.filter_nodes(this.all_nodes, this.node_scale, this.options.size_threshold);

    var minmax = get_matrixminmax(data.matrix);
    if (minmax[0] < this.options.link_threshold[0]) minmax[0] = this.options.link_threshold[0];
    if (minmax[1] > this.options.link_threshold[1]) minmax[1] = this.options.link_threshold[1];
    var link_scale = this.link_scale = make_scale(minmax);
    var links = force_links(this.all_nodes, data.matrix, this.options.link_threshold,
                            this.options.size_threshold, this.node_scale);

    var that = this;
    this.info.clear();
    // populate the force layout
    this.force.nodes(this.nodes).links(links)
              .linkStrength(function (d) {
                return that.options.max_link_strength * link_scale(d.weight);
              }).start();
    // this.calc_layout();

    this.maing.selectAll('*').remove();
    this.maing.append('g').classed('all-links', true);
    this.maing.append('g').classed('all-nodes', true);
    // create links first so they're behind everything
    this.create_links(links, link_scale);
    this.create_nodes(this.nodes, this.data, this.node_scale);
    // update the positions of all the created nodes
    // this.update_positions();
    this.start_ticking();

    //first load should zoom in to see...
    if (this.first) {
      this.zoom_in.on('click')();
      this.first = false;
    }
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

  set_link_th: function (threshold_lk) {
    var data = this.data;
    this.options.link_threshold = threshold_lk;
    var minmax = get_matrixminmax(data.matrix);
    if (minmax[0] < threshold_lk[0]) minmax[0] = threshold_lk[0];
    if (minmax[1] > threshold_lk[1]) minmax[1] = threshold_lk[1];
    var scale = make_scale(minmax);
    this.remove_links();
    var links = force_links(this.all_nodes, data.matrix, this.options.link_threshold,
                            this.options.size_threshold, this.node_scale);
    this.create_links(links, scale);
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

  set_size_th: function (threshold_sz) {
    this.options.size_threshold = threshold_sz;
    this.force.stop();
    this.load(this.data);
  },

  filter_nodes: function (nodes, scale, threshold) {
    var filtered = [];
    for(var k = 0; k < nodes.length; k++) {
      var node = nodes[k];
      if(in_range(node, scale, threshold)) {
         filtered.push(nodes[k]);
      }
    }
    return filtered;
  },

  create_nodes: function (nodes, data, scale) {
    var that = this;
    this.node = this.maing.select('g.all-nodes').selectAll("g.node")
        .data(nodes)
      .enter().append('g')
        .attr('class', function (d, i) { return 'node node-' + i; })
        .attr('pointer-events', 'all')
        .on('click', function (d, i) {
          that.node_click(d, this, data.topics[d.abs_idx]);
        }).call(this.force.drag)
        .on('mouseover', function (d, i) {
          d3.select('text.node-text-' + i)
            .transition().attr('transform', 'translate(0, -3) scale(3)');
        }).on('mouseout', function (d, i) {
          d3.select('text.node-text-' + i)
            .transition().attr('transform', 'translate(0, -3) scale(1)');
        });
    this.create_circles(scale);
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

    this.info.load_topic(data.abs_idx, topic, this.data.metrics);
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

