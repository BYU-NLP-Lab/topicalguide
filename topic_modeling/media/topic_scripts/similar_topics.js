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

function get_similar_topics()
{
	cursor_wait();
	var link = "/feeds/similar-topics/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic_vars.curtopic_number;
	link += "/measures/" + $("#similarity-measure-select").val();
	$.getJSON(link, {}, function(data) {
		var base = $.fn.topics_url + "/";
		var topics = '';
		for (var i = 0; i < data.topics.length; i++) {
			topics += '<tr>';
			topics += '<td><a href="' + base + data.topics[i].number + '">';
			topics += data.topics[i].name + '</a></td>';
			topics += '<td class="value">'+data.values[i].toFixed(2)+'</td>';
			topics += '</tr>';
		}
		$("#similar-topics-table").html(topics);
		cursor_default();
	});
}
