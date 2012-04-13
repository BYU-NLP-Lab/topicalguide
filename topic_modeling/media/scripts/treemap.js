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