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

var ChordViewer = Backbone.View.extend({
  el: '#chord-diagram',
  defaults: {
    width: 720,
    height: 720,
    outer_padding: 10,
    inner_padding: 24,
    padding: .04,
    num_topics: 10
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
    d3.json(URLS['pairwise'], function (data) {
      if (Storage) {
        localStorage.topics_data = JSON.stringify(data);
      }
      that.onloaded(data);
    });
  },
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
      .attr("transform", "translate(" + this.options.width / 2 + "," + this.options.height / 2 + ")");

    svg.append("circle") .attr("r", outerRadius);
  },
  topic_row: function (tid) {
    var row = [];
    // console.log('row', tid, this.topics.length);
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

var chords = new ChordViewer();

/*
d3.json(URLS['pairwise'], function (data) {
 layout.matrix(data.matrix);

 // Add a group per neighborhood.
 var group = svg.selectAll(".group")
 .data(layout.groups)
 .enter().append("g")
 .attr("class", "group")
 .on("mouseover", mouseover);

 // Add a mouseover title.
 group.append("title").text(function(d, i) {
 return cities[i].name + ": " + formatPercent(d.value) + " of origins";
 });

 // Add the group arc.
 var groupPath = group.append("path")
 .attr("id", function(d, i) { return "group" + i; })
 .attr("d", arc)
 .style("fill", function(d, i) { return cities[i].color; });

 // Add a text label.
 var groupText = group.append("text")
 .attr("x", 6)
 .attr("dy", 15);

 groupText.append("textPath")
 .attr("xlink:href", function(d, i) { return "#group" + i; })
 .text(function(d, i) { return cities[i].name; });

 // Remove the labels that don't fit. :(
 groupText.filter(function(d, i) { return groupPath[0][i].getTotalLength() / 2 - 16 < this.getComputedTextLength(); })
 .remove();

 // Add the chords.
 var chord = svg.selectAll(".chord")
 .data(layout.chords)
 .enter().append("path")
 .attr("class", "chord")
 // .style("fill", function(d) { return cities[d.source.index].color; })
 .attr("d", path);

 /*
 // Add an elaborate mouseover title for each chord.
 chord.append("title").text(function(d) {
 return cities[d.source.index].name
 + " → " + cities[d.target.index].name
 + ": " + formatPercent(d.source.value)
 + "\n" + cities[d.target.index].name
 + " → " + cities[d.source.index].name
 + ": " + formatPercent(d.target.value);
 });

 function mouseover(d, i) {
  chord.classed("fade", function(p) {
   return p.source.index != i
   && p.target.index != i;
  });
 }
});
*/

