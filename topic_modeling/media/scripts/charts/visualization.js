/**
 * Part of Topical Guide (c) BYU 2013
 */

/**
 * Make a select thing .. where items:
 *  [name, title, fn]
 */
var SelectUI = function (el, items) {
  this.el = $(el);
  if (!this.el.length) throw new Error('no element given');
  this.selected = 0;
  this.title = $('a.dropdown-toggle span', this.el);
  this.body = $('ul.dropdown-menu', this.el);
  this.render = function () {
    this.title.html(items[this.selected][1]);
    this.body.empty();
    var that = this;
    for (var i=0; i<items.length; i++) {
      if (i === this.selected) continue;
      (function(i){
        $('<li><a href="#' + items[i][0] + '">' + items[i][1] + '</a></li>')
          .appendTo(that.body).click(function () {
            that.select(i);
          });
      })(i);
    }
    if (items.length === 1) {
      $('<li><a class="disabled">no other visualizations defined</a></li>')
        .appendTo(this.body);
    }
  };
  this.select = function (i) {
    items[i][2]();
    this.selected = i;
    this.render();
  };
  this.render();
  return this;
};

/** This view manages the content of the page
 *
 * It also handles the request and storage of data.
 *
 * - select the type of visualization
 * - select the model to use (topic / document / wordtype?)
 * - select the pairwise metric
 */
var MainView = Backbone.View.extend({
  el: '#main',
  url: URLS['pairwise'],
  initialize: function () {
    // $('#refresh-button').click(_.bind(this.reload, this));
    this.showing = null;
    this.views = {};
    this.loaded = false;
    this.setup_views();
    if (Storage && localStorage.topics_data) {
      try {
        this.load_data(JSON.parse(localStorage.topics_data));
      } catch (e) {
        console.log('loading error' + e);
        if (confirm('An error occurred loading cached data: reload?')) {
          this.reload();
        } else {
          throw e;
        }
      }
    } else {
      this.reload();
    }
  },
  setup_views: function () {
    var items = [];
    var that = this;
    this.views = {};
    this.$el.empty();
    _.forOwn(this.constructor.visualizations, function (value, key) {
      var node = $('<div></div>').attr('id', key).appendTo(that.$el).hide();
      var menu = $('#menu-' + key);
      var info = $('#info-' + key);
      that.views[key] = new value({parent: that, el: node, menu_el: menu,
        info_el: info
      });
      items.push([key, that.views[key].title, _.bind(that.view, that, key)]);
    });
    this.vlist = new SelectUI('#viz-picker', items);
    this.showing = items[0][0];
  },
  reload: function () {
    var that = this;
    d3.json(this.url, function (data) {
      if (Storage) {
        localStorage.topics_data = JSON.stringify(data);
      }
      that.load_data(data);
    });
  },
  load_data: function (data) {
    this.data = data;
    this.views[this.showing].load(data);
    this.views[this.showing].show();
  },
  view: function (name) {
    this.views[this.showing].hide();
    this.views[name].load(this.data);
    this.views[name].show();
  }
}, {
  visualizations: {},
  add: function (base, config) {
    if (arguments.length === 1) {
      config = base;
      base = VisualizationView;
    }
    var cls = base.extend(config);
    this.visualizations[config.name] = cls;
  }
});

/**
 * This is the base view for visualizations
 */
var VisualizationView = Backbone.View.extend({
  base_defaults: {
    width: 720,
    height: 720
  },
  defaults: {},

  initialize: function () {
    this.options = _.extend(this.base_defaults, this.defaults, this.options);
    if (!this.options.parent) throw new Error('No parent app given in options');
    if (!this.el) throw new Error('No element given in options');
    if (!this.options.menu_el) throw new Error('No element given in options');
    if (!this.options.info_el) throw new Error('No element given in options');
    this.main = this.options.parent;
    this.data = this.main.data;
    this.setup_menu(this.options.menu_el);
    this.setup_info(this.options.info_el);
    this.setup_base();
    this.setup_d3();
  },

  setup_menu: function (menu) {
    /** setup the menu. Arg: $(this.options.menu_el) **/
  },

  setup_info: function (info) {
    /** setup the info pane. Arg: $(this.options.info_el) **/
  },

  setup_base: function () {
    /** this sets up the basic d3 svg scaffolding, zooming, etc. **/
    this.svg = d3.select(this.el).append('svg')
      .attr('width', this.options.width)
      .attr('height', this.options.height)
      .attr("pointer-events", "all");
    this.outer = this.svg.append('svg:g');
    this.outer.append('rect').attr('class', 'background')
      .attr('width', this.options.width)
      .attr('height', this.options.height);
    this.maing = this.outer.append('svg:g').attr('class', 'main-g');
    this.zoom = d3.behavior.zoom().on("zoom", _.bind(this.redraw, this));
  },

  setup_d3: function () {
    /** create your layout, colors, etc. **/
  },

  load: function (data) {
    if (!this.loaded) {
      this.load(data);
      this.loaded = true;
    }
  },

  show: function () {
    this.$el.show();
    this.options.menu_el.show();
    this.options.info_el.show();
  },

  hide: function () {
    this.menu.hide();
    this.info.hide();
    this.$el.hide();
  },

  load: function () {
    /** override this. Data can be accessed through this.main.data **/
  },
  redraw_smooth: function () {
    /** updates the svg container to match this.zoom's transform and scale with a smooth
     * transition */
    this.maing.transition().attr("transform",
          "translate(" + this.zoom.translate() + ")"
          + " scale(" + this.zoom.scale() + ")");
  },
  redraw: function () {
    /** updates the svg container to match this.zoom's transform and scale
     * without a transition */
    this.maing.attr("transform",
          "translate(" + this.zoom.translate() + ")"
          + " scale(" + this.zoom.scale() + ")");
  },
});

/**
 * A view with built-in zooming
 */
var ZoomableView = VisualizationView.extend({

  base_defaults: _.extend(VisualizationView.prototype.base_defaults, {
    zoom_control: true
  }),
  
  setup_base: function () {
    /** create the zoom object + svg elements **/
    VisualizationView.prototype.setup_base.apply(this, arguments);
    this.outer.call(this.zoom)
    if (this.options.zoom_control) {
      this.make_zoom_ctrl();
    }
  },

  make_zoom_ctrl: function () {
    /** makes the zoom in and out controls **/
    var that = this;
    this.zoom_out = this.outer.append('g')
      .attr('class', 'zoom-out')
      .attr('pointer-events', 'all')
      .on('click', function () {
        var pos = that.zoom.translate();
        that.zoom.scale(that.zoom.scale() / 2);
        that.zoom.translate([pos[0]/2+that.options.width/4, pos[1]/2+that.options.height/4]);
        that.redraw_smooth();
      })
      .attr('transform', 'translate(10, 30)');
    this.zoom_out.append('rect').attr('class', 'bg').attr('width', 20).attr('height', 20);
    this.zoom_out.append('rect')
      .attr('class', 'cross').attr('width', 16)
      .attr('height', 4).attr('x', 2).attr('y', 8);

    this.zoom_in = this.outer.append('g')
      .attr('class', 'zoom-in')
      .attr('pointer-events', 'all')
      .on('click', function () {
        var pos = that.zoom.translate();
        that.zoom.scale(that.zoom.scale() * 2);
        that.zoom.translate([pos[0]*2-that.options.width/2, pos[1]*2-that.options.height/2]);
        that.redraw_smooth();
      })
      .attr('transform', 'translate(10, 10)');
    this.zoom_in.append('rect').attr('class', 'bg').attr('width', 20).attr('height', 20);
    this.zoom_in.append('rect')
      .attr('class', 'cross').attr('width', 4)
      .attr('height', 16).attr('x', 8).attr('y', 2);
    this.zoom_in.append('rect')
      .attr('class', 'cross').attr('width', 16)
      .attr('height', 4).attr('x', 2).attr('y', 8);
  },
});

