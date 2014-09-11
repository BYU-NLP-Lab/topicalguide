
var AllDocumentsSubView = DefaultView.extend({
    readableName: "Browse All Documents",
    
    initialize: function() {
        var defaults = {
            documentContinue: 0, 
            displayNDocuments: 30,
        };
        this.settingsModel.set(_.extend(defaults, this.settingsModel.attributes));
    },
    
    cleanup: function(topics) {},
    
    render: function() {
        this.$el.html("<div id=\"top-matter-container\"></div><div id=\"documents-container\"></div>");
        this.renderTopMatter();
        this.renderTable();
        this.listenTo(this.settingsModel, "change", this.renderTopMatter);
        this.listenTo(this.settingsModel, "change", this.renderTable);
    },
    
    renderTopMatter: function() {
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selection["dataset"],
                "dataset_attr": "document_count",
        }, function(data) {
            var documentCount = data.datasets[selection["dataset"]].document_count;
            var pageNumber = this.settingsModel.attributes["documentContinue"]/this.settingsModel.attributes["displayNDocuments"] + 1;
            d3.select(this.el).select("#top-matter-container")
                .html("<p>Document Count: "+documentCount+"</p><p>Page: "+pageNumber+"</p>");
        }.bind(this), this.renderError.bind(this));
    },
    
    tableTemplate:
"<div class=\"row\"><div class=\"col-xs-1\">"+
"    <span class=\"glyphicon glyphicon-step-backward pointer\"></span>"+
"    <span class=\"glyphicon glyphicon-chevron-left pointer\"></span>"+
"</div>"+
"<div id=\"documents-table-container\" class=\"col-xs-10\"></div>"+
"<div class=\"col-xs-1\">"+
"    <span class=\"glyphicon glyphicon-chevron-right pointer\"></span>"+
"    <span class=\"glyphicon glyphicon-step-forward pointer\"></span>"+
"</div></div>",
    
    renderTable: function() {
        var container = d3.select("#documents-container").html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selection["dataset"],
                "analyses": selection["analysis"],
                "dataset_attr": "document_count",
                "documents": "*",
                "document_continue": this.settingsModel.attributes["documentContinue"],
                "document_limit": this.settingsModel.attributes["displayNDocuments"],
        }, function(data) {
            var documents = extractDocuments(data);
            var documentCount = data.datasets[selection["dataset"]].document_count;
            var documentContinue = this.settingsModel.attributes["documentContinue"];
            var displayNDocuments = this.settingsModel.attributes["displayNDocuments"];
            container.html(this.tableTemplate);
            container.selectAll("span")
                .style("color", "green")
                .style("font-size", "1.5em");
            container.select(".glyphicon-step-backward")
                .on("click", function() {
                    this.settingsModel.set({ documentContinue: 0 });
                }.bind(this))
                .style("display", function() {
                    if(documentContinue === 0) return "none";
                    else return "inline-block";
                });
            container.select(".glyphicon-chevron-left")
                .on("click", function() {
                    this.settingsModel.set({ documentContinue: (documentContinue-displayNDocuments) });
                }.bind(this))
                .style("display", function() {
                    if(documentContinue === 0) return "none";
                    else return "inline-block";
                });
            container.select(".glyphicon-step-forward")
                .on("click", function() {
                    this.settingsModel.set({ documentContinue: (documentCount - (documentCount%displayNDocuments)) });
                }.bind(this))
                .style("display", function() {
                    if(documentContinue > (documentCount-displayNDocuments)) return "none";
                    else return "inline-block";
                });
            container.select(".glyphicon-chevron-right")
                .on("click", function() {
                    this.settingsModel.set({ documentContinue: (documentContinue + displayNDocuments) });
                }.bind(this))
                .style("display", function() {
                    if(documentContinue > (documentCount-displayNDocuments)) return "none";
                    else return "inline-block";
                });
            container.select(".col-xs-1")
                .classed("text-center", true);
            var table = container.select("#documents-table-container").append("table")
                .classed("table table-hover table-condensed", true);
            
            var header = ["", "Document"];
            var documents = d3.entries(documents).map(function(entry) {
                return [entry.key, entry.key];
            });
            var onClick = function(d, i) {
                this.selectionModel.set({ "document": d[0] });
            }.bind(this);
            createSortableTable(table, {
                header: header, 
                data: documents, 
                onClick: { "1": onClick },
                favicon: [0, "documents", this],
                sortBy: 1,
                sortAscending: true,
            });
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return "<p>Select a document from the list to learn more about it. Use the green arrows to navigate the pages.</p>";
    },
});

var DocumentInfoView = DefaultView.extend({
    readableName: "Document Information",
    
    textFormTemplate:
"<div class=\"row\"><div class=\"col-xs-12\">"+
"    <form id=\"text-highlight-form\" role=\"form\" class=\"input-group\">"+
"        <span id=\"highlight-buttons\" class=\"input-group-btn\" data-toggle=\"buttons\">"+
"            <label class=\"btn btn-primary active\">No Highlights<input type=\"radio\" name=\"options\" id=\"no-highlights\" checked></label>"+
"            <label class=\"btn btn-primary\">Topic Highlights<input type=\"radio\" name=\"options\" id=\"topic-highlights\"></label>"+
"            <label class=\"btn btn-primary\">Word Highlights<input type=\"radio\" name=\"options\" id=\"word-highlights\"></label>"+
"        </span>"+
"        <input disabled class=\"form-control\" type=\"text\" id=\"topic-word-input\" placeholder=\"\">"+
"        <span class=\"input-group-btn\">"+
"            <input disabled class=\"btn btn-default\" id=\"topic-word-submit-button\" type=\"submit\"></input>"+
"        </span>"+
"    </form>"+
"</div></div>",
    
    initialize: function() {
        var defaults = {
            selectedTab: "Text",
            selectedHighlight: "no-highlights",
            topics: "",
            words: "",
        };
        this.settingsModel.set(_.extend(defaults, this.settingsModel.attributes));
        this.model = new Backbone.Model();
        this.listenTo(this.selectionModel, "change:document", this.render);
    },
    cleanup: function() {
        this.selectionModel.on(null, null, this);
    },
    
    renderText: function(title, d3Element) {
        var that = this;
        d3Element.html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selection["dataset"],
                "analyses": selection["analysis"],
                "documents": selection["document"],
                "document_attr": ["text"],
                "topics": "*",
                "topic_attr": "names",
        }, function(data) {
            var text = extractDocuments(data, this.selectionModel)[selection["document"]].text;
            var topics = extractTopics(data, this.selectionModel);
            var topicNames = _.reduce(topics, function(result, value, key) { result[key] = value.names.Top3; return result; }, {});
            this.model.set({ text: text, topicNames: topicNames });
            
            // Set up the form.
            var container = d3Element.html("").append("div")
                .classed("container-fluid", true)
                .html(this.textFormTemplate);
            // Set up text div.
            container.append("div")
                .classed("row", true)
                .append("div")
                .classed("col-xs-12", true)
                .attr("id", "highlighted-text")
                .text("");
            // Set up form functionality.
            d3.select("#text-highlight-form").on("submit", function() {
                d3.event.preventDefault();
                var textBox = d3.select("#topic-word-input");
                var input = textBox.property("value");
                input = _.map(input.split(/[\s,]+/), function(word) { return word.trim().toLowerCase(); });
                input.sort();
                textBox.property("value", input.join(" "));
                if(that.settingsModel.attributes.selectedHighlight === "word-highlights") {
                    that.settingsModel.set({ words: input });
                } else if(that.settingsModel.attributes.selectedHighlight === "topic-highlights") {
                    that.settingsModel.set({ topics: input });
                }
            });
            d3.select("#highlight-buttons").selectAll("label").on("click", function() {
                var id = d3.select(this).select("input").attr("id");
                that.settingsModel.set({ selectedHighlight: id });
            });
            
            this.listenTo(this.settingsModel, "change:selectedHighlight", this.highlightChanged);
            this.listenTo(this.settingsModel, "change:words", this.requestWordHighlightData);
            this.listenTo(this.settingsModel, "change:topics", this.requestTopicHighlightData);
            this.highlightChanged();
        }.bind(this), this.renderError.bind(this));
    },
    
    highlightChanged: function() {
        var input = d3.select("#topic-word-input");
        var submit = d3.select("#topic-word-submit-button");
        var selected = this.settingsModel.get("selectedHighlight");
        
        if(selected === "no-highlights") {
            input.attr("disabled", "true").attr("placeholder", "")
                .property("value", "");
            submit.attr("disabled", "true");
            this.highlightText();
        } else if(selected === "topic-highlights") {
            var topics = this.settingsModel.attributes.topics;
            input.attr("disabled", null).attr("placeholder", "Enter topics by number.")
                .property("value", topics.length===0?"":topics.join(" "));
            submit.attr("disabled", null);
            this.requestTopicHighlightData();
        } else if(selected === "word-highlights") {
            var words = this.settingsModel.attributes.words;
            input.attr("disabled", null).attr("placeholder", "Enter words.")
                .property("value", words.length===0?"":words.join(" "));
            submit.attr("disabled", null);
            this.requestWordHighlightData();
        }
    },
    
    requestTopicHighlightData: function() {
        var topics = this.settingsModel.get("topics");
        if(topics.length === 0) {
            this.highlightText();
            return;
        }
        
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "documents": selection["document"],
            "topics": topics,
            "topic_attr": ["word_token_documents_and_locations"],
        }, function(data) {
            var doc = selection.document;
            var topics = extractTopics(data, this.selectionModel);
            var justTopics = {};
            var tokens = [];
            for(topic in topics) {
                var docTokens = topics[topic].word_token_documents_and_locations;
                if(doc in docTokens) {
                    var docTokens = docTokens[doc];
                    for(var i = 0; i < docTokens.length; i++) {
                        var t = docTokens[i];
                        tokens.push([t[0], t[1], topic]);
                    }
                    justTopics[topic] = true;
                }
            }
            this.highlightText(justTopics, tokens);
        }.bind(this), this.renderError.bind(this));
    },
    
    requestWordHighlightData: function() {
        var words = this.settingsModel.get("words");
        if(words.length === 0) {
            this.highlightText();
            return;
        }
        
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
            "datasets": selection["dataset"],
            "analyses": selection["analysis"],
            "documents": selection["document"],
            "document_attr": ["word_token_topics_and_locations"],
            "words": words,
        }, function(data) {
            var topicsAndLocations = extractDocuments(data, this.selectionModel)[selection.document].word_token_topics_and_locations;
            var topics = {};
            var tokens = [];
            for(word in topicsAndLocations) {
                var tempTokens = topicsAndLocations[word];
                for(var i = 0; i < tempTokens.length; i++) {
                    topics[tempTokens[i][0]] = true;
                    var start = tempTokens[i][1];
                    tokens.push([start, start+word.length, tempTokens[i][0]]);
                }
            }
            this.highlightText(topics, tokens);
        }.bind(this), this.renderError.bind(this));
    },
    
    highlightText: function(topics, tokens) {
        var container = d3.select(this.el).select("#highlighted-text").html("");
        
        if(topics === undefined || tokens === undefined || (_.size(topics) === 0 && tokens.length === 0)) {
            var html = this.model.attributes.text.split("\n");
            var html = _.reduce(html, function(result, item) { 
                if(item === "") {
                    return result;
                } else {
                    result.push(item);
                    return result;
                }
            }, []);
            container.append("div").classed("row container-fluid", true).append("h4").text("Document Text");
            container.append("div").classed("row container-fluid", true)
                .html(html.join("<br><br>"));
            return;
        }
        
        // Get and format data and create color scale.
        var text = this.model.attributes.text;
        var topicNames = this.model.attributes.topicNames;
        var topicsArray = _.reduce(topics, function(result, value, key) { result.push(key); return result; }, []);
        topicsArray.sort(function(a, b) { return parseInt(a) - parseInt(b); });
        tokens.sort(function(a, b) { return parseInt(a[0]) - parseInt(b[0]); }); // Put tokens in ascending order.
        var colors = ["#FF0000", "#FFFF00", "#00FF00", "#00FFFF", "#0000FF", "#FF00FF", "#DD0000"]; // Neonish colors.
        var colorDomain = d3.scale.ordinal().domain(colors).rangePoints([0, 1], 0).range();
        topicsArray.push("hi");
        var ordinalRange = d3.scale.ordinal().domain(topicsArray).rangePoints([0, 1], 0).range();
        topicsArray.slice(0, topicsArray.length - 1);
        var ordToNum = d3.scale.ordinal().domain(topicsArray).range(ordinalRange);
        var numToColor = d3.scale.linear().domain(colorDomain).range(colors);
        var colorScale = function ordinalColorScale(val) { return numToColor(ordToNum(val)); };
        for(topic in topics) {
            topics[topic] = hexToRGBA(colorScale(topic), 0.3);
        }
        
        // Convenience function to make sure that text is not drowned out.
        function hexToRGBA(hex, alpha) {
            var r = parseInt(hex.slice(1,3), 16);
            var g = parseInt(hex.slice(3,5), 16);
            var b = parseInt(hex.slice(5,7), 16);
            return "rgba("+r+","+g+","+b+","+0.3+")";
        }
        
        // Make topic color legend.
        var legend = container.append("div").classed("row container-fluid", true);
        legend.append("h4").text("Topic Legend: ");
        legend.selectAll("span")
            .data(d3.entries(topics).sort(function(a, b) { return a.key - b.key; }))
            .enter().append("span")
            .style("background-color", function(d) { return d.value; })
            .style({ "margin-left": "4px", "margin-right": "4px" })
            .text(function(d) { return d.key+": "+topicNames[d.key]; });
        
        // Makes sure that newlines are displayed.
        function detectNewLine(array, inputText) {
            var tmp = inputText.split("\n");
            for(var i = 0; i < tmp.length-1; i++) {
                if(tmp[i] !== "") {
                    array.push(tmp[i]);
                    array.push("");
                }
            }
            if(tmp[tmp.length-1] !== "") {
                array.push(tmp[tmp.length-1]);
            } else {
                array.push("");
            }
        }
        
        // Parse tokens from the beginning of the text.
        var textFragments = [];
        var textFragmentToTopic = {};
        for(var i = 0; i < tokens.length; i++) {
            var token = tokens[i];
            var tokenText = text.slice(token[0], token[1]);
            if(i === 0 && token[0] !== 0) {
                var previousText = text.slice(0, token[0]);
                detectNewLine(textFragments, previousText);
            }
            textFragments.push(tokenText);
            textFragmentToTopic[textFragments.length-1] = token[2];
            if(i === tokens.length-1) {
                var nextText = text.slice(token[1], text.length);
                detectNewLine(textFragments, nextText);
            } else {
                var nextText = text.slice(token[1], tokens[i+1][0]);
                detectNewLine(textFragments, nextText);
            }
        }
        
        // Text header.
        container.append("div").classed("row container-fluid", true).append("h4").text("Document Text");
        var content = container.append("div").classed("row container-fluid", true);
        content.selectAll("span")
            .data(textFragments)
            .enter().append("span")
            .style("background-color", function(d, i) {
                if(i.toString() in textFragmentToTopic) {
                    return topics[textFragmentToTopic[i]];
                } else {
                    return null;
                }
            })
            .classed("highlighted-word", function(d, i) {
                if(i.toString() in textFragmentToTopic) {
                    return true;
                } else {
                    return null;
                }
            })
            .each(function(d) {
                if(d === "") {
                    d3.select(this).html("<br><br>");
                } else {
                    d3.select(this).text(d);
                }
            });
    },
    
    renderMetadataAndMetrics: function(title, d3Element) {
        d3Element.html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selection["dataset"],
                "analyses": selection["analysis"],
                "documents": selection["document"],
                "document_attr": ["metadata", "metrics"],
        }, function(data) {
            var document = extractDocuments(data)[selection["document"]];
            d3Element.html("");
            var container = d3Element.append("div");
            createTableFromHash(container, document.metadata, ["Key", "Value"], "metadata");
            createTableFromHash(container, document.metrics, ["Metric", "Value"], "metadata");
        }.bind(this), this.renderError.bind(this));
    },
    
    render: function() {
        this.$el = $(this.el);
        if(this.selectionModel.get("document") === "") {
            this.$el.html("<p>A document needs to be selected in order to use this view.</p>");
            return;
        }
        
        this.$el.html("");
        
        tabs = {
            "Text": this.renderText.bind(this),
            "Metadata and Metrics": this.renderMetadataAndMetrics.bind(this),
        };
        
        // Set this.settings selected to the selected tab.
        var tabOnClick = function(label) {
            this.settingsModel.set({ selectedTab: label });
        }.bind(this);
        
        this.$el.html("<h3>Document: "+this.selectionModel.get("document")+"</h3>");
        this.$el.append("<div></div>");
        var container = d3.select(this.el).select("div");
        createTabbedContent(container, { 
            tabs: tabs, 
            selected: this.settingsModel.get("selectedTab"), 
            tabOnClick: tabOnClick, 
        });
    },
    
    renderHelpAsHtml: function() {
        return "<h4>Text</h4>"+
        "<p>Displays the text of the document as given to the import system. "+
        "Select one of the highlighting methods. "+
        "Topic Highlights will allow you to specify topics in the text field (by their numbers) and Word Highlights takes words. "+
        "The text box takes topics or words separated by spaces, tabs, or commas. "+
        "Click submit once you've entered your selection.</p>"+
        "<h4>Metadata and Metrics</h4>"+
        "<p>The metadata and metrics of the document in key value pairs.</p>";
    },
});

var SingleDocumentSubView = DefaultView.extend({
    readableName: "View Single Document",
    
    initialize: function() {},
    
    mainTemplate: "<div id=\"single-doc-topmatter\" class=\"col-xs-12\"></div>"+
                  "<div id=\"document-info-container\" class=\"col-xs-12\"></div>",
    
    cleanup: function(topics) {
        if(this.docInfoView !== undefined) {
            this.docInfoView.dispose();
        }
    },
    
    render: function() {
        this.$el.html(this.mainTemplate);
        this.renderTopMatter();
        if(this.docInfoView === undefined) {
            this.docInfoView = new DocumentInfoView({ el: $("#document-info-container"), settingsModel: this.settingsModel, selectionModel: this.selectionModel });
        }
        this.docInfoView.render();
    },
    
    renderTopMatter: function() {
        var top = d3.select("#single-doc-topmatter");
        top.append("button")
            .classed("btn btn-default", true)
            .attr("type", "button")
            .html("<span class=\"glyphicon glyphicon-chevron-left pewter\"></span> Back to All Documents")
            .on("click", function() {
                this.selectionModel.set({ "document": "" });
            }.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return this.docInfoView.renderHelpAsHtml();
    },
});


var DocumentView = DefaultView.extend({
    
    readableName: "Documents",
    
    initialize: function() {
        var defaults = { selectedTab: "Text" };
        this.settingsModel.set(_.extend(defaults, this.settingsModel.attributes));
        this.listenTo(this.selectionModel, "change:document", this.render, this);
    },
    
    render: function() {
        if(this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<div id=\"info\"></div>");
            this.cleanupViews();
            if(this.selectionModel.nonEmpty(["document"])) {
                this.subView = new SingleDocumentSubView({ el: "#info", selectionModel: this.selectionModel, settingsModel: this.settingsModel });
            } else {
                this.subView = new AllDocumentsSubView({ el: "#info", selectionModel: this.selectionModel, settingsModel: this.settingsModel });
            }
            this.subView.render();
        } else {
            this.$el.html("<p>You should select a <a href=\"#\">dataset and analysis</a> before proceeding.</p>");
        }
    },
    
    renderHelpAsHtml: function() {
        if(this.subView !== undefined) {
            return this.subView.renderHelpAsHtml();
        }
        return DefaultView.prototype.renderHelpAsHtml();
    },
    
    cleanupViews: function() {
        if(this.subView !== undefined) {
            this.subView.dispose();
        }
    },
    
    cleanup: function() {
        this.cleanupViews();
        this.selectionModel.off(null, this.render, this);
    },
    
});

// Add the Document View to the top level menu
globalViewModel.addViewClass([], DocumentView);
