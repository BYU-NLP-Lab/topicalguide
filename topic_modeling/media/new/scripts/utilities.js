/*
 * The following are an assortment of useful utilities.
 */

function makeSingular(word) {
    if(word === "analyses") return "analysis";
    else return word.slice(0, word.length - 1)
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
            if(keyAndValue[1]===undefined) keyAndValue.push("")
            hash[unescape(keyAndValue[0])] = unescape(keyAndValue[1]);
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
            return escape(item);
        } else if(item instanceof Array) {
            item = item.slice(0); // Clone the array.
            item.sort();
            for(i=0; i<item.length; i++) {
                item[0] = normalize(item[0]);
            }
            return item.join(",");
        } else {
            return escape(item.toString());
        }
    };
    var items = [];
    _.forOwn(hash, function(value, key) {
        items.push(escape(key) + '=' + normalize(value));
    });
    return items.join('&');
}

function hasLocalStorage() {
    try {
        localStorage["storage-test"] = "test";
        delete localStorage["storage-test"];
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
 * Helper function to pull out a deeply nested sub-hash.
 * name - One of: datasets, analyses, topics
 * hash - The hash the data is being extracted from.
 * Return sub-hash if found; empty hash otherwise.
 */
function extractSubHash(name, hash) {
    console.log("extractSubHash is deprecated");
    var list = ["datasets", globalSelectionModel.get("dataset"), "analyses",
                globalSelectionModel.get("analysis"), "topics", globalSelectionModel.get("topic")];
    for(i=0; i<list.length; i++) {
        hash = hash[list[i]];
        if(list[i] === name) break;
    }
    return hash;
}

// TODO make extraction functions take a selection model or default to the global one.
// Convenience method to extract documents.
function extractDocuments(data) {
    return data.datasets[globalSelectionModel.get("dataset")].documents;
}

// Convenience method to extract topics.
function extractTopics(data) {
    return data.datasets[globalSelectionModel.get("dataset")].analyses[globalSelectionModel.get("analysis")].topics;
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
 * onClick - Maps columns to click functions with d as the inner array (not element of inner array).
 * bars - Indicates the rows to display with percentage bars.
 * percentages - Indicates which rows should be displayed as percentages.
 * favicon - If specified it is an array of length 3 e.g. [indexOfFavsColumn, "datasets", view object].
 * Return nothing.
 */
function createSortableTable(table, options) {
    var defaults = {
        header: [],
        data: [],
        rowOnClick: false,
        onClick: {},
        bars: [],
        percentages: [],
        favicon: false,
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
    
    // Variables for sorting.
    var ascending = true;
    var lastColumn = 0;
    // Create column headers with sort icons.
    var headerRow = table.append("thead")
        .append("tr").selectAll("th")
        .data(options.header)
        .enter()
        .append("th")
        .append("a")
        .style("cursor", "pointer")
        .on("click", function(d, i) {
            var sortAscending = function(a, b) {
                if($.isNumeric(a[i]) && $.isNumeric(b[i])) return parseFloat(a[i]) - parseFloat(b[i]);
                else return a[i].localeCompare(b[i]);
            };
            var sortDescending = function(a, b) { return sortAscending(b, a); };
            if(lastColumn !== i) ascending = true;
            lastColumn = i;
            if(ascending) {
                ascending = false;
                tableRows.sort(sortAscending);
            } else {
                ascending = true;
                tableRows.sort(sortDescending); 
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
};

/*
 * Create tabbed content.
 * container - A d3 selection of the container to opperate in.
 * tabs - A dictionary mapping the tab name to a function. The function must take a d3 element
 *           as an argument and render the desired content in there.
 */
function createTabbedContent(container, tabs) {
    container.html("<ul role=\"tablist\" class=\"nav nav-tabs\"></ul>"+
                   "<div class=\"tab-content\"></div>");
    var selection = null;
    for(key in tabs) {
        selection = key;
        break;
    }
    
    // Active function.
    var active = function(d, i) { 
        if(d.key === selection) return true; 
        else return false; 
    }.bind(this);
    
    // Set up the content
    var content = container.select("div.tab-content");
    var contentPanes = content.selectAll("div.tab-pane");
    contentPanes.data(d3.entries(tabs))
        .enter()
        .append("div")
        .classed("tab-pane", true)
        .classed("active", active)
        .each(function(d, i) { tabs[d.key](d3.select(this)); });
    
    // Set up tabbed navigation
    var nav = container.select("ul.nav-tabs");
    var li = nav.selectAll("li");
    li.data(d3.entries(tabs))
        .enter()
        .append("li")
        .classed("active", active)
        .append("a")
        .text(function(d) { return d.key; })
        .on("click", function(d, i) {
            if(d.key !== selection) {
                selection = d.key;
                nav.selectAll("li").classed("active", active);
                content.selectAll("div.tab-pane").classed("active", active);
            }
        });
};

/*
 * Create a table from a hash/dictionary/object.
 * container - A d3 element in which the table will be rendered.
 * hash - The hash to use to populate the table.
 * header - An array of length 2 with the first item the name for the key and second for the value.
 * word - The word to be inserted into the message if the hash is empty.
 */
function createTableFromHash(container, hash, header, word) {
    if(_.size(hash) === 0) {
        container.html("<p>No "+word+" available.</p>");
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
            return [entry.key, entry.value.toString()];
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
 * value - A string of the corresponding dataset, analysis, etc.
 * view - The view that must contain a favsModel. This is done to make cleanup easier.
 *        Just call .off(null, null, view) to cleanup all favorites event bindings.
 * Returns the function that needs to be removed from the favsModel event listeners.
 * e.g. favsModel.off(null, returnedFunction);
 */
function createFavsIcon(iconContainer, key, value, view) {
    iconContainer.style("cursor", "pointer");
    var listener = function() {
        if(view.favsModel.has(key, value)) {
            iconContainer.html(icons.filledStar);
        } else {
            iconContainer.html(icons.emptyStar);
        }
    };
    listener();
    iconContainer.on("click", function() {
        view.favsModel.toggle(key, value);
    });
    view.favsModel.on("change:"+key, listener, view); // Listen to specific selection.
}
