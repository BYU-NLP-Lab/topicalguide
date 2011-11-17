/*
 * The Topical Guide
 * Copyright 2010-2011 Brigham Young University
 * 
 * This file is part of the Topical Guide <http://nlp.cs.byu.edu/topic_browser>.
 * 
 * The Topical Guide is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.
 * 
 * The Topical Guide is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
 * License for more details.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with the Topical Guide.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * If you have inquiries regarding any further use of the Topical Guide, please
 * contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
 * Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.
 */

function get_top_attribute_values()
{
	cursor_wait();
	var link = "/feeds/attrvaltopic/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic.number;
	link += "/attributes/" + $("#id_attribute").val();
	link += "/order-by/" + $("input:radio[name=ordering]:checked").val();
	$.getJSON(link, {}, function(data) {
		var base = $.fn.analysis_url + '/';
		values = '';
		for (var i = 0; i < data.values.length; i++) {
			values += '<tr>';
			values += '<td><a href="' + base + 'attributes/' +
			data.attribute + '/values/' + data.values[i].value +
			'">' + data.values[i].value + '</a></td>';
			values += '<td>'+data.values[i].count+'</td>';
			values += '<td>'+data.values[i].percent.toFixed(2)+'</td>';
			values += '</tr>';
		}
		$("#attr_values_body").html(values);
		cursor_default();
	});
}
