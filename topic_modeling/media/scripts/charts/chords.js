
var width = 720,
    height = 720,
    outerRadius = Math.min(width, height) / 2 - 10,
    innerRadius = outerRadius - 24;

var formatPercent = d3.format(".1%");

var arc = d3.svg.arc()
    .innerRadius(innerRadius)
    .outerRadius(outerRadius);

var layout = d3.layout.chord()
    .padding(.04)
    .sortSubgroups(d3.descending)
    .sortChords(d3.ascending);

var path = d3.svg.chord()
    .radius(innerRadius);

var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height)
  .append("g")
    .attr("id", "circle")
    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

svg.append("circle") .attr("r", outerRadius);

var dumb_matrix = [[11975,  5871, 8916, 2868],
               [ 1951, 10048, 2060, 6171],
               [ 8010, 16145, 8090, 8045],
               [ 1013,   990,  940, 6907]];

d3.json(URLS['pairwise'], function (data) {
 layout.matrix(data);

               /*
 // Add a group per neighborhood.
 var group = svg.selectAll(".group")
 .data(layout.groups)
 .enter().append("g")
 .attr("class", "group")
 .on("mouseover", mouseover);

 // Add a mouseover title.
 group.append("title").text(function(d, i) {
 return cities[i].name + ": " + formatPercent(d.value) + " of origins";
 });

 // Add the group arc.
 var groupPath = group.append("path")
 .attr("id", function(d, i) { return "group" + i; })
 .attr("d", arc)
 .style("fill", function(d, i) { return cities[i].color; });

 // Add a text label.
 var groupText = group.append("text")
 .attr("x", 6)
 .attr("dy", 15);

 groupText.append("textPath")
 .attr("xlink:href", function(d, i) { return "#group" + i; })
 .text(function(d, i) { return cities[i].name; });

 // Remove the labels that don't fit. :(
 groupText.filter(function(d, i) { return groupPath[0][i].getTotalLength() / 2 - 16 < this.getComputedTextLength(); })
 .remove();
 */

 // Add the chords.
 var chord = svg.selectAll(".chord")
 .data(layout.chords)
 .enter().append("path")
 .attr("class", "chord")
 // .style("fill", function(d) { return cities[d.source.index].color; })
 .attr("d", path);

 /*
 // Add an elaborate mouseover title for each chord.
 chord.append("title").text(function(d) {
 return cities[d.source.index].name
 + " → " + cities[d.target.index].name
 + ": " + formatPercent(d.source.value)
 + "\n" + cities[d.target.index].name
 + " → " + cities[d.source.index].name
 + ": " + formatPercent(d.target.value);
 });
 */

 function mouseover(d, i) {
  chord.classed("fade", function(p) {
   return p.source.index != i
   && p.target.index != i;
  });
 }
});

