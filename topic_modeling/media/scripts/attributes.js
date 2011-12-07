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

function update_list_contents(values_list) {
    var new_html = '';
    for (var i = 0; i < values_list.length; i++) {
    	var value = values_list[i].value;
    	var url = $.fn.attributes_url + '/' + $.fn.attribute + '/values/' + value;
    	
        new_html += '<li';
        if (value == $.fn.attrvalue) {
            new_html += ' class="selected"';
        }
        new_html += ' value="' + value + '"';
        new_html += '>';
        
        new_html += '<a href="' + url + '">';
        new_html += value + '</a></li>';
    }
    
    $("ul#sidebar-list").html(new_html);
}

function redraw_list_control(json_link) {
	$.getJSON(json_link, {}, function(data) {
		set_nav_arrows(data.page, data.num_pages);
		update_list_contents(data.values);
	});
}

function get_page(page, value) {
	var link = '/feeds/attribute-page/datasets/' + $.fn.dataset
            + '/analyses/' + $.fn.analysis
            + '/attributes/' + $.fn.attribute
            + '/number/' + page;
	redraw_list_control(link);
}
