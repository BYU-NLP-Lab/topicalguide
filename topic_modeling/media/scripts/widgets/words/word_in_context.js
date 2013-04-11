/*
 * The Topical Guide
 * Copyright 2010-2011 Brigham Young University
 * 
 * This file is part of the Topical Guide <http://nlp.cs.byu.edu/topic_browser>.
 * 
 * The Topical Guide is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.
 * 
 * The Topical Guide is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
 * License for more details.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with the Topical Guide.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * If you have inquiries regarding any further use of the Topical Guide, please
 * contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
 * Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.
 */

function get_context_for_word(word, num) {
	cursor_wait();
	var link = "/feeds/word-in-context/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
    if(typeof $.fn.topic != "undefined") {
        link += "/topics/" + $.fn.topic.number;
    }
	link += "/words/" + word;
	$.getJSON(link, {}, function(word) {
		var lc_word = word.word.toLowerCase();
		new_html = '';
        new_html += '<td class="document"><a href="' + $.fn.documents_url + '/';
		new_html += word.doc_id;
		new_html += '"><img src="/site-media/images/tango/22x22/mimetypes/text-x-generic.png" title="Source Document: ';
		new_html += word.doc_name;
		new_html += '"/></a></td>';
		new_html += '<td class="lcontext">';
		new_html += word.left_context;
		new_html += '</td><td class="word">';
//<<<<<<< HEAD
      /*  new_html += '<a href="' + $.fn.words_url + '/';
        new_html += lc_word;
		new_html += '">'+word.word+'</a></td>';
    */
		new_html += word.word+'</td>';
//=======
/*
        new_html += '<a href="' + $.fn.words_url + '/';
        new_html += lc_word;
		new_html += '">'+word.word+'</a></td>';
  */
//>>>>>>> f8dd438e98e3b38aafd2dff38157010037ca6a96
		new_html += '<td class="rcontext">';
		new_html += word.right_context;
		new_html += '</td>';
		new_html += '<td id="id_new_context_';
		new_html += lc_word + "_" + num + '" class="reload">';
		new_html += '<img src="/site-media/images/tango/22x22/actions/view-refresh.png" title="Load New Context" border="0"/>';
		new_html += '</td>';
		$('tr[word="'+lc_word+'"][position='+num+']').html(new_html);
		cursor_default();
	});
}

function update_word_context(word, position) {
	var lc_word = word.toLowerCase();
	var link = "/feeds/word-in-context/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	if(typeof $.fn.topic != "undefined") {
        link += "/topics/" + $.fn.topic.number;
    }
	link += "/words/" + word;
	$.getJSON(link, {}, function(word) {
		var row = $('tr[word="'+lc_word+'"][position='+position+']');
		var docTd = $('td.document', row);
		var docLink = $('a', docTd);
		var docHref = $.fn.documents_url + '/' + word.doc_id;
		docLink.attr("href", docHref);
		
		var docImg = $('img', docTd);
		var title = "Source Document: " + word.doc_name;
		docImg.attr("title", title);
		
		var lcontextTd = $("td.lcontext", row);
		lcontextTd.text(word.left_context);
		
		var wordTd = $("td.word", row);
		var wordLink = $("a", wordTd);
		var wordHref = $.fn.words_url + '/' + lc_word;
		wordLink.attr("href", wordHref);
		wordLink.text(word.word);
		
		var rcontextTd = $("td.rcontext", row);
		rcontextTd.text(word.right_context);
	});
}

$(document).ready(function() {
	$("td.reload").live('click', function() {
		var row = $(this).parent();
		var word = row.attr("word");
		var position = row.attr("position");
		update_word_context(word, position);
	});
});
