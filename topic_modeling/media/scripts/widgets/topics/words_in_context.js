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

function update_word_context(word) {
	var lc_word = word.toLowerCase();
	var link = "/feeds/word-in-context/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic.number;
	link += "/words/" + word;
	$.getJSON(link, {}, function(word) {
		var row = $("tr[word="+lc_word+"]");
		var docTd = $('td.document', row);
		var docLink = $('a', docTd);
		var href = $.fn.topics_url + '/' + $.fn.topic.number + '/documents/' + word.doc_id;
		docLink.attr("href", href);
		
		var docImg = $('img', docTd);
		var title = "Source Document: " + word.doc_name;
		docImg.attr("title", title);
		
		var lcontextTd = $("td.lcontext", row);
		lcontextTd.text(word.left_context);
		
		var wordTd = $("td.word", row);
		var wordLink = $("a", wordTd);
		var wordHref = $.fn.topics_url + '/' + $.fn.topic.number + '/words/' + lc_word;
		wordLink.attr("href", wordHref);
		wordLink.text(word.word);
		
		var rcontextTd = $("td.rcontext", row);
		rcontextTd.text(word.right_context);
	});
}