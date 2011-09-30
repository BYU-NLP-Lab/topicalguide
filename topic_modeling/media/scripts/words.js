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

function update_list_contents(word_list, word) {
    var new_html = '';
    for (var i = 0; i < word_list.length; i++) {
        new_html += '<li';
        if (word_list[i].type == word) {
            new_html += ' class="selected"';
        }
        new_html += '>';
        new_html += '<a href="' + $.fn.words_url;
        new_html += '/' + word_list[i].type + '">';
        new_html += word_list[i].type + '</a></li>';
    }
    $("ul#sidebar-list").html(new_html);
}

function redraw_list_control(json_link, word) {
	$.getJSON(json_link, {}, function(data) {
		set_nav_arrows(data.page, data.num_pages);
		update_list_contents(data.words, word);
		cursor_default();
	});
}

function get_page(page, current_word) {
    cursor_wait();
    var link = '/feeds/word-page/datasets/' + $.fn.dataset
            + '/analyses/' + $.fn.analysis
            + '/number/' + page;
    redraw_list_control(link, current_word);
}
function find_word(current_word) {
    cursor_wait();
    var word_base = $("#id_find_word").val();
    var link = '/feeds/word-page-find/datasets/' + $.fn.dataset
            + '/analyses/' + $.fn.analysis
            + '/words/' + word_base;
    redraw_list_control(link, current_word);
}