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

function redraw_values(values_list, page, num_pages) {
    var curvalue = $.fn.attr_vars.curvalue;
    var new_html = render_nav_arrows(page, num_pages, 'attribute');
    
    new_html += '<ul class="list centered" id="attribute_list_body">';
    for (var i = 0; i < values_list.length; i++) {
        new_html += '<li';
        if (values_list[i].value == curvalue) {
            new_html += ' class="highlight"';
        }
        new_html += '>';
        new_html += '<a href="' + $.fn.attr_vars.baseurl;
        new_html += '/' + $.fn.attr_vars.curattr;
        new_html += '/values/' + values_list[i].value + '">';
        new_html += values_list[i].value + '</a></li>';
    }
    new_html += '</ul>';
    
    $("#attributes_list").html(new_html);
}
function get_attribute_page(page) {
    $.getJSON('/feeds/attribute-page/datasets/'
            + $.fn.attr_vars.dataset
            + '/analyses/' + $.fn.attr_vars.analysis
            + '/attributes/' + $.fn.attr_vars.curattr
            + '/number/' + page,
            {}, function(data) {
            redraw_values(data.values, data.page, data.num_pages);
    });
}
