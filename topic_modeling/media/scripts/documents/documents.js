function fix_tab_height() {
	$("#document_text").css('height', $(window).height()-160);
}

function tabify() {
	$("div#presentation-area div.tabs, div#presentation-area div.tabs .lower-tabs").tabs();
}

$(document).ready(function () {
	fix_tab_height();
	tabify();
	$(window).resize(function(){
        fix_tab_height();
    });
});
