/*
 * The Topic Browser
 * Copyright 2010-2011 Brigham Young University
 * 
 * This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
 * 
 * The Topic Browser is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.
 * 
 * The Topic Browser is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
 * License for more details.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * If you have inquiries regarding any further use of the Topic Browser, please
 * contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
 * Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.
 */

function update_list_contents(documents_list) {
	var curdoc = $.fn.doc_vars.document_id;
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
	
	$("ul#documents-list").html(new_html);
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
	link += "/documents/" + $.fn.doc_vars.document_id;
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