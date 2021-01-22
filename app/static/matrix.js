
// Set global dimensions
var margin = {top: 300, right: 600, left: 500},
    width = 500,
    height = 500;



var x = d3.scale.ordinal().rangeBands([0, width]),
    z = d3.scale.linear().domain([0, 4]).clamp(true),
    c = d3.scale.category10().domain(d3.range(1));
    var colorScale = d3.scale.category10()
	.range(['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f']);

var zoom = d3.behavior.zoom()
    .scaleExtent([1, 10])
    .on("zoom", zoomed);




function zoomed() {

  svg.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")")
    ;
}



function countProperties(obj) {
    var count = 0;

    for(var prop in obj) {
        if(obj.hasOwnProperty(prop))
            ++count;
    }
    percentage = (25*count)/100;
    return percentage;
}





/*
var drag = d3.behavior.drag()
    .on("drag", dragmove);

function dragmove(d) {
  var x = d3.event.x;
  var y = d3.event.y;
  d3.select(this).attr("transform", "translate(" + x + "," + y + ")");
}
*/




// Add a svg
var svg = d3.select("div.container").append("svg")
    .attr("viewBox", [0, 0, 1500, 1500])
    /*
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top)
     */
    /*.style("margin-left", margin.left + "px") */
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
    .call(zoom);

// Import json, initialize the matrix, retrieve labels and dimensions



    document.getElementById("h33").textContent = "Text: " + $json.__comment__ ;
    var matrix = [],
        matricepesi =[],
        nodes = $json.nodes;
        n = nodes.length;
        sampleCategoricalData =[];




    nodes.forEach(function(node, i) {
        node.index = i;
        node.count = 0;
        matrix[i] = d3.range(n).map(function(j) { return {x: j, y: i, z: 0, w:""}; });
    });
    // Convert links to matrix and count annotators' positive judgements
    $json.links.forEach(function(link) {
            if (matrix[link.source]) {

                matrix[link.source][link.target].z += link.annotators;
                matrix[link.source][link.target].w = link.weight;
                nodes[link.source].count += link.annotators;
                nodes[link.target].count += link.annotators;

            }


    });



    // Compute the different orders
    var orders = {
        name: d3.range(n).sort(function(a, b) { return d3.ascending(nodes[a].name, nodes[b].name); }),
        frequency: d3.range(n).sort(function(a, b) { return nodes[b].frequence - nodes[a].frequence; }),
        cluster: d3.range(n).sort(function(a, b) { return nodes[b].cluster - nodes[a].cluster; }),
        temporal: d3.range(n).sort(function(a, b) { return Math.min.apply(Math,nodes[a].sentence) - Math.min.apply(Math,nodes[b].sentence); })
        //TODO: add ordering by number of co-occurrances in the same section
        // co_occurrance: d3.range(n).sort(function(a, b) { return nodes[a].sections - nodes[b].sections; });
    };

    // Set the default sorting (by name)
    x.domain(orders.name);

    svg.append("rect")
        .attr("class", "background")
        .attr("width", width)
        .attr("height", height);


    var row = svg.selectAll(".row")
        .data(matrix)
        .enter().append("g")
        .attr("class", "row")
        .attr("transform", function(d, i) { return "translate(0," + x(i) + ")"; })
        .each(row);

    row.append("line")
        .attr("x2", width);

    row.append("text")
        .attr("x", -6)
        .attr("y", x.rangeBand() / 2)
        .attr("dy", ".32em")
        .attr("text-anchor", "end")
        .style("font-size", "5px")
        .text(function(d, i) { return nodes[i].name; });

    var column = svg.selectAll(".column")
        .data(matrix)
        .enter().append("g")
        .attr("class", "column")
        .attr("transform", function(d, i) { return "translate(" + x(i) + ")rotate(-90)"; });

    column.append("line")
        .attr("x1", -width);

    column.append("text")
        .attr("x", 6)
        .attr("y", x.rangeBand() / 2)
        .attr("dy", ".32em")
        .attr("text-anchor", "start")
        .style("font-size", "5px")
        .text(function(d, i) { return nodes[i].name; });

    function row(row) {
        var cell = d3.select(this).selectAll(".cell")
            .data(row.filter(function(d) { return d.z; }))
            .enter().append("rect")
            .attr("class", "cell")
            .attr("x", function(d) { return x(d.x); })
            .attr("width", x.rangeBand())
            .attr("height", x.rangeBand())
            .style("fill-opacity", function(d) { return z(d.z); })
            .style("fill", function(d) {return "blue" })
            .on("mouseover", mouseover)
            .on("mouseout", mouseout)
            .append('title').text(function (d) { return nodes[d.y].name + ' ---> ' + nodes[d.x].name;});
    }

    function mouseover(p) {
        d3.selectAll(".row text").classed("active", function(d, i) { return i == p.y; });
        d3.selectAll(".column text").classed("active", function(d, i) { return i == p.x; });
    }


    function mouseout() {
        d3.selectAll("text").classed("active", false);
        //document.getElementById("popup").style.display = 'none';
    }

    d3.select("#order").on("change", function() {
        clearTimeout(timeout);
        order(this.value);
    });
    d3.select("#colored").on("change", function() {
        clearTimeout(timeout);
        changecolor(this.value);
    });

    function order(value) {
        x.domain(orders[value]);

        var t = svg.transition().duration(60);

        t.selectAll(".row")
            .delay(function(d, i) { return x(i) * 4; })
            .attr("transform", function(d, i) { return "translate(0," + x(i) + ")"; })
            .selectAll(".cell")
            .delay(function(d) { return x(d.x) * 4; })
            .attr("x", function(d) { return x(d.x); });

        t.selectAll(".column")
            .delay(function(d, i) { return x(i) * 4; })
            .attr("transform", function(d, i) { return "translate(" + x(i) + ")rotate(-90)"; });
    }
    function changecolor(value) {

        if(value=="annotators")
            {
                var t = svg.transition().duration(60);
                t.selectAll(".cell")
                .transition()
                .duration(60)
                .style("fill", function(d){ return colorScale(d.z) });

            }

        if(value=="weight")
            {
               var t = svg.transition().duration(60);
                t.selectAll(".cell")
                .transition()
                .duration(60)
                .style("fill", function(d){ if (d.w == "strong") {return "red"}
            else if(d.w == "weak") { return "green" } else { return "blue" }});
            }
        if(value=="normal") {
            var t = svg.transition().duration(60);
            t.selectAll(".cell")
                .transition()
                .duration(60)
                .style("fill-opacity", function (d) {
                    return z(d.z);
                })
                .style("fill", function (d) {
                    return "blue"
                });
        }


    }

    var timeout = setTimeout(function() {
        order("group");
        d3.select("#order").property("selectedIndex", 2).node().focus();
    }, 5000);

    function download(content, fileName, contentType) {
    const a = document.createElement("a");
    const file = new Blob([content], { type: contentType });
    a.href = URL.createObjectURL(file);
    a.download = fileName;
    a.click();
        }

        function onDownload(){
    download(JSON.stringify($json), "Graph_Structure.json", "text/plain");
        }







