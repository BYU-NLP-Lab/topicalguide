/*
 * The following are an assortment of useful utilities.
 */


/*
 * Maps datasets => dataset, analyses => analysis, etc. for just the common terms for this site.
 */
function makeSingular(word) {
    if(word === "analyses") return "analysis";
    else return word.slice(0, word.length - 1)
}

/*
 * Return a string in title case.
 */
function toTitleCase(str) {
    return str.replace(/\w\S*/g, function(substr){ return substr.charAt(0).toUpperCase() + substr.slice(1); });
}

/*
 * Parse url arguments to a hash.
 */
function urlToHash(args) {
    var hash = {};
    var items = args.split('&');
    if(items[0] !== "") {
        for(i=0; i<items.length; i++) {
            var keyAndValue = items[i].split('=');
            if(keyAndValue[1]===undefined) keyAndValue.push("");
            hash[decodeURIComponent(keyAndValue[0])] = decodeURIComponent(keyAndValue[1]);
        }
    }
    return hash;
}

/*
 * Convert a hash to url arguments, url will be normalized.
 * hash - Any valid hash with strings, arrays, and numbers as the values.
 */
function hashToUrl(hash) {
    function normalize(item){
        if(item instanceof String) {
            return encodeURIComponent(item);
        } else if(item instanceof Array) {
            item = item.slice(0); // Clone the array.
            item.sort();
            for(i=0; i<item.length; i++) {
                item[0] = normalize(item[0]);
            }
            return item.join(",");
        } else {
            return encodeURIComponent(item.toString());
        }
    };
    var keys = [];
    _.forOwn(hash, function(value, key) { keys.push(key); });
    keys.sort();
    var items = [];
    _.forEach(keys, function(key) {
        items.push(encodeURIComponent(key) + '=' + normalize(hash[key]));
    });
    return items.join('&');
}

/*
 * Return true if local storage is enabled.
 */
function hasLocalStorage() {
    try {
        localStorage["storage-test"] = "test";
        delete localStorage["storage-test"];
        return true;
    } catch(e) {
        return false;
    }
}

/*
 * Remove every item from the hash where the key starts with the prefix.
 */
function deletePrefixFromHash(prefix, hash) {
    var len = prefix.length;
    for(key in hash) {
        if(key.slice(0, len) === prefix) {
            delete hash[key];
        }
    }
}

/*
 * Return true if session storage is enabled.
 */
function hasSessionStorage() {
    try {
        sessionStorage["storage-test"] = "test";
        delete sessionStorage["storage-test"];
        return true;
    } catch(e) {
        return false;
    }
}

// Helper function to pull out information such as readable_name, description, and anything else
function extractMetadata(hash, metadata, defaults) {
    for(key in defaults) {
        if(key in metadata) {
            hash[key] = metadata[key];
            delete metadata[key];
        } else {
            hash[key] = defaults[key];
        }
    }
}

/*
 * Convenience method to extract documents.
 * data - The data returned by the server in the form of hashes and arrays.
 * [model] - The selection model, defaults to the global selection model if not provided.
 */
function extractDocuments(data, model) {
    if(model === undefined) {
        return data.datasets[globalSelectionModel.get("dataset")].analyses[globalSelectionModel.get("analysis")].documents;
    } else {
        return data.datasets[model.get("dataset")].analyses[model.get("analysis")].documents;
    }
}

/*
 * Convenience method to extract topics.
 * data - The data returned by the server in the form of hashes and arrays.
 * [model] - The selection model, defaults to the global selection model if not provided.
 */
function extractTopics(data, model) {
    if(model === undefined) {
        return data.datasets[globalSelectionModel.get("dataset")].analyses[globalSelectionModel.get("analysis")].topics;
    } else {
        return data.datasets[model.get("dataset")].analyses[model.get("analysis")].topics;
    }
}

/*
 * Create a sortable table.
 * table - A d3 selection of just the table element, it should be empty.
 * options - A hash/object specifying options as follows:
 * header - The titles at the top of the columns.
 * data - The data in the format of an array of arrays, all atomic elements must be numbers or strings.
 *        Must be a d3 array object.
 * rowOnClick - Function specifying the action if a row is clicked on.
 *              e.g. function(d, i) { } where d is an inner array.
 * onClick - Maps columns to click functions with the argument being the inner array as the inner array (not element of inner array).
 * onSort - Function called when a column is sorted.
 *          e.g. function(column, ascending) where column is an index into the header array and ascending is a boolean.
 * bars - Indicates the rows to display with percentage bars.
 * percentages - Indicates which rows should be displayed as percentages.
 * favicon - If specified it is an array of length 3 e.g. [indexOfFavsColumn, "datasets", view object].
 * sortBy - The column to sort by on creation.
 * sortAscending - How to sort the column, true for ascending, false for descending.
 * Return nothing.
 */
function createSortableTable(table, options) {
    var defaults = {
        header: [],
        data: [],
        rowOnClick: false,
        onSort: false,
        onClick: {},
        bars: [],
        percentages: [],
        favicon: false,
        sortBy: 0,
        sortAscending: true,
    };
    options = _.extend(defaults, options);
    // Find all of the maxes.
    var maxes = {};
    for(i=0; i<options.bars.length; i++) {
        var index = options.bars[i];
        maxes[index] = options.data.reduce(function(p, c, i, a) { 
            return (p > c[index])?p:c[index]; 
        }, 0);
    }
    // Turn percentages to array.
    var percent = {};
    for(i=0; i<options.percentages.length; i++) {
        percent[options.percentages[i].toString()] = null;
    }
    
    // Sort functions where i is the column to sort by.
    var makeSortAscending = function(i) {
        var sortAscending = function(a, b) {
            if($.isNumeric(a[i]) && $.isNumeric(b[i])) return parseFloat(a[i]) - parseFloat(b[i]);
            else return a[i].localeCompare(b[i]);
        };
        return sortAscending;
    }
    var makeSortDescending = function(i) {
        var sortAscending = makeSortAscending(i);
        var sortDescending = function(a, b) { return sortAscending(b, a); };
        return sortDescending;
    }
    
    // Variables for sorting.
    var ascending = options.sortAscending;
    var lastColumn = options.sortBy;
    // Create column headers with sort icons.
    var headerRow = table.append("thead")
        .append("tr").selectAll("th")
        .data(options.header)
        .enter()
        .append("th")
        .append("a")
        .style("cursor", "pointer")
        .on("click", function(d, i) {
            // On click sort the table.
            if(lastColumn !== i) ascending = true;
            lastColumn = i;
            if(ascending) {
                ascending = false;
                tableRows.sort(makeSortAscending(i));
            } else {
                ascending = true;
                tableRows.sort(makeSortDescending(i)); 
            }
            if(options.onSort) {
                options.onSort(i, !ascending);
            }
        })
        .classed({ "nounderline": true })
        .style("white-space", "nowrap")
        .text(function(title) { return title+" "; });
    headerRow.filter(function(d, i) { return !options.favicon || (options.favicon && i!==options.favicon[0]); })
        .append("span")
        .classed({"glyphicon": true, "glyphicon-sort": true});
    
    // Create tr entries.
    var tableRows = table.append("tbody")
        .selectAll("tr")
        .data(options.data)
        .enter()
        .append("tr");
    // Specify action on row click.
    if(options.rowOnClick) {
        tableRows.on("click", options.rowOnClick).style("cursor", "pointer");
    }
    // Create td entries
    tableRows.each(function(rowData, index) {
        var row = d3.select(this);
        var td = row.selectAll("td")
            .data(rowData)
            .enter()
            .append("td");
        // Fill in table values
        td.filter(function(d, i) { return (i in maxes)?false:true; })
            .append("a")
            .style("color", "black")
            .classed("nounderline", true)
            .text(function(d) { return d; })
            .each(function(d, i) {
                if(options.favicon && i === options.favicon[0]) {
                    createFavsIcon(d3.select(this), options.favicon[1], d.toString(), options.favicon[2]);
                }
            });
        td.each(function(d, i) { 
            var el = d3.select(this);
            if(i in options.onClick) {
                el.style("cursor", "pointer")
                    .on("click", function() { return options.onClick[i](rowData, index); });
            }
        });
            
        // Create the percentage bars.
        for(key in maxes) {
            var maxIndex = parseFloat(key);
            var max = maxes[key];
            var column = td.filter(function(d, i) { return (i === maxIndex)?true:false; });
            var svg = column.append("svg")
                .attr("width", 60)
                .attr("height", "1em");
            // Create bar.
            svg.append("rect")
                .attr("height", "100%")
                .attr("width", "100%")
                .attr("fill", "blue");
            // Fill in part of bar with whitesmoke.
            svg.append("rect")
                .attr("height", "100%")
                .attr("width", function(d) {
                    if(max === 0) return 60;
                    else return (1-(d/max)) * 60;
                })
                .attr("fill", "whitesmoke");
            // Append text.
            column.append("span")
                .text(function(d) {
                    if(maxIndex.toString() in percent) return " "+d.toFixed(2)+"%";
                    else return " "+d;
                })
                .attr("fill", "black")
                .attr("padding-left", "5px");
        }
    });
    
    // Set initial sort.
    if(ascending) {
        tableRows.sort(makeSortAscending(lastColumn));
    } else {
        tableRows.sort(makeSortDescending(lastColumn));
    }
    ascending = !ascending;
};

/*
 * Create tabbed content.
 * container - A d3 selection of the container to opperate in.
 * options - A hash with the options.
 * 
 * tabs - A hash mapping the tab name to a function. The function will be called
 *        when the corresponding tab is clicked.  The function must be of the form
 *        function(key, container) where key is the key in tabs and container is
 *        a d3 element to render content in.
 * selected - The tab to be active first.
 * tabOnClick - A function called when a tab is clicked, the function is passed the label of the tab.
 */
function createTabbedContent(container, options) {
    var defaults = {
        tabs: {},
        selected: null,
        tabOnClick: function() {},
    };
    options = _.extend(defaults, options);
    
    container.html("<ul role=\"tablist\" class=\"nav nav-tabs\"></ul>"+
                   "<div class=\"tab-content\"></div>");
    // Make sure a tab is selected to begin with.
    if(!(options.selected in options.tabs)) {
        for(key in options.tabs) {
            options.selected = key;
            break;
        }
    }
    
    // Active function, return true if the tab is the one selected.
    var active = function(d, i) { 
        if(d.key === options.selected) {
            return true;
        } else {
            return false;
        }
    };
    
    // Set up the content
    var content = container.select("div.tab-content");
    var contentPanes = content.selectAll("div.tab-pane");
    contentPanes.data(d3.entries(options.tabs))
        .enter()
        .append("div")
        .classed("tab-pane", true)
        .classed("active", active)
        .each(function(d, i) { options.tabs[d.key](d.key, d3.select(this)); });
    
    // Set up tabbed navigation
    var nav = container.select("ul.nav-tabs");
    var li = nav.selectAll("li");
    li.data(d3.entries(options.tabs))
        .enter()
        .append("li")
        .classed("active", active)
        .append("a")
        .style("cursor", "pointer")
        .text(function(d) { return d.key; })
        .on("click", function(d, i) {
            if(d.key !== options.selected) {
                options.selected = d.key;
                nav.selectAll("li").classed("active", active);
                content.selectAll("div.tab-pane").classed("active", active);
                options.tabOnClick(d.key);
            }
        });
};

/*
 * Create a table from a hash/dictionary/object.
 * container - A d3 element in which the table will be rendered.
 * hash - The hash to use to populate the table.
 * header - An array of length 2 with the first item the name for the key and second for the value.
 * word - The word to be inserted into the message if the hash is empty (e.g. "No metrics available.").
 */
function createTableFromHash(container, hash, header, word) {
    if(_.size(hash) === 0) {
        container.append("p")
            .text("No "+word+" available.");
    } else {
        var table = container.append("table")
            .classed("table table-hover table-condensed", true);
        table.append("thead")
            .append("tr")
            .selectAll("th")
            .data(header)
            .enter()
            .append("th")
            .text(function(d) { return d; });
        var entries = d3.entries(hash).map(function(entry) {
            if(entry.value == null) {
                return [entry.key, "null"];
            } else {
                return [entry.key, entry.value.toString()];
            }
        });
        table.append("tbody")
            .selectAll("tr")
            .data(entries)
            .enter()
            .append("tr")
            .selectAll("td")
            .data(function(d) { return d; })
            .enter()
            .append("td")
            .text(function(d) { return d; });
    }
}

/*
 * Create the favorite icon in the given container. Make sure that on click and favs model events 
 * work properly.
 * iconContainer - The container to render the icon in, this must be a d3 element.
 * key - A string, one of "datasets", "analyses", etc.
 * value - A string of the corresponding dataset name or analysis name, etc.
 * view - The view that must contain a favsModel. This is done to make cleanup easier.
 *        Just call .off(null, null, view) to cleanup all favorites event bindings.
 * Return nothing.
 * e.g. favsModel.off(null, returnedFunction);
 */
function createFavsIcon(iconContainer, key, value, view) {
    iconContainer.style("cursor", "pointer");
    var listener = function faviconListener() {
        if(view.favsModel.has(key, value)) {
            iconContainer.html(icons.filledStar);
        } else {
            iconContainer.html(icons.emptyStar);
        }
    };
    listener();
    iconContainer.on("click", function iconContainerOnClick() {
        view.favsModel.toggle(key, value);
    });
    view.listenTo(view.favsModel, "change:"+key, listener); // Listen to specific selection.
}

/*
 * Create a word cloud.
 * cloudContainer - The d3 element to render the cloud in.
 * options - A hash with the options.
 * 
 * Options:
 * words - A hash maping each word to a numerical value, the numerical values are used to size the words.
 * wordOnClick - A function that is executed on click being passed the word that was clicked.
 * minFontSize - The minimum font size in px. Must be less than maxFontSize.
 * maxFontSize - The maximum font size in px.
 * Return nothing.
 */
function createWordCloud(cloudContainer, options) {
    var defaults = {
        words: {},
        wordOnClick: function() {},
        minFontSize: 10,
        maxFontSize: 60,
    };
    options = _.extend(defaults, options);
    
    // Find the min and max.
    var min = _.reduce(options.words, function(result, value, key) {
        return value < result? value: result;
    }, Number.MAX_VALUE);
    var max = _.reduce(options.words, function(result, value, key) {
        return value > result? value: result;
    }, -Number.MAX_VALUE);
    
    
    var fontSize = d3.scale.sqrt().domain([min, max]).range([10, 100])
        .range([options.minFontSize, options.maxFontSize]);
    
    var data = d3.entries(options.words).map(function(item) {
        return { text: item.key, size: fontSize(item.value) };
    });
    
    var width = 900;
    var height = 450;
    var fill = d3.scale.category10();
    
    var data = d3.entries(options.words).sort(function(a, b) { return b.value - a.value; });
    var angle = d3.scale.linear().domain([0, 1]).range([-30, 30]);
    
    d3.layout.cloud().size([width, height])
        .timeInterval(10)
        .words(data)
        .padding(1)
        .rotate(function(d) { return angle(Math.random()); })
        .font("Impact")
        .fontSize(function(d) { return fontSize(d.value); })
        .spiral("archimedean")
        .on("end", draw)
        .start();
    
    function draw(words) {
        var g = cloudContainer.append("svg")
            .attr("width", "100%")
            .attr("height", 300)
            .attr("viewBox", "0, 0, "+width+", "+height)
            .attr("preserveAspectRatio", "xMidYMin meet")
            .append("g");
        g.attr("transform", "translate("+width/2+","+height/2+")")
            .selectAll("text")
            .data(words)
            .enter().append("text")
            .style("font-size", function(d) { return fontSize(d.value) + "px"; })
            .style("font-family", "Impact")
            .style("fill", function(d, i) { return fill(i); })
            .style("cursor", "pointer")
            .attr("text-anchor", "middle")
            .attr("transform", function(d) {
                return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
            })
            .text(function(d) { return d.key; })
            .on("click", function(d) { options.wordOnClick(d.key); });
    }
    // Simple word cloud.
    //~ var maxFontFactor = options.maxFontSize/options.minFontSize;
    //~ var diff = max - min;
    
    //~ // Sort words alphabetically.
    //~ var words = d3.entries(options.words).sort(function(a, b) { return a.key.localeCompare(b.key); });
    //~ 
    //~ // Create the visualization.
    //~ var spans = cloudContainer.selectAll("span")
        //~ .data(words)
        //~ .enter()
        //~ .append("span");
    //~ spans.append("span")
        //~ .style({ "color": "black", "cursor": "pointer" })
        //~ .style("font-size", function(d) {
            //~ if(d.value === min) {
                //~ return options.minFontSize + "px";
            //~ } else {
                //~ return (Math.ceil((maxFontFactor*(d.value - min))/diff)*options.minFontSize) + "px";
            //~ }
        //~ })
        //~ .text(function(d) { return d.key; })
        //~ .on("click", function(d) { options.wordOnClick(d.key); })
        //~ .on("mouseenter", function(d) { d3.select(this).style("color", "blue"); })
        //~ .on("mouseleave", function(d) { d3.select(this).transition().duration(1000).style("color", "black"); });
    //~ spans.append("span")
        //~ .text(" ");
}
