$(document).ready(function (){
    bind_favorites();
});

$.fn.favs = new Array();
$.fn.fav_handlers = _default_handlers();

function _default_fav_handler() {
	var handler = new Object();
	handler.fav = function(){}
	handler.unfav = function(){}
	handler.fav_succeeded = function(){}
	handler.fav_failed = function(){}
	handler.unfav_succeeded = function(){}
	handler.unfav_failed = function(){}
	return handler;
}

function _default_handlers() {
	var handlers = [];
	$.fn.fav_handlers = handlers;
	
	var classHandler = _default_fav_handler();
	classHandler.fav_succeeded = function(favElement) {
		favElement.addClass('fav');
	};
	classHandler.unfav_succeeded = function(favElement) {
		favElement.removeClass('fav');
	};
	handlers.push(classHandler);
	
	var ajaxHandler = _default_fav_handler();
	ajaxHandler.fav = function(favElement) {
		$.ajax({
			url: favElement.attr("favurl"),
			type: 'PUT',
			success: function() {
				fav_succeeded(favElement);
			}
		});
	};
	ajaxHandler.unfav = function(favElement) {
		$.ajax({
			url: favElement.attr("favurl"),
			type: 'DELETE',
			success: function() {
				unfav_succeeded(favElement);
			}
		});
	};
	handlers.push(ajaxHandler);
	
	var menuHandler = _default_fav_handler();
	menuHandler.fav_succeeded = function(favElement) {
		var type = favElement.attr("type");
		var text = favElement.attr("text");
		var url = favElement.attr("url");
		var favurl = favElement.attr("favurl");
		add_favorite_to_menu(type, text, url, favurl);
	}
	menuHandler.unfav_succeeded = function(favElement) {
		var type = favElement.attr("type");
		var favurl = favElement.attr("favurl");
		remove_favorite_from_menu(type, favurl);
	}
	handlers.push(menuHandler);
	return handlers;
}

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
	$("img.star:not(.inactive)").each(function() {
		var jqobj = $(this);
		register_favorite(jqobj.attr("favurl"), this);
		jqobj.unbind('click').click(function() {
			toggle_fav($(this));
		});
	});
}

function register_favorite(favurl, favElement) {
	$.fn.favs[favurl] = favElement;
}

function add_fav_handler(handler) {
	$.fn.fav_handlers.add(handler);
}

function fav(favElement) {
	for(var i = 0; i < $.fn.fav_handlers.length; i++) {
		$.fn.fav_handlers[i].fav(favElement);
	}
}

function fav_succeeded(favElement) {
	for(var i = 0; i < $.fn.fav_handlers.length; i++) {
		$.fn.fav_handlers[i].fav_succeeded(favElement);
	}
}

function fav_failed(favElement) {
	for(var i = 0; i < $.fn.fav_handlers.length; i++) {
		$.fn.fav_handlers[i].fav_failed(favElement);
	}
}

function unfav(favElement) {
	for(var i = 0; i < $.fn.fav_handlers.length; i++) {
		$.fn.fav_handlers[i].unfav(favElement);
	}
}

function unfav_succeeded(favElement) {
	for(var i = 0; i < $.fn.fav_handlers.length; i++) {
		$.fn.fav_handlers[i].unfav_succeeded(favElement);
	}
}

function unfav_failed(favElement) {
	for(var i = 0; i < $.fn.fav_handlers.length; i++) {
		$.fn.fav_handlers[i].unfav_failed(favElement);
	}
}

function toggle_fav(favElement) {
	if(favElement.hasClass("fav"))
		unfav(favElement);
	else
		fav(favElement);
}

function add_favorite_to_menu(category, text, url, favurl) {
	var newFav = '<li class="favorite">';
	newFav += '<img class="star fav" url="' + url + '" favurl="' + favurl + '" type="' + category + '" text="' + text + '"/>';
	newFav += '<a href="' + url + '">' + text + '</a>';
	
	var ul = $("ul#entities");
	var li = $("> li.entity#" + category.toLowerCase(), ul);
	if(li.length == 0) {
		var newLi = '<li id="' + category.toLowerCase() + '" class="entity">';
		newLi += '<a class="entity-type">' + _title_case(category) + '</a>';
		newLi += '<ul></ul>';
		newLi += '</li>';
		ul.append(newLi);
		li = $("> li.entity#" + category.toLowerCase(), ul);
	}
	
	$(" > ul", li).append(newFav);
	bind_favorites();
}

function _title_case(s) {
	return s.charAt(0).toUpperCase() + s.substr(1);
}

function remove_favorite_from_menu(category, favurl) {
	var entityLi = $("ul#entities > li#" + category.toLowerCase());
	var items = $(" > ul > li.favorite", entityLi);
	var total = items.length;
	items.each(function() {
		if($(" > img[favurl='" + favurl + "']", this).length > 0) {
			var hideMe = total > 1 ? $(this) : entityLi;
			hideMe.hide('slow', function(){ hideMe.remove(); });
		}
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

