"use strict";

var TreemapView = DefaultView.extend({

/******************************************************************************
 *                             STATIC VARIABLES
 ******************************************************************************/

    readableName: 'Treemap',
    shortName: 'treemap',
    
    redirectTemplate:
'<div class="text-center">'+
'   <button class="treemap-redirect btn btn-default">'+
'       <span class="glyphicon glyphicon-chevron-left pewter"></span> Datasets'+
'   </button>'+
'   <span> You need to select a dataset and analysis before using this view. </span>'+
'</div>',

    baseTemplate:
'<div class="row">'+
'   <div class="treemap-container col-xs-12">'+
'   </div>'+
'</div>',

/******************************************************************************
 *                            INHERITED METHODS
 ******************************************************************************/

    initialize: function initialize() {
        this.listenTo(this.selectionModel, "change", this.render);
        this.model = new Backbone.Model();
    },
    
    cleanup: function cleanup() {},
    
    render: function render() {
        if(!this.selectionModel.nonEmpty(['dataset', 'analysis'])) {
            this.$el.html(this.redirectTemplate);
        } else {
            this.$el.html(this.baseTemplate);
            if(this.selectionModel.nonEmpty(['document'])) {
                var topicNumber = this.selectionModel.get('topic');
                if(topicNumber === '') {
                    topicNumber = '0';
                }
                this.renderTopicSimilarity();
            } else {
                this.renderDocuments();
            }
        }
    },

/******************************************************************************
 *                            HELPER METHODS
 ******************************************************************************/

    renderDocuments: function renderDocuments() {
        var $treemapContainer = this.$el.find('.treemap-container');
        $treemapContainer.html(this.loadingTemplate);
        
        var datasetName = this.selectionModel.get('dataset');
        var analysisName = this.selectionModel.get('analysis');
        var request = this.getRequestObject(datasetName, analysisName);
        
        this.dataModel.submitQueryByHash(
            request,
            function callback(data) {
                $treemapContainer.html('');
                var documentData = data.datasets[datasetName].analyses[analysisName].documents;
                this.model.set({ documentData: documentData });
                
                var formatedData = this.formatedDocumentData(documentData, ['metrics', 'Token Count']);
                this.createTreemap(
                    $treemapContainer.get(0), 
                    {
                        data: formatedData,
                        leafNodeFunction: function leafNodeFunction(d, i) {
                            d3.select(this)
                                .attr('data-tg-document-name', d.name)
                                .classed('tg-select pointer', true);
                        },
                    }
                );
            }.bind(this),
            function errorCallback(msg) {
            }.bind(this)
        );
    },
    
    renderTopicSimilarity: function renderTopicSimilarity() {
        
    },
    
    getRequestObject: function getRequestObject(datasetName, analysisName) {
        var result = {
            datasets: datasetName,
            analyses: analysisName,
            documents: '*',
            document_attr: ['metadata', 'metrics'],
            document_continue: 0,
            document_limit: 1000,
        };
        return result;
    },
    
    
    
/******************************************************************************
 *                             PURE FUNCTIONS
 ******************************************************************************/
    
    /**
     * Puts the documents into the format needed for the createTreemap method.
     */
    formatedDocumentData: function formatedDocumentData(documents, dataAccessList) {
        var result = {
            'name': 'documents',
        };
        
        var children = [];
        
        for(var docName in documents) {
            var obj = {};
            obj['name'] = docName;
            var size = documents[docName];
            for(var index in dataAccessList) {
                var accessor = dataAccessList[index];
                size = size[accessor];
            }
            obj['size'] = size;
            children.push(obj);
        }
        result['children'] = children;
        
        return result;
    },
    
    /**
     * el -- the element to render the svg in
     * options -- contains the following:
     * data -- data in the format of { name: name, children: [..], size: optional }
     *         where children is an object like the parent
     *         leaf nodes must have the "size" attribute
     * margin -- { top: 40, right: 10, bottom: 10, left: 10 }
     * width -- number
     * height -- number
     */
    createTreemap: function createTreemap(el, options) {
        var defaults = {
            data: JSON.parse(temp_data),
            margin: { top: 0, right: 0, bottom: 0, left: 0 },
            width: 960,
            height: 500,
            parentColorScale: d3.scale.category20c(),
            childColorScale: d3.scale.category20c(),
            leafNodeFunction: function() {}, 
        };
        var options = _.extend({}, defaults, options);
        console.log('Options:');
        console.log(options);
        
        var d3El = d3.select(el);
        var treemap = d3.layout.treemap()
            .size([options.width, options.height])
            .sticky(true)
            .value(function (d) { return d.size; });
        
        var div = d3El.append('div')
            .classed('.treemap-div', true)
            .style('position', 'relative')
            .style("width", (options.width + options.margin.left + options.margin.right) + "px")
            .style("height", (options.height + options.margin.top + options.margin.bottom) + "px")
            .style("left", options.margin.left + "px")
            .style("top", options.margin.top + "px");
        
        var node = div.datum(options.data)
            .selectAll('.node')
            .data(treemap.nodes)
            .enter()
            .append('div')
            .classed('node', true)
            .each(function(d, i) {
                d.children ? null : options.leafNodeFunction.call(this, d, i);
            })
            .style({ 
                'border': 'solid 1px white', 
                'font': '10px sans-serif', 
                'line-height': '12px',
                'overflow': 'hidden',
                'position': 'absolute',
                'text-indent': '2px',
            })
            .call(position)
            .style('background', function(d) { return d.children ? options.parentColorScale(d.name) : options.childColorScale(d.name); })
            .text(function(d) { return d.children ? null : d.name; });
        
        function position() {
            this.style("left", function(d) { return d.x + "px"; })
                .style("top", function(d) { return d.y + "px"; })
                .style("width", function(d) { return Math.max(0, d.dx - 1) + "px"; })
                .style("height", function(d) { return Math.max(0, d.dy - 1) + "px"; });
        }
    },
    
/******************************************************************************
 *                           EVENT HANDLERS
 ******************************************************************************/
    
    events: {
        'click .treemap-redirect': 'clickRedirect',
    },
    
    clickRedirect: function clickRedirect() {
        this.viewModel.set({ currentView: 'datasets' });
    },
    
});

addViewClass(['Visualizations'], TreemapView);



var curLayer = -1;

function initTreemap() {
	var w = 960, h = 500;
	var treemap = d3.layout.treemap().size([ w, h ]).sticky(false).value(function(d) {
		return d.size;
	});

	if (d3.select("#treemap_container") != null) {
		d3.select("#treemap_container").remove();
	}
	if (d3.select("#titleDiv") != null) {
		d3.select("#titleDiv").remove();
	}

	var titleDiv = d3.select("#titleDiv");
	var colorDiv = d3.select("#colorDiv");
	var mapDiv = d3.select("#chart").append("div").style("position", "relative").style("width", w + "px").style(
			"height", h + "px").style("float", "left").attr("id", "treemap_container");
	return {
		"div" : mapDiv,
		"treemap" : treemap,
		"title" : titleDiv,
		"colorDef" : colorDiv
	};
}

function setCookie(c_name,value,exdays){
	var exdate=new Date();
	exdate.setDate(exdate.getDate() + exdays);
	var c_value=escape(value) + ((exdays==null) ? "" : "; expires="+exdate.toUTCString());
	document.cookie=c_name + "=" + c_value;
}

function getCookie(c_name){
	var i,x,y,ARRcookies=document.cookie.split(";");
	for (i=0;i<ARRcookies.length;i++){
		x=ARRcookies[i].substr(0,ARRcookies[i].indexOf("="));
		y=ARRcookies[i].substr(ARRcookies[i].indexOf("=")+1);
		x=x.replace(/^\s+|\s+$/g,"");
		if (x==c_name){
			return unescape(y);
		}
	}
}

function createDefaultTreemap(defaultDataset){
	// if the cookie is set to a dataset, dispaly that dataset
	var chosedDataset = getCookie("chosedDataset"); 
	if (chosedDataset != null && chosedDataset != ""){
		createDocTreemap(chosedDataset);
	}else{
		if(defaultDataset != null && defaultDataset != "")
			createDocTreemap(defaultDataset);
		else
			alert("choose a dataset!");
	}
}

// given a document, return a topic treemap of that document
function createTopicTreemap(docId,datasetName, topicId) {
	url = "/feeds/topic-token-counts/datasets/"+datasetName+"/analyses/lda100topics/doc_id/" + docId;

	// init default value
	if (typeof (topicId) === 'undefined') {
	} else {
		url += "/cmp_topic_id/" + topicId;
	}

	var mapObj = initTreemap();
	d3.json(url, function(json) {
        
		if(json!=null) {
			defineColor(mapObj);
			d3.select("#curTopic").text("> " + json['name']);
	
			// put the cell(rectangle) in the treemp_container
			mapObj.div.data([ json ]).selectAll("div").data(mapObj.treemap.nodes).enter().append("div").attr("class",
					"cell").attr("title", function(d) {
				if (d.size)
					return "topic: " + d.name + ", tokens: " + d.size + ", similarity: " + d.similarity;
			}).style("background", function(d) {
				// cell color
				return getColor(parseFloat(d.similarity));
			}).call(cell).text(function(d) {
				if (d.size > 30)
					return d.children ? null : d.name;
			}).on("mouseover", function() {
				d3.select(this).style("border", "3px solid black");
				if (curLayer == -1) {
					curLayer = d3.select(this).attr("z-index");
				}
			}).on("mouseout", function() {
				d3.select(this).style("border", "1px solid black");
			}).attr("onclick", function(d) {
				if (d.tid)
					return "createTopicTreemap(" + docId + ",'" + datasetName + "'," + d.tid +")";
			});
		}
	});
}

// given a dataset, return a document treemap of that dataset
function createDocTreemap(datasetName) {

	// oldDataset: change active to normal
	// cur dataset: change normal to active
	var oldChosedDataset = getCookie('chosedDataset');
	if (oldChosedDataset != null && oldChosedDataset != ""){
		d3.select("#id_"+oldChosedDataset).attr("class", "normal");
	}
	d3.select("#id_"+datasetName).attr("class", "active");						
	setCookie('chosedDataset', datasetName, 30);	
	
	d3.select("#curTopic").text("");
	var mapObj = initTreemap();
	// mapObj.colorDef.text("Color: represent different document");
	mapObj.colorDef.text("");
	d3.json("/feeds/document-token-counts/datasets/"+datasetName, function(json) {
		if(json!=null) {
			// put the cell(rectangle) in the treemp_container
			mapObj.div.data([ json ]).selectAll("div").data(mapObj.treemap.nodes).enter().append("div").attr("class",
					"cell").attr("title", function(d) {
				if (d.size)
					return d.size + " tokens";
			}).attr("onclick", function(d) {
				if (d.child_doc_ids) {
					return "createTopicTreemap(" + d.child_doc_ids[0] + ",'"+datasetName+"')";
				}
			}).style("background", function(d) {
				// cell color
				return getRandomColor();
			}).call(cell).text(function(d) {
				// cell title
				return d.children ? null : d.name;
			});
		}
	});
}

function defineColor(mapObj) {
	if (mapObj.colorDef[0][0].childElementCount < 2) {
		var colorN = 8;
		var range = d3.range(0, 1, 0.125);
		mapObj.colorDef.append("div").text("Similarity:").attr("id", "colorDef");
		for ( var i = 0; i < colorN; i++) {
			mapObj.colorDef.append("div").style("background", function() {
				return getColor(range[i]);
			}).style("float", "left").text(function(d) {
				if (i + 1 < colorN)
					return " < " + range[i + 1];
				else if (i + 1 == colorN)
					return " < 1";
			});
		}
		mapObj.colorDef.append("div");
	}
}

function cell() {
	this.style("left", function(d) {
		return d.x + "px";
	}).style("top", function(d) {
		return d.y + "px";
	}).style("width", function(d) {
		return Math.max(0, d.dx - 1) + "px";
	}).style("height", function(d) {
		return Math.max(0, d.dy - 1) + "px";
	});
}

function getRandomColor() {
	color = colorbrewer.Tobias[22][Math.floor(Math.random() * colorbrewer.Tobias[22].length)];
	return color;
}

function getColor(similarity) {
	var colorScheme = 8;
	if (similarity < 0.125)
		return colorbrewer.Tobias[colorScheme][0];
	else if (similarity < 0.25)
		return colorbrewer.Tobias[colorScheme][1];
	else if (similarity < 0.375)
		return colorbrewer.Tobias[colorScheme][2];
	else if (similarity < 0.5)
		return colorbrewer.Tobias[colorScheme][3];
	else if (similarity < 0.625)
		return colorbrewer.Tobias[colorScheme][4];
	else if (similarity < 0.725)
		return colorbrewer.Tobias[colorScheme][5];
	else if (similarity < 0.875)
		return colorbrewer.Tobias[colorScheme][6];
	else
		return colorbrewer.Tobias[colorScheme][7];
}

var temp_data = '{  "name": "flare",  "children": [   {    "name": "analytics",    "children": [     {      "name": "cluster",      "children": [       {"name": "AgglomerativeCluster", "size": 3938},       {"name": "CommunityStructure", "size": 3812},       {"name": "HierarchicalCluster", "size": 6714},       {"name": "MergeEdge", "size": 743}      ]     },     {      "name": "graph",      "children": [       {"name": "BetweennessCentrality", "size": 3534},       {"name": "LinkDistance", "size": 5731},       {"name": "MaxFlowMinCut", "size": 7840},       {"name": "ShortestPaths", "size": 5914},       {"name": "SpanningTree", "size": 3416}      ]     },     {      "name": "optimization",      "children": [       {"name": "AspectRatioBanker", "size": 7074}      ]     }    ]   },   {    "name": "animate",    "children": [     {"name": "Easing", "size": 17010},     {"name": "FunctionSequence", "size": 5842},     {      "name": "interpolate",      "children": [       {"name": "ArrayInterpolator", "size": 1983},       {"name": "ColorInterpolator", "size": 2047},       {"name": "DateInterpolator", "size": 1375},       {"name": "Interpolator", "size": 8746},       {"name": "MatrixInterpolator", "size": 2202},       {"name": "NumberInterpolator", "size": 1382},       {"name": "ObjectInterpolator", "size": 1629},       {"name": "PointInterpolator", "size": 1675},       {"name": "RectangleInterpolator", "size": 2042}      ]     },     {"name": "ISchedulable", "size": 1041},     {"name": "Parallel", "size": 5176},     {"name": "Pause", "size": 449},     {"name": "Scheduler", "size": 5593},     {"name": "Sequence", "size": 5534},     {"name": "Transition", "size": 9201},     {"name": "Transitioner", "size": 19975},     {"name": "TransitionEvent", "size": 1116},     {"name": "Tween", "size": 6006}    ]   },   {    "name": "data",    "children": [     {      "name": "converters",      "children": [       {"name": "Converters", "size": 721},       {"name": "DelimitedTextConverter", "size": 4294},       {"name": "GraphMLConverter", "size": 9800},       {"name": "IDataConverter", "size": 1314},       {"name": "JSONConverter", "size": 2220}      ]     },     {"name": "DataField", "size": 1759},     {"name": "DataSchema", "size": 2165},     {"name": "DataSet", "size": 586},     {"name": "DataSource", "size": 3331},     {"name": "DataTable", "size": 772},     {"name": "DataUtil", "size": 3322}    ]   },   {    "name": "display",    "children": [     {"name": "DirtySprite", "size": 8833},     {"name": "LineSprite", "size": 1732},     {"name": "RectSprite", "size": 3623},     {"name": "TextSprite", "size": 10066}    ]   },   {    "name": "flex",    "children": [     {"name": "FlareVis", "size": 4116}    ]   },   {    "name": "physics",    "children": [     {"name": "DragForce", "size": 1082},     {"name": "GravityForce", "size": 1336},     {"name": "IForce", "size": 319},     {"name": "NBodyForce", "size": 10498},     {"name": "Particle", "size": 2822},     {"name": "Simulation", "size": 9983},     {"name": "Spring", "size": 2213},     {"name": "SpringForce", "size": 1681}    ]   },   {    "name": "query",    "children": [     {"name": "AggregateExpression", "size": 1616},     {"name": "And", "size": 1027},     {"name": "Arithmetic", "size": 3891},     {"name": "Average", "size": 891},     {"name": "BinaryExpression", "size": 2893},     {"name": "Comparison", "size": 5103},     {"name": "CompositeExpression", "size": 3677},     {"name": "Count", "size": 781},     {"name": "DateUtil", "size": 4141},     {"name": "Distinct", "size": 933},     {"name": "Expression", "size": 5130},     {"name": "ExpressionIterator", "size": 3617},     {"name": "Fn", "size": 3240},     {"name": "If", "size": 2732},     {"name": "IsA", "size": 2039},     {"name": "Literal", "size": 1214},     {"name": "Match", "size": 3748},     {"name": "Maximum", "size": 843},     {      "name": "methods",      "children": [       {"name": "add", "size": 593},       {"name": "and", "size": 330},       {"name": "average", "size": 287},       {"name": "count", "size": 277},       {"name": "distinct", "size": 292},       {"name": "div", "size": 595},       {"name": "eq", "size": 594},       {"name": "fn", "size": 460},       {"name": "gt", "size": 603},       {"name": "gte", "size": 625},       {"name": "iff", "size": 748},       {"name": "isa", "size": 461},       {"name": "lt", "size": 597},       {"name": "lte", "size": 619},       {"name": "max", "size": 283},       {"name": "min", "size": 283},       {"name": "mod", "size": 591},       {"name": "mul", "size": 603},       {"name": "neq", "size": 599},       {"name": "not", "size": 386},       {"name": "or", "size": 323},       {"name": "orderby", "size": 307},       {"name": "range", "size": 772},       {"name": "select", "size": 296},       {"name": "stddev", "size": 363},       {"name": "sub", "size": 600},       {"name": "sum", "size": 280},       {"name": "update", "size": 307},       {"name": "variance", "size": 335},       {"name": "where", "size": 299},       {"name": "xor", "size": 354},       {"name": "_", "size": 264}      ]     },     {"name": "Minimum", "size": 843},     {"name": "Not", "size": 1554},     {"name": "Or", "size": 970},     {"name": "Query", "size": 13896},     {"name": "Range", "size": 1594},     {"name": "StringUtil", "size": 4130},     {"name": "Sum", "size": 791},     {"name": "Variable", "size": 1124},     {"name": "Variance", "size": 1876},     {"name": "Xor", "size": 1101}    ]   },   {    "name": "scale",    "children": [     {"name": "IScaleMap", "size": 2105},     {"name": "LinearScale", "size": 1316},     {"name": "LogScale", "size": 3151},     {"name": "OrdinalScale", "size": 3770},     {"name": "QuantileScale", "size": 2435},     {"name": "QuantitativeScale", "size": 4839},     {"name": "RootScale", "size": 1756},     {"name": "Scale", "size": 4268},     {"name": "ScaleType", "size": 1821},     {"name": "TimeScale", "size": 5833}    ]   },   {    "name": "util",    "children": [     {"name": "Arrays", "size": 8258},     {"name": "Colors", "size": 10001},     {"name": "Dates", "size": 8217},     {"name": "Displays", "size": 12555},     {"name": "Filter", "size": 2324},     {"name": "Geometry", "size": 10993},     {      "name": "heap",      "children": [       {"name": "FibonacciHeap", "size": 9354},       {"name": "HeapNode", "size": 1233}      ]     },     {"name": "IEvaluable", "size": 335},     {"name": "IPredicate", "size": 383},     {"name": "IValueProxy", "size": 874},     {      "name": "math",      "children": [       {"name": "DenseMatrix", "size": 3165},       {"name": "IMatrix", "size": 2815},       {"name": "SparseMatrix", "size": 3366}      ]     },     {"name": "Maths", "size": 17705},     {"name": "Orientation", "size": 1486},     {      "name": "palette",      "children": [       {"name": "ColorPalette", "size": 6367},       {"name": "Palette", "size": 1229},       {"name": "ShapePalette", "size": 2059},       {"name": "SizePalette", "size": 2291}      ]     },     {"name": "Property", "size": 5559},     {"name": "Shapes", "size": 19118},     {"name": "Sort", "size": 6887},     {"name": "Stats", "size": 6557},     {"name": "Strings", "size": 22026}    ]   },   {    "name": "vis",    "children": [     {      "name": "axis",      "children": [       {"name": "Axes", "size": 1302},       {"name": "Axis", "size": 24593},       {"name": "AxisGridLine", "size": 652},       {"name": "AxisLabel", "size": 636},       {"name": "CartesianAxes", "size": 6703}      ]     },     {      "name": "controls",      "children": [       {"name": "AnchorControl", "size": 2138},       {"name": "ClickControl", "size": 3824},       {"name": "Control", "size": 1353},       {"name": "ControlList", "size": 4665},       {"name": "DragControl", "size": 2649},       {"name": "ExpandControl", "size": 2832},       {"name": "HoverControl", "size": 4896},       {"name": "IControl", "size": 763},       {"name": "PanZoomControl", "size": 5222},       {"name": "SelectionControl", "size": 7862},       {"name": "TooltipControl", "size": 8435}      ]     },     {      "name": "data",      "children": [       {"name": "Data", "size": 20544},       {"name": "DataList", "size": 19788},       {"name": "DataSprite", "size": 10349},       {"name": "EdgeSprite", "size": 3301},       {"name": "NodeSprite", "size": 19382},       {        "name": "render",        "children": [         {"name": "ArrowType", "size": 698},         {"name": "EdgeRenderer", "size": 5569},         {"name": "IRenderer", "size": 353},         {"name": "ShapeRenderer", "size": 2247}        ]       },       {"name": "ScaleBinding", "size": 11275},       {"name": "Tree", "size": 7147},       {"name": "TreeBuilder", "size": 9930}      ]     },     {      "name": "events",      "children": [       {"name": "DataEvent", "size": 2313},       {"name": "SelectionEvent", "size": 1880},       {"name": "TooltipEvent", "size": 1701},       {"name": "VisualizationEvent", "size": 1117}      ]     },     {      "name": "legend",      "children": [       {"name": "Legend", "size": 20859},       {"name": "LegendItem", "size": 4614},       {"name": "LegendRange", "size": 10530}      ]     },     {      "name": "operator",      "children": [       {        "name": "distortion",        "children": [         {"name": "BifocalDistortion", "size": 4461},         {"name": "Distortion", "size": 6314},         {"name": "FisheyeDistortion", "size": 3444}        ]       },       {        "name": "encoder",        "children": [         {"name": "ColorEncoder", "size": 3179},         {"name": "Encoder", "size": 4060},         {"name": "PropertyEncoder", "size": 4138},         {"name": "ShapeEncoder", "size": 1690},         {"name": "SizeEncoder", "size": 1830}        ]       },       {        "name": "filter",        "children": [         {"name": "FisheyeTreeFilter", "size": 5219},         {"name": "GraphDistanceFilter", "size": 3165},         {"name": "VisibilityFilter", "size": 3509}        ]       },       {"name": "IOperator", "size": 1286},       {        "name": "label",        "children": [         {"name": "Labeler", "size": 9956},         {"name": "RadialLabeler", "size": 3899},         {"name": "StackedAreaLabeler", "size": 3202}        ]       },       {        "name": "layout",        "children": [         {"name": "AxisLayout", "size": 6725},         {"name": "BundledEdgeRouter", "size": 3727},         {"name": "CircleLayout", "size": 9317},         {"name": "CirclePackingLayout", "size": 12003},         {"name": "DendrogramLayout", "size": 4853},         {"name": "ForceDirectedLayout", "size": 8411},         {"name": "IcicleTreeLayout", "size": 4864},         {"name": "IndentedTreeLayout", "size": 3174},         {"name": "Layout", "size": 7881},         {"name": "NodeLinkTreeLayout", "size": 12870},         {"name": "PieLayout", "size": 2728},         {"name": "RadialTreeLayout", "size": 12348},         {"name": "RandomLayout", "size": 870},         {"name": "StackedAreaLayout", "size": 9121},         {"name": "TreeMapLayout", "size": 9191}        ]       },       {"name": "Operator", "size": 2490},       {"name": "OperatorList", "size": 5248},       {"name": "OperatorSequence", "size": 4190},       {"name": "OperatorSwitch", "size": 2581},       {"name": "SortOperator", "size": 2023}      ]     },     {"name": "Visualization", "size": 16540}    ]   }  ] } ';
