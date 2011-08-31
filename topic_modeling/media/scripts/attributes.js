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

function update_list_contents(values_list, attribute, value) {
    var new_html = '';
    for (var i = 0; i < values_list.length; i++) {
        new_html += '<li';
        if (values_list[i].value == value) {
            new_html += ' class="selected"';
        }
        new_html += '>';
        new_html += '<a href="' + $.fn.attributes_url + "/";
        new_html += attribute;
        new_html += '/values/' + values_list[i].value + '">';
        new_html += values_list[i].value + '</a></li>';
    }
    
    $("ul#attributes-list").html(new_html);
}

function redraw_list_control(json_link, attribute, value) {
	$.getJSON(json_link, {}, function(data) {
		set_nav_arrows(data.page, data.num_pages);
		update_list_contents(data.values, attribute, value);
	});
}

function get_page(page, attribute, value) {
	var link = '/feeds/attribute-page/datasets/' + $.fn.dataset
            + '/analyses/' + $.fn.analysis
            + '/attributes/' + attribute
            + '/number/' + page;
	redraw_list_control(link, attribute, value);
}
