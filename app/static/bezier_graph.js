



var margin = {top: 360, right: 10, left: 440},
    width = 1500,
    height = 1500;

var svg = d3.select("div.container").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top);
    //width = +svg.attr("width"),
    //height = +svg.attr("height");



var color = d3.scaleOrdinal(d3.schemeCategory20);

document.getElementById("h33").textContent = "Text: " + $json.__comment__ ;

var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().distance(10).strength(0.5))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(width / 2, height / 2));


var annotators = new Set();

function countProperties(obj) {
    var count = 0;

    for(var prop in obj) {
        if(obj.hasOwnProperty(prop))
            ++count;
    }

    return count;
        }

    svg.append("svg:defs").append("svg:marker")
        .attr("id", "arrow")
        .attr("viewBox", "0 -5 10 10")
        .attr('refX', -20)//so that it comes towards the center.
        .attr("markerWidth", 3)
        .attr("markerHeight", 3)
        .attr("orient", "auto")
        .append("svg:path")
        .attr("d", "M0,-5L10,0L0,5");
    var nodes = $json.nodes,
        nodeById = d3.map(nodes, function(d) { return d.id; }),
        links = $json.links,
        bilinks = [];
    links.forEach(function(link) {
        var s = link.source = nodeById.get(link.source),
            t = link.target = nodeById.get(link.target),
            i = {}; // intermediate node
        nodes.push(i);
        links.push({source: s, target: i}, {source: i, target: t});
        bilinks.push([s, i, t]);
        for (var a=0; a<link.annotators.length; a++) {
            if (!annotators.has(link.annotators[a])) {
                annotators.add(link.annotators[a]);
                //populate the list of the Annotator filter
                //document.getElementById('annotator-select').innerHTML += '<option value="' + link.annotators[a] + '">' + link.annotators[a] + '</option>';
            }
        }

    });
    //console.log($json.annotator.lenght);
    var count = 0;
    var c=0;
    c = countProperties($json.annotator);
    if(c>1)
    {
        var sel = document.getElementById('annotator-select');
                    var opt = document.createElement("option");
                    opt.value = "All";
                    opt.text = "All";
                    sel.options.add(opt, 0);
                    sel.selectedIndex=0;
    }
    Array.from($json.annotator).forEach(function(ann){
            if(ann=="1")
            {
                document.getElementById("h44").textContent = "Method: Lexical Relation";
            }
            if(ann=="2")
            {
                document.getElementById("h44").textContent = "Method: Lexical Syntactic Pattern Match";
            }
            if(ann=="3")
            {
                document.getElementById("h44").textContent = "Method: Relational Metric";
            }
            if(ann=="4")
            {
                document.getElementById("h44").textContent = "Method: Wikipedia-based relations";
            }
            if(ann=="5")
            {
                document.getElementById("h44").textContent = "Method: Textbook Structure";
            }
            if(ann=="6")
            {
                document.getElementById("h44").textContent = "Method: Temporal Patterns";
            }
            else {



                if (c>1) {

                    //document.getElementById('annotator-select').innerHTML += '<option value="All">All</option>';
                    document.getElementById('annotator-select').innerHTML += '<option value="' + ann + '">' + ann.split(".").pop() + '</option>';


                }
                else {
                    if(ann.startsWith("uid")) {
                        document.getElementById("h44").textContent = "Annotator: " + ann.slice(6);
                    }
                    /*

                    document.getElementById('select').innerHTML += "Annotator:";
                    if(ann.startsWith("uid"))
                    {
                        document.getElementById('annotator-select').innerHTML += '<option value="' + ann.slice(6) + '">' + ann.slice(6)+ '</option>';
                    }
                    else {
                        document.getElementById('annotator-select').innerHTML += '<option value="' + ann + '">' + ann + '</option>';
                    }
                    */
                }
            }
        })


    var link = svg.selectAll(".link")
        .data(bilinks)
        .enter().append("path")
        //.attr("id", "path: "+ links.source.name + " --> "+ links.target.name)
        .attr('id', function (d) { return 'path: ' + d[0].name + ' --> ' + d[2].name; })
        .attr("class", "link")
        .attr('marker-start', (d) => "url(#arrow)");//attach the arrow from defs

    var node = svg.selectAll(".node")
        .data(nodes.filter(function(d) { return d.id; }))
        .enter().append("circle")
        .attr("class", "node")
        .attr("r", 5)
        .attr("fill", function(d) { return color(d.cluster); })
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    node.append("title")
        .text(function(d) { return d.name; });

    simulation
        .nodes(nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(links);

    function ticked() {
        link.attr("d", positionLink);
        node.attr("transform", positionNode);
        //link.attr( "d", (d) => "M" + d.source.x + "," + d.source.y + ", " + d.target.x + "," + d.target.y);
        //link.attr( "d", (d) => "M" + d[0].x + "," + d[0].y + ", " + d[2].x + "," + d[2].y);
        link.attr( "d", (d) => positionLink(d));
    }



    /**
     * Annotator filer
     */
    d3.select('#annotator-select')
        .on('change', function () {
            var selection = this.value;
            //FIXME: is 'all' is selected show all sections!!!
            if (selection === "All") {
                var l = document.getElementsByClassName('link');
                for (var x of l) {
                    document.getElementById(x.id).style.display = 'block';
                }
            }else {
                $json.links.forEach(function (e) {
                    if (e.annotators) {
                        selezione =selection.charAt(0);
                        if (e.annotators == "uid."+selezione)  {
                            document.getElementById('path: ' + e.source.name + ' --> ' + e.target.name).style.display = 'block';
                        } else {
                            document.getElementById('path: ' + e.source.name + ' --> ' + e.target.name).style.display = 'none';
                        }
                    }

                });
            }
        });



function positionLink(d) {
    return "M" + d[0].x + "," + d[0].y
        + "S" + d[1].x + "," + d[1].y
        + " " + d[2].x + "," + d[2].y;
}

function positionNode(d) {
    return "translate(" + d.x + "," + d.y + ")";
}

function dragstarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function dragended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}
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