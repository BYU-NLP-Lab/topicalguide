/**
 * Part of Topical Guide (c) BYU 2013
 */

var ChordControls = Backbone.View.extend({
  initialize: function (options) {
    var parent = this.parent = options.parent;
    var t = parent.options.threshhold;
    this.$('.threshhold').slider({
      range: true,
      min: 0,
      max: 1,
      values: parent.options.threshhold,
      step: .05,
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


var ChordViewer = MainView.add({
  name: 'chords',
  title: 'Chord Diagram',
  controls_class: ChordControls,

  defaults: {
    outer_padding: 10,
    inner_padding: 24,
    padding: .04,
    num_topics: 10,
    tid: 0,
    threshhold: [.7, 1],
    pairwise: 'document correlation'
  },

  url: function () {
    return URLS['pairwise topics'][this.options.pairwise];
  },

  setup_d3: function () {
    var outerRadius = (Math.min(this.options.width, this.options.height) / 2
                        - this.options.outer_padding),
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
  },

  topic_row: function (tid) {
    var row = [];
    for (var i=0; i<this.options.num_topics; i++) {
      row.push(this.matrix[tid][this.topics[tid].topics[i]] * 100);
    }
    return row;
  },

  thresh_matrix: function () {
    var matrix = [], row;
    for (var i=0; i<this.matrix.length; i++) {
      row = [];
      for (var y=0; y<this.matrix[i].length; y++) {
        if (this.matrix[i][y] < this.options.threshhold[0]) {
          row.push(0);
        } else {
          row.push(this.matrix[i][y]);
        }
      }
      matrix.push(row);
    }
    return matrix;
  },

  topic_matrix: function (tid) {
    var tids = [tid].concat(this.topics[tid].topics.slice(0, this.options.num_topics));
    var matrix = [], row;
    for (var i=0; i<tids.length; i++) {
      row = [];
      for (var y=0; y<tids.length; y++) {
        if (this.matrix[tids[i]][tids[y]] < this.options.threshhold[0]) {
          row.push(0);
        } else {
          row.push(this.matrix[tids[i]][tids[y]] * 100);
        }
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

  set_threshhold: function (threshhold) {
    this.options.threshhold = threshhold;
    this.reload();
  },

  load: function (data) {
    var outerRadius = (Math.min(this.options.width, this.options.height) / 2
                        - this.options.outer_padding),
        innerRadius = outerRadius - this.options.inner_padding;
    this.topics = data.topics;
    this.matrix = data.matrix;
    this.metrics = data.metrics;
    this.maing.attr("id", "circle")
          .attr("transform",
                "translate(" + this.options.width / 2 + "," + this.options.height / 2 + ")");
    this.maing.append("circle") .attr("r", outerRadius);
    var tid = this.options.tid;
    var matrix = this.current_matrix = this.thresh_matrix(); //this.topic_matrix(tid);
    this.minmax = get_matrixminmax(this.current_matrix);
    this.current_topics = this.topics[tid].topics.slice();
    this.current_topics.splice(0, 0, tid);
    this.layout.matrix(this.current_matrix);

    this.maing.selectAll('*').remove();

    /**
    var topics = [], colors = [];
    var perc;
    var mn = 'Number of tokens';
    for (var i=0; i<this.current_topics.length; i++) {
      topics.push(this.topics[this.current_topics[i]]);
      num = this.topics[this.current_topics[i]].metrics[mn];
      perc = (num - this.metrics[mn].min)/(this.metrics[mn].max - this.metrics[mn].min);
      colors.push(d3.hsl(0, 1, perc));
    }
    **/

    var chord = this.maing.selectAll("path.chord")
      .data(this.layout.chords)
      .enter().append("svg:path")
        .attr("class", "chord")
        // .style("fill", _.bind(this.topic_color, this))
        .attr("d", this.path); /*
      .append('svg:title')
        .text(function(d) { return topics[d.source.index].names[0] + ' :: ' +
                                   topics[d.target.index].names[0] + ' :: ' +
                                   matrix[d.source.index][d.target.index]; });
      // */

    var g = this.maing.selectAll("g.group")
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
        // .style("fill", function(d) { return colors[d.index]; })
        .attr("id", function(d, i) { return "group" + d.index; })
        .attr("d", this.arc)
      .append("svg:title");
        // .text(function(d) { return topics[d.index].names[0]; });

    if (false) {
    // Add the group label (but only for large groups, where it will fit).
    // An alternative labeling mechanism would be nice for the small groups.
    g.append("svg:text")
        .attr("x", 6)
        .attr("dy", 15)
      .append("svg:textPath")
        .attr("xlink:href", function(d) { return "#group" + d.index; })
        .text(function(d) { return topics[d.index].names[0]; });
    }


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

