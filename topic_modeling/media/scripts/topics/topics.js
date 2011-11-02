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

function slugify(text) {
    return text.toLowerCase()
	    .replace(/[^\w ]+/g,'')
	    .replace(/ +/g,'-')
	    .replace(/\//g, '-');
}

function favorite_this_view(name, favid) {
	var url = '/favs/topics/' + favid;
	var fullUrl = window.location.origin + url;
//	{"dataset":"state_of_the_union", "analysis":"lda100topics", "topic":10, "name":"The best topics"}
	var params = '{"dataset":"' + $.fn.dataset + '", "analysis":"' + $.fn.analysis + '", '
				  + '"topic":' + $.fn.topic.number + ', "name":"' + name + '"}';
	$.ajax({
		type:'PUT',
		url:url,
		data:params,
		success: function() {
			infoMessage('View now available at <a href="' + url + '">' + fullUrl + '</a>');
		},
		error: function() {
			errorMessage('View at ' + fullUrl + ' already exists');
		}
	});
}

function load_favorites() {
	$.getJSON($.fn.topics_url+'.favs', function(data){
		$("ul#sidebar-list img.star").each(function(){
			var img = $(this);
			var topicNum = parseInt(img.attr('topicnum'));
			if(data.indexOf(topicNum) != -1)
				img.addClass('fav');
		});
	});
}

function update_list_contents(topics_list) {
	var topic = $.fn.topic.number;
	var new_html = '';
	for (var i = 0; i < topics_list.length; i++) {
		new_html += '<li';
		if (topics_list[i].number == topic) {
			new_html += ' class="selected"';
		}
		new_html += '>';
		
		new_html += '<img class="star" topicnum="' + topics_list[i].number + '" favurl="' + $.fn.topics_url + '/' + topics_list[i].number + '/fav"/>';
		
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
	load_favorites();
	bind_favorites();
}

function redraw_list_control(json_link) {
	$.getJSON(json_link, {}, function(data) {
		$("div#sidebar table.filters").html(data.filter_form);
		bind_filters();
		set_nav_arrows(data.page, data.num_pages);
		update_list_contents(data.topics);
		cursor_default();
	});
}

function redraw_topics(json_link) {
	$.getJSON(json_link, {}, function(data) {
		$("div#sidebar table.filters").html(data.filter_form);
		bind_filters();
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
