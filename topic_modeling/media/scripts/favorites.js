function redraw_values(values_list, page, num_pages) {
    var curvalue = $.fn.attr_vars.curr_favorite;

    var new_html = render_nav_arrows(page, num_pages, 'favorite');
    
    new_html += '<ul class="list centered" id="favorite_list_body">';
    for (var i = 0; i < values_list.length; i++) {
        new_html += '<li';
        if (values_list[i].id == curvalue) {
            new_html += ' class="highlight"';
        }
        new_html += '>';
        new_html += '<a href="/favorite';
        new_html += '/datasets/' + $.fn.attr_vars.dataset;
        new_html += '/analyses/' + $.fn.attr_vars.analysis;
        new_html += '/id/' + values_list[i].id + '">';
        new_html += values_list[i].name;
        new_html += '</a></li>';
    }
    new_html += '</ul>';

    $("#favorites_list").html(new_html);
}
function get_favorite_page(page) {
    cursor_wait();
    $.getJSON('/feeds/favorite-page/number/' + page,
        {}, function(data) {
        redraw_values(data.favorites, data.page, data.num_pages);
        cursor_default();
    });
}