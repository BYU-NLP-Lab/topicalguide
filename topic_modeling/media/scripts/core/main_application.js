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

$("a.new-window[href]").live(
    "click",
    function(event)
    {
        window.open($(this).attr("href"));
        event.preventDefault();
    }
);

function set_nav_arrows(current_page, num_pages) {
	$("div#list-nav > span#page-situation > span#current-page").html(current_page);
	$("div#list-nav > span#page-situation > span#page-count").html(num_pages);
	
	$("div#list-nav > span#back-arrows > a#first").unbind('click').click(function() {
		get_page(1);
	});
	$("div#list-nav > span#back-arrows > a#prev").unbind('click').click(function() {
		get_page(current_page-1);
	});
	$("div#list-nav > span#fwd-arrows > a#last").unbind('click').click(function() {
		get_page(num_pages);
	});
	$("div#list-nav > span#fwd-arrows > a#next").unbind('click').click(function() {
		get_page(current_page+1);
	});
	
	if (current_page == 1)
		$("div#list-nav > span#back-arrows").css("visibility", "hidden");
	else
		$("div#list-nav > span#back-arrows").css("visibility", "visible");
	
	if(current_page == num_pages)
		$("div#list-nav > span#fwd-arrows").css("visibility", "hidden");
	else
		$("div#list-nav > span#fwd-arrows").css("visibility", "visible");
}