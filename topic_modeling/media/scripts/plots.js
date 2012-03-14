var jqPlotCharts = {};
var legends;
var ticks;

function numerical_sort_function(a, b) {
	return (a - b)
}

function highlight_all_topic_attribute_values(refresh) {
	$("select#id_values").each(function() {
		$("select#id_values option").attr("selected", true);
	});
	if (refresh) {
		update_topic_attribute_plot()
	}
}

function update_topic_attribute_plot() {
	var url_base = "/feeds/topic-attribute-plot/";
	attribute = $("select#id_attribute").val();
	url_base += 'attributes/' + attribute + '/';
	// Now get selected values and make a list of them
	var selected = $("select#id_values").val();
	selected = selected.sort(numerical_sort_function);
	url_base += "values/" + selected[0];
	for ( var i = 1; i < selected.length; i++) {
		url_base += "." + selected[i];
	}
	url_base += "/topics";

	// Now get selected topics and make a list of them
	var selected = $("select#id_topics").val()
	url_base += '/';
	selected = selected.sort(numerical_sort_function)
	url_base += selected[0];
	for ( var i = 1; i < selected.length; i++) {
		url_base += "." + selected[i];
	}
	var added_query = false;
	if ($('#id_by_frequency:checked').val() != null) {
		url_base += "?frequency=true";
		added_query = true;
	}
	$("a#csv_data").attr("href", url_base + '?fmt=csv');
	url_base += '?fmt=json';
	added_query = true;
	if ($('#id_histogram:checked').val() != null) {
		if (!added_query) {
			url_base += '?';
		} else {
			url_base += '&';
		}
		url_base += "histogram=true";		
	}	
		
	get_chart(url_base, "main");
	
	
}

function update_plot(plot_name){
	var jqplotId = '#'+plot_name+'_jqplot';
	var containerId = jqplotId + '_container';
	var infoId = jqplotId + '_info';
	
	if(plot_name in jqPlotCharts) {
		jqPlotCharts[plot_name].replot( { resetAxes: true } );
	
		$(jqplotId).unbind('jqplotDataClick');
		$(jqplotId).bind('jqplotDataClick', function (ev, seriesIndex, pointIndex, data) {
			//console.log(legends[seriesIndex]+"idx:"+seriesIndex);
			//console.log(legends);
			//console.log("idx:"+seriesIndex);
			$(infoId).html(legends[seriesIndex].label+'<br/> ( '+ticks[pointIndex]+', '+parseFloat(data[1]).toFixed(5) +" )");
			$(infoId).offset({ top: $(jqplotId).offset().top + 20, left: $(jqplotId).offset().left + $(jqplotId).width() - $(infoId).width()-220 });
		 });
		$(infoId).offset({ top: $(jqplotId).offset().top + 20, left: $(jqplotId).offset().left + $(jqplotId).width() - $(infoId).width()-220 });
		var fontSize = '';
		containerWidth = $(containerId).width();
		if(containerWidth < 600){
			fontSize = '12px';
		}else if(containerWidth < 1000){
			fontSize = '14px';
		}else{
			fontSize = '18px';
		}	
		$(infoId).css("font-size", fontSize);
		//$('#jqplot_container').height($('.jqplot-table-legend').height());
		//console.log("container.height: "+$('#jqplot_container').height());
		//console.log("legends.height: "+$('.jqplot-table-legend').height());
	}
}

function get_chart(url, plot_name){
	
	var jqplotId = plot_name + "_jqplot";
	var histogram = 0;
	var uri = url.split('?');
	if(uri.length > 1){
		query = uri[1].split('&');
		for(var i = 0; i < query.length; i++){
			//console.log(query[i]);
			if(query[i].indexOf("histogram") != -1){
				histogram = 1;
			}
		}
	}
	
	$.getJSON(url, function(data) {
		// key is the data title
		// data[key] is the string
		var linedata = [];
		legends = [];
		ticks = data['x-data'].toString().split(',');
		
		$.each(data['y-data'], function(key, val) {
			legends.push({'label':key});
			tmp = data['y-data'][key].toString().split(',');
			var tmpline = [];
			$.each(tmp, function(index, value) {
				//console.log("idx:" + index + " cont:"+ticks[index]);
				tmpline.push(parseFloat(value));
			});
			linedata.push(tmpline);
		});
		var jqplot_options = {
			axes : {
				yaxis : {
					labelRenderer : $.jqplot.CanvasAxisLabelRenderer,
					label: "",
					labelOptions : {
						angle:-90
					},
					tickOptions : {
						formatString : '%.3f',						
					},
					min : 0
				},
				xaxis : {
					label: "",
					tickRenderer : $.jqplot.CanvasAxisTickRenderer,
					tickOptions : {
						angle : -90,
						fontSize : '10pt'
					},
					ticks : ticks,
					renderer : $.jqplot.CategoryAxisRenderer
				}
			},
			seriesDefaults : {
			},
			series : legends,
			legend : {
				show : true,
				placement: 'outsideGrid',
				location: 'ne',
			},
			cursor: {},
			highlighter: {}
		};
	
		jqplot_options.axes.xaxis.label = data['x-axis-label'];
		jqplot_options.axes.yaxis.label = data['y-axis-label'];
		
		if (histogram == 1) {
			jqplot_options.stackSeries = true;
			jqplot_options.seriesDefaults.renderer = $.jqplot.BarRenderer;
			jqplot_options.seriesDefaults.rendererOptions = [];
			jqplot_options.seriesDefaults.rendererOptions.push({'barMargin': 10, 'highlightMouseDown': true});
			jqplot_options.captureRightClick = true;
		}
		
		$('#'+jqplotId).html("");
		jqPlotCharts[plot_name] = $.jqplot(jqplotId, linedata, jqplot_options);
		update_plot(plot_name);
	});
}

/*
 * The 'analysis' argument is retained so the signature is the same as that of
 * update_topic_metric_plot
 */
function update_attribute_values(dataset, analysis) {
	attribute = $("select#id_attribute").val();
	$.getJSON("/feeds/attribute-values/datasets/" + dataset + "/attributes/"
			+ attribute, {}, function(j) {
		var options = '';
		for ( var i = 0; i < j.length; i++) {
			options += '<option value = "' + j[i][0] + '" selected="true">'
					+ j[i][1] + '</option>';
		}
		$("#id_values").html(options);
		update_topic_attribute_plot();
	})
}

function update_topic_metric_plot(dataset, analysis) {
	set_loading_image();
	var url_base = "/feeds/topic-metric-plot/datasets/" + dataset
			+ "/analyses/" + analysis + "/metrics/";
	first_metric = $("select#id_first_metric").val();
	url_base += first_metric;
	url_base += '.';
	second_metric = $("select#id_second_metric").val();
	url_base += second_metric;
	if ($('#id_linear_fit:checked').val() != null) {
		url_base += "?linear_fit=true";
	}

	// When the URL is ready, change the source of the
	// image to point to the correct one
	$("img#plot_image").attr("src", url_base);
}

// From http://www.stainlessvision.com/collapsible-box-jquery
function boxToggle(box) {
	// Get the first and highest heading (prioritising highest over first)
	var firstHeading = box.find("label")[0];
	var firstHeadingJq = $(firstHeading);

	// Select the heading's ancestors
	var headingAncestors = firstHeadingJq.parents();
	// Add in the heading
	var headingAncestors = headingAncestors.add(firstHeading);
	// Restrict the ancestors to the box
	headingAncestors = headingAncestors.not(box.parents());
	headingAncestors = headingAncestors.not(box);
	// Get the siblings of ancestors (uncle, great uncle, ...)
	var boxContents = headingAncestors.siblings();

	// *** TOGGLE FUNCTIONS ***
	var hideBox = function() {
		firstHeadingJq.one("click", function() {
			showBox();
			return false;
		})
		// toggleLink.text("Show")
		firstHeadingJq.attr("class", "box-toggle-show");

		boxContents.attr("style", "display:none");
	}

	var showBox = function() {
		firstHeadingJq.one("click", function() {
			hideBox();
			return false;
		})
		// toggleLink.text("Hide");
		firstHeadingJq.attr("class", "box-toggle-hide");

		boxContents.removeAttr("style");
	}

	// When the URL is ready, change the source of the
	// image to point to the correct one
	$("img#plot_image").attr("src", url_base);
}
