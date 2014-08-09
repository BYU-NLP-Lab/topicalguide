
var AllDocumentsSubView = DefaultView.extend({
    readableName: "Browse All Documents",
    
    initialize: function() {
        this.model = new Backbone.Model();
        this.model.set({ documentContinue: 0, displayNDocuments: 30 });
    },
    
    cleanup: function(topics) {
    },
    
    render: function() {
        this.$el.html("<div id=\"top-matter-container\"></div><div id=\"documents-container\"></div>");
        this.renderTopMatter();
        this.renderTable();
        this.model.on("change", this.renderTopMatter, this);
        this.model.on("change", this.renderTable, this);
    },
    
    renderTopMatter: function() {
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selection["dataset"],
                "dataset_attr": "document_count",
        }, function(data) {
            var documentCount = data.datasets[selection["dataset"]].document_count;
            var pageNumber = this.model.attributes["documentContinue"]/this.model.attributes["displayNDocuments"] + 1;
            d3.select(this.el).select("#top-matter-container")
                .html("<p>Document Count: "+documentCount+"</p><p>Page: "+pageNumber+"</p>");
        }.bind(this), this.renderError.bind(this));
    },
    
    tableTemplate:
"<div class=\"row\"><div class=\"col-xs-1\">"+
"    <span class=\"glyphicon glyphicon-step-backward\"></span>"+
"    <span class=\"glyphicon glyphicon-chevron-left\"></span>"+
"</div>"+
"<div id=\"documents-table-container\" class=\"col-xs-10\"></div>"+
"<div class=\"col-xs-1\">"+
"    <span class=\"glyphicon glyphicon-chevron-right\"></span>"+
"    <span class=\"glyphicon glyphicon-step-forward\"></span>"+
"</div></div>",
    
    renderTable: function() {
        var container = d3.select("#documents-container").html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selection["dataset"],
                "dataset_attr": "document_count",
                "documents": "*",
                "document_continue": this.model.attributes["documentContinue"],
                "document_limit": this.model.attributes["displayNDocuments"],
        }, function(data) {
            var documents = extractDocuments(data);
            var documentCount = data.datasets[selection["dataset"]].document_count;
            var documentContinue = this.model.attributes["documentContinue"];
            var displayNDocuments = this.model.attributes["displayNDocuments"];
            container.html(this.tableTemplate);
            container.selectAll("span")
                .style("color", "green")
                .style("font-size", "1.5em");
            container.select(".glyphicon-step-backward")
                .on("click", function() {
                    this.model.set({ documentContinue: 0 });
                }.bind(this))
                .style("display", function() {
                    if(documentContinue === 0) return "none";
                    else return "inline-block";
                });
            container.select(".glyphicon-chevron-left")
                .on("click", function() {
                    this.model.set({ documentContinue: (documentContinue-displayNDocuments) });
                }.bind(this))
                .style("display", function() {
                    if(documentContinue === 0) return "none";
                    else return "inline-block";
                });
            container.select(".glyphicon-step-forward")
                .on("click", function() {
                    this.model.set({ documentContinue: (documentCount - (documentCount%displayNDocuments)) });
                }.bind(this))
                .style("display", function() {
                    if(documentContinue > (documentCount-displayNDocuments)) return "none";
                    else return "inline-block";
                });
            container.select(".glyphicon-chevron-right")
                .on("click", function() {
                    this.model.set({ documentContinue: (documentContinue + displayNDocuments) });
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
            });
        }.bind(this), this.renderError.bind(this));
    },
    
    renderHelpAsHtml: function() {
        return "<p>Select a document from the list to learn more about it. Use the green arrows to navigate.</p>";
    },
});

var DocumentInfoView = DefaultView.extend({
    readableName: "Document Information",
    
    initialize: function() {
        this.selectionModel.on("change:document", this.render, this);
    },
    cleanup: function() {
        this.selectionModel.on(null, this.render, this);
    },
    
    renderText: function(d3Element) {
        d3Element.html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        globalDataModel.submitQueryByHash({
                "datasets": selection["dataset"],
                "documents": selection["document"],
                "document_attr": ["html"],
        }, function(data) {
            var html = extractDocuments(data)[selection["document"]].html;
            d3Element.html("");
            d3Element.append("div")
                .classed("col-xs-12", true)
                .html(html);
        }.bind(this), this.renderError.bind(this));
    },
    
    renderMetadataAndMetrics: function(d3Element) {
        d3Element.html(this.loadingTemplate);
        var selection = this.selectionModel.attributes;
        this.dataModel.submitQueryByHash({
                "datasets": selection["dataset"],
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
        if(this.selectionModel.attributes["document"] === "") {
            this.$el.html("<p>A document needs to be selected in order to use this view.</p>");
            return;
        }
        
        tabs = {
            "Text": this.renderText.bind(this),
            "Metadata/Metrics": this.renderMetadataAndMetrics.bind(this),
        };
        
        this.$el.html("<h3>Document: "+this.selectionModel.get("document")+"</h3>");
        this.$el.append("<div></div>");
        var container = d3.select(this.el).select("div");
        createTabbedContent(container, tabs);
    },
    
    renderHelpAsHtml: function() {
        return "<h4>Text</h4>"+
        "<p>The text of the document as given to the import system.</p>"+
        "<h4>Metadata/Metrics</h4>"+
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
            this.docInfoView.cleanup();
        }
    },
    
    render: function() {
        this.$el.html(this.mainTemplate);
        this.renderTopMatter();
        if(this.docInfoView === undefined) {
            this.docInfoView = new DocumentInfoView({ el: $("#document-info-container") });
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
        this.selectionModel.on("change:analysis", this.render, this);
        this.selectionModel.on("change:document", this.render, this);
    },
    
    render: function() {
        if(this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html("<div id=\"info\"></div>");
            this.cleanupViews();
            if(this.selectionModel.nonEmpty(["document"])) {
                this.subview = new SingleDocumentSubView({ el: "#info" });
            } else {
                this.subview = new AllDocumentsSubView({ el: "#info" });
            }
            this.subview.render();
        } else {
            this.$el.html("<p>You should select a <a href=\"#\">dataset and analysis</a> before proceeding.</p>");
        }
    },
    
    renderHelpAsHtml: function() {
        if(this.subview !== undefined) {
            return this.subview.renderHelpAsHtml();
        }
        return DefaultView.prototype.renderHelpAsHtml();
    },
    
    cleanupViews: function() {
        if(this.subview !== undefined) {
            this.subview.cleanup();
        }
    },
    
    cleanup: function() {
        this.cleanupViews();
        this.selectionModel.off(null, this.render, this);
    },
    
});

// Add the Document View to the top level menu
globalViewModel.addViewClass([], DocumentView);
