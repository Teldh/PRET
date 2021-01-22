/**
 * @author Modified and adapted for PRET from Dimitry Kudrayvtsev and Keyvan Fatehi
 *
 */

//var nodeList = [];

var clickedConcept = "";
var selectedBurstPair = [];
var currStartSent = null;
var currendSent = null;

$(document).on('dblclick', function(e) {
    //show prerequisite relations if a concept is clicked
    if (e.target.parentNode.classList.contains("tick")) {
        clickedConcept = $(event.target).text();
        if (concepts.includes(clickedConcept)) {
            //$("#selectedConcept").val(clickedConcept);
            $("#modalShowRelations").modal("show");
        }
    }
});
console.log($json);

$("#modalShowRelations").on('show.bs.modal', function(e) {
    $("#table_burstSummary").find("tr:not(:first)").remove();
    for (let pair of burstsPairs) {
        if (pair["x"] === clickedConcept || pair["y"] === clickedConcept) {
            let table = document.getElementById("table_burstSummary");
            let row = table.insertRow(table.rows.length);
            row.insertCell(0).innerHTML = pair["x"];
            row.insertCell(1).innerHTML = pair["y"];
            row.insertCell(2).innerHTML = pair["Bx_id"];
            row.insertCell(3).innerHTML = pair["By_id"];
            row.insertCell(4).innerHTML = pair["Bx_start"];
            row.insertCell(5).innerHTML = pair["Bx_end"];
            row.insertCell(6).innerHTML = pair["By_start"];
            row.insertCell(7).innerHTML = pair["By_end"];
            row.insertCell(8).innerHTML = pair["Rel"];
        }
    }
    /*$(e.currentTarget).find('h4[id="conceptSummary_name"]').text(clickedConcept);
    $("#table_goldSummary").find("tr:not(:first)").remove();
    for (let rel of edgeList) {
        if (rel.includes(clickedConcept)) {
            console.log(rel);
            let table = document.getElementById("table_goldSummary");
            let row = table.insertRow(table.rows.length);
            let cell0 = row.insertCell(0);
            let cell1 = row.insertCell(1);
            let cell2 = row.insertCell(2);
            cell0.innerHTML = rel[0];
            cell1.innerHTML = rel[1];
            cell2.innerHTML = rel[2];
        }
    }*/
    //make the rows clickable and open a box with burst comparisons
    $("tr").on('click', function(e) {
        selectedBurstPair = [];
        selectedBurstPair.push($(this).find("td")[0].innerHTML);
        selectedBurstPair.push($(this).find("td")[1].innerHTML);
        $("#modalShowBursts").modal("show");
    });
});

$("#modalShowBursts").on('show.bs.modal', function(e) {
    $(e.currentTarget).find('h4[id="conceptsPair"]').text(selectedBurstPair[0] + " -- > " + selectedBurstPair[1]);
    $("#table_conceptPair").find("tr:not(:first)").remove();
    for (let pair of burstsPairs) {
        if ((pair["x"] === selectedBurstPair[0] && pair["y"] === selectedBurstPair[1]) ||
            (pair["y"] === selectedBurstPair[0] && pair["x"] === selectedBurstPair[1])) {
            let table = document.getElementById("table_conceptPair");
            let row = table.insertRow(table.rows.length);
            let cell0 = row.insertCell(0);
            cell0.innerHTML = pair["x"];
            cell0.setAttribute("style", "background-color:" + getColor(pair["Bx_id"]));
            let cell1 = row.insertCell(1);
            cell1.innerHTML = pair["y"];
            cell1.setAttribute("style", "background-color:" + getColor(pair["By_id"]));
            let cell2 = row.insertCell(2);
            cell2.innerHTML = pair["Bx_start"];
            let cell3 = row.insertCell(3);
            cell3.innerHTML = pair["Bx_end"];
            let cell4 = row.insertCell(4);
            cell4.innerHTML = pair["By_start"];
            let cell5 = row.insertCell(5);
            cell5.innerHTML = pair["By_end"];
            let cell6 = row.insertCell(6);
            cell6.innerHTML = pair["Rel"];
            /*
            //change color according to the status of the burst
            let Bx_id = bursts.find(x => x.ID === pair["Bx_id"]).status;
            let By_id = bursts.find(x => x.ID === pair["By_id"]).status;
            */
        }
    }
});


$("#modalShowContext").on('show.bs.modal', function(e) {
    $(e.currentTarget).find('h4[id="context"]').text(clickedConcept + " (from " + currStartSent + " to " + currendSent + ")");
    $("#table_sentences").find("tr:not(:first)").remove();
    for (let s = currStartSent; s <= currendSent; s++) {
        //console.log($sentList.filter(x => x.sent_id === s)[0]['text']);
        let table = document.getElementById("table_sentences");
        let row = table.insertRow(table.rows.length);
        let cell0 = row.insertCell(0);
        cell0.innerHTML = s;
        let cell1 = row.insertCell(1);
        cell1.innerHTML = $sentList.filter(x => x.sent_id === s)[0]['text'];
        if ($sentList.filter(x => x.sent_id === s)[0]['type'].endsWith("title")) {
            cell1.setAttribute("style", "font-weight: bold" );
        }
    }
});

function getColor (burstID) {
    let status = bursts.find(x => x.ID === burstID).status;
    let colors = {
        "FIRST" : "#669900",
        "LAST" : "#CC0000",
        "ONGOING" : "#33b5e5",
        "UNIQUE" : "#ffbb33"
    };
    return colors[status];
}


d3.gantt = function() {
    var FIT_TIME_DOMAIN_MODE = "fit";
    var FIXED_TIME_DOMAIN_MODE = "fixed";

    var margin = {
        top : 20,
        right : 40,
        bottom : 20,
        left : 150
    };
    var timeDomainStart = d3.timeDay.offset(new Date(),-3);
    var timeDomainEnd = d3.timeHour.offset(new Date(),+3);
    var timeDomainMode = FIT_TIME_DOMAIN_MODE;// fixed or fit
    var burstTypes = [];
    var burstStatus = [];
    /*original:
    var height = document.body.clientHeight - margin.top - margin.bottom-5;
    */
    var height = concepts.length * 30;
    var width = document.body.clientWidth - margin.right - margin.left-5;

    var tickFormat = "%H:%M";

    var keyFunction = function(d) {
        return d.startSent + d.concept + d.endSent;
    };

    var rectTransform = function(d) {
        return "translate(" + x(d.startSent) + "," + y(d.concept) + ")";
    };

    var x,y,xAxis,yAxis;

    initAxis();

    var initTimeDomain = function() {
        if (timeDomainMode === FIT_TIME_DOMAIN_MODE) {
            if (bursts === undefined || bursts.length < 1) {
                timeDomainStart = d3.time.day.offset(new Date(), -3);
                timeDomainEnd = d3.time.hour.offset(new Date(), +3);
                return;
            }
            bursts.sort(function(a, b) {
                return a.endSent - b.endSent;
            });
            timeDomainEnd = bursts[bursts.length - 1].endSent;
            bursts.sort(function(a, b) {
                return a.startSent - b.startSent;
            });
            timeDomainStart = bursts[0].startSent;
        }
    };

    function initAxis() {
        /*original:*/
        //x = d3.scaleTime().domain([ timeDomainStart, timeDomainEnd ]).range([ 0, width ]).clamp(true);

        x = d3.scaleLinear()
            .domain([1,maxSent])
            .range([0,width]);

        y = d3.scaleBand()
            .domain(burstTypes)
            .range([0,height]);/*original: .rangeRound([ 0, height - margin.top - margin.bottom ], .1);*/

        /*original:*/
        //xAxis = d3.axisBottom().scale(x).tickFormat(d3.timeFormat(tickFormat))
        //.tickSize(8).tickPadding(8);

        xAxis = d3.axisBottom().scale(x).ticks(50).tickSize(10);

        yAxis = d3.axisLeft().scale(y).tickSize(0);
    }


    function gantt(bursts) {

        initTimeDomain();
        initAxis();

        var svg = d3.select("#container")
            .append("svg")
            .attr("style","background: none")
            .attr("class", "chart")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("class", "gantt-chart")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .attr("transform", "translate(" + margin.left + ", " + margin.top + ")");

        svg.selectAll(".chart")
            .data(bursts, keyFunction).enter()
            .append("rect")
            .attr('stroke', 'black')
            // TODO SE2020: il bordo più spesso per il primo burst "lungo" non è indispensabile in PRET. Commentare il codice se si decide poi di non avere questa funzione, anche perché per settare l'attributo bisogna avere in input l'informazione sul firstLongest, che non è detto che ci sia in futuro
            //use a thicker border for the first burst longer than the average length of a concept
            //.attr('stroke-width', function (d) {
               // if (firstLongest[d.concept] === d.ID) {return "3";} else {return "1";}})
            .attr("rx", 5)
            .attr("ry", 5)
            .attr("class", function(d){
                if(burstStatus[d.status] == null){ return "bar";}
                return burstStatus[d.status];
            })
            .attr("y", 0)
            .attr("transform", rectTransform)
            .attr('id', function (d) { return "burst" + d.ID; })
            .attr("concept", function (d) { return d.concept;})
            .attr("height", function(d) { return 20; }) //height of the burst-rectangles
            .attr("width", function(d) {
                return (x(d.endSent) - x(d.startSent) + 1);
            });

        console.log(bursts)

        // append hidden ruler lines
        svg.selectAll(".chart")
            .data(bursts, keyFunction).enter()
            .append("line")
            .attr("id", function(d) { return "burst" + d.ID + "_start" })
            .attr("class", "ruler")
            .attr("x1", function(d) { return (x(d.startSent)) })
            .attr("y1", 0)
            .attr("x2", function(d) { return (x(d.startSent)) })
            .attr("y2", height)
            .style("stroke-width", 1)
            .style("stroke", "grey")
            .style("display", "none");
        svg.selectAll(".chart")
            .data(bursts, keyFunction).enter()
            .append("line")
            .attr("id", function(d) { return "burst" + d.ID + "_end" })
            .attr("class", "ruler")
            .attr("x1", function(d) { return (x(d.endSent)) })
            .attr("y1", 0)
            .attr("x2", function(d) { return (x(d.endSent)) })
            .attr("y2", height)
            .style("stroke-width", 1)
            .style("stroke", "grey")
            .style("display", "none");



        // draw vertical lines to mark boundaries between sections

        var sectionTitlesSents = $sentList.filter(x => x.type === "section title").map(x => x.sent_id);

        // TODO SE2020: vedere se in PRET si possono sistemare queste linee separatrici per i capitoli
        for (let num in sectionTitlesSents) {
            svg.selectAll(".chart")
                .data(bursts, keyFunction).enter()
                .append("line")
                .attr("id", function() { return "section" + num })
                .attr("class", "boundary")
                .attr("x1", function() { return (x(sectionTitlesSents[num])) })
                .attr("y1", 0)
                .attr("x2", function() { return (x(sectionTitlesSents[num])) })
                .attr("y2", height)
                .style("stroke-width", 2)
                .style("stroke", "grey");
        }


        svg.selectAll("rect")
            .on("click", function() {
                d3.select(this).classed("selected", !d3.select(this).classed("selected"));
                var rulers = document.getElementsByClassName("ruler");
                for (var r=0; r<rulers.length; r++) {
                    if (rulers[r].id.startsWith(this.id+"_")){
                        if (rulers[r].style.display && rulers[r].style.display !== "none") {
                            document.getElementById(rulers[r].id).style.display = "none";
                        }
                        else {
                            document.getElementById(rulers[r].id).style.display = "block";
                        }
                    }
                }
            })
            // on rightclick, open a box with the text of sentences
            .on("contextmenu", function (d) {
                d3.event.preventDefault();
                clickedConcept = d.concept;
                currStartSent = d.startSent;
                currendSent = d.endSent;
                $("#modalShowContext").modal("show");

            })
            .append('title').text(function (d) { return (d.concept +
            " (id: " + d.ID + ")\n" +
            "start: " + d.startSent + "\nend: " + d.endSent + "\n" +
            "freq of term: " + d.freqOfTerm);});

        svg.append("g")
            .attr("class", "x axis")
            /*orignal:
            .attr("transform", "translate(0, " + (height - margin.top - margin.bottom) + ")")*/
            .attr("transform", "translate(0, " + (height) + ")")
            .transition()
            .call(xAxis);

        svg.append("g")
            .attr("class", "y axis")
            .transition()
            .call(yAxis);

        return gantt;

    }


    gantt.redraw = function(bursts) {

        initTimeDomain();
        initAxis();

        var svg = d3.select("svg");

        var ganttChartGroup = svg.select(".gantt-chart");
        var rect = ganttChartGroup.selectAll("rect").data(bursts, keyFunction);

        rect.enter()
            .insert("rect",":first-child")
            .attr("rx", 5)
            .attr("ry", 5)
            .attr("class", function(d){
                if(burstStatus[d.status] == null){ return "bar";}
                return burstStatus[d.status];
            })
            .transition()
            .attr("y", 0)
            .attr("transform", rectTransform)
            .attr("height", function(d) { return y.range()[1]; })
            .attr("width", function(d) {
                return (x(d.endSent) - x(d.startSent) + 1);
            });

        rect.transition()
            .attr("transform", rectTransform)
            .attr("height", function(d) { return y.range()[1]; })
            .attr("width", function(d) {
                return (x(d.endSent) - x(d.startSent) + 1);
            });

        rect.exit().remove();

        svg.select(".x").transition().call(xAxis);
        svg.select(".y").transition().call(yAxis);

        return gantt;
    };




    gantt.margin = function(value) {
        if (!arguments.length)
            return margin;
        margin = value;
        return gantt;
    };

    gantt.timeDomain = function(value) {
        if (!arguments.length)
            return [ timeDomainStart, timeDomainEnd ];
        timeDomainStart = +value[0];
        timeDomainEnd = +value[1];
        return gantt;
    };


    gantt.timeDomainMode = function(value) {
        if (!arguments.length)
            return timeDomainMode;
        timeDomainMode = value;
        return gantt;

    };

    gantt.burstTypes = function(value) {
        if (!arguments.length)
            return burstTypes;
        burstTypes = value;
        return gantt;
    };

    gantt.burstStatus = function(value) {
        if (!arguments.length)
            return burstStatus;
        burstStatus = value;
        return gantt;
    };

    gantt.width = function(value) {
        if (!arguments.length)
            return width;
        width = +value;
        return gantt;
    };

    gantt.height = function(value) {
        if (!arguments.length)
            return height;
        height = +value;
        return gantt;
    };

    gantt.tickFormat = function(value) {
        if (!arguments.length)
            return tickFormat;
        tickFormat = value;
        return gantt;
    };

    return gantt;
};


$(document).click(function (event) {
    //hide all rulers when click outside rects
    if (event.target.tagName !== "rect") {
        var rulers = $(".ruler");
        for (var r=0; r<rulers.length; r++) {
            rulers[r].style.display = "none";
        }
        $(".selected").removeClass("selected");
    }
});



//TODO SE2020: vedere se in PRET è fattibile poosizionare il gantt sulla sezione richiesta
$(".time-btn").click(function () {
    changeTimeDomain(this.id);
})
/*
function changeTimeDomain(timeDomainString) {
    this.timeDomainString = timeDomainString;
    switch (timeDomainString) {
        case "0"://"1hr":
            //format = "%H:%M:%S";
            gantt.timeDomain([ d3.timeHour.offset(getEndDate(), -1), getEndDate() ]);
            break;
        case "1"://"3hr":
            //format = "%H:%M";
            gantt.timeDomain([ d3.timeHour.offset(getEndDate(), -3), getEndDate() ]);
            break;

        case "2"://"6hr":
            //format = "%H:%M";
            gantt.timeDomain([ d3.timeHour.offset(getEndDate(), -6), getEndDate() ]);
            break;

        case "3"://"1day":
            //format = "%H:%M";
            gantt.timeDomain([ d3.timeDay.offset(getEndDate(), -1), getEndDate() ]);
            break;

        case "4"://"1day":
            //format = "%H:%M";
            gantt.timeDomain([ d3.timeDay.offset(getEndDate(), -1), getEndDate() ]);
            break;

        case "5"://"1day":
            //format = "%H:%M";
            gantt.timeDomain([ d3.timeDay.offset(getEndDate(), -1), getEndDate() ]);
            break;

        //default:
            //format = "%H:%M"

    }
    //gantt.tickFormat(format);
    gantt.redraw(tasks);
}*/


bursts.sort(function(a, b) {
    return a.endSent - b.endSent;
});
var maxSent = bursts[bursts.length - 1].endSent;
bursts.sort(function(a, b) {
    return a.startSent - b.startSent;
});
var minSent = bursts[0].startSent;

//FIXME: change tick format
var format = "%H:%M";

var burstStatus = {
    "FIRST" : "bar-running",
    "LAST" : "bar-failed",
    "ONGOING" : "bar-succeeded",
    "UNIQUE" : "bar-killed"
};


var gantt = d3.gantt().burstTypes(concepts).burstStatus(burstStatus).tickFormat(format);
gantt(bursts);