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

function get_similar_documents() {
	cursor_wait();
	var link = "/feeds/similar-documents/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/documents/" + $.fn.doc_vars.document_id;
	link += "/measures/" + $("select#similarity_measure").val();
	$.getJSON(link, {}, function(data) {
		var base = $.fn.documents_url + "/";
		var documents = '';
		for (var i = 0; i < data.documents.length; i++) {
			documents += '<tr>';
			documents += '<td class="key"><a href="' + base;
			documents += data.documents[i].id + '">';
			documents += data.documents[i].name + '</a></td>';
			documents += '<td class="value">'+data.values[i].toFixed(2)+'</td>';
			documents += '</tr>\n';
		}
		$("table#similar-documents > tbody").html(documents);
		cursor_default();
	});
}