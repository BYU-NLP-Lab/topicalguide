$(document).ready(function () {
	fix_tab_height();
	tabify();
	$(window).resize(function(){
        fix_tab_height();
    });
});

function fix_tab_height() {
	$("div#widget-document_text > div").css('height', $(window).height()-220);
}

function tabify() {
//	$("div#presentation-area div.tabs, div#presentation-area div.tabs .lower-tabs").tabs();
	$("div#tabs").tabs();
}

/***** Sidebar *****/
function update_list_contents(documents_list) {
	var curdoc = $.fn.doc.id;
	var new_html = '';
	for (var i = 0; i < documents_list.length; i++) {
		new_html += '<li';
		if (documents_list[i].id == curdoc) {
			new_html += ' class="selected"';
		}
		new_html += '>';
		new_html += '<a href="' + $.fn.documents_url + '/';
		new_html += documents_list[i].id + '">';
		new_html += documents_list[i].name + '</a></li>';
	}
	
	$("ul#sidebar-list").html(new_html);
}

function redraw_list_control(json_link) {
	$.getJSON(json_link, {}, function(data) {
		set_nav_arrows(data.page, data.num_pages);
		update_list_contents(data.documents);
		cursor_default();
	});
}

function get_page(page) {
	cursor_wait();
	var link = "/feeds/document-page/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/documents/" + $.fn.doc.id;
	link += "/number/" + page;
	redraw_list_control(link);
}

function sort_documents() {
	cursor_wait();
	ordering = $("#id_sort").val();
	var link = "/feeds/document-ordering/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/order-by/" + ordering;
	redraw_list_control(link);
}