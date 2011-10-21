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

function add_new_filter()
{
	cursor_wait();
	var link = "/feeds/new-topic-filter/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic.number;
	link += "/name/" + $("#id_filter").val();
	$.get(link, {}, function(filter) {
		$("div#sidebar table.filters").html(filter);
		cursor_default();
	});
}
function remove_filter(id)
{
	cursor_wait();
	var link = "/feeds/remove-topic-filter/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic.number;
	link += "/number/" + id;
	redraw_topics(link);/*
	$.getJSON(link, {}, function(data) {
		$("div#sidebar table.filters").html(data.filter_form);
		redraw_topics(data.topics, data.page, data.num_pages);
		cursor_default();
	});
	*/
}
function update_attr_filter_attribute(id)
{
	cursor_wait();
	var link = "/feeds/update-topic-attribute-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic.number;
	link += "/number/" + id;
	link += "/attributes/" + $("#id_attribute_filter_"+id).val();
	redraw_list_control(link);/*
	$.getJSON(link, {}, function(data) {
		$("div#sidebar table.filters").html(data.filter_form);
		redraw_topics(data.topics, data.page, data.num_pages);
		cursor_default();
	});*/
}
function update_attr_filter_value(id)
{
	cursor_wait();
	var link = "/feeds/update-topic-attribute-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic.number;
	link += "/number/" + id;
	link += "/attributes/" + $("#id_attribute_filter_"+id).val();
	link += "/values/" + $("#id_attribute_filter_value_"+id).val();
	redraw_list_control(link);/*
	$.getJSON(link, {}, function(data) {
		$("div#sidebar table.filters").html(data.filter_form);
		redraw_topics(data.topics, data.page, data.num_pages);
		cursor_default();
	});*/
}
function update_metric_filter_metric(id)
{
	cursor_wait();
	var link = "/feeds/update-topic-metric-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic.number;
	link += "/number/" + id;
	link += "/metrics/" + $("#id_metric_filter_"+id).val();
	redraw_list_control(link);/*
	$.getJSON(link, {}, function(data) {
		$("div#sidebar table.filters").html(data.filter_form);
		redraw_topics(data.topics, data.page, data.num_pages);
		cursor_default();
	});*/
}
function update_metric_filter(id)
{
	cursor_wait();
	var link = "/feeds/update-topic-metric-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic.number;
	link += "/number/" + id;
	link += "/metrics/" + $("#id_metric_filter_"+id).val();
	link += "/comps/" + $("#id_metric_filter_comp_"+id).val();
	link += "/values/" + $("#id_metric_filter_value_"+id).val();
	redraw_list_control(link);/*
	$.getJSON(link, {}, function(data) {
		$("div#sidebar table.filters").html(data.filter_form);
		redraw_topics(data.topics, data.page, data.num_pages);
		cursor_default();
	});*/
}
function update_document_filter_document(id)
{
	cursor_wait();
	var link = "/feeds/update-topic-document-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic.number;
	link += "/number/" + id;
	link += "/documents/" + $("#id_document_filter_"+id).val();
	redraw_list_control(link);/*
	$.getJSON(link, {}, function(data) {
		$("div#sidebar table.filters").html(data.filter_form);
		redraw_topics(data.topics, data.page, data.num_pages);
		cursor_default();
	});*/
}
function update_word_filter_word(id)
{
	cursor_wait();
	var link = "/feeds/update-topic-word-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/topics/" + $.fn.topic.number;
	link += "/number/" + id;
	link += "/words/" + $("#id_word_filter_"+id).val();
	redraw_list_control(link);/*
	$.getJSON(link, {}, function(data) {
		$("div#sidebar table.filters").html(data.filter_form);
		redraw_topics(data.topics, data.page, data.num_pages);
		cursor_default();
	});*/
}
