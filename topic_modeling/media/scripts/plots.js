function numerical_sort_function(a,b) {
  return (a - b)
}

function highlight_all_topic_attribute_values(refresh) {
    $("select#id_values").each(function() {
        $("select#id_values option").attr("selected", true);
        });
    if(refresh) {
        update_topic_attribute_plot()
    }
}

function update_topic_attribute_plot() {
    set_loading_image();
    var plot_url_base = "/feeds/topic-attribute-plot/";
    var csv_url_base = "/feeds/topic-attribute-csv/";
    var url_path = "";
    attribute = $("select#id_attribute").val();
    url_path += 'attributes/'+attribute+'/';
    
    if ($("select#id_topics").val() == null) {
        $("select#id_topics option:first").attr("selected", true);
    }
    if ($("select#id_values").val() == null) {
        highlight_all_topic_attribute_values(0);
    }
   
    // Now get selected values and make a list of them 
    var selected = $("select#id_values").val();
    selected = selected.sort(numerical_sort_function);
    url_path += "values/" + selected[0];
    for (var i = 1; i < selected.length; i++) {
        url_path += "." + selected[i];
    }
    url_path += "/topics";

    // Now get selected topics and make a list of them 
    var selected = $("select#id_topics").val()
    url_path += '/';
    selected = selected.sort(numerical_sort_function)
    url_path += selected[0];
    for (var i = 1; i < selected.length; i++) {
        url_path += "." + selected[i];
    }
    var added_query = false;
    if ($('#id_by_frequency:checked').val() != null) {
        url_path += "?frequency=true";
        added_query = true;
    }
    if ($('#id_histogram:checked').val() != null) {
        if (!added_query) {
            url_path += '?';
        } else {
            url_path += '&';
        }
        url_path += "histogram=true";
    }
    // When  the URL is ready, change the source of the
    // image to point to the correct one
    $("img#plot_image").attr("src", plot_url_base + url_path);
    $("a#csv_data").attr("href", csv_url_base + url_path);
}

/* The 'analysis' argument is retained so the signature is the same as that of update_topic_metric_plot */
function update_attribute_values(dataset, analysis){
    attribute = $("select#id_attribute").val();
    $.getJSON("/feeds/attribute-values/datasets/"+dataset+"/attributes/"
            + attribute, {}, function(j) {
        var options = '';
        for (var i = 0; i < j.length; i++) {
            options += '<option value = "' + j[i][0] + '" selected="true">' +
            j[i][1] + '</option>';
        }
        $("#id_values").html(options);
        update_topic_attribute_plot();
    })
}

function update_topic_metric_plot(dataset, analysis) {
    set_loading_image();
    var url_base = "/feeds/topic-metric-plot/datasets/"+dataset+"/analyses/"+
        analysis+"/metrics/";
    first_metric = $("select#id_first_metric").val();
    url_base += first_metric;
    url_base += '.';
    second_metric = $("select#id_second_metric").val();
    url_base += second_metric;
    if ($('#id_linear_fit:checked').val() != null) {
        url_base += "?linear_fit=true";
    }

    // When  the URL is ready, change the source of the
    // image to point to the correct one
    $("img#plot_image").attr("src", url_base);
}

//From http://www.stainlessvision.com/collapsible-box-jquery
function boxToggle(box) {
	// Get the first and highest heading (prioritising highest over first)
	var firstHeading = box.find("label")[0];
	var firstHeadingJq = $(firstHeading);
	
	// Select the heading's ancestors
	var headingAncestors = firstHeadingJq.parents();
	// Add in the heading
	var headingAncestors  = headingAncestors.add(firstHeading);
	// Restrict the ancestors to the box
	headingAncestors = headingAncestors.not(box.parents());
	headingAncestors = headingAncestors.not(box);
	// Get the siblings of ancestors (uncle, great uncle, ...)
	var boxContents = headingAncestors.siblings();

	// *** TOGGLE FUNCTIONS ***
	var hideBox = function() {
		firstHeadingJq.one("click", function(){
			showBox();
			return false;
		})
		//toggleLink.text("Show")
		firstHeadingJq.attr("class", "box-toggle-show");

		boxContents.attr("style", "display:none");
	}

	var showBox = function() {
		firstHeadingJq.one("click", function(){
			hideBox();
			return false;
		})
		//toggleLink.text("Hide");
		firstHeadingJq.attr("class", "box-toggle-hide");

		boxContents.removeAttr("style");
	}

	// Initiate
	hideBox();
}