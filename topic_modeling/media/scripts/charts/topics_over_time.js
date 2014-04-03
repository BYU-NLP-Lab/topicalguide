/**
 * Part of Topical Guide (c) BYU 2013
 */


/** The Info **/
var TopicsOverTimeInfo = InfoView.extend({

  initialize: function () {
    this.$el.hide();
  },

  clear: function () {
    this.$('tbody').empty();
  },

  view_plot: function () {
  },

  load_topic: function (tid, info) {
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


/** The Controls **/
var TopicsOverTimeControls = Backbone.View.extend({

  initialize: function (options) {
  },

  show: function () {
    this.$el.show();
  },

  hide: function () {
    this.$el.hide();
  }

});


/** The main visualization class
 *
 * Instance Variables:
 *   svg:      the $(svg) element
 *   maing:    the <g> element that you should add things too that are to be
 *             effected by the zoom object.
 *   zoom:     a zoom object for resizing your visualization
 *   options:  a dictionary of the {dict} passed in at initialization,
 *             extending the "defaults" dict
 *   info:     the info object
 *   menu:     the menu object
 *   controls: the controls object
 *
 * **/
var TopicsOverTimeViewer = MainView.add({
  name: 'topics_over_time',
  title: 'Topics Over Time',
  controls_class: TopicsOverTimeControls,
  info_class: TopicsOverTimeInfo,

  /** any defaults that you want. In the class, this.options will be populated
   * with these defaults + an options dictionary passed in when the object is
   * initialized **/
  defaults: {
  },

  /**
    return the url to grab your data (can be dependent on options)
    look in fancy.html (the template) to see what urls are available in the
    global URLS variable (and you can add your own to that object).
  **/
  url: function () {
    return URLS['documents']['metrics'];
  },


  /** setup the d3 layout, etc. Everything you can do without data **/
  setup_d3: function () {
  },

  /** populate everything! data is the JSON response from your url(). For
   * information on the return values of specific urls, look at the docs for
   * the function (probably in topic_modeling/visualize/topics/ajax.py)
   *
   * NOTE: this data is cached in localStorage unless you click "refresh" at
   * the bottom of the right-hand bar
   */
  load: function (data) {
    console.log(data);
  }

});

