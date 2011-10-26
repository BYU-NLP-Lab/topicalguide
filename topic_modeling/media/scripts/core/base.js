$(document).ready(function (){
    bind_favorites();
});

function cursor_wait() {
	document.body.style.cursor = 'wait';
}
function cursor_default() {
	document.body.style.cursor = 'default';
}
function set_name_scheme() {
    cursor_wait();
    var link = "/feeds/set-current-name-scheme/" + $("#namescheme-dropdown-select").val();
    $.get(link, {}, function() {
        cursor_default();
    });
    location.reload()
}

function bind_favorites() {
	$("img.star:not(.inactive)").click(function() {
		toggle_favorite($(this));
	});
}

function toggle_favorite(fav) {
	var type = fav.attr("type");
	var itemid = fav.attr("itemid");
	
	if(fav.hasClass("fav")) {
		fav.removeClass("fav");
		$.ajax({
			url: fav.attr("favurl"),
			type: 'DELETE'
		});
	} else {
		fav.addClass("fav");
		$.ajax({
			url: fav.attr("favurl"),
			type: 'PUT'
		});
	}
}