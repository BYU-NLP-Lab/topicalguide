$(document).ready(function (){
    bind_favorites();
});

/***** Utility Functions *****/
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

function slugify(text) {
    return text.toLowerCase()
	    .replace(/[^\w ]+/g,'')
	    .replace(/ +/g,'-')
	    .replace(/\//g, '-');
}

/***** Favorites *****/
function bind_favorites() {
	$("img.star:not(.inactive)").unbind('click').click(function() {
		toggle_favorite($(this));
	});
}

function toggle_favorite(fav) {
	var category = fav.attr("type");
	var favurl = fav.attr("favurl");
	
	if(fav.hasClass("fav")) {
		$.ajax({
			url: fav.attr("favurl"),
			type: 'DELETE',
			success: function() {
				fav.removeClass("fav");
				remove_favorite_from_menu(category, favurl);
			}
		});
	} else {
		$.ajax({
			url: fav.attr("favurl"),
			type: 'PUT',
			success: function() {
				fav.addClass("fav");
				var text = fav.attr("text");
				var url = fav.attr("url");
				add_favorite_to_menu(category, text, url, favurl);
			}
		});
	}
}

function add_favorite_to_menu(category, text, url, favurl) {
	var newFav = '<li class="favorite">';
	newFav += '<img class="star fav" favurl="' + favurl + '"/>';
	newFav += '<a href="' + url + '">' + text + '</a>';
	$("li#favorites > ul > li#" + category.toLowerCase() + " > ul").append(newFav);
	bind_favorites();
}

function remove_favorite_from_menu(category, favurl) {
	$("li#favorites > ul > li#" + category.toLowerCase() + " > ul > li.favorite").each(function() {
		$(this, " > img[favurl='" + favurl + "']").each(function(i,val){
			val.hide('slow', function(){ $(this).remove(); })
		});
	});
}

/***** Status Messages *****/
function infoMessage(text) {
	message(text, 'ui-state-highlight');
}

function errorMessage(text) {
	message(text, 'ui-state-error');
}

function message(text, klass) {
    if($("div#notification").length < 1) {
        //If the message div doesn't exist, create it
    	$("li#favorites").prepend('<div id="notification" style="float:right">' + text + '</div>');
    } else {
        //Else, update the text
        $("div#notification").html(text);
    }
    
    $("div#notification").removeClass().addClass(klass).click(function(){
    	$(this).hide();
    });
    
    //Fade message in
    $("li#favorites span#buttons").hide("slow");
    $("div#notification").show('slow');
    //Fade message out in 5 seconds
    setTimeout('$("div#notification").hide("slow")',5000);
    setTimeout('$("li#favorites span#buttons").show()',5000);
    
    $("div#notification").unbind('click');
}

