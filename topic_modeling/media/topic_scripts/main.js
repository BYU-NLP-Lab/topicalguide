$(document).ready(function () {

$("div.top-level-widget-list li").click(function() {
	var title = $(this).text();
	$("div.top-level-widget:not(.hidden)").addClass("hidden");
	var this_widget = $("div.top-level-widget[title='"+title+"']");
	this_widget.removeClass("hidden");
});

$("div.lower-level-widget-list li").click(function() {
	var title = $(this).text();
	var top_level = $(this).parent().parent().parent();
	$("div.lower-level-widget:not(.hidden)", top_level).addClass("hidden");
	var this_widget = $("div.lower-level-widget[title='"+title+"']", top_level);
	this_widget.removeClass("hidden");
});


});
