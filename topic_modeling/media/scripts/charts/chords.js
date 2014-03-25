/**
 * Part of Topical Guide (c) BYU 2013
 */


var ChordInfo = InfoView.extend({
  initialize: function () {
    this.$('button.view-plot').click(_.bind(this.view_plot, this));
    this.$el.hide();
  },

  clear: function () {
    this.$('tbody').empty();
  },

  view_plot: function () {
    this.options.parent.main.nav('plot-documents', {'topic': this.current_tid});
  },

  load_topic: function (tid, info) {
    this.$el.hide();
    this.current_tid = tid;
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
    // preload the popover
    var details_url = location.href.split('/').slice(0,-1).join('/') + '/topics/' + tid;
    this.preload_popover(details_url);
    // show yourself
    this.$el.show();
  },
  show: function () {
    // this.$el.show();
  },
  hide: function () {
    this.$el.hide();
  }
});

// TODO change step to be based on number of topics? or something more sensible than 20...
var ChordControls = Backbone.View.extend({
  initialize: function (options) {
    var parent = this.parent = options.parent;
    var t = parent.options.chord_threshold;
    var tb = parent.options.threshhold_bounds;
    this.$('#chords-slider').slider({
      range: true,
      min: tb[0],
      max: tb[1],
      values: parent.options.chord_threshold,
      step: (tb[1] - tb[0]) / 20,
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
  info_class: ChordInfo,

  defaults: {
    outer_padding: 10,
    inner_padding: 24,
    padding: .04,
    num_topics: 10,
    tid: 0,
    chord_threshold: [.87, 0.94],
    threshhold_bounds: [.5, 1],
    pairwise: 'document correlation'
  },

  url: function () {
    return URLS['pairwise topics'][this.options.pairwise];
  },

  setup_d3: function () {
    this.options.inner_padding = this.options.width / 26;
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
        if (this.matrix[i][y] < this.options.chord_threshold[0] ||
            this.matrix[i][y] > this.options.chord_threshold[1] ) {
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
        if (this.matrix[tids[i]][tids[y]] < this.options.chord_threshold[0] ||
            this.matrix[tids[i]][tids[y]] > this.options.chord_threshold[1] ) {
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
		this.options.chord_threshold = threshhold;
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


    // scale.quantize() means the domain is continuous, but the range is discrete
    var fill = d3.scale.quantize()
    .domain([this.options.chord_threshold[0],this.options.chord_threshold[1]])
    .range(colorbrewer.RdBu[9].reverse())
    //.range(colorbrewer.Reds[9]);


    var chord = this.maing.append('g').classed('all-chords', true).selectAll("path.chord")
      .data(this.layout.chords)
      .enter().append("svg:path")
        .attr("class", "chord")
        .style("fill", function(d) {return fill(d.source.value);})
        .attr("d", this.path); 
        /*.append('svg:title')
        .text(function(d) { return topics[d.source.index].names[0] + ' :: ' +
                                   topics[d.target.index].names[0] + ' :: ' +
                                   matrix[d.source.index][d.target.index]; });*/

    var g = this.maing.append('g').classed('all-groups', true).selectAll("g.group")
      .data(this.layout.groups)
      .enter().append("svg:g")
      .attr("class", "group")
      .on('mouseover', fade(.2, true))
      .on('mouseout', fade(1, false));

    var that = this;

    // Returns an event handler for fading a given chord group.
    function fade(opacity, show) {
      return function(g, i) {
        //alert("triggered");
        // d3.select(this).classed('hovered', show);
        that.svg.selectAll('g.group')
          .filter(function (d) { return data.matrix[i][d.index] > that.options.chord_threshold[0] &&
                                        data.matrix[i][d.index] < that.options.chord_threshold[1]; })
          .classed('hovering', show);
	//this filter selects all chords not being hovered and sets the opacity lower
        that.svg.selectAll("path.chord")
        .filter(function(d) { return d.source.index != i && d.target.index != i; })
        .transition()
        .style("opacity", opacity);
      };
    }

    // Add the group arc.
    var paths = g.append("svg:path")
        // .style("fill", function(d) { return colors[d.index]; })
        .attr("id", function(d, i) { return "group" + d.index; })
        .attr("d", this.arc);
    paths.append("svg:title")
      .text(function(d) { return data.topics[d.index].names[0]; });

    var spacing = this.options.height / 42;
    setTimeout(function () {
    paths.each(function (d, i) {
      var b = this.getBBox();
      //This makes sure that we are not creating titles on hidden chords
      var shouldAllow = false;
      for(var k = 0; k < data.matrix[i].length; k++)
        if (data.matrix[i][k] > that.options.chord_threshold[0] &&
           data.matrix[i][k] < that.options.chord_threshold[1])
            shouldAllow = true;
      if(shouldAllow) {
      d.textnode = d3.select(this.parentNode).append('svg:text')
        .attr('transform', 'translate(' + parseInt(b.x + b.width/2) + ' ' + (parseInt(b.y + b.height/2) - 15) + ')')
        .classed('chord-title', true);
      var parts = data.topics[i].names[0].split(' ');
      for (var i=0; i<parts.length; i++) {
        d.textnode.append('tspan')
          .attr('class', 'back')
          .text(parts[i])
          .attr('y', i*spacing)
          .attr('x', 0);
      }
      for (var i=0; i<parts.length; i++) {
        d.textnode.append('tspan')
          .text(parts[i])
          .attr('y', i*spacing)
          .attr('x', 0);
      }
    }});
    }, 100);

    var highlight_id = 48;
    setTimeout(function() {
        fade(.1, true)(null, highlight_id);
        $('#group' + highlight_id).parent().children('text').css('display', 'block');
        //pop up a modal to say to mouseover the outer nodes
      }, 500);
    setTimeout(function() {fade(1, false)(null, highlight_id);
        $('#group' + highlight_id).parent().children('text').css('display', '');
      }, 4000);
    /*
    // Add the group label (but only for large groups, where it will fit).
    // An alternative labeling mechanism would be nice for the small groups.
    // maybe smaller text?
    g.append("svg:text")
        .attr("x", 6)
        .attr("dy", 15)
      .append("svg:tspan")
        // .attr("xlink:href", function(d) { return "#group" + d.index; })
        .text(function(d) { return data.topics[d.index].names[0]; });
    */


    g.on('click', function (g, i) {
      that.info.load_topic(i, data.topics[i]);
    });
  }
});

