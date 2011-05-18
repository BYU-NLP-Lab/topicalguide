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

function redraw_documents(documents_list, page, num_pages) {
	var curdoc = $.fn.doc_vars.curdocument_id;
	
	var new_html = render_nav_arrows(page, num_pages, 'document');
	
	new_html += '<ul class="list" id="document_list_body">';
	for (var i = 0; i < documents_list.length; i++) {
		new_html += '<li';
		if (documents_list[i].id == curdoc) {
			new_html += ' class="highlight"';
		}
		new_html += '>';
		new_html += '<a href="' + $.fn.documents_url + '/';
		new_html += documents_list[i].id + '">';
		new_html += documents_list[i].name + '</a></li>';
	}
	new_html += '</ul>';
	
	$("#documents_list").html(new_html);
}
function get_document_page(page) {
	cursor_wait();
	var link = "/feeds/document-page/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/documents/" + $.fn.doc_vars.curdocument_id;
	link += "/number/" + page;
	$.getJSON(link, {}, function(data) {
		redraw_documents(data.documents, data.page, data.num_pages);
	});
	cursor_default();
}
function sort_documents() {
	cursor_wait();
	ordering = $("#id_sort").val();
	var link = "/feeds/document-ordering/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/order-by/" + ordering;
	$.getJSON(link, {}, function(data) {
		redraw_documents(data.documents, data.page, data.num_pages);
		cursor_default();
	});
}
