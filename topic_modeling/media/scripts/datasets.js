$(document).ready(function() {
    $("#accordion").accordion({autoHeight: false});
//    $(".dataset-sections").accordion({collapsible: true,autoHeight: false});
    $("button.explore").button().click(explore);
    $("img.plot").click(explore);
    
    $("select#analysis").select(function(){
    	
    });
    
    //image_preview();
    $(".analysis-link").click(function(){
        $("html").hide("fade", {}, 250);
    });
    bind_favorites();
});

function explore() {
	window.location.href = $("select#analysis > option:selected").attr("url");
}

function load_plot_image() {
	$("select#analysis > option:selected").attr("img_url")
}