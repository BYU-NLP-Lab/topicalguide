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

function update_list_contents(topics_list) {
	var topic = $.fn.topic.number;
	var new_html = '';
	for (var i = 0; i < topics_list.length; i++) {
		new_html += '<li';
		if (topics_list[i].number == topic) {
			new_html += ' class="selected"';
		}
		new_html += '>';
		new_html += '<a href="' + $.fn.topics_url;
		new_html += '/' + topics_list[i].number;
		new_html += $.fn.topic.post_link;
		new_html += '">';
		new_html += topics_list[i].name;
        if (topics_list[i].topicgroup) {
          new_html += ' - GROUP</a></li>';
          for(var j = 0; j < topics_list[i].topicgroup.length; j++) {
              new_html += '<li>';
              new_html += topics_list[i].topicgroup[j];
              new_html += '</li>';
          }
        } else {
          new_html += '</a></li>';
        }
	}
	$("ul#sidebar-list").html(new_html);
}

function redraw_list_control(json_link) {
	$.getJSON(json_link, {}, function(data) {
		set_nav_arrows(data.page, data.num_pages);
		update_list_contents(data.topics);
		cursor_default();
	});
}

function get_page(page) {
	cursor_wait();
	var link = "/feeds/topic-page/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/number/" + page;
	redraw_list_control(link);
}
function sort_topics() {
	cursor_wait();
	ordering = $("#id_sort").val();
	var link = "/feeds/topic-ordering/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/order-by/" + ordering;
	redraw_list_control(link);
}
