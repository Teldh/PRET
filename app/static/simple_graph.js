

    var idToNode = {};
    var nodeList = [];
    var edgeList = [];
    var disconnected = [];
    document.getElementById("h33").textContent = "Text: " + $json.__comment__ ;
    $json.nodes.forEach(function (n) {

        idToNode[n.id] = n;
        nodeList.push(n.name);
    });

    $json.links.forEach(function (e) {
        e.source = idToNode[e.source].name;
        e.target = idToNode[e.target].name;
        edgeList.push([e.source, e.target]);
    });


    $json["disconnected nodes"].forEach(function (n) {
        disconnected.push(n);
    });



    var G = new jsnx.DiGraph();
    var sizeScale = d3.scale.linear().domain([0,1]).range([4,10]);

    function countProperties(obj) {
    var count = 0;

    for(var prop in obj) {
        if(obj.hasOwnProperty(prop))
            ++count;
    }

    return count;
        }


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



    // Add nodes with different colors
    nodeList.forEach(function (n) {
        if (disconnected.includes(n)) {
            G.addNodesFrom([[n, {color: '#ffdda2'}]]);
        }
        else {
            G.addNodesFrom([[n, {color: '#7FFFD4'}]]);//'#FFB3D4'
        }
    });


    // Add edges with different colors
    $json.links.forEach(function (e) {
        if (e.is_transitive) {
            G.addEdgesFrom([[e.source, e.target, {color: '#911aff'}]]);
        }
        else if (e.has_mutual){
            G.addEdgesFrom([[e.source, e.target, {color: '#FF0000'}]]);
        }
        else {
            G.addEdgesFrom([[e.source, e.target, {color: '#FFA07A'}]]);
        }
    });



    // Draw the graph
    jsnx.draw(G, {
        element: '#canvas',
        layoutAttr: {
             charge:function (d) {
                    if (d.data.color == "#ffdda2")
                        return -300;
                    else
                        return -600;
                 },
            'gravity' : 0,
            'linkDistance': 400
        },
        withLabels: true,
        nodeAttr: {
        r: 10,
        title: function(d) { return d.label;},
        id: function(d) {

            return 'node-' + d.node.replace(/\s/g,"X"); // assign unique ID
        }
         },
        nodeStyle: {
            'stroke': "none",
            fill: function (d) {
                return d.data.color;
            }

        },
        edgeAttr: {
        id: function(d) {
            return 'edges-' + d.edge;// assign unique ID
        }
         },
        edgeStyle: {
            'stroke-width': 5,
            fill: function (d) {
                return d.data.color;
            }
        },
        labelStyle: {
            "font-size": '10px',
            "font-family": "sans-serif",
            //'text-anchor': 'outside',
            "dominant-baseline": "text-before-edge",
           //"dominant-baseline" : "hanging",
            //"text-anchor": "middle",

        },
        stickyDrag: true
    }, true);


    function highlight_nodes(nodes, on) {
    nodes.forEach(function(n) {
        if (disconnected.includes(n)) {
            return null;
        }
        else
        d3.select('#node-'+n.replace(/\s/g,"X")).style('fill', function(d) {
            return on ? 'red' : d.data.color;
            });
        });
    }

    d3.selectAll('.node').on('mouseover', function(d) {
    highlight_nodes(d.G.neighbors(d.node).concat(d.node), true);
    //console.log(d.G.neighbors(d.node).concat(d.node));
    });

    d3.selectAll('.node').on('mouseout', function(d) {
    highlight_nodes(d.G.neighbors(d.node).concat(d.node), false);
    });



    d3.select('#annotator-select')
        .on('change', function () {
            var selection = this.value;
            //FIXME: is 'all' is selected show all sections!!!

            if (selection === "All") {

                var l = document.getElementsByClassName('line');
                for (var x of l) {
                    document.getElementById(x.id).style.display = 'block';
                }
                d3.selectAll('.node').on('mouseover', function(d) {
                    highlight_nodes(d.G.neighbors(d.node).concat(d.node), true);
                    //console.log(d.G.neighbors(d.node).concat(d.node));
                    });

                    d3.selectAll('.node').on('mouseout', function(d) {
                    highlight_nodes(d.G.neighbors(d.node).concat(d.node), false);
                    });

            }else {

                $json.links.forEach(function (e) {
                    selezione =selection.charAt(0);
                    console.log(selezione);
                    if (e.annotators == "uid."+selezione) {

                        document.getElementById('edges-' + e.source + ',' + e.target).style.display = 'block';
                    } else {
                        document.getElementById('edges-' + e.source + ',' + e.target).style.display = 'none';
                    }

                });
                d3.selectAll('.node').on('mouseover', function(d) {
                    highlight_nodes(d.G.neighbors(d.node).concat(d.node), false);
                    //console.log(d.G.neighbors(d.node).concat(d.node));
                    });

                    d3.selectAll('.node').on('mouseout', function(d) {
                    highlight_nodes(d.G.neighbors(d.node).concat(d.node), false);
                    });


            }


        });

    /*
    var D = new jsnx.DiGraph();

    nodeList.forEach(function (n) {

        D.addNodesFrom([[n, {color: '#ffdda2'}]]);

    });

    $json.links.forEach(function (e) {

        D.addEdgesFrom([[e.source, e.target, {color: '#FFA07A'}]]);

    });
    var exemples = [];
    exemples = Array.from(D.degreeIter());
    //console.log(exemples)
    var sortedArray = exemples.sort(function(a, b) {
     if (a[1] == b[1]) {
    return a[0] - b[0];
     }
     return b[1] - a[1];
     });
    //console.log(nodeList)
    //console.log(sortedArray)
    */
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

