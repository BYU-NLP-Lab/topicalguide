
/*
//$(document).ready(function () {
  console.log("Flag2");
  var main = $('#main');
  var sidebar = $('#right-bar');
  console.log(main);
  console.log(sidebar);
  console.log("document: " + $(document).width() + " " + $(document).height());
  console.log("window: " + $(window).width() + " " + $(window).height());
  //we are going to be limited by height
  //establish a hard minimum
  //do we need to check width at all?
  var window_height = $(window).height();
  var vis_height = window_height - 100;
  if(vis_height < 630)
    vis_height = 630;

  //fixed width sidebar
  var sidebar_width = 300;
  console.log(vis_height);

  main.attr('height', vis_height);
  main.attr('width', vis_height);
  sidebar.attr('height', vis_height);
  sidebar.attr('width', sidebar_width);
  
//});
*/

var app = new MainView();

