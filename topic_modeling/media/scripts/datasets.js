$(document).ready(function() {
    /*
    $("#accordion").accordion({autoHeight: false, collapsible: true, active: false})
                   .bind('accordionchange', function(event, ui) {
                      update_plot(ui.newHeader.attr('dataset_name'));
                   });
                   */
    

    //Event handlers
    $("a.explore").click(explore);
    $("img.plot").click(explore);
    $("select.analysis").change(load_plot_image);
    
    bind_favorites();
});

function explore() {
    var dataset = _dataset_node($(this));
    window.location.href = $("select.analysis > option:selected", dataset).attr("url");
}

function load_plot_image() {
    var dataset = _dataset_node($(this));
    var img = $("img.plot", dataset);
    var selected = $("select.analysis > option:selected", dataset);
    img.attr('src', selected.attr('img_url'));
}

function _dataset_node(element) {
    while(!element.attr('dataset')) {
        element = element.parent();
    }
    return element;
}
