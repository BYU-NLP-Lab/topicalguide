"use strict";

/**
 * The following are an assortment of useful utilities.
 */
var tg = new function() {
    
    /**
     * Basic site functions for convenience.
     */
    this.site = {
        /**
         * Initializes the span for you so that the global TG View can
         * keep it updated on clicking.
         * domElement -- must be a "span"
         * The dom element must have one of the following data attributes set:
         *      tg-data-dataset-name
         *      tg-data-analysis-name
         *      tg-data-topic-number
         *      tg-data-document-name
         *      tg-data-topic-name-scheme
         * favsModel -- must be the favoritesModel to pull from
         */
        initFav: function(domElement, favsModel) {
            var el = d3.select(domElement);
            var type = null;
            var clsName = null;
            if(tg.dom.hasAttr(domElement, "data-tg-dataset-name")) {
                type = "datasets";
                clsName = "data-tg-dataset-name";
            } else if(tg.dom.hasAttr(domElement, "data-tg-analyis-name")) {
                type = "analyses";
                clsName = "data-tg-analyis-name";
            } else if(tg.dom.hasAttr(domElement, "data-tg-topic-number")) {
                type = "topics";
                clsName = "data-tg-topic-number";
            } else if(tg.dom.hasAttr(domElement, "data-tg-document-name")) {
                type = "documents";
                clsName = "data-tg-document-name";
            } else if(tg.dom.hasAttr(domElement, "data-tg-topic-name-scheme")) {
                type = "topicNameSchemes";
                clsName = "tg-data-topic-name-scheme";
            }
            if(clsName !== null) {
                if(favsModel.has(type, el.attr(clsName).toString())) {
                    el.classed({ "glyphicon": true, "glyphicon-star": true, "glyphicon-star-empty": false, "gold": true, "pointer": true });
                } else {
                    el.classed({ "glyphicon": true, "glyphicon-star": false, "glyphicon-star-empty": true, "gold": true, "pointer": true });
                }
            }
        },
        
        /**
         * Convert from the short string representation to a human readable one.
         */
        readableTypes: {
            "int": "Integer",
            "float": "Float",
            "datetime": "Date/Time",
            "bool": "Boolean",
            "text": "Text",
            "ordinal": "Ordinal",
        },
        
        /**
         * Injectible icon html.
         */
        icons: {
            emptyStar: "<span class=\"glyphicon glyphicon-star-empty gold\"></span>",
            filledStar: "<span class=\"glyphicon glyphicon-star gold\"></span>",
            
            pencil: "<span class=\"glyphicon glyphicon-pencil purple\"></span>",
            help: "<span class=\"glyphicon glyphicon-question-sign blue\"></span>",
            settings: "<span class=\"caret\" style=\"text-size: 1.5em\"></span>",
            share: "<span class=\"glyphicon glyphicon-plus\"></span>",
            
            document: "<span class=\"glyphicon glyphicon-book brown document\"></span>",
            previous: "<span class=\"glyphicon glyphicon-chevron-left green previous\"></span>",
            next: "<span class=\"glyphicon glyphicon-chevron-right green next\"></span>",
            beginning: "<span class=\"glyphicon glyphicon-step-backward green beginning\"></span>",
            end: "<span class=\"glyphicon glyphicon-step-forward green end\"></span>",
            
            loading: "<p class=\"text-center\"><img src=\"/static/images/large-spinner.gif\"/></p><p class=\"text-center\">Loading...</p>",
        },
    };
    
    this.rand = {
        /**
         * Return an integer in [min, max).
         */
        getRandomIntegerInRange: function(min, max) {
            return Math.floor(Math.random()*(max - min)) + min;
        },
    };
    
    /**
     * Basic DOM convenience functions.
     */
    this.dom = {
        /**
         * domElement -- DOM element
         * attrName -- string of the attribute name
         * Return true if the attribute exists; false otherwise.
         */
        hasAttr: function(domElement, attrName) {
            var a = $(domElement).attr(attrName);
            return typeof a !== typeof undefined && a !== false;
        },
    };
    
    /**
     * Small library to makeup for inconsistencies in JavaScript and across 
     * browsers.
     * Basic functions for type checking or otherwise.
     */
    this.js = {
        /**
         * i -- a number
         * Return true if it is an integer; false otherwise.
         */
        isInteger: function(i) {
            return !isNaN(i) && 
                   parseInt(Number(i)) == i && 
                   !isNaN(parseInt(i, 10));
        },
        
        /**
         * s -- an object
         * Return true if it is a string; false otherwise.
         */
        isString: function(str) {
            if(typeof str === "string" || str instanceof String) {
                return true;
            } else {
                return false;
            }
        },
        
        /**
         * obj -- any javascript object
         * Return true if obj isn't undefined or null; false otherwise;
         */
        isDefined: function(obj) {
            return (obj !== null && obj !== undefined);
        },
        
        /**
         * Return the value of the cookie with the supplied name; null if not present.
         * This code is from the Django project:
         * https://docs.djangoproject.com/en/1.7/ref/contrib/csrf/
         */
        getCookie: function(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },
        
        /**
         * Return true if session storage is enabled.
         */
        hasSessionStorage: function() {
            try {
                sessionStorage["storage-test"] = "test";
                delete sessionStorage["storage-test"];
                return true;
            } catch(e) {
                return false;
            }
        },
        
    };
    
    this.str = {
        /**
         * Returns a new string with the start of each word capitalized.
         */
        toTitleCase: function(str) {
            return str.replace(/\w\S*/g, function(substr){ return substr.charAt(0).toUpperCase() + substr.slice(1); });
        },
        
    };
    
    this.color = {
        pastels: ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a", 
                  "#d62728", "#ff9896", "#9467bd", "#c5b0d5", "#8c564b", "#c49c94", 
                  "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7", "#bcbd22", "#dbdb8d", 
                  "#17becf", "#9edae5"],
        blueToRed: ["blue", "#F0EAD6", "red"],
        black: ["black"],
        /**
         * Return a function that takes and index in the range of listOfValues 
         * and maps to a color.
         */
        getDiscreteColorScale: function(listOfValues, colorPalette) {
            var colorDomain = d3.scale.ordinal().domain(colorPalette).rangePoints([0, 1], 0).range();
            var ordinalRange = d3.scale.ordinal().domain(listOfValues).rangePoints([0, 1], 0).range();
            var ordToNum = d3.scale.ordinal().domain(listOfValues).range(ordinalRange);
            var numToColor = d3.scale.linear().domain(colorDomain).range(colorPalette);
            return function ordinalColorScale(val) { return numToColor(ordToNum(val)); };
        },
    };
    
    this.url = {
        /**
         * Turns arrays and other objects to URI friendly strings.
         */
        uriStringify: function(item) {
            var result = null;
            if(item instanceof String) {
                result = encodeURIComponent(item);
            } else if(item instanceof Array) {
                item = item.slice(0); // Clone the array.
                item.sort();
                for(var i = 0; i<item.length; i++) {
                    item[0] = tg.url.stringify(item[0]);
                }
                result = item.join(",");
            } else {
                result = encodeURIComponent(item.toString());
            }
            return result;
        },
        
        /**
         * Parse url arguments to a hash.
         */
        urlToHash: function(args) {
            var hash = {};
            var items = args.split('&');
            if(items[0] !== "") {
                for(var i = 0; i<items.length; i++) {
                    var keyAndValue = items[i].split('=');
                    if(keyAndValue[1]===undefined) keyAndValue.push("");
                    hash[decodeURIComponent(keyAndValue[0])] = decodeURIComponent(keyAndValue[1]);
                }
            }
            return hash;
        },

        /**
         * Convert a hash to url arguments, url will be normalized.
         * hash - Any valid hash with strings, arrays, and numbers as the values.
         */
        hashToUrl: function(hash) {
            var keys = [];
            _.forOwn(hash, function(value, key) { keys.push(key); });
            keys.sort();
            var items = [];
            _.forEach(keys, function(key) {
                items.push(encodeURIComponent(key) + '=' + tg.url.uriStringify(hash[key]));
            });
            return items.join('&');
        },
    };
};

/**
 * Easy to inject icons used throughout the site.
 */
var icons = {
    emptyStar: "<span class=\"glyphicon glyphicon-star-empty gold\"></span>",
    filledStar: "<span class=\"glyphicon glyphicon-star gold\"></span>",
    
    help: "<span class=\"glyphicon glyphicon-question-sign blue\"></span>",
    settings: "<span class=\"caret\" style=\"text-size: 1.5em\"></span>",
    share: "<span class=\"glyphicon glyphicon-plus\"></span>",
    
    document: "<span class=\"glyphicon glyphicon-book brown document\"></span>",
    previous: "<span class=\"glyphicon glyphicon-chevron-left green previous\"></span>",
    next: "<span class=\"glyphicon glyphicon-chevron-right green next\"></span>",
    beginning: "<span class=\"glyphicon glyphicon-step-backward green beginning\"></span>",
    end: "<span class=\"glyphicon glyphicon-step-forward green end\"></span>",
    
    loading: "<p class=\"text-center\"><img src=\"/static/images/large-spinner.gif\"/></p><p class=\"text-center\">Loading...</p>",
    
    pencil: "<span class=\"glyphicon glyphicon-pencil purple\"></span>",
};


/**
 * Types recognized by the import system.
 */
var readableTypes = {
    "int": "Integer",
    "float": "Float",
    "datetime": "Date/Time",
    "bool": "Boolean",
    "text": "Text",
    "ordinal": "Ordinal",
};


var colorPalettes = {
    pastels: ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a", 
              "#d62728", "#ff9896", "#9467bd", "#c5b0d5", "#8c564b", "#c49c94", 
              "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7", "#bcbd22", "#dbdb8d", 
              "#17becf", "#9edae5"],
    blueToRed: ["blue", "#F0EAD6", "red"],
    black: ["black"],
    
    /**
     * Return a function that takes and index in the range of listOfValues 
     * and maps to a color.
     */
    getDiscreteColorScale: function(listOfValues, colorPalette) {
        var colorDomain = d3.scale.ordinal().domain(colorPalette).rangePoints([0, 1], 0).range();
        var ordinalRange = d3.scale.ordinal().domain(listOfValues).rangePoints([0, 1], 0).range();
        var ordToNum = d3.scale.ordinal().domain(listOfValues).range(ordinalRange);
        var numToColor = d3.scale.linear().domain(colorDomain).range(colorPalette);
        return function ordinalColorScale(val) { return numToColor(ordToNum(val)); };
    },
};

/**
 * Return true if the given number or object is an integer.
 */
function isInteger(i) {
    return !isNaN(i) && 
        parseInt(Number(i)) == i && 
        !isNaN(parseInt(i, 10));
}

/**
 * Return an integer in [min, max).
 */
function getRandomIntegerInRange(min, max) {
    return Math.floor(Math.random()*(max - min)) + min;
}


/**
 * Handles printing a nice message to the user.
 */
function reportReadableErrorToUser(message) {
    alert(message);
}


/**
 * Returns true if the object is a string; false otherwise.
 */
function isString(str) {
    if(typeof str === "string" || str instanceof String) {
        return true;
    } else {
        return false;
    }
}

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
        for(var i = 0; i<items.length; i++) {
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
            for(var i = 0; i<item.length; i++) {
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
    for(var key in hash) {
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
    for(var key in defaults) {
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
    return data.datasets[model.get("dataset")].analyses[model.get("analysis")].documents;
}

/*
 * Convenience method to extract topics.
 * data - The data returned by the server in the form of hashes and arrays.
 * [model] - The selection model, defaults to the global selection model if not provided.
 */
function extractTopics(data, model) {
    var result = {};
    try {
        result = data.datasets[model.get("dataset")].analyses[model.get("analysis")].topics;
    } catch(err) {}
    return result;
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
        temperatures: [],
        favicon: false,
        sortBy: 0,
        sortAscending: true,
    };
    options = _.extend(defaults, options);
    // Find all of the maxes for columns containing bars
    var barmaxes = {};
    for(var i = 0; i<options.bars.length; i++) {
        var index = options.bars[i];
        barmaxes[index] = options.data.reduce(function(p, c, i, a) { 
            return (p > c[index])?p:c[index]; 
        }, 0);
    }
    // Find all of the maxes and mins for columns containing temperatures
    var tempmaxes = {};
    var tempmins = {};
    for(var i = 0; i<options.temperatures.length; i++) {
        var index = options.temperatures[i];
        tempmaxes[index] = options.data.reduce(function(p, c, i, a) { 
            return (p > c[index])?p:c[index];
        }, 0);
        tempmins[index] = options.data.reduce(function(p, c, i, a) {
            return (p < c[index])?p:c[index];
        }, 0);
    }

    // Turn percentages to array.
    var percent = {};
    for(var i = 0; i<options.percentages.length; i++) {
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
        td.filter(function(d, i) { return ((i in barmaxes) || (i in tempmaxes))?false:true; })
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
        
        createPercentageGauge(td, barmaxes, percent);
        
        createTemperatureGauge(td, tempmaxes, tempmins);
    });
    
    // Set initial sort.
    if(ascending) {
        tableRows.sort(makeSortAscending(lastColumn));
    } else {
        tableRows.sort(makeSortDescending(lastColumn));
    }
    ascending = !ascending;
};

function createPercentageGauge(td, barmaxes, percent) {
    // Create the percentage bars.
    for(var key in barmaxes) {
        var maxIndex = parseFloat(key);
        var max = barmaxes[key];
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
};


function createTemperatureGauge(td, tempmaxes, tempmins) {
    // Create the thermometer bars.
    for(var key in tempmaxes) {
        var index = parseFloat(key);
        var max = tempmaxes[key];
        var min = tempmins[key];
        var range = max - min;
        var zero = (Math.abs(min) / range) * 60;
        if (range !== 0.0) {
            var column = td.filter(function(d, i) { return (i === index)?true:false; });
            var svg = column.append("svg")
                .attr("width", 60)
                .attr("height", "1em")
                .style("background-color", "whitesmoke");
            // Create bar.
            svg.append("rect")
                .each(function(d) {
                    var rect = d3.select(this);
                    var width = Math.abs(d)/range * 60;
                    rect.attr("height", "100%")
                        .attr("width", width)
                        .attr("fill", (d > 0.0 ? "red" : "blue"))
                        .attr("transform", "translate("+ (d>0.0 ? zero : zero-width) +","+0+")");
                });
            // Fill in part of bar with whitesmoke.
            //~ group.append("rect")
                //~ .attr("height", "100%")
                //~ .attr("width", function(d) {
                    //~ if(max === 0) return 60;
                    //~ else return (1-(d/max)) * 60;
                //~ })
                //~ .attr("fill", "whitesmoke");
            // Append text.
            svg.append("line")
                .attr("x1", zero)
                .attr("y1", 0)
                .attr("x2", zero)
                .attr("y2", "1em")
                .attr("stroke", "black")
                .attr("strokewidth", "1.5px");
        }
        column.append("span")
            .text(function(d) {
                return " "+d;
            })
            .attr("fill", "black")
            .attr("padding-left", "5px");
    }
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
        rendered: {},
        selected: null,
        tabOnClick: function() {},
    };
    options = _.extend(defaults, options);
    
    container.html("<ul role=\"tablist\" class=\"nav nav-tabs\"></ul>"+
                   "<div class=\"tab-content\"></div>");
    // Make sure a tab is selected to begin with.
    if(!(options.selected in options.tabs)) {
        for(var key in options.tabs) {
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
    var renderedAreas = contentPanes.data(d3.entries(options.tabs))
        .enter()
        .append("div")
        .classed("tab-pane", true)
        .classed("active", active)
        .each(function(d, i) { 
            if(active(d, i)) { // Only render the content of the tab when clicked.
                options.tabs[d.key](d.key, d3.select(this));
                options.rendered[d.key] = true;
            }
        });
    
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
                if(!(d.key in options.rendered)) {
                    renderedAreas.filter(active)
                        .each(function(d, i) {
                            options.tabs[d.key](d.key, d3.select(this));
                        });
                    options.rendered[d.key] = true;
                }
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
