/**
 * Part of Topical Guide (c) BYU 2013
 */

var dumb_matrix = [[11975,  5871, 8916, 2868],
               [ 1951, 10048, 2060, 6171],
               [ 8010, 16145, 8090, 8045],
               [ 1013,   990,  940, 6907]];

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

var FancyViewer = Backbone.View.extend({
  el: '#fancy',
  url: '',
  defaults: {
    width: 720,
    height: 720,
  },
  initialize: function () {
    this.options = _.extend(this.defaults, this.options);
    $('#refresh-button').click(_.bind(this.reload, this));
    if (Storage && localStorage.topics_data) {
      try {
        this.onloaded(JSON.parse(localStorage.topics_data));
      } catch (e) {
        console.log('loading error' + e);
        if (confirm('An error occurred loading cached data: reload?')) {
          this.reload();
        }
      }
    } else {
      this.reload();
    }
  },
  reload: function () {
    var that = this;
    d3.json(this.url, function (data) {
      if (Storage) {
        localStorage.topics_data = JSON.stringify(data);
      }
      that.onloaded(data);
    });
  },
});

var ForceViewer = FancyViewer.extend({
  el: '#force-topics',
  defaults: _.extend(FancyViewer.prototype.defaults, {
    circle_r: 10,
    charge: -360,
    link_distance: 50,
    line_width: 3
  }),
  onloaded: function (data) {
  console.log('loaded');
    this.matrix = data.matrix;
    this.topics = data.topics;
    this.metrics = data.metrics;
    this.setup_d3();
    this.load_all();
  },
  setup_d3: function () {
    var color = d3.scale.category20();
    var force = this.force = d3.layout.force()
      .charge(this.options.charge)
      .linkDistance(this.options.link_distance)
      .size([this.options.width, this.options.height]);

    var svg = this.svg = d3.select(this.el).append('svg')
      .attr('width', this.options.width)
      .attr('height', this.options.height)
      .attr("pointer-events", "all");

    var maing;
    var redraw = function () {
      maing.attr("transform",
            "translate(" + d3.event.translate + ")"
            + " scale(" + d3.event.scale + ")");
    };
    
    maing = this.maing = svg.append('svg:g')
                    .call(d3.behavior.zoom().on("zoom", redraw))
                      .append('svg:g');
  },
  make_links: function (nodes) {
    var links = [], target;
    for (var i=0; i<nodes.length; i++) {
      for (var j=0; j<nodes[i].topics.length; j++) {
        target = nodes[i].topics[j];
        links.push({source: i, target: target, weight: this.matrix[i][target]});
      }
    }
    return links;
  },
  load_all: function () {
    var nodes = this.topics;
    var links = this.make_links(nodes);
    var minmax = get_matrixminmax(this.matrix);
    var rng = minmax[1] - minmax[0];
    var rel = function (x) {
      return (x - minmax[0]) / rng;
    };
    var that = this;

    this.maing.selectAll('*').remove();

    this.maing.append('rect').attr('class', 'background')
      .attr('width', this.options.width)
      .attr('height', this.options.height);

    this.force.nodes(nodes).links(links)
              .linkStrength(function (d) { return rel(d.weight); }).start();

    var link = this.link = this.maing.selectAll('line.link')
      .data(links).enter().append('line')
        .attr('class', 'link')
        .style('stroke-width', function (d) { return that.options.line_width * rel(d.weight) });

    var node = this.node = this.maing.selectAll("g.node")
        .data(nodes)
      .enter().append('g')
        .attr('class', function (d, i) { return 'node node-' + i; })
        .on('mouseover', _.bind(this.mouseover, this))
        .on('mouseout', _.bind(this.mouseout, this));
    
    var circles = this.circles = node.append("circle")
        .attr("class", "node")
        .attr("r", this.options.circle_r)
        .style("fill", 'green');

    var texts = this.texts = node.append('svg:text')
      .attr('x', 10).attr('y', 10)
      .append('svg:textPath')
        .attr('xlink:href', function (d) { return '#group-' + d.index;})
        .text(function(d) { return d.names[0]; });

    circles.append("title")
        .text(function(d) { return d.names[0]; });

    this.calc_layout();
    this.update_positions();

  },
  mouseover: function (d, i) {
    $('g.node-' + i).addClass('highlighted');
  },
  mouseout: function (d, i) {
    $('g.node-' + i).removeClass('highlighted');
  },
  calc_layout: function () {
     this.force.start();
     for (var i = 0; i < 1000; ++i) this.force.tick();
     this.force.stop();
  },
  update_positions: function () {
     this.link.attr("x1", function(d) { return d.source.x; })
         .attr("y1", function(d) { return d.source.y; })
         .attr("x2", function(d) { return d.target.x; })
         .attr("y2", function(d) { return d.target.y; });

     this.circles.attr("cx", function(d) { return d.x; })
         .attr("cy", function(d) { return d.y; });
  },
     /*this.force.on("tick", function() {
       link.attr("x1", function(d) { return d.source.x; })
           .attr("y1", function(d) { return d.source.y; })
           .attr("x2", function(d) { return d.target.x; })
           .attr("y2", function(d) { return d.target.y; });

       node.attr("cx", function(d) { return d.x; })
           .attr("cy", function(d) { return d.y; });
     });*/
});



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
    /**
    var mn = 'Number of tokens';
    console.log('topic color', tid, arguments.length);
    var num = this.topics[tid].metrics[mn];
    var perc = (num - this.metrics[mn].min)/(this.metrics[mn].max - this.metrics[mn].min);
    **/
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

var chords = new ForceViewer();

