/**
 * Responsible for rendering the lists of documents for the user to select a
 * document from.
 */
var AllDocumentsView = DefaultView.extend({
    readableName: "All Documents",
    shortName: "all_documents",
    
    redirectTemplate:
'<div class="text-center">'+
'   <button class="all-docs-redirect btn btn-default">'+
'       <span class="glyphicon glyphicon-chevron-left pewter"></span> Datasets'+
'   </button>'+
'   <span> You need to select a dataset and analysis before using this view. </span>'+
'</div>',
    
    htmlTemplate:
'<div class="all-docs-top-matter-container text-center">'+
'    <form role="form" class="form-inline center">'+
'    <div class="form-group">'+
'    <div class="input-group">'+
'        <div class="input-group-addon">Page</div>'+
'        <input class="all-docs-page form-control" type="number" placeholder="">'+
'    </div>'+
'    </div>'+
'    <div class="form-group">'+
'    <div class="input-group">'+
'        <div class="input-group-addon">Documents per Page</div>'+
'        <input class="all-docs-num-per-page form-control" type="number" placeholder="">'+
'    </div>'+
'    </div>'+
'    <div>'+
'        <span>Showing documents <span class="all-docs-start-range"></span> &nbsp;&ndash;&nbsp; <span class="all-docs-end-range"></span> of <span class="all-docs-total-docs">__</span> documents.</span>'+
'    </div>'+
'    </form>'+
'</div>'+
'<div class="all-docs-documents-container">'+
'    <div class="row">'+
'        <div class="all-docs-left-nav col-xs-1 text-center">'+
'           <span class="all-docs-beginning pointer all-docs-nav">' + icons.beginning + '</span>'+
'           <span class="all-docs-previous pointer all-docs-nav">' + icons.previous + '</span>'+
'        </div>'+
'        <div class="all-docs-table-container col-xs-10"></div>'+
'        <div class="all-docs-right-nav col-xs-1 text-center">'+
'           <span class="all-docs-next pointer all-docs-nav">' + icons.next + '</span>'+
'           <span class="all-docs-end pointer all-docs-nav">' + icons.end + '</span>'+
'        </div>'+
'    </div>'+
'</div>',

    helpTemplate:
'<p>Select/click a document from the list to learn more about it. Use the green arrows to navigate the pages.</p>',
    
    initialize: function initialize() {
        var defaultSettings = {
            page: 1,
            docsPerPage: 30,
            ascending: true,
        };
        // Set the settingsModel to the defaults if the values aren't present already.
        this.settingsModel.set(_.extend(defaultSettings, this.settingsModel.attributes));
        this.listenTo(this.selectionModel, "change:analysis", this.render);
        
        var defaultData = {
            documents: {},
        };
        this.model = new Backbone.Model();
        this.model.set(defaultData);
    },
    
    cleanup: function cleanup(topics) {},
    
    renderHelpAsHtml: function renderHelpAsHtml() {
        return this.helpTemplate;
    },
    
    render: function render() {
        // Check that dataset and analysis are set.
        if(!this.selectionModel.nonEmpty(["dataset", "analysis"])) {
            this.$el.html(this.redirectTemplate);
            return;
        }
        
        this.$el.html(this.loadingTemplate);
        
        // Get the total number of documents.
        var dataset = this.selectionModel.get("dataset");
        this.documentCount = this.dataModel.getDatasetDocumentCount(dataset);
        this.maxDocumentsPerRequest = this.dataModel.getServerInfo()['max_documents_per_request'];
        
        var el = d3.select(this.el);
        
        // Display the page.
        el.html(this.htmlTemplate);
        el.selectAll(".all-docs-nav")
            .style("font-size", "1.5em");
        
        // Setup listeners
        this.listenTo(this.settingsModel, "change:page change:docsPerPage", this.updateDocumentsRange);
        this.listenTo(this.settingsModel, "change:page change:docsPerPage", this.updateAllDocumentsTable);
        this.listenTo(this.selectionModel, "change:document", this.updateHighlightedRow);
        
        // Display
        el.select(".all-docs-total-docs")
            .text(this.documentCount);
        this.updatePageField();
        this.updateDocumentsPerPageField();
        this.updateDocumentsRange();
        this.updateAllDocumentsTable();
        
        // Create popover functionality for document metadata and metrics.
        var that = this;
        this.$el.popover({
            container: this.$el.get(0),
            content: function renderDocumentPopupContent() {
                // Construct the contents of the popover.
                var emptyElement = document.createElement("div");
                var documentName =  $(this).attr("data-tg-document-name");
                var documents = that.model.get("documents");
                var metadata = documents[documentName].metadata;
                metadata = _.reduce(metadata, function keyToReadableKey(result, value, key) {
                    result[tg.str.toTitleCase(key.replace(/_/g, " "))] = value;
                    return result;
                }, {});
                var metrics = documents[documentName].metrics;
                tg.gen.createTableFromHash(emptyElement, metadata, ["Metadata", "Value"], "No metadata available.");
                tg.gen.createTableFromHash(emptyElement, metrics, ["Metric", "Value"], "No metrics available.");
                return $(emptyElement).html();
            },
            html: true,
            placement: "auto right",
            selector: ".all-docs-document-popover",
            template: '<div class="popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>',
            title: "Metadata and Metrics",
            trigger: "hover",
        });
    },
    
    events: {
        "click .all-docs-redirect": "clickRedirect",
        "click .all-docs-next": "clickNext",
        "click .all-docs-previous": "clickPrevious",
        "click .all-docs-beginning": "clickBeginning",
        "click .all-docs-end": "clickEnd",
        "change .all-docs-page": "changePageNumber",
        "change .all-docs-num-per-page": "changeDocumentsPerPage",
        "click .all-docs-explore": "clickExplore",
    },
    
    /**
     * Go to the datasets page.
     */
    clickRedirect: function clickRedirect() {
        this.viewModel.set({ currentView: "datasets" });
    },
    
    /**
     * Increment the page number.
     */
    clickNext: function clickNext(e) {
        this.setPage(this.settingsModel.get("page") + 1);
    },
    
    /**
     * Decrement the page number.
     */
    clickPrevious: function clickPrevious(e) {
        this.setPage(this.settingsModel.get("page") - 1);
    },
    
    /**
     * Set page number to 1.
     */
    clickBeginning: function clickBeginning(e) {
        this.setPage(1);
    },
    
    /**
     * Set the page number to the last possible.
     */
    clickEnd: function clickEnd(e) {
        this.setPage(this.getLastPage());
    },
    
    /**
     * Jump to the page number.
     */
    changePageNumber: function changePageNumber(e) {
        var page = parseInt(d3.select(this.el).select(".all-docs-page").property("value"));
        if(isInteger(page)) {
            this.setPage(page);
        } else {
            this.updatePageField();
        }
    },
    
    /**
     * Change the documents per page.
     * Update the page number as necessary (keep the first document currently visible, visible on the new page).
     */
    changeDocumentsPerPage: function changeDocumentsPerPage(e) {
        var perPage = parseInt(d3.select(this.el).select(".all-docs-num-per-page").property("value"));
        if(isInteger(perPage)) {
            this.setDocumentsPerPage(perPage);
        } else {
            this.updateDocumentsPerPageField();
        }
    },
    
    /**
     * Redirect the user to the single document view.
     */
    clickExplore: function clickExplore(e) {
        setTimeout(function delayRedirect() {
            this.viewModel.set({ currentView: "single_document" });
        }.bind(this), 100);
    },
    
    getLastPage: function getLastPage() {
        return Math.ceil(this.documentCount/this.settingsModel.get("docsPerPage"));
    },
    
    /**
     * Gets the document index at the top of the page.
     */
    getDocumentContinue: function getDocumentContinue() {
        var page = this.settingsModel.get("page");
        var currPerPage = this.settingsModel.get("docsPerPage");
        return (page*currPerPage - currPerPage);
    },
    
    /**
     * Sets the page number, the pageNumber is forced to be in the correct range.
     * pageNumber -- an integer
     */
    setPage: function setPage(pageNumber) {
        var lastPage = this.getLastPage();
        if(pageNumber > lastPage) {
            pageNumber = lastPage;
        }
        if(pageNumber < 1) {
            pageNumber = 1;
        }
        this.settingsModel.set({ page: pageNumber });
        this.updatePageField();
    },
    
    /**
     * Sets the documents per page, the integer is forced to be greater than one
     * and less than or equal to the maximum documents per request.
     */
    setDocumentsPerPage: function setDocumentsPerPage(perPage) {
        if(perPage < 1) {
            perPage = 1;
        }
        if(perPage > this.maxDocumentsPerRequest) {
            perPage = this.maxDocumentsPerRequest;
        }
        if(perPage > this.documentCount) {
            perPage = this.documentCount;
        }
        
        var docContinue = this.getDocumentContinue();
        var page = Math.floor((docContinue/perPage) + 1);
        
        this.settingsModel.set({ page: page, docsPerPage: perPage });
        this.updatePageField();
        this.updateDocumentsPerPageField();
    },
    
    /**
     * Updates the page field.
     */
    updatePageField: function updatePageField() {
        d3.select(this.el).select(".all-docs-page").property("value", this.settingsModel.get("page"));
    },
    
    /**
     * Updates the documents per page field.
     */
    updateDocumentsPerPageField: function updateDocumentsPerPageField() {
        d3.select(this.el).select(".all-docs-num-per-page").property("value", this.settingsModel.get("docsPerPage"));
    },
    
    /**
     * Updates the document index range text.
     */
    updateDocumentsRange: function updateDocumentsRange() {
        var start = this.getDocumentContinue() + 1;
        var end = start + this.settingsModel.get("docsPerPage") - 1;
        if(end > this.documentCount) {
            end = this.documentCount;
        }
        d3.select(this.el).select(".all-docs-start-range").text(start);
        d3.select(this.el).select(".all-docs-end-range").text(end);
    },
    
    /**
     * When a document is selected highlight the right row.
     */
    updateHighlightedRow: function updateHighlightedRow() {
        var that = this;
        d3.select(this.el).selectAll(".all-docs-update-document-highlight")
            .classed("success", function isRowHighlighted(d, i) {
                if(d3.select(this).attr("data-tg-document-name") === that.selectionModel.get("document")) {
                    return true;
                } else {
                    return false;
                }
            });
    },
    
    /**
     * Updates the table by sending a query to the server and re-rendering
     * to show the desired documents.
     */
    updateAllDocumentsTable: function updateAllDocumentsTable() {
        var container = this.$el.find(".all-docs-table-container");
        container.html(this.loadingTemplate);
        var datasetName = this.selectionModel.get("dataset");
        var analysisName = this.selectionModel.get("analysis");
        this.dataModel.submitQueryByHash({
                "datasets": datasetName,
                "analyses": analysisName,
                "dataset_attr": ["document_count"],
                "documents": "*",
                "document_continue": this.getDocumentContinue(),
                "document_limit": this.settingsModel.get("docsPerPage"),
                "document_attr": ["metadata", "metrics", "intro_snippet"],
        }, function dataCallback(data) {
            var that = this;
            
            var documents = extractDocuments(data, this.selectionModel);
            this.model.set({ documents: documents });
            var documentCount = data.datasets[datasetName].document_count;
            var documentContinue = this.settingsModel.get("documentContinue");
            var displayNDocuments = this.settingsModel.get("displayNDocuments");
            container.html('<span class="text-center"></span>');
            container = container.find("span");
            
            var header = ["", "Document", "Preview", ""];
            var sortable = [false, true, true, false];
            var sortBy = 1;
            var sortAscending = this.settingsModel.get("ascending");
            var onSortFunction = function onSortFunction(index, ascending) {
                this.settingsModel.set({ ascending: !this.settingsModel.get("ascending") });
            }.bind(this);
            var tableData = _.map(documents, function createTableData(value, key) {
				return [key, key, documents[key]["intro_snippet"], key];
			});
            var dataFunctions = [
                function col1(d, i) {
                    var el = d3.select(this)
                        .append("span")
                        .attr("data-tg-document-name", d)
                        .classed("tg-fav", true);
                    tg.site.initFav(el[0][0], that.favsModel);
                },
                function col2(d, i) {
                    d3.select(this)
                        .text(d);
                },
                function col3(snippet, i) {
					d3.select(this)
						.append('div')
						.style({ "float": "left" , "text-align": "left", "max-width": "200px" })
						.text(snippet);
				},
                function col4(d, i) {
                    d3.select(this)
                        .append("button")
                        .classed("btn btn-success", true)
                        .style({ "padding": "1px 4px" })
                        .attr("data-tg-document-name", d)
                        .classed("tg-select all-docs-explore", true)
                        .text("Explore!");
                },
            ];
            var tableRowFunction = function tableRowFunction(rowData, index) {
                d3.select(this)
                    .attr("data-tg-document-name", rowData[1])
					.classed("tg-select pointer", true)
                    .classed("all-docs-update-document-highlight all-docs-document-popover", true)
                    .classed("success", function isRowHighlighted(d, i) {
                        if(d3.select(this).attr("data-tg-document-name") === that.selectionModel.get("document")) {
                            return true;
                        } else {
                            return false;
                        }
                    });
            };
            
            tg.gen.createSortableTable(container.get(0), {
                header: header, 
                sortable: sortable,
                sortBy: sortBy,
                sortAscending: sortAscending,
                onSortFunction: onSortFunction,
                data: tableData,
                dataFunctions: dataFunctions,
                tableRowFunction: tableRowFunction,
                shrinkTable: true,
            });
            
        }.bind(this), this.renderError.bind(this));
    },
    
});

addViewClass(["Document"], AllDocumentsView);
