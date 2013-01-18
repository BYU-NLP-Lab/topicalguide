/**
 * Part of Topical Guide (c) BYU 2013
 */

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
    if (topics[i].metrics['Number of tokens'] > max) max = topics[i].metrics['Number of tokens'];
    if (topics[i].metrics['Number of tokens'] < min) min = topics[i].metrics['Number of tokens'];
  }
  return [min, max];
}

function force_links(nodes, matrix) {
  /** create links for the force layout **/ 
  var links = [], target;
  for (var i=0; i<nodes.length; i++) {
    for (var j=0; j<nodes[i].topics.length; j++) {
      target = nodes[i].topics[j];
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

/**
 * This is a Force visualization
 */
var ForceViewer = MainView.add(ZoomableView, {
  name: 'force-topics',
  title: 'Force Diagram',
  defaults: {
    circle_r: 20,
    circle_min: 2,
    charge: -360,
    link_distance: 50,
    line_width: 3,
    full_scale: 3
  },

  initialize: function () {
    VisualizationView.prototype.initialize.apply(this, arguments);
    this.ticking = false;
  },

  setup_menu: function (menu) {
    var that = this;
    $('button[name=unfreeze]', menu).click(function () {
      if ($(this).hasClass('active')) {
        that.stop_ticking();
      } else {
        that.start_ticking();
      }
    });
  },

  setup_d3: function () {
    this.force = d3.layout.force()
      .charge(this.options.charge)
      .linkDistance(this.options.link_distance)
      .size([this.options.width, this.options.height]);
  },

  load: function (data) {
    var nodes = data.topics;
    var links = force_links(nodes, data.matrix);
    var minmax = get_matrixminmax(data.matrix);
    var tminmax = get_topicsminmax(data.topics);
    var rel = make_rel(minmax);
    var trel = make_rel(tminmax);
    var that = this;
    // populate the force layout
    this.force.nodes(nodes).links(links)
              .linkStrength(function (d) { return rel(d.weight); }).start();
    this.calc_layout();

    this.maing.selectAll('*').remove();
    // create links first so they're behind everything
    this.create_links(links, rel);
    this.create_nodes(nodes, data, trel);
    // update the positions of all the created nodes
    this.update_positions();
  },

  create_links: function (links, rel) {
    var that = this;
    this.link = this.maing.selectAll('line.link')
      .data(links).enter().append('line')
      .attr('class', 'link').attr('name', function (d) {
        return 'link-' + d.source.index + '-' + d.target.index;
      }).style('stroke-width', function (d) {
        return that.options.line_width * rel(d.weight)
      });
  },

  create_nodes: function (nodes, data, trel) {
    var that = this;
    this.node = this.maing.append('g')
      .classed('all-nodes', true).selectAll("g.node")
        .data(nodes)
      .enter().append('g')
        .attr('class', function (d, i) { return 'node node-' + i; })
        .attr('pointer-events', 'all')
        .on('click', function (d, i) {
          that.node_click(d, this, data.topics[d.index]);
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
          return parseInt(ret);
        });
  },

  create_texts: function (nodes) {
    /* texts for the circles need to be above the circles */
    this.texts = this.maing.append('g')
      .classed('all-texts', true).selectAll('g.text')
        .data(nodes)
      .enter().append('svg:g')
        .attr('pointer-events', 'none')
        .attr('class', 'text')
    // add the lines of text
    this.texts.append('svg:text')
        .attr('transform', 'translate(0, -3)')
        .each(function (d, i) {
          var node = d3.select(this);
          var parts = d.names[0].split(' ');
          for (var i=0; i<parts.length; i++) {
            node.append('tspan')
              .attr('class', 'back')
              .text(parts[i])
              .attr('y', i*4)
              .attr('x', 0);
          }
          for (var i=0; i<parts.length; i++) {
            node.append('tspan')
              .text(parts[i])
              .attr('y', i*4)
              .attr('x', 0);
          }
        });
  },

  node_click: function (data, node, topic) {
    /* click callback for the nodes */
    console.log(i);
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

  calc_layout: function () {
    /* run 1000 ticks so that the layout settles down, then freeze it */
    this.force.start();
    for (var i = 0; i < 1000; ++i) this.force.tick();
    this.force.stop();
  },

  update_positions: function () {
    /* update the positions to match the force layout */
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

/*
var ChordViewer = FancyViewer.extend({
  el: '#chord-diagram',
  url: URLS['pairwise'],
  defaults: _.extend(FancyViewer.prototype.defaults, {
    outer_padding: 10,
    inner_padding: 24,
    padding: .04,
    num_topics: 10
  }),
  onloaded: function (data) {
    this.matrix = data.matrix;
    this.topics = data.topics;
    this.metrics = data.metrics;
    this.setup_d3();
    this.load_topic(0);
  },
  setup_d3: function () {
    var outerRadius = Math.min(this.options.width, this.options.height) / 2 - this.options.outer_padding,
        innerRadius = outerRadius - this.options.inner_padding;

    var formatPercent = d3.format(".1%");

    var arc = this.arc = d3.svg.arc()
    .innerRadius(innerRadius)
    .outerRadius(outerRadius);

    var layout = this.layout = d3.layout.chord()
      .padding(this.options.padding)
      .sortSubgroups(d3.descending)
      .sortChords(d3.ascending);

    var path = this.path = d3.svg.chord()
      .radius(innerRadius);

    var svg = this.svg = d3.select(this.el).append("svg")
      .attr("width", this.options.width)
      .attr("height", this.options.height)
      .append("g")
      .attr("id", "circle")
      .attr("transform",
            "translate(" + this.options.width / 2 + "," + this.options.height / 2 + ")");
    svg.append("circle") .attr("r", outerRadius);
  },
  topic_row: function (tid) {
    var row = [];
    for (var i=0; i<this.options.num_topics; i++) {
      row.push(this.matrix[tid][this.topics[tid].topics[i]] * 100);
    }
    return row;
  },
  topic_matrix: function (tid) {
    var tids = [tid].concat(this.topics[tid].topics.slice(0, this.options.num_topics));
    var matrix = [], row;
    for (var i=0; i<tids.length; i++) {
      row = [];
      for (var y=0; y<tids.length; y++) {
        row.push(this.matrix[tids[i]][tids[y]] * 100);
      }
      matrix.push(row);
    }
    return matrix;
  },
  topic_color: function (d) {
    var tid = d.source.index;
    var did = d.target.index;
    var val = this.current_matrix[tid][did];
    var perc = (val - this.minmax[0]) / (this.minmax[1] - this.minmax[0]);
    return d3.hsl(120, 1, perc);
  },
  load_topic: function (tid, prevpos) {
    var matrix = this.current_matrix = this.topic_matrix(tid);
    this.minmax = get_matrixminmax(this.current_matrix);
    this.current_topics = this.topics[tid].topics.slice();
    this.current_topics.splice(prevpos || 0, 0, tid);
    this.layout.matrix(this.current_matrix);
    
    var topics = [], colors = [];
    var perc;
    var mn = 'Number of tokens';
    for (var i=0; i<this.current_topics.length; i++) {
      topics.push(this.topics[this.current_topics[i]]);
      num = this.topics[this.current_topics[i]].metrics[mn];
      perc = (num - this.metrics[mn].min)/(this.metrics[mn].max - this.metrics[mn].min);
      colors.push(d3.hsl(0, 1, perc));
    }

    this.svg.selectAll('*').remove();

    var chord = this.svg.selectAll("path.chord")
      .data(this.layout.chords)
      .enter().append("svg:path")
        .attr("class", "chord")
        .style("fill", _.bind(this.topic_color, this))
        .attr("d", this.path)
      .append('svg:title')
        .text(function(d) { return topics[d.source.index].names[0] + ' :: ' +
                                   topics[d.target.index].names[0] + ' :: ' +
                                   matrix[d.source.index][d.target.index]; });

    var g = this.svg.selectAll("g.group")
      .data(this.layout.groups)
      .enter().append("svg:g")
      .attr("class", "group")
      .on('mouseover', fade(.1))
      .on('mouseout', fade(1));

    var that = this;

    // Returns an event handler for fading a given chord group.
    function fade(opacity) {
      return function(g, i) {
        that.svg.selectAll("path.chord")
        .filter(function(d) { return d.source.index != i && d.target.index != i; })
        .transition()
        .style("opacity", opacity);
      };
    }

    // Add the group arc.
    g.append("svg:path")
        .style("fill", function(d) { return colors[d.index]; })
        .attr("id", function(d, i) { return "group" + d.index; })
        .attr("d", this.arc)
      .append("svg:title")
        .text(function(d) { return topics[d.index].names[0]; });

    // Add the group label (but only for large groups, where it will fit).
    // An alternative labeling mechanism would be nice for the small groups.
    g.append("svg:text")
        .attr("x", 6)
        .attr("dy", 15)
      .append("svg:textPath")
        .attr("xlink:href", function(d) { return "#group" + d.index; })
        .text(function(d) { return topics[d.index].names[0]; });


    g.on('click', function (g, i) {
      that.load_topic(that.current_topics[i], i);
    });

    function mouseover(d, i) {
      chord.classed("fade", function(p) {
      return p.source.index != i
      && p.target.index != i;
      });
    }
  }
});
*/

