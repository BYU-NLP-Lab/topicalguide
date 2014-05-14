/**
 * Part of Topical Guide (c) BYU 2013
 */

Backbone.View.prototype.event_aggregator = _.extend({}, Backbone.Events);

function url_args(args) {
  var items = args.split('&');
  var hash = {};
  for (var i=0; i<items.length; i++) {
    hash[items[i].split('=')[0]] = unescape(items[i].split('=').slice(1).join('='));
  }
  return hash;
}

function url_deargs(options) {
  var items = [];
  _.forOwn(options, function(value, key) {
    items.push(key + '=' + escape(value));
  });
  return items.join('&');
}

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
  this.titles = {};
  for (var i=0; i<items.length; i++) {
    this.titles[items[i][0]] = items[i][1];
  }
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
    if (items[i][2]() === false) return;
    this.selected = i;
    this.render();
  };
  this.set_selected = function (value) {
    for (var i=0; i<items.length; i++) {
      if (value === items[i][0]) {
        this.selected = i;
        this.render();
        return true;
      }
    }
    return false;
  };
  this.render();
  return this;
};


var InfoView = Backbone.View.extend({

  parent: $('#info'),

  trigger: $('#info-trigger'),

  defaults: {
    resize_trigger: "resize", // You can change this in implementation classes, though it is not recommended
  },

  initialize: function (options) {

    var el_selector = '#' + options.el_id;
    this.infoView = this.parent;
    $('<div id="' + options.el_id + '" class="info-item">').appendTo(this.infoView);
    this.setElement(el_selector);

    this.width = this.parent.outerWidth();
    this.height = this.parent.outerHeight();

    this.$el.hide();

    _.bindAll(this, "resize");
    this.event_aggregator.bind(this.defaults.resize_trigger, this.resize);

    InfoView.prototype.open = false; // Set for all InfoViews so it stays open across visualizations
  },

  preload_popover: function (url) {
    // set the url
    this.$('.view-details-btn')
    .attr('href', url)
    .click(function (e) {
      e.preventDefault();
      // reset the innards to just be loading
      $('#iframe-modal iframe.theframe')[0].contentDocument.body.innerHTML=$('script#iframe-loading')[0].innerHTML;
      $('#iframe-modal iframe.theframe').attr('src', url + '?in_iframe=true');
      $('#iframe-modal').modal('show');
      return false;
    });
  },

  show: function () {

    this.$el.show();
    var infoView = this;
    var event_aggregator = this.event_aggregator;
    var resize_trigger = this.defaults.resize_trigger;

    // Set click handler for info trigger
    this.trigger.click(function() {

      // Set up resize event for other views
      InfoView.prototype.open = !InfoView.prototype.open; // Toggle open or closed
      var width = infoView.width; // Get the width of the info view
      width = InfoView.prototype.open ? width * -1 : width; // Get pixels to add to main view

      // By resizing the main view, the info view will get pushed into the overflow and hidden
      event_aggregator.trigger(resize_trigger, { dWidth : width }); // Trigger resize event
      return false;
    });
  },

  hide: function () {
    this.$el.hide();
    this.trigger.off("click"); // Un-register click handler for this infoview when switching to another view
  },

  resize: function(attr) {
    if (attr && attr.dHeight) {
      this.height = this.height + attr.dHeight;
      this.$el.animate({
        height : this.height + "px"
      }, 400);
    }
  },

  appendItem: function(html) {
    return $(html).appendTo(this.$el);
  },

  appendItems: function(items) {
    var elements = [];
    for (var i in items) {
      var html = items[i];
      elements.push(this.appendItem(html));
    }
    return elements;
  }
  
});


var ControlsView = Backbone.View.extend({

  parent: $('#controls'),

  trigger: $('#control-trigger'),

  showing: false,

  initialize: function(options) {

    var el_selector = '#' + options.el_id;
    var controlsView = this.controlsView = this.parent;
    $('<div id="' + options.el_id + '" class="control-item">').appendTo(this.controlsView);
    this.setElement(el_selector);

    this.parent.hide();
    this.$el.hide();

    this.height = this.parent.outerHeight();
    ControlsView.prototype.open = false; // Set for all InfoViews so it stays open across visualizations
  },

  show: function() {
    this.$el.show();
    var controlView = this;
    var event_aggregator = this.event_aggregator;
    var open = false;

    // Create controls trigger event
    this.trigger.click(function() {
      $('#controls').slideToggle(400);

      ControlsView.prototype.open = !ControlsView.prototype.open;
      var height = controlView.height;
      height = ControlsView.prototype.open ? height * -1 : height;

      var resize_trigger = "resize";
      event_aggregator.trigger(resize_trigger, { dHeight : height });
      return false;
    });
  },

  hide: function() {
    this.$el.hide();

    // remove controls trigger event
    this.trigger.off("click");
  },

  appendItem: function(html) {
    return $(html).appendTo(this.$el);
  },

  appendItems: function(items) {
    var elements = [];
    for (var i in items) {
      var html = items[i];
      elements.push(this.appendItem(html));
    }
    return elements;
  }

})

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

  initialize: function () {
    // $('#refresh-button').click(_.bind(this.reload, this));
    this.showing = null;
    this.views = {};
    this.loaded = false;
    this.setup_views();
    this.cache = {};
    $('#refresh button').click(_.bind(function () {
      this.view(this.showing, {refresh: true});
    }, this));
    this.last_refreshed = $('#refresh time');
    this.last_refreshed.timeago();
    this.refreshed_times = {};
    if (Storage && localStorage.refreshed_times) {
      this.refreshed_times = JSON.parse(localStorage.refreshed_times);
    }

    this.follow_hash();
    $(window).on('hashchange', _.bind(this.follow_hash, this));
  },

  /*
   * The hashes we use for navigation look like
   * page-name:arg1=val1&arg2=val2&...
   */
  follow_hash: function () {
    var parts = document.location.hash.slice(1).split(':');
    var options = {};
    if (parts.length && parts[0].length) {
      var navto = parts[0];
      var args = parts.slice(1).join(':');
      options = url_args(args);
      
      if (this.views[navto] && navto !== this.showing) {
        this.vlist.set_selected(navto);
      }
    } else {
      document.location.hash = '#' + this.showing;
      navto = this.showing;
    }
    this.view(navto, {}, options);
  },

  nav: function (page, options) {
    document.location.hash = '#' + page + ':' + url_deargs(options);
  },

  fetch_data: function (url, callback) {
    if (!url) throw new Error('invalid URL specified');
    var that = this;
    if (this.cache[url]) {
      // using a timeout so the loading indicator will show before any long
      // JS processing freezes the UI
      return setTimeout(function () {callback(that.cache[url])}, 100);
    }
    if (Storage && localStorage[url]) {
      try {
        this.cache[url] = JSON.parse(localStorage[url]);
        if (this.cache[url]) {
          // using a timeout so the loading indicator will show before any long
          // JS processing freezes the UI
          return setTimeout(function () {callback(that.cache[url])}, 100);
        } else {
          this.reload(url, callback);
        }
      } catch (e) {
        console.log('loading error: ' + e);
        if (confirm('An error occurred loading cached data: reload?')) {
          this.reload(url, callback);
        } else {
          throw e;
        }
      }
    } else {
      this.reload(url, callback);
    }
  },

  setup_views: function () {
    var items = [];
    var that = this;
    this.views = {};
    // this.$el.empty();
    _.forOwn(this.constructor.visualizations, function (value, key) {
      var node = $('<div class="viz-main vis-full-height"></div>').attr('id', key).appendTo($('#main')).hide();
      var menu = $('#menu-' + key);
      var info_id = 'info-' + key;
      var controls_id = 'controls-' + key;
      that.views[key] = new value({parent: that, el: node, menu_el: menu,
        info_el_id: info_id, controls_el_id: controls_id
      });
      items.push([key, that.views[key].title, _.bind(that.view, that, key)]);
    });
    this.vlist = new SelectUI('#viz-picker', items);
    this.showing = items[0][0];
  },

  reload: function (url, callback) {
    var that = this;
    var when_refreshed = new Date();
    d3.json(url, function (data) {
      that.cache[url] = data;
      that.refreshed_times[url] = when_refreshed;
      if (Storage) {
        localStorage[url] = JSON.stringify(data);
        localStorage.refreshed_times = JSON.stringify(that.refreshed_times);
      }
      callback(data);
    });
  },

  update_refreshed: function (date) {
    this.last_refreshed.text(jQuery.timeago(date));
    this.last_refreshed.attr('datetime', date);
  },

  start_loading: function () {
    this.loading = true;
    $(document.body).addClass('loading');
  },

  stop_loading: function () {
    this.loading = false;
    $(document.body).removeClass('loading');
  },

  disable: function () {
    $('#disable-nav').show();
    $('#disable-right').show();
    $('#disable-main').show();
  },

  enable: function () {
    $('#disable-nav').hide();
    $('#disable-right').hide();
    $('#disable-main').hide();
  },

  view: function (name, options, sub_options) {
    if (this.loading) return false;
    options = options || {};
    if (options.reload || options.refresh) {
      this.disable();
    } else if (!options.dont_hide) {
      this.views[this.showing].hide();
    }
    $('head title').text('Topical Guide | ' + this.vlist.titles[name]);
    this.start_loading();
    var that = this;
    this.showing = name;
    var url = this.views[name].url();
    var callb = function (data) {
      that.loading = false;
      that.update_refreshed(that.refreshed_times[url]);
      that.views[name].load(data);
      if (options.reload || options.refresh) {
        that.enable();
      } else {
        that.views[name].show(sub_options);
      }
      that.stop_loading()
    };
    if (options.refresh) {
      return this.reload(url, callb);
    } else {
      this.fetch_data(url, callb);
    }
  },

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
    width:  $('#main').outerWidth(),
    height: $('#main').outerHeight(),
  },
  menu_class: null,
  info_class: null,
  controls_class: null,
  defaults: {},

  initialize: function () {

    this.options = _.extend(this.base_defaults, this.defaults, this.options);
    if (!this.options.parent) throw new Error('No parent app given in options');
    if (!this.el) throw new Error('No element given in options');
    if (!this.options.menu_el) throw new Error('No element given in options');
    if (!this.options.info_el_id) throw new Error('No element given in options');

    this.width = this.base_defaults.width;
    this.height = this.base_defaults.height;
    this.set_new_dimensions();

    this.main = this.options.parent;
    this.data = this.main.data;
    this.loading = false;
    this.setup_menu(this.options.menu_el);
    this.setup_info(this.options.info_el_id);
    this.setup_controls(this.options.controls_el_id);
    this.setup_base();
    this.setup_d3();
  },

  set_new_dimensions: function(override) {

    if (override) {
      if (override.width)
        this.width = override.width;
      if (override.height)
        this.height = override.height;
    }
  },

  url: function () {
    throw new Error('url() should be overridden');
  },

  /** setup the menu. Arg: $(this.options.menu_el) **/
  setup_menu: function (menu) {
    if (this.menu_class) {
      this.menu = new this.menu_class({el: menu, parent: this});
    }
  },

  /** setup the info pane. Arg: $(this.options.info_el) **/
  setup_info: function (info_id) {
    if (this.info_class) {
      this.info = new this.info_class({el_id: info_id, parent: this});
      this.info.hide();
    }
  },

  /** setup the controls pane. Arg: $(this.options.controls_el_id} **/
  setup_controls: function (controls_id) {
    if (this.controls_class) {
      this.controls = new this.controls_class({el_id: controls_id, parent: this});
      this.controls.hide();
    }
  },

  /** this sets up the basic d3 svg scaffolding, zooming, etc. **/
  setup_base: function () {
    this.svg = d3.select(this.el).append('svg')
      // .attr('width', this.options.width)
      // .attr('height', this.options.height)
      .attr("pointer-events", "all");
    this.outer = this.svg.append('svg:g');
    this.outer.append('rect').attr('class', 'background')
      .attr('width', this.options.width)
      .attr('height', this.options.height);
    this.maing = this.outer.append('svg:g').attr('class', 'main-g');
    this.zoom = d3.behavior.zoom().on("zoom", _.bind(this.redraw, this));
  },

  /** create your layout, colors, etc. **/
  setup_d3: function () {
  },

  /** populate your layout with the JSON data **/
  load: function (data) {
    if (!this.loaded) {
      this.load(data);
      this.loaded = true;
    }
  },

  show: function () {
    this.$el.show();
    if (this.menu) this.menu.show();
    if (this.info) this.info.show();
    if (this.controls) this.controls.show();
  },

  hide: function () {
    if (this.menu) this.menu.hide();
    if (this.info) this.info.hide();
    if (this.controls) this.controls.hide();
    this.$el.hide();
  },

  reload: function () {
    this.main.view(this.name, {reload: true});
  },

  refresh: function () {
    this.main.view(this.name, {refresh: true});
  },

  /** override this. Data can be accessed through this.main.data **/
  load: function () {
  },

  /** updates the svg container to match this.zoom's transform and scale with a smooth
  * transition */
  redraw_smooth: function () {
    this.maing.transition().attr("transform",
          "translate(" + this.zoom.translate() + ")"
          + " scale(" + this.zoom.scale() + ")");
  },

  /** updates the svg container to match this.zoom's transform and scale
    * without a transition */
  redraw: function () {
    this.maing.attr("transform",
          "translate(" + this.zoom.translate() + ")"
          + " scale(" + this.zoom.scale() + ")");
  },

  resize: function(options) {
    var newDimensions = {};
    var svg = this.svg;

    if (options.dWidth) {
      var width = this.width + options.dWidth;
      var goal = { width : width + "px" };
      // this.$el.animate(goal, 1000);
      $('#main').animate(goal, 400);
      // Magical jQuery syntax to animate html attributes, rather than changing the styling
      // I'm leaving this here in case someone needs to know how to do this in the future
      // $({ width : svg.attr("width") }).animate(goal,
      //                                               { duration: 1000,
      //                                                 step : function(now) {
      //                                                   svg.attr("width", now);
      //                                                 }
      //                                               });

      newDimensions.width = width;
    }

    if (options.dHeight) {
      var height = this.height + options.dHeight;
      var goal = { height : height + "px" };
      $('#visualization .vis-full-height').animate(goal, 400);
      // console.log(this.$el);
      // this.$el.animate(goal, 400);

      newDimensions.height = height;
    }

    this.set_new_dimensions(newDimensions);
  },

  /**
   * Hashes the html transform attribute
   * i.e. parseTransformAttr('translate(6,5),scale(3,3.5),a(1,1),b(2,23,-34),c(300)')
   *      RETURNS
   *      {
   *        translate: [ '6', '5' ],
   *        scale: [ '3', '3.5' ],
   *        a: [ '1', '1' ],
   *        b: [ '2', '23', '-34' ],
   *        c: [ '300' ]
   *      }
   */
  parseTransformAttr: function(attributes) {
    var b={};
    for (var i in attributes = attributes.match(/(\w+\((\-?\d+\.?\d*,?)+\))+/g)) // for all valid attributes (including negative and decimal)
    {
        var c = attributes[i].match(/[\w\.\-]+/g); // Split transform name and values into array
        b[c.shift()] = c; // First item is name, equal to array of values left
    }
    return b;
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

