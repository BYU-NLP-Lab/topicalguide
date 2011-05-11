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