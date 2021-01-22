var i, j, node;
// blank space between groups of nodes of the same section
var groupSep = 10;

var nodeRadius = d3.scaleSqrt().range([3, 7]);

var linkWidth = d3.scaleLinear().range([1.5, 2 * nodeRadius.range()[0]]);

var margin = {
    top: nodeRadius.range()[1] + 1,
    right: nodeRadius.range()[1] + 1,
    bottom: nodeRadius.range()[1] + 1,
    left: nodeRadius.range()[1] + 1
};

var width = 960 - margin.left - margin.right;
var height = 400 - margin.top - margin.bottom;

var x = d3.scaleLinear().range([0, width]);/*.domain(d3.extent($json.nodes, function (d) { return d; }));*/

var div = d3.select("div.arc")
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)

var svg = div.append('svg')
    .attr('width', width + margin.left + margin.right +500)
    .attr('height', height+ margin.top + margin.bottom)
    .append('g')
    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

document.getElementById("h33").textContent = "Text: " + $json.__comment__ ;

    var idToNode = {};
    var sectionsCount = 0;
    var connectedNodes = new Set();
    console.log($json);
    $json.nodes.forEach(function (n) {
        idToNode[n.id] = n;
        // update the counter of sections
        if (n.sections[n.sections.length - 1] > sectionsCount) {
            sectionsCount = n.sections[n.sections.length - 1];
        }
    });

    $json.nodes.forEach(function (n) {
        n.firstSection = n.sections[0];
    });

    // Sort nodes by first appearance (section)
    $json.nodes.sort(function (a, b) {
        return sectionCompare(a.firstSection, b.firstSection);
    }).reverse();

    $json.links.forEach(function (e) {
        e.source = idToNode[e.source];
        e.target = idToNode[e.target];
        connectedNodes.add(e.source);
        connectedNodes.add(e.target);

        // populate the table at the end of the page
        var table = document.getElementById("relationsTable");
        // Create an empty <tr> element and append it at end of the table
        var row = table.insertRow();
        // Insert new cells (<td> elements) in the row
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        var cell3 = row.insertCell(2);
        var cell4 = row.insertCell(3);
        // fill the new cells:
        cell1.innerHTML = e.source.name;
        cell2.innerHTML = e.target.name;
        if (e.source.firstSection > e.target.firstSection) {
            cell3.innerHTML = 'backward';
        } else {
            cell3.innerHTML = 'forward';
        }
        cell4.innerHTML = e.weight;
    });


    // Compute x,y coordinates (have a little extra separation when we switch volumes)
    for (i = 0, j = 0; i < $json.nodes.length; ++i) {
        node = $json.nodes[i];
        if (i > 0 && $json.nodes[i-1].firstSection !== node.firstSection) ++j;
        //TODO increase empty space between nodes
        node.x = j * groupSep + i * (width - 4 * groupSep) / ($json.nodes.length - 1);
        node.y = height;
    }

    nodeRadius.domain(d3.extent($json.nodes, function (d) { return d.sections.length; }));

    linkWidth.domain(d3.extent($json.links, function (d) { return d.annotators.length; }));

    var link = svg.append('g')
        .attr('class', 'links')
        .selectAll('path')
        .data($json.links)
        .enter().append('path')
        .attr('d', function (d) {
            return ['M', d.source.x, height, 'A',
                (d.source.x - d.target.x)/2, ',',
                (d.source.x - d.target.x)/2, 0, 0, ',',
                d.source.x < d.target.x ? 1 : 0, d.target.x, ',', height]
                .join(' ');
        })
        .attr('stroke-width', function (d) { return linkWidth(d.annotators.length); })
        .attr('id', function (d) { return 'path: '+d.source.name+' --> '+d.target.name; })
        .attr('class', function (d) {
            if (d.source.firstSection > d.target.firstSection) {
                return 'backward'
            }
            else {
                return 'forward'
            }
        })
        .on('mouseover', function (d) {
            link.style('stroke', null);

            // use different colors according to the direction of the edge
            if (d.source.firstSection > d.target.firstSection) {
                // backward edge
                d3.select(this).style('stroke', '#d62333');
            } else {
                // forward edge
                d3.select(this).style('stroke', '#0f0dd9');
            }

            node.style('fill', function (node_d) {
                return node_d === d.source || node_d === d.target ? 'black' : null;
            });
        })
        .on('mouseout', function (d) {
            link.style('stroke', null);
            node.style('fill', null);
        });


    var node = svg.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data($json.nodes)
        .enter().append('circle')
        .attr('cx', function (d) { return d.x; })
        .attr('cy', function (d) { return d.y; })
        .attr('r', function (d) { return nodeRadius(d.sections.length); })
        .attr('id', function (d) { return 'node: '+d.name; })
        .on('mouseover', function (d) {
            node.style('fill', null);
            d3.select(this).style('fill', 'black');
            var nodesToHighlight = $json.links.map(function (e) { return e.source === d ? e.target : e.target === d ? e.source : 0})
                .filter(function (d) { return d; });
            node.filter(function (d) { return nodesToHighlight.indexOf(d) >= 0; })
                .style('fill', '#555');
            link.style('stroke', function (link_d) {
                var color = null;
                // use different colors according to the direction of the edge
                if (link_d.source.firstSection > link_d.target.firstSection) {
                    // backward edge
                    color = '#d62333';
                } else {
                    // forward edge
                    color = '#0f0dd9';
                };
                return link_d.source === d | link_d.target === d ? color : null;
            });
        })
        .on('mouseout', function (d) {
            node.style('fill', null);
            link.style('stroke', null);
        })
        // TODO: filter the graph by selecting a node
        .on('click', function (d) {
            //d3.select(this).classed("selected", !d3.select(this).classed("selected"));
            node.style('fill', null);
            var currNode = this.id;
            d3.select(this).style('fill', 'yellow');
            link.filter(function (d) { return ("node: " + d.source.name) === currNode; })
                .style('fill', 'reds');
        });



    node.append('title').text(function (d) { return d.name;});
    link.append('title').text(function (d) { return d.source.name + ' (' + d.source.firstSection + ')' +  ' --> ' + d.target.name  + ' (' + d.target.firstSection + ')';});

    function sectionCompare (sectionA, sectionB) {
        if (sectionA != sectionB)
            return sectionB - sectionA;

        return 0;
    }



    /**
     * Section filter
     */

    //populate the list
    var sectionSelect = d3.select('#section-select');
    for (var x = 1; x <= sectionsCount; x++) {
        sectionSelect.append('option')
            .text(x);
    }
    d3.select('#section-select')
        .on('change', function () {
            var selection = this.value;
            //FIXME: is 'all' is selected show all sections!!!
            if (selection === "All") {
            var paths = document.getElementsByClassName('links')[0].childNodes;
            var circles = document.getElementsByClassName('nodes')[0].childNodes;
            for (f=0; f<paths.length; f++) {
                       paths[f].style.display = "block";
                   }
             for (c=0; c<circles.length; c++) {
                       circles[c].style.display = "block";
                   }

            } else
            {
                $json.nodes.forEach(function (n) {

                    if (connectedNodes.has(n.name)) {
                        document.getElementById("node: " + n.name).style.display = 'block';
                    } else {
                        document.getElementById("node: " + n.name).style.display = 'none';
                    }

                    if (n.sections[0] === selection) {
                        document.getElementById("node: " + n.name).style.display = 'block';
                    } else {
                        document.getElementById("node: " + n.name).style.display = 'none';
                    }
                });
                $json.links.forEach(function (e) {
                    if (e.source.sections[0] === selection &&
                        e.target.sections[0] === selection) {
                        document.getElementById('path: ' + e.source.name + ' --> ' + e.target.name).style.display = 'block';
                        document.getElementById("node: " + e.source.name).style.display = "block";
                        document.getElementById("node: " + e.target.name).style.display = "block";
                    } else {
                        document.getElementById('path: ' + e.source.name + ' --> ' + e.target.name).style.display = 'none';
                        document.getElementById("node: " + e.source.name).style.display = "none";
                        document.getElementById("node: " + e.target.name).style.display = "none";
                    }
                });
            }

        });





    /**
     * Direction filter
     */
    d3.select('#direction-select')
        .on('change', function () {
           var selection = this.value;
           var paths = document.getElementsByClassName('links')[0].childNodes;

           console.log(paths);
           switch (selection) {
               case 'Backward':
                   for (var f=0; f<paths.length; f++) {
                       if (paths[f].classList.contains("forward")) {
                           paths[f].style.display = "none";
                       }
                       else {
                           paths[f].style.display = "block";
                       }
                   }
                   break;
               case 'Forward':
                   for (f=0; f<paths.length; f++) {
                       if (paths[f].classList.contains("backward")) {
                           paths[f].style.display = "none";
                       }
                       else {
                           paths[f].style.display = "block";
                       }
                   }
                   break;
               case 'All':
                   for (f=0; f<paths.length; f++) {
                       paths[f].style.display = "block";
                   }
           }});


    /**
     * Searching bar
     */
    d3.select('#text-search')
        .on('keyup', function () {
            var text = this.value;
            //var circles = document.getElementsByTagName('circle');
            var circles = document.getElementsByClassName('nodes')[0].childNodes;
            var paths = document.getElementsByClassName('links')[0].childNodes;
            if (text.length) {
                for (var c=0; c<circles.length; c++) {
                    console.log(circles[c].id);
                    if (!circles[c].id.includes(text)) {

                        document.getElementById(circles[c].id).style.display = "none";
                    }
                    else {
                        document.getElementById(circles[c].id).style.display = "block";
                    }
                }
                for (var p=0; p<paths.length; p++) {
                    //if (!paths[p].getElementsByTagName('title')[0].innerHTML.includes(text.toUpperCase())) {
                    if (!paths[p].id.includes(text)) {
                        document.getElementById(paths[p].id).style.display = "none";
                        //d3.select("#" + paths[p].id).on('mouseover', function (d) { d.style("stroke", "white");})
                    }
                    else {
                        document.getElementById(paths[p].id).style.display = "block";
                    }
                }
            } else {
                //contraFilters.search = null;
                for (c=0; c<circles.length; c++) {
                    document.getElementById(circles[c].id).style.display = "block";
                }
                for (var p=0; p<paths.length; p++) {
                    //if (!paths[p].getElementsByTagName('title')[0].innerHTML.includes(text.toUpperCase())) {
                    document.getElementById(paths[p].id).style.display = "block";
                }
            }
        });



/**
 * Function to show the full list of relations in the hide/show textbox at the end of the page
 */
function showList() {
    var x = document.getElementById("summary");
    if (x.style.display && x.style.display !== 'none') {
        x.style.display = "none";
    } else {
        x.style.display = "block";
    }
}


/**
 * Function to search autoConcepts in the table.
 */
function tableSearch() {
    // Declare variables
    var input, filter, table, tr, td, i;
    input = document.getElementById("myInput");
    filter = input.value.toUpperCase();
    table = document.getElementById("relationsTable");
    tr = table.getElementsByTagName("tr");

    // Loop through all table rows, and hide those who don't match the search query
    for (i = 1; i < tr.length; i++) {
        td = tr[i].getElementsByTagName("td")[0];
        td2 = tr[i].getElementsByTagName("td")[1];
        if (td) {
            if ((td.innerHTML.toUpperCase().indexOf(filter) > -1) ||
                (td2.innerHTML.toUpperCase().indexOf(filter) > -1)) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
}


/**
 * Function to sort table rows according to the clicked column header
 */
function sortTable(n) {
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementById("relationsTable");
    console.log(table);
    switching = true;
    // Set the sorting direction to ascending:
    dir = "asc";
    /* Make a loop that will continue until
    no switching has been done: */
    while (switching) {
        // Start by saying: no switching is done:
        switching = false;
        rows = table.rows;
        /* Loop through all table rows (except the
        first, which contains table headers): */
        for (i = 1; i < (rows.length - 1); i++) {
            // Start by saying there should be no switching:
            shouldSwitch = false;
            /* Get the two elements you want to compare,
            one from current row and one from the next: */
            x = rows[i].getElementsByTagName("td")[n];
            y = rows[i + 1].getElementsByTagName("td")[n];
            /* Check if the two rows should switch place,
            based on the direction, asc or desc: */
            if (dir == "asc") {
                console.log("x.innerHTML: " + x.innerHTML);
                if (x.innerHTML.toUpperCase() > y.innerHTML.toUpperCase()) {
                    // If so, mark as a switch and break the loop:
                    shouldSwitch = true;
                    break;
                }
            } else if (dir == "desc") {
                if (x.innerHTML.toUpperCase() < y.innerHTML.toUpperCase()) {
                    // If so, mark as a switch and break the loop:
                    shouldSwitch = true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            /* If a switch has been marked, make the switch
            and mark that a switch has been done: */
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            // Each time a switch is done, increase this count by 1:
            switchcount ++;
        } else {
            /* If no switching has been done AND the direction is "asc",
            set the direction to "desc" and run the while loop again. */
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
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


