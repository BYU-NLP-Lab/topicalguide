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

function get_context_for_word(word)
{
	cursor_wait();
	var link = "/feeds/word-in-context/datasets/" + $.fn.topic_vars.dataset;
	link += "/analyses/" + $.fn.topic_vars.analysis;
	link += "/topics/" + $.fn.topic_vars.curtopic_number;
	link += "/words/" + word;
	$.getJSON(link, {}, function(word) {
		new_html = '';
		new_html += '<td class="doc-name"><a href="'+$.fn.topic_vars.baseurl+'/';
		new_html += $.fn.topic_vars.curtopic_number + '/documents/';
		new_html += word.doc_id;
		new_html += '">'+word.doc_name;
		new_html += '</a></td>';
		new_html += '<td class="right-align">';
		new_html += word.left_context;
		new_html += '</td><td class="word">';
		new_html += '<a href="'+$.fn.topic_vars.baseurl+'/';
		new_html += $.fn.topic_vars.curtopic_number;
		new_html += '/words/' + word.word;
		new_html += '">'+word.word+'</a></td>';
		new_html += '<td class="left-align">';
		new_html += word.right_context;
		new_html += '</td>';
		new_html += '<td id="id_new_context_';
		new_html += word.word + '" class="clickable_text">';
		new_html += '<img src="/site-media/stock_reload.png" border="0"/>';
		new_html += '</td>';
		$("#id_"+word.word).html(new_html);
		cursor_default();
	});
}
$(document).ready(function() {
	$("[id*='id_new_context_']").live('click', function() {
		var word = $(this).attr('id').substring(15);
		get_context_for_word(word);
	});
});
