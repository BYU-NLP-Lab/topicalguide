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
	var link = "/feeds/new-document-filter/datasets/" + $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/documents/" + $.fn.doc.id;
	link += "/name/" + $("#id_filter").val();
	$.get(link, {}, function(filter) {
		$("#id_filter_form").html(filter);
		cursor_default();
	});
}
function remove_filter(id)
{
	cursor_wait();
	var link = "/feeds/remove-document-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/documents/" + $.fn.doc.id;
	link += "/number/" + id;
	$.getJSON(link, {}, function(data) {
		$("#id_filter_form").html(data.filter_form);
		redraw_documents(data.documents, data.page, data.num_pages);
		cursor_default();
	});
}
function update_attr_filter_attribute(id)
{
	cursor_wait();
	var link = "/feeds/update-document-attribute-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/documents/" + $.fn.doc.id;
	link += "/number/" + id;
	link += "/attributes/" + $("#id_attribute_filter_"+id).val();
	$.getJSON(link, {}, function(data) {
		$("#id_filter_form").html(data.filter_form);
		redraw_documents(data.documents, data.page, data.num_pages);
		cursor_default();
	});
}
function update_attr_filter_value(id)
{
	cursor_wait();
	var link = "/feeds/update-document-attribute-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/documents/" + $.fn.doc.id;
	link += "/number/" + id;
	link += "/attributes/" + $("#id_attribute_filter_"+id).val();
	link += "/values/" + $("#id_attribute_filter_value_"+id).val();
	$.getJSON(link, {}, function(data) {
		$("#id_filter_form").html(data.filter_form);
		redraw_documents(data.documents, data.page, data.num_pages);
		cursor_default();
	});
}
function update_metric_filter_metric(id)
{
	cursor_wait();
	var link = "/feeds/update-document-metric-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/documents/" + $.fn.doc.id;
	link += "/number/" + id;
	link += "/metrics/" + $("#id_metric_filter_"+id).val();
	$.getJSON(link, {}, function(data) {
		$("#id_filter_form").html(data.filter_form);
		redraw_documents(data.documents, data.page, data.num_pages);
		cursor_default();
	});
}
function update_metric_filter(id)
{
	cursor_wait();
	var link = "/feeds/update-document-metric-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/documents/" + $.fn.doc.id;
	link += "/number/" + id;
	link += "/metrics/" + $("#id_metric_filter_"+id).val();
	link += "/comps/" + $("#id_metric_filter_comp_"+id).val();
	link += "/values/" + $("#id_metric_filter_value_"+id).val();
	$.getJSON(link, {}, function(data) {
		$("#id_filter_form").html(data.filter_form);
		redraw_documents(data.documents, data.page, data.num_pages);
		cursor_default();
	});
}
function update_topic_filter(id)
{
	cursor_wait();
	var link = "/feeds/update-document-topic-filter/datasets/";
	link += $.fn.dataset;
	link += "/analyses/" + $.fn.analysis;
	link += "/documents/" + $.fn.doc.id;
	link += "/number/" + id;
	link += "/topics/" + $("#id_topic_filter_"+id).val();
	$.getJSON(link, {}, function(data) {
		$("#id_filter_form").html(data.filter_form);
		redraw_documents(data.documents, data.page, data.num_pages);
		cursor_default();
	});
}
