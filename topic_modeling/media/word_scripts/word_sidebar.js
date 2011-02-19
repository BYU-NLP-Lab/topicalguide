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

function redraw_words(word_list, page, num_pages) {
    var curword = $.fn.word_vars.curword;
    var new_html = render_nav_arrows(page, num_pages, 'word');
    
    new_html += '<ul class="list centered" id="word_list_body">';
    for (var i = 0; i < word_list.length; i++) {
        new_html += '<li';
        if (word_list[i].type == curword) {
            new_html += ' class="highlight"';
        }
        new_html += '>';
        new_html += '<a href="' + $.fn.words_url;
        new_html += '/' + word_list[i].type + '">';
        new_html += word_list[i].type + '</a></li>';
    }
    new_html += '</ul>';
    $("#word_list").html(new_html);
}
function get_word_page(page) {
    cursor_wait();
    $.getJSON('/feeds/word-page/datasets/' + $.fn.dataset
            + '/analyses/' + $.fn.analysis
            + '/number/' + page,
            {}, function(data) {
            redraw_words(data.words, data.page, data.num_pages);
            cursor_default();
    });
}
function find_word() {
    cursor_wait();
    word_base = document.getElementById("id_find_word").value;
    $.getJSON('/feeds/word-page-find/datasets/' + $.fn.dataset
            + '/analyses/' + $.fn.analysis
            + '/words/' + word_base,
            {}, function(data) {
            redraw_words(data.words, data.page, data.num_pages);
            cursor_default();
    }); 
}
