/**
 * import the text
 */

/*
var sectionToAnnotate = document.getElementById("sel1").value;
switch(sectionToAnnotate) {
    case "1. Data Storage":
        //FIXME: change when the textfile is ready
        textFile = '../datasets/cap1_annotato.txt';
        break;
    case "3. OS":
        //FIXME: change when the textfile is ready
        textFile = '../datasets/cap3_annotato.txt';
        break;
    case "4. NAI":
        */
        
        /*
        $.ajax({
            type: "GET" ,
            url: "../datasets/testo allineato con T2K/prova23genn.xml" ,
            dataType: "xml" ,
            success: function(xml) {
                //var xmlDoc = $.parseXML( xml );   <------------------this line
                //if single item
                var chapter = $(xml).find('chapter')[0].innerHTML;
                document.getElementById("annotatedText").innerHTML = chapter;
            }});
        */
        //$.get('../datasets/cap4_annotato_PRET_multiwords_e_frasi_risolte.txt',{},function(content){
        //$.get('../datasets/testo allineato con T2K/cap4_annotato_PRET_allineato_con_T2K.txt',{},function(content){
/*
        $.get('../datasets/AIED2019/cap4_annotato_PRET_allineato_con_T2K_1marzo.txt',{},function(content){
            var textBox = document.getElementById("annotatedText");
            textBox.innerHTML = content;
            highlightText();
        });

        break;
    case "11. AI":
        //FIXME: change when the textfile is ready
        textFile = '../datasets/cap11_annotato.txt';
        break;
    default:
        //FIXME: change when all textfiles are available
        textFile = '../datasets/cap4_annotato_PRET.txt';
}

*/




//FIXME: dynamically change the array when terminologies of other chapters are ready
// initialize list of manualConcepts added by the annotator
var manualConcepts = [];
//keep track of the first indexes of a manual concept (needed when download/upload json)
var manualConceptsFirstToks = {};




// populate the horizontal scroll bar with initial autoConcepts
var tempScroll = document.getElementById("pnProductNavContents");
for (let c=0; c < $autoConcepts.length; c++) {
    tempScroll.innerHTML += '<a href="#" class="pn-ProductNav_Link" ' + 'id="scroll_' + c +'"' + ' aria-selected="true" data-toggle="modal" data-target="#conceptSummary" data-to-pass="my_value" onclick="setCentralConcept(this.text);">'+$autoConcepts[c]+'</a>';
}
tempScroll.innerHTML += '<span id="pnIndicator" class="pn-ProductNav_Indicator"></span>';

// populate the horizontal scroll bar with added manualConcepts

// PROVA PER TOGLIERE CONCETTI MANUALI 27/9
//var tempScroll2 = document.getElementById("pnProductNavContents2");
//for (let c=0; c<manualConcepts.length; c++) {
//    tempScroll2.innerHTML += '<a href="#" class="pn-ProductNav_Link" ' + 'id="scroll2_' + c +'"' + ' aria-selected="true" data-toggle="modal" data-target="#conceptSummary" data-to-pass="my_value" onclick="setCentralConcept(this.text);">'+manualConcepts[c]+'</a>';
//}
//tempScroll2.innerHTML += '<span id="pnIndicator2" class="pn-ProductNav_Indicator"></span>';

// variables to keep track of relations, autoConcepts and sentences
var insertedConcepts = new Set();// FIXME: still needed after moving to new version?
var insertedRelations = [];
var num_relations = 0;
var textOnFocus = '';
var sentOnFocus = null;
var target_scelto = ""; // usato per tracciare dove mettere le icone del target
var tokensOnFocus = [];
var candidatesToHighlight = [];
//concept activated in the scroll bar
var centralConcept = "";
var textBox = document.getElementById("annotatedText");
textBox.innerHTML = $tagged;
highlightText()
if (flag) {
    uploadJSON(JSON.parse(json))
}
/* Scripts for adding and deleting entries
*
*/
// number of relations in the modal box
var num_slots=1;
$("#modalAddRelation").ready(function(){
    console.log("num_relations after loaded page: ", num_relations);
    console.log("num_slots after loaded page: ", num_slots);
    $('#add').click(function(){
        // handle cases when there are no slots
        if (num_slots == 0) {
            num_slots++;
            $('#dynamic_field2').append('<tr id="row' + num_slots + '" class="decrementable">\n' +
                '                           <td>' + num_slots +
                '                           </td>' +
                '                           <td>\n' +
                '                               <input type="text" name="name[]" autocomplete="off" id="prerequisite' + num_slots + '" placeholder="Insert a prerequisite" class="form-control name_list autocomplete decrementable" required/>\n' +
                '                           </td>\n' +
                '                           <td>\n' +
                '                               <div class="form-group">\n' +
                '                                   <select class="form-control decrementable" id="weight' + num_slots + '">\n' +
                '                                       <option>strong</option>\n' +
                '                                       <option>weak</option>\n' +
                '                                   </select>\n' +
                '                               </div>\n' +
                '                           </td>\n' +
                '                           <td>' +
                '                               <button type="button" name="remove" id="' + num_slots + '" class="btn btn-danger btn_remove decrementable">X</button>' +
                '                           </td>' +
                '                       </tr>');
            autocomplete(document.getElementById("prerequisite" + num_slots), $autoConcepts.concat(manualConcepts), $autoConcepts.indexOf(document.getElementById("selectedAdvanced").value));
        }
        console.log("num_slots after clicked 'add': ", num_slots);
        console.log("num_relations after clicked 'add': ", num_relations);
        // prevent a null reference when the modal retrieve relations previously inserted
        if (!document.getElementById("prerequisite"+num_slots)) {
            num_slots--;
        }
        if ((document.getElementById("prerequisite"+num_slots).value === "") ||
                (document.getElementById("selectedAdvanced").value === "")) {
            alert("You must choose a concept!"); return false;
        }
        else if (!$autoConcepts.includes(document.getElementById("prerequisite"+num_slots).value) &&
                 !manualConcepts.includes(document.getElementById("prerequisite"+num_slots).value)) {
            alert("Use only concepts already included in the terminology!");
            document.getElementById("prerequisite"+num_slots).value = "";
        }
        else if (document.getElementById("prerequisite" + num_slots).value === document.getElementById("selectedAdvanced").value) {
            alert("A concept can not be prerequisite of itself !");
            document.getElementById("prerequisite"+num_slots).value = "";
        }
        else {
            //avoid duplicate relations (even id they have a different weight)
            let prereqList = [];
            for (let inp of document.getElementsByTagName("input")) {
                if (inp.id.startsWith("prerequisite")) {
                    if (prereqList.includes(inp.value)) {
                        alert("You inserted a relation twice!");
                        return false;
                    }
                    else {
                        prereqList.push(inp.value);
                    }
                }
            }
            //FIXME: prevent num_relations to be < 0
            if (num_relations == 0) {
                //console.log("num_relations < 0");
            }
            num_relations++;
            num_slots++;
            console.log("num_relations:", num_relations);
            console.log("num_slots:", num_slots);
            $('#dynamic_field2').append('<tr id="row' + num_slots + '" class="decrementable">\n' +
                '                           <td>' + num_slots +
                '                           </td>' +
                '                           <td>\n' +
                '                               <input type="text" name="name[]" autocomplete="off" id="prerequisite' + num_slots + '" placeholder="Insert a prerequisite" class="form-control name_list autocomplete decrementable" required/>\n' +
                '                           </td>\n' +
                '                           <td>\n' +
            '                                   <select class="form-control decrementable" id="weight' + num_slots + '">\n' +
            '                                       <option>strong</option>\n' +
            '                                       <option>weak</option>\n' +
            '                                   </select>\n' +
                '                           </td>\n' +
                '                           <td>' +
                '                               <button type="button" name="remove" id="' + num_slots + '" class="btn btn-danger btn_remove decrementable">X</button>' +
                '                           </td>' +
                '                       </tr>');

            autocomplete(document.getElementById("prerequisite" + num_slots), $autoConcepts.concat(manualConcepts), $autoConcepts.indexOf(document.getElementById("selectedAdvanced").value));

            /*
            var relation = $("#add_name").serialize();
            //console.log(relation);
            pre = $("#prerequisite"+(i-1)).val();
            sub = $("#advanced"+(i-1)).val();
            var rel={"prerequisite":pre, "subsidiary":sub,
                "sentWithAdvance": sentWithAdvance};
            $.ajax({
                type: 'PUT',
                contentType: 'application/json;charset=utf-8',
                //data: JSON.stringify(relation),
                data: JSON.stringify(rel),
                dataType: 'json',
                url: 'processjson',
                success: function () {
                    alert("Success: " );
                },
                error: function(error) {
                    alert("AJAX Error: "+ console.log(error));
                }
            });
            //reset sentence's index
            sentWithAdvance = null;
            */
        }

    });
    $(document).on('click', '.btn_remove', function(){
        var button_id = $(this).attr("id");
        //console.log("button_id: ", button_id);
        var ask = confirm("The relation will be PERMANENTLY removed! Press OK to confirm.");
        if (ask == true) {
            var sentRemove = document.getElementById("selectedsentence").value;
            var prereqRemove = document.getElementById("prerequisite"+button_id).value;
            var advancedRemove = document.getElementById("selectedAdvanced").value;
            var weightRemove = document.getElementById("weight"+button_id).value;
            for (let rel of insertedRelations) {
                if (rel["sent"] == sentRemove &&
                    rel["prerequisite"] === prereqRemove &&
                    rel["advanced"] === advancedRemove &&
                    rel["weight"] === weightRemove) {
                    let index = insertedRelations.indexOf(rel);
                    //console.log("DELETED: ");
                    //console.log(rel);
                    //console.log(index);
                    insertedRelations.splice(index, 1);


                    break;
                }
            }
            $('#dynamic_field2 > #row'+button_id).remove();
            //num_relations --;
            console.log("num_slots: ", num_slots);
            num_slots = $('#dynamic_field2 tr').length;
            console.log("num_relations: ", num_relations);
            console.log("num_slots: ", num_slots);
            var toDecrement = document.getElementsByClassName('decrementable');
            for (var x=0; x < toDecrement.length; x++) {
                var curr_id = toDecrement[x].id;
                if (curr_id.slice(-1) > button_id) {
                    // decrease the indicator of the row
                    if (curr_id.startsWith("row")) {
                        let numCell = parseInt($("#"+curr_id).find('td:first').text()) - 1;
                        $("#"+curr_id).find('td:first').text(numCell.toString());
                    }
                    toDecrement[x].id = curr_id.slice(0, -1) + (parseInt(curr_id.slice(-1))-1).toString();
                }
            }
        }
    });

    function checkSymmetric(prereq, advanced){
        /* X -> Y e Y -> X*/
        for (var i in insertedRelations)
            if(insertedRelations[i].advanced == prereq && insertedRelations[i].prerequisite == advanced)
                return true;

        return false;
    }

    function checkCycle(prereq, advanced){
        /* faccio una ricerca partendo dal target
        se dal target riesco ad arrivare al prerequisito vuol dire che mettendo la relazione
        prereq -> target si creerebbe un ciclo */
        return BFS(advanced, prereq)
    }

    function isTransitive(prereq, advanced){
        /* faccio una ricerca partendo dal prerequisito arrivando al target
        * se esiste già un path che li collega allora la relazione che sto per immettere è transitiva*/
        return BFS(prereq, advanced);
    }


    function getNeighbors (concept){
        neighbors = [];
        for (let key in insertedRelations){
            if(insertedRelations[key].prerequisite == concept)
                neighbors.push(insertedRelations[key].advanced)
        }
        return neighbors;
    }

    function BFS(from, to) {

        let queue = [from];

        while (queue.length) {

            let curr = queue.pop();
            nextLevel = getNeighbors(curr);

            if( nextLevel.includes(to))
                return true; //found
            else
                for(let i=0; i<nextLevel.length; i++)
                    queue.push(nextLevel[i]);
        }

        return false; //not found
    }

    $('#confirm_relations').click(function(){
        let advanced = document.getElementById("selectedAdvanced").value;
        let sent_id = document.getElementById("selectedsentence").value;

        //avoid duplicate relations (even id they have a different weight)
        let prereqList = [];
        for (let inp of document.getElementsByTagName("input")) {
            if (inp.id.startsWith("prerequisite")) {
                if (prereqList.includes(inp.value)) {
                    alert("You inserted a relation twice!");
                    return false;
                }
                else {
                    prereqList.push(inp.value);
                }
            }
        }

        // other checks against errors
        for (let rel=1; rel<=$('#dynamic_field2 tr').length; rel++) {
            let prereq = document.getElementById("prerequisite" + rel).value;
            let weight = document.getElementById("weight" + rel).value;

            // avoid empty inputs
            if ((prereq === "") ||
                (advanced === "")) {
                alert("Concepts must be non-empty!");
                return false;
            }
            // avoid concepts not inserted (advanced)
            else if (!$autoConcepts.includes(advanced) &&
                !manualConcepts.includes(advanced)) {
                alert("The advanced concept is not yet in the terminology!\nClose this box and insert it.");
                return false;
            }
            // avoid concepts not inserted (prerequisites)
            else if (!$autoConcepts.includes(prereq) &&
                !manualConcepts.includes(prereq)) {
                alert("Use only prerequisites already included in the terminology!");
                document.getElementById("prerequisite" + rel).value = "";
                return false;
            }
            // avoid reflexive relations
            else if (prereq === advanced) {
                alert("A concept can not be prerequisite of itself !");
                document.getElementById("prerequisite" + rel).value = "";
                return false;
            }
            //avoid symmetric relations
            else if(checkSymmetric(prereq, advanced)){
                alert("Cannot insert symmetric relation");
                return false;
            }
            //avoid cycles
            else if(checkCycle(prereq, advanced)){
                alert("Cannot insert the relation '" + prereq + "' --> '" + advanced +"' because it will create a cycle");
                return false;
            }
            else {
                // the relation is valid
                let toInsert = {"sent": sent_id, "advanced": advanced, "prerequisite": prereq, "weight": weight,"advanced_id":target_scelto.getAttribute("concept_id")};

                //check if already present
                var already_present = JSON.stringify(insertedRelations).includes(JSON.stringify(toInsert));

                //warning if the relation is transitive
                //ask the user if he is sure
                var confirmed = false;

                if(isTransitive(prereq,advanced) && !already_present)
                    confirmed = confirm('The relation "' + prereq + '" --> ' + ' "' + advanced + ' " is transitive, do you want to insert it? ');
                else
                    confirmed = true;

                // check if already exists a inserted relation that only differs for the weight
                var res = insertedRelations.reduce(function(acc, curr, index) {
                    if (curr.sent === toInsert["sent"] &&
                        curr.prerequisite === toInsert["prerequisite"] &&
                        curr.advanced === toInsert["advanced"] &&
                        curr.weight !== toInsert["weight"]) {
                        acc.push(index);
                    }
                    return acc;
                }, []);

                // if the relation has already been inserted with a different weight, change the weight
                if (res.length) {
                    insertedRelations[res[0]] = toInsert;
                }
                // else, insert the full relation (if not previously inserted)
                else {
                    if (!already_present && confirmed) {
                        insertedRelations.push(toInsert);

                        //icona sul target (se non già presente)
                        if($(target_scelto).find("img").length == 0) {
                            var icona = document.createElement("img");
                            icona.src = '../static/images/transfer.svg';
                            target_scelto.appendChild(icona);
                        }
                    }
                }
            }
        }
        renderHTML();
    });
});


$(document).on('click', '.btn_remove_full', function(){
    let rel_idx = this.id.split('_')[1];
    var ask = confirm("The relation will be removed! Press OK to confirm.");
    if (ask == true) {
        var target = insertedRelations[rel_idx].advanced;
        var target_id = insertedRelations[rel_idx].advanced_id;
        var sentence = insertedRelations[rel_idx].sent;

        console.log(insertedRelations[rel_idx]);
        insertedRelations.splice(rel_idx, 1);

        //Se non ho altre relazioni con lo stesso target nella stessa frase rimuovo icona
        var altra_rel = false;
        for (let rel of insertedRelations){
            if(rel['advanced'] == target && rel["sent"]== sentence ){
                altra_rel = true;
                break;
            }
        }

        if(!altra_rel)
            $('sent[sent_id='+sentence+']').find('concept[concept_id=' + target_id + ']').find('img').remove();

        renderHTML();
    }
});


/** Scripts for autocompletion
 *
 * @param inp: the text field element;
 * @param arr: an array of possible autocompleted values;
 * @param pos: the index ("pos") of the inserted concept A inside the array
                (used to change the color of the prerequisite autoConcepts)
 */
function autocomplete(inp, arr, pos=0) {
    var currentFocus;
    /*execute a function when someone writes in the text field:*/
    inp.addEventListener("input", function(e) {
        var a, b, i, val = this.value;
        /*close any already open lists of autocompleted values*/
        closeAllLists();
        if (!val) { return false;}
        currentFocus = -1;
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        /*append the DIV element as a child of the autocomplete container:*/
        this.parentNode.appendChild(a);
        //arr.splice(arr[pos], 1);
        /*for each item in the array...*/
        for (i = 0; i < arr.length; i++) {
            /*check if the item starts with the same letters as the text field value:*/
            if (arr[i].substr(0, val.length).toUpperCase() === val.toUpperCase()) {
                /*create a DIV element for each matching element:*/
                b = document.createElement("DIV");
                if ($autoConcepts.includes(arr[i])) {
                    b.classList.add("automatic_concept");
                }
                else if (manualConcepts.includes(arr[i])) {
                    b.classList.add("manual_concept");
                }

                /*make the matching letters bold:*/
                b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
                b.innerHTML += arr[i].substr(val.length);
                /*insert a input field that will hold the current array item's value:*/
                b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
                /*execute a function when someone clicks on the item value (DIV element):*/
                b.addEventListener("click", function(e) {
                    /*insert the value for the autocomplete text field:*/
                    inp.value = this.getElementsByTagName("input")[0].value;
                    //call autocomplete passing the index of the inserted advanced concept
                    if (inp.id.startsWith("advanced")) {
                        autocomplete(document.getElementById("prerequisite"+inp.id.slice(-1)), $autoConcepts, $autoConcepts.indexOf(inp.value));
                    }

                    /*close the list of autocompleted values,
                    (or any other open lists of autocompleted values:*/
                    closeAllLists();
                });
                a.appendChild(b);
            }
        }
    });

    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        //console.log(this.id);
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            /*If the arrow DOWN key is pressed,
            increase the currentFocus variable:*/
            currentFocus++;
            /*and and make the current item more visible:*/
            addActive(x);
            //autocomplete(document.getElementById("prerequisite" + this.id), $autoConcepts.concat(manualConcepts), $autoConcepts.indexOf(document.getElementById("selectedAdvanced").value));
        } else if (e.keyCode == 38) { //up
            /*If the arrow UP key is pressed,
            decrease the currentFocus variable:*/
            currentFocus--;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 13) {
            /*If the ENTER key is pressed, prevent the form from being submitted,*/
            e.preventDefault();
            if (currentFocus > -1) {
                /*and simulate a click on the "active" item:*/
                if (x) x[currentFocus].click();
                //set the concept on focus in the scroll bar
                //moveIndicator(document.getElementById('scroll_'+ $autoConcepts.indexOf(document.getElementById("advanced" + num_relations).value)), 'red');
                // FIXME: commmented after moving from old to new version
                //updateScrollBar(document.getElementById("advanced" + num_relations).value);
            }
        }
    });

    function addActive(x) {
        /*a function to classify an item as "active":*/
        if (!x) return false;
        /*start by removing the "active" class on all items:*/
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        /*add class "autocomplete-active":*/
        x[currentFocus].classList.add("autocomplete-active");
        x[currentFocus].style.backgroundColor = "lightBlue";
    }

    function removeActive(x) {
        /*a function to remove the "active" class from all autocomplete items:*/
        for (let i = 0; i < x.length; i++) {
            x[i].classList.remove("autocomplete-active");
            x[i].style.backgroundColor = "white";
        }
    }

    function closeAllLists(elmnt) {
        /*close all autocomplete lists in the document,
        except the one passed as an argument:*/
        var x = document.getElementsByClassName("autocomplete-items");
        for (let i = 0; i < x.length; i++) {
            if (elmnt != x[i] && elmnt != inp) {
                x[i].parentNode.removeChild(x[i]);
            }
        }
    }

    /*execute a function when someone clicks in the document:*/
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
}

function setCentralConcept(c) {
    centralConcept = c;
    $('#conceptSummary').modal('show');
}


$('#conceptSummary').on('show.bs.modal', function(e) {
    $(e.currentTarget).find('h4[id="conceptSummary_name"]').text(centralConcept);
    //$("#table_conceptSummary").empty();
    $("#table_conceptSummary").find("tr:not(:first)").remove();
    for (let rel of insertedRelations) {
        if (rel["prerequisite"] === centralConcept || rel["advanced"] === centralConcept) {
            let table = document.getElementById("table_conceptSummary");
            let row = table.insertRow(table.rows.length);
            let cell0 = row.insertCell(0);
            let cell1 = row.insertCell(1);
            let cell2 = row.insertCell(2);
            let cell3 = row.insertCell(3);
            cell0.innerHTML = rel["sent"];
            cell1.innerHTML = rel["prerequisite"];
            cell2.innerHTML = rel["advanced"];
            cell3.innerHTML = rel["weight"];
        }
    }

});

/**
 * script for filling the preview area
*/
function renderHTML(){
    $("#table_recap_full").find("tr:not(:first)").remove();
    for (let rel of insertedRelations) {
        let table = document.getElementById("table_recap_full");
        let row = table.insertRow(table.rows.length);
        let cell0 = row.insertCell(0);
        let cell1 = row.insertCell(1);
        let cell2 = row.insertCell(2);
        let cell3 = row.insertCell(3);
        let cell4 = row.insertCell(4);
        let cell5 = row.insertCell(5);
        let cell6 = row.insertCell(6);
        cell0.innerHTML = '<input id="reopenRel_' + insertedRelations.indexOf(rel) + '" class="reopen_button" type="image" src="../static/images/eye2.png" title="click to re-open the box with relations" />';
        cell1.innerHTML = insertedRelations.indexOf(rel).toString();
        cell2.innerHTML = rel["sent"];
        cell3.innerHTML = rel["prerequisite"];
        cell4.innerHTML = rel["advanced"];
        cell5.innerHTML = rel["weight"];
        cell6.innerHTML = '<button type="button" name="remove" id="removeRel_' + insertedRelations.indexOf(rel) + '" class="btn btn-danger btn_remove_full" title="click to delete this relation">X</button>';
    }


    $(".reopen_button").on('click', function (e) {
        let clickedRow = parseInt( $(e.currentTarget)[0].id.replace("reopenRel_", "") ) + 1;
        //let clickedRow = $(this).id;//.replace("reopenRel_", "");
        console.log(clickedRow);
        sentOnFocus = $("#table_recap_full")[0].rows[clickedRow].cells[2].innerHTML;
        console.log(sentOnFocus);
        textOnFocus = $("#table_recap_full")[0].rows[clickedRow].cells[4].innerHTML;
        console.log(textOnFocus);

        $('#modalAddRelation').modal('show');
        return false;
    });

    /*
    var data = new FormData();
    data.append("data" , document.getElementById("prerequisite"+i).value+";"+document.getElementById("advanced"+i).value);
    //var xhr = (window.XMLHttpRequest) ? new XMLHttpRequest() : new activeXObject("Microsoft.XMLHTTP");
    var xhr = new XMLHttpRequest();
        xhr.open( 'post', 'data.php', true );
        xhr.send(data);
    */


}





/**
 *  script for highlighting autoConcepts in the text
 *
*/
//FIXME: find <concept> tag to decide what need to be highlighted
function highlightText() {
    
    var x = document.getElementsByTagName('concept');
    if (insertedConcepts) {
    for (var el=0; el<x.length; el++) {
        if (!insertedConcepts.has(x[el])) {
            x[el].classList.add("highlight");
            //x[el].setAttribute("class", "highlight");
        }
        else {
            x[el].classList.remove("highlight");
        }
    }
    }

    $('concept').on('dblclick', function(e) {

         target_scelto = this;
        //console.log("clicked a concept");
        //retieve concept
        // FIXME: check if the clicked concept belongs to a nested multiword
        if ($(e.currentTarget).parents('.nested_concept').length || textOnFocus.includes("<concept"))  {
            $('#chooseConcept').modal('show');
            autocomplete(document.getElementById("properAdvanced"), $autoConcepts.concat(manualConcepts), 0);
        }
        else if ($(e.currentTarget).hasClass("automatic_concept")) {
            textOnFocus = $autoConcepts[$(e.currentTarget).attr("concept_id")];
        }
        else if ($(e.currentTarget).hasClass("manual_concept")) {
            textOnFocus = manualConcepts[$(e.currentTarget).attr("concept_id")];
        }

        //retrieve sentence
        sentOnFocus = $(e.currentTarget).parent().attr('sent_id');
        $('#modalAddRelation').modal('show');
        //$(".modal-body #dataToDisplay").text($(e.target).html());
    });
}


$('#modalAddTerm').on('show.bs.modal', function(e) {
    $(e.currentTarget).find('input[id="newConcept"]').val(textOnFocus.trim());
    document.getElementById('active_concept').value = "";
    //insert the lemma of each tokens
    var lemma = "";

    candidatesToHighlight = {};
    //console.log(tokensOnFocus);
    for (let t of tokensOnFocus) {
        let currLemma = $conll[t]["lemma"];
        lemma += currLemma.toUpperCase() + " ";
        let matches = $conll.filter(t => t["lemma"].toUpperCase() === currLemma.toUpperCase()).map(t => t["tok_id"]);
        for (let m of matches) {
            candidatesToHighlight[m-1] = currLemma;
        }
    }
    $(e.currentTarget).find('input[id="newConceptLemma"]').val(lemma.trim());
    //console.log(candidatesToHighlight);
});

function addTerm() {
    document.getElementById('active_concept').value = "";
    var conceptToAdd = document.getElementById("newConceptLemma").value.toUpperCase();
    if (conceptToAdd === "") {
        alert("You must insert something!"); return false;
    }
    if ($autoConcepts.includes(conceptToAdd) || manualConcepts.includes(conceptToAdd)) {
        alert("The concept is already present in the terminologies."); return false;
    }

    manualConcepts.push(conceptToAdd);
    // populate the horizontal scroll bar with added manualConcepts
    var tempScroll2 = document.getElementById("pnProductNavContents2");
    tempScroll2.innerHTML += '<a href="#" class="pn-ProductNav_Link" ' + 'id="scroll2_' + conceptToAdd +'"' + ' aria-selected="true" data-toggle="modal" data-target="#conceptSummary" data-to-pass="my_value" onclick="setCentralConcept(this.text);">'+conceptToAdd+'</a>';
    tempScroll2.innerHTML += '<span id="pnIndicator2" class="pn-ProductNav_Indicator"></span>';


    //use the database to retrieve all the IDs of the tokens part of the concept
    var toHighlight = [];

    for (var x in candidatesToHighlight) {
        //let firstLemma = $conll[tokensOnFocus[0]-1]["lemma"];
        let tokens = conceptToAdd.split(" ");
        if (candidatesToHighlight[x].toUpperCase() === tokens[0].toUpperCase()) {
            var j = 1;
            while (j < tokens.length) {
                var next = parseInt(x)+j;
                let currLemma = $conll[next]["lemma"];
                if (next in candidatesToHighlight && candidatesToHighlight[next].toUpperCase() === currLemma.toUpperCase()) {
                    j++;
                }
                else {
                    break;
                }
            }
            if (j === tokens.length) {
                toHighlight.push(x);
            }
        }
    }
    //console.log(toHighlight);
    //manualConceptsFirstToks[conceptToAdd] = range(parseInt(toHighlight[0]), toHighlight[0]+conceptToAdd.length);
    manualConceptsFirstToks[conceptToAdd] = toHighlight;

    for (let c of toHighlight) {
        updateText(parseInt(c), conceptToAdd.split(" ").length, manualConcepts.indexOf(conceptToAdd));
    }

    highlightText();
}

function updateText(firstTok, conceptLength, conceptID) {
    for (let t of range(firstTok, firstTok+conceptLength)) {
        if ($("[tok_id=" + t + "]").attr("partof_autoconcept") ||
            $("[tok_id=" + t + "]").attr("partof_manualconcept")) {
            return null;
        }
    }
    for (let t of range(firstTok, firstTok+conceptLength)) {
        $("[tok_id=" + t + "]").attr("partof_manualconcept", conceptID);
        $("[tok_id=" + t + "]").addClass("inner");
    }
    // embed the tokens in a <concept>
    $(".inner").wrapAll( "<concept class='manual_concept' concept_id='"+conceptID+"' />");
    $("token").removeClass("inner");
    // reinsert white spaces after they get deleted with wrapall
    for (let t of range(firstTok, firstTok+conceptLength-1)) {
        $("[tok_id=" + t + "]").after(" ");
    }
}


$('#modalAddRelation').on('show.bs.modal', function(e) {
    // hide the recap box
    document.getElementById("recap_adv").style.display = 'none';
    document.getElementById("recap_sentence").style.display = 'none';
    var selectedConcept = textOnFocus;
    //console.log(selectedConcept);
    $(e.currentTarget).find('input[id="selectedAdvanced"]').val(selectedConcept);
    //retrieve the context (can be a sentence, a title of the chapter, of a section or subsection)
    // fix the problem when the context is sentX_tokenY
    //console.log(sentOnFocus);
    if (sentOnFocus.includes("_token")) {
        sentOnFocus = sentOnFocus.substr(0, sentOnFocus.indexOf("_token"));
    }
    var context = sentOnFocus;


    $(e.currentTarget).find('input[id="selectedsentence"]').val(context);

    // FIXME: reset empty slots if there are no inserted relations
    num_slots = 1;
    $('#dynamic_field2').empty();
    $('#dynamic_field2').append(
        '                       <tr id="row' + num_slots + '" class="decrementable">\n' +
        '                           <td>' + num_slots +
        '                           </td>' +
        '                           <td>' +
        '                               <input type="text" name="name[]" autocomplete="off" id="prerequisite1" placeholder="Insert a prerequisite" class="form-control name_list autocomplete decrementable" required/>' +
        '                           </td>' +
        '                           <td>' +
        '                                    <select class="form-control decrementable" id="weight1">' +
        '                                       <option>strong</option>' +
        '                                       <option>weak</option>' +
        '                                   </select>' +
        '                           </td>' +
        '                           <td>' +
        '                               <button type="button" name="remove" id="' + num_slots + '" " class="btn btn-danger btn_remove decrementable">X</button> ' +
        '                           </td>' +
        '                       </tr>');

    autocomplete(document.getElementById("prerequisite1"), $autoConcepts.concat(manualConcepts), $autoConcepts.indexOf(selectedConcept));

    for (let rel of insertedRelations) {
        if (rel["sent"] === context && rel["advanced"] === selectedConcept) {
            //console.log("num_slots after founded", num_slots);
            if (num_slots > 1) {
                $('#dynamic_field2').append('<tr id="row' + num_slots + '" class="decrementable">\n' +
                    '                        <td>' + num_slots +
                    '                        </td>' +
                    '                        <td>\n' +
                    '                            <input type="text" name="name[]" autocomplete="off" id="prerequisite' + num_slots + '" placeholder="Insert a prerequisite" class="form-control name_list autocomplete decrementable" required/>\n' +
                    '                        </td>\n' +
                    '                        <td>\n' +
                    '                            <div class="form-group">\n' +
                    '                                <select class="form-control decrementable" id="weight' + num_slots + '">\n' +
                    '                                    <option>strong</option>\n' +
                    '                                    <option>weak</option>\n' +
                    '                                </select>\n' +
                    '                            </div>\n' +
                    '                        </td>\n' +
                    '                        <td>' +
                    '                            <button type="button" name="remove" id="' + num_slots + '" class="btn btn-danger btn_remove decrementable">X</button>' +
                    '                        </td></tr>');
            }
            let currPrereq = "prerequisite" + num_slots;
            let currWeight = "weight" + num_slots;
            //console.log(currPrereq);
            //console.log(currWeight);
            //console.log(rel["prerequisite"]);
            document.getElementById(currPrereq).value = rel["prerequisite"];
            document.getElementById(currWeight).value = rel["weight"];
            autocomplete(document.getElementById("prerequisite" + num_slots), $autoConcepts.concat(manualConcepts), $autoConcepts.indexOf(document.getElementById("selectedAdvanced").value));
            num_slots++;
        }
    }

});

$("#show_save_modal").on('click', function (e) {
    $("#save_modal").modal("show");
});


/**
 * Delete manual terms
 */
$("#delete_concept").on('click', function (e) {
    $("#modalDeleteTerm").modal("show");
    //return false;
});

$('#modalDeleteTerm').on('show.bs.modal', function(e) {
    autocomplete(document.getElementById("del_select"), manualConcepts);
});

function deleteTerm() {
    let toDelete = document.getElementById("del_select").value;
    // avoid deleting not-inserted concepts
    if (!manualConcepts.includes(toDelete)) {
        alert("Sorry, you can only delete concepts manually added by you!");
        document.getElementById("del_select").value = "";
        return false;
    }
    // avoid deleting concepts that are prerequisite or advance in some relation
    // TODO: in future handle this case by asking the user if he also wants to delete the relations
    for (let rel of insertedRelations) {
        if (rel["advanced"] === toDelete || rel["prerequisite"] === toDelete) {
            alert("Sorry, the current version of the tool does not allow to delete this concept because it's a prerequisite or an advance concept in some relation.");
            document.getElementById("del_select").value = "";
            return false;
        }
    }

    var ask = confirm("The concept will be removed from the terminology!\nPress OK to confirm.");
    if (ask === true) {
        manualConcepts.splice(manualConcepts.indexOf(toDelete), 1);

        // populate the horizontal scroll bar with added manualConcepts
        let tempScroll2 = document.getElementById("pnProductNavContents2");
        tempScroll2.innerHTML = "";
        for (let c=0; c<manualConcepts.length; c++) {
            tempScroll2.innerHTML += '<a href="#" class="pn-ProductNav_Link" ' + 'id="scroll2_' + c +'"' + ' aria-selected="true" data-toggle="modal" data-target="#conceptSummary" data-to-pass="my_value" onclick="setCentralConcept(this.text);">'+manualConcepts[c]+'</a>';
        }
        tempScroll2.innerHTML += '<span id="pnIndicator2" class="pn-ProductNav_Indicator"></span>';

        //FIXME: handle ID of the concepts now that the list has changed!!!

        //remove green highlighting from the text
        for (let c of manualConceptsFirstToks[toDelete]) {
            removeHighlight(parseInt(c), toDelete.split(" ").length, manualConcepts.indexOf(toDelete));
        }
        highlightText();
        // remove toDelete from manualConceptsFirstToks
        delete manualConceptsFirstToks[toDelete];
    }
    document.getElementById("del_select").value = "";
}

function removeHighlight(firstTok, conceptLength) {
    for (let t of range(firstTok, firstTok+conceptLength)) {
        //remove attribute "partof_manualconcept"
        $("[tok_id=" + t + "]").removeAttr("partof_manualconcept");
        $("[tok_id=" + t + "]").parent("concept").addClass("outer");
    }
    // remove the tag <concept> that embeds the string
    $("concept.outer").contents().unwrap();
}


/**
 * Add a violet bookmark in the annotated text (at sentence level)
 */
function highlightSentence() {
    $("sent[sent_id='" + sentOnFocus + "']").toggleClass('selected');
}

/**
 * set the concept on focus in the scroll bar
 *
 * @param conceptToFocus
 */
function updateScrollBar(conceptToFocus) {
    //document.getElementById('scroll_'+ $autoConcepts.indexOf(clickedConcept)).setAttribute("aria-selected", "true");
    centralConcept = $autoConcepts.indexOf(conceptToFocus);
    moveIndicator(document.getElementById('scroll_'+ centralConcept), 'red');
    var leftmostConcept = 0;
    if (centralConcept > 3) {
        leftmostConcept = centralConcept - 3;
    }
    $('#pnProductNav').scrollTo('#scroll_'+ leftmostConcept);
}

/**
 * script for populating the recap boxes
 *
 * @param conceptType
 */
function showRecap(selectedAdvanced) {
    document.getElementById("recap_adv").innerHTML = '<table class="table table-bordered" id="table_recap"><tr><th>SENTENCE</th><th>PREREQUISITE</th><th>WEIGHT</th></tr></table>';
    let currSent = document.getElementById("selectedsentence").value;
    for (let rel of insertedRelations) {
        if (rel["advanced"] === selectedAdvanced.value && rel["sent"] !== currSent) {
            let table = document.getElementById("table_recap");
            let row = table.insertRow(table.rows.length);
            let cell0 = row.insertCell(0);
            let cell1 = row.insertCell(1);
            let cell2 = row.insertCell(2);
            cell0.innerHTML = rel["sent"];
            cell1.innerHTML = rel["prerequisite"];
            cell2.innerHTML = rel["weight"];
        }
    }

    // hide/show the box
    let x = document.getElementById("recap_adv");
    if (x.style.display && x.style.display !== 'none') {
        x.style.display = 'none';
    } else {
        x.style.display = 'block';
    }
}

function showSentence() {
    let currSent = document.getElementById("selectedsentence").value;
    //document.getElementById("recap_sentence").innerHTML = '<textarea>' + $sentList[currSent-1].text + '</textarea>';
    document.getElementById("recap_sentence").innerHTML = '<table class="table table-bordered"><textarea id="sent_textarea" rows="3" class="form-control z-depth-1" readonly>' + $sentList[currSent-1].text + '</textarea></table>';

    // hide/show the box
    let x = document.getElementById("recap_sentence");
    if (x.style.display && x.style.display !== 'none') {
        x.style.display = 'none';
    } else {
        x.style.display = 'block';
    }
}


/** script for the horizontal scroll bar
 *
 * @type {{navBarTravelling: boolean, navBarTravelDirection: string, navBarTravelDistance: number}}
 */


var SETTINGS = {
    navBarTravelling: false,
    navBarTravelDirection: "",
    navBarTravelDistance: 150
};


// advancer buttons
var pnAdvancerLeft = document.getElementById("pnAdvancerLeft");
var pnAdvancerRight = document.getElementById("pnAdvancerRight");
// indicator
var pnIndicator = document.getElementById("pnIndicator");

var pnProductNav = document.getElementById("pnProductNav");
var pnProductNavContents = document.getElementById("pnProductNavContents");

pnProductNav.setAttribute("data-overflowing", determineOverflow(pnProductNavContents, pnProductNav));

// Set the indicator
if(pnProductNav.querySelector("[aria-selected=\"true\"]") != null)
    moveIndicator(pnProductNav.querySelector("[aria-selected=\"true\"]"), "red");

// Handle the scroll of the horizontal container
var last_known_scroll_position = 0;
var ticking = false;

function doSomething(scroll_pos) {
    pnProductNav.setAttribute("data-overflowing", determineOverflow(pnProductNavContents, pnProductNav));
}

pnProductNav.addEventListener("scroll", function() {
    last_known_scroll_position = window.scrollY;
    if (!ticking) {
        window.requestAnimationFrame(function() {
            doSomething(last_known_scroll_position);
            ticking = false;
        });
    }
    ticking = true;
});


pnAdvancerLeft.addEventListener("click", function() {
    // If in the middle of a move return
    if (SETTINGS.navBarTravelling === true) {
        return;
    }
    // If we have content overflowing both sides or on the left
    if (determineOverflow(pnProductNavContents, pnProductNav) === "left" || determineOverflow(pnProductNavContents, pnProductNav) === "both") {
        // Find how far this panel has been scrolled
        var availableScrollLeft = pnProductNav.scrollLeft;
        // If the space available is less than two lots of our desired distance, just move the whole amount
        // otherwise, move by the amount in the settings
        if (availableScrollLeft < SETTINGS.navBarTravelDistance * 2) {
            pnProductNavContents.style.transform = "translateX(" + availableScrollLeft + "px)";
        } else {
            pnProductNavContents.style.transform = "translateX(" + SETTINGS.navBarTravelDistance + "px)";
        }
        // We do want a transition (this is set in CSS) when moving so remove the class that would prevent that
        pnProductNavContents.classList.remove("pn-ProductNav_Contents-no-transition");
        // Update our settings
        SETTINGS.navBarTravelDirection = "left";
        SETTINGS.navBarTravelling = true;
    }
    // Now update the attribute in the DOM
    pnProductNav.setAttribute("data-overflowing", determineOverflow(pnProductNavContents, pnProductNav));
});

pnAdvancerRight.addEventListener("click", function() {
    // If in the middle of a move return
    if (SETTINGS.navBarTravelling === true) {
        return;
    }
    // If we have content overflowing both sides or on the right
    if (determineOverflow(pnProductNavContents, pnProductNav) === "right" || determineOverflow(pnProductNavContents, pnProductNav) === "both") {
        // Get the right edge of the container and content
        var navBarRightEdge = pnProductNavContents.getBoundingClientRect().right;
        var navBarScrollerRightEdge = pnProductNav.getBoundingClientRect().right;
        // Now we know how much space we have available to scroll
        var availableScrollRight = Math.floor(navBarRightEdge - navBarScrollerRightEdge);
        // If the space available is less than two lots of our desired distance, just move the whole amount
        // otherwise, move by the amount in the settings
        if (availableScrollRight < SETTINGS.navBarTravelDistance * 2) {
            pnProductNavContents.style.transform = "translateX(-" + availableScrollRight + "px)";
        } else {
            pnProductNavContents.style.transform = "translateX(-" + SETTINGS.navBarTravelDistance + "px)";
        }
        // We do want a transition (this is set in CSS) when moving so remove the class that would prevent that
        pnProductNavContents.classList.remove("pn-ProductNav_Contents-no-transition");
        // Update our settings
        SETTINGS.navBarTravelDirection = "right";
        SETTINGS.navBarTravelling = true;
    }
    // Now update the attribute in the DOM
    pnProductNav.setAttribute("data-overflowing", determineOverflow(pnProductNavContents, pnProductNav));
});

pnProductNavContents.addEventListener(
    "transitionend",
    function() {
        // get the value of the transform, apply that to the current scroll position (so get the scroll pos first) and then remove the transform
        var styleOfTransform = window.getComputedStyle(pnProductNavContents, null);
        var tr = styleOfTransform.getPropertyValue("-webkit-transform") || styleOfTransform.getPropertyValue("transform");
        // If there is no transition we want to default to 0 and not null
        var amount = Math.abs(parseInt(tr.split(",")[4]) || 0);
        pnProductNavContents.style.transform = "none";
        pnProductNavContents.classList.add("pn-ProductNav_Contents-no-transition");
        // Now lets set the scroll position
        if (SETTINGS.navBarTravelDirection === "left") {
            pnProductNav.scrollLeft = pnProductNav.scrollLeft - amount;
        } else {
            pnProductNav.scrollLeft = pnProductNav.scrollLeft + amount;
        }
        SETTINGS.navBarTravelling = false;
    },
    false
);

// Handle setting the currently active link
pnProductNavContents.addEventListener("click", function(e) {
    var links = [].slice.call(document.querySelectorAll(".pn-ProductNav_Link"));
    // Pass the clicked item and a colour to the move indicator
    moveIndicator(e.target, "red");
});

function moveIndicator(item, color) {
    var textPosition = item.getBoundingClientRect();
    var container = pnProductNavContents.getBoundingClientRect().left;
    var distance = textPosition.left - container;
    var scroll = pnProductNavContents.scrollLeft;
    pnIndicator.style.transform = "translateX(" + (distance + scroll) + "px) scaleX(" + textPosition.width * 0.01 + ")";

    if (color) {
        pnIndicator.style.backgroundColor = color;
    }
}


function determineOverflow(content, container) {
    var containerMetrics = container.getBoundingClientRect();
    var containerMetricsRight = Math.floor(containerMetrics.right);
    var containerMetricsLeft = Math.floor(containerMetrics.left);
    var contentMetrics = content.getBoundingClientRect();
    var contentMetricsRight = Math.floor(contentMetrics.right);
    var contentMetricsLeft = Math.floor(contentMetrics.left);
    if (containerMetricsLeft > contentMetricsLeft && containerMetricsRight < contentMetricsRight) {
        return "both";
    } else if (contentMetricsLeft < containerMetricsLeft) {
        return "left";
    } else if (contentMetricsRight > containerMetricsRight) {
        return "right";
    } else {
        return "none";
    }
}


$(".pn-ProductNav_Link").on('mouseover', function () {
    console.log(document.getElementById(this.id));
    let color = "";
    if (document.getElementById(this.id).parentNode.id === "pnProductNavContents") {
        color = "#efef2f"
    }
    //FIXME: change background-color also for manual concepts
    else if (document.getElementById(this.id).parentNode.id === "pnProductNavContents2") {
        color = "#37d99b";
    }
    document.getElementById(this.id).style.backgroundColor = color;
});

$(".pn-ProductNav_Link").on('mouseout', function () {
    document.getElementById(this.id).style.backgroundColor = "white";
});

/**
 * scripts for the context menu
 */
function makeContextMenu() {
    if (!window.x) {
        x = {};
    }

    x.Selector = {};
    x.Selector.getSelected = function() {
        var t = '';
        if (window.getSelection) {
            t = window.getSelection();
        } else if (document.getSelection) {
            t = document.getSelection();
        } else if (document.selection) {
            t = document.selection.createRange().text;
        }
        return t;
    };

    var pageX;
    var pageY;

    $(document).ready(function() {

        $(document).on('contextmenu', function(ev) {
            ev.preventDefault();
            var selectedText = x.Selector.getSelected();
            if(selectedText != ''){
                textOnFocus = selectedText.toString();
                sentOnFocus = x.Selector.getSelected().focusNode.parentNode;
                $('ul.tools').css({
                    'left': pageX,
                    'top' : pageY - 20
                }).fadeIn(200);
            } else {
                $('ul.tools').fadeOut(200);
            }
        });

        $(document).on("click", function(e){
            $('ul.tools').fadeOut(200);
        });

        $(document).on("mousedown", function(e){
            pageX = e.pageX;
            pageX = e.pageX;
            pageY = e.pageY;
        });

    });

}

/** Script for retrieving the ID of sentence when clicked on a concept
 *
 * @param node
 * @param tagname
 * @returns {*}
 */
function getParentByTagName(node, tagname) {
    var parent;
    if (node === null || tagname === '') return;
    parent  = node.parentNode;
    tagname = tagname.toUpperCase();

    while (parent.tagName !== "HTML") {
        if (parent.tagName === tagname) {
            return parent;
        }
        parent = parent.parentNode;
    }

    return parent;
}


/**
 * Script for make each word selectable and move the word in the input box
 * */
var activeText = '';
function gText(e) {
    if (document.all) {
        activeText = document.selection.createRange().text;
    }
    else {
        activeText = document.getSelection();
    }

    document.getElementById('active_concept').value = activeText;//.toUpperCase().trim();

    //retrieve IDs of sentence and tokens (needed to access the lemma)
    sentOnFocus = $(activeText.anchorNode.parentNode).attr("partof_sent");
    let firstTok = Math.min($(activeText.anchorNode.parentNode).attr("tok_id"), $(activeText.focusNode.parentNode).attr("tok_id"));
    let lastTok = Math.max($(activeText.anchorNode.parentNode).attr("tok_id"), $(activeText.focusNode.parentNode).attr("tok_id"));
    //console.log(firstTok);
    //console.log(lastTok);
    tokensOnFocus = [];
    for (let i = firstTok; i<= lastTok; i++) {
        tokensOnFocus.push(i);
    }
    textOnFocus = document.getElementById('active_concept').value;
    document.getElementById('active_concept').value = "";

    $("#active_concept").focus(function(){
        $("#modalAddTerm").modal("show");
    });
}
document.onmouseup = gText;
if (!document.all) document.captureEvents(Event.MOUSEUP);


/**
 * Download JSON
 *
 */
 
 
function downloadJSON(el) {
    
    let currentdate = new Date();
    var data1 = {}
    data1['savedInsertedRelations'] = insertedRelations;
    data1['savedManualConceptsFirstToks'] = manualConceptsFirstToks;
    
    var entry = {
        data : JSON.stringify(data1),
        datetime :  "y" + currentdate.getFullYear() + "-"
        + "m" + (currentdate.getMonth()+1)  + "-"
        + "d" + currentdate.getDate() + "-"
        + "h" + currentdate.getHours() + "-"
        + "m" + currentdate.getMinutes() + "-"
        + "s" + currentdate.getSeconds(),
        cap : $cap,
        bid : $bid
    };
    
    fetch('/annotation_upload', {
        method: "POST",
        credentials: "include",
        body: JSON.stringify(entry),
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    
    })
    .then(function (response) {
    
        document.body.classList.remove("loading");
        if (response.status !== 200) {
        
            document.getElementById('bootstrap-alert').style.display = 'block';
            setTimeout(function(){document.getElementById('bootstrap-alert').style.display = 'none'}, 1700);
  
            //THIS IS JS ALERT
            
                   
          }
        
        response.json().then(function(data) {
        
            document.getElementById('bootstrap-alert').style.display = 'block';
            setTimeout(function(){document.getElementById('bootstrap-alert').style.display = 'none'}, 1700);
  
            //THIS IS JS ALERT
            alert(data)
            
        })
    })
}
 /*   
    //console.log(manualConceptsFirstToks);
    //var data = "text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(insertedRelations));
    var data = "text/json;charset=utf-8," + '{\n"savedInsertedRelations": ' + encodeURIComponent(JSON.stringify(insertedRelations));
    data += ',\n"savedManualConceptsFirstToks": ' + encodeURIComponent(JSON.stringify(manualConceptsFirstToks)) + "\n}";
    //+ encodeURIComponent(JSON.stringify(manualConceptsFirstToks)
    //var data = "text/json;charset=utf-8," + "var savedInsertedRelations = " + encodeURIComponent(JSON.stringify(insertedRelations)) +";\nvar savedManualConcepts = " + encodeURIComponent(JSON.stringify(manualConcepts)) + ";";
    //FIXME what to return in order to show download window?
    let currentdate = new Date();
    let datetime =  "y" + currentdate.getFullYear() + "-"
        + "m" + (currentdate.getMonth()+1)  + "-"
        + "d" + currentdate.getDate() + "-"
        + "h" + currentdate.getHours() + "-"
        + "m" + currentdate.getMinutes() + "-"
        + "s" + currentdate.getSeconds();
    
     fetch('/json_upload', {
        method: "POST",
        credentials: "include",
        body: JSON.stringify(data),
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    })
}
    
    fetch('/json_upload', {
        method: "POST",
        credentials: "include",
        body: JSON.stringify(data),
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    })
    	

*/
/**
 * Upload JSON
 */


function uploadJSON(result){
    
        //console.log(e);
        //var result = JSON.parse(e.target.result);
        //console.log(result);
        //var formatted = JSON.stringify(result, null, 2);
        // modify the text and the list of manualconcepts if the json contains new concepts

        /* TODO: restore if the new version doesn't work
        for (let rel in result) {
            insertedRelations[rel] = result[rel];
            if (!$autoConcepts.includes(result[rel]["advanced"]) && !manualConcepts.includes(result[rel]["advanced"])) {
                //
                //document.getElementById("newConcept").value = result[rel]["advanced"].toLowerCase();
                //addTerm();
                manualConcepts.push(result[rel]["advanced"]);

            }
            if (!$autoConcepts.includes(result[rel]["prerequisite"]) && !manualConcepts.includes(result[rel]["prerequisite"])) {
                //document.getElementById("newConcept").value = result[rel]["prerequisite"].toLowerCase();
                //addTerm();
                manualConcepts.push(result[rel]["prerequisite"]);
            }


            // populate the horizontal scroll bar with added manualConcepts
            var tempScroll2 = document.getElementById("pnProductNavContents2");
            for (let c=0; c<manualConcepts.length; c++) {
                tempScroll2.innerHTML += '<a href="#" class="pn-ProductNav_Link" ' + 'id="scroll2_' + c +'"' + ' aria-selected="true" data-toggle="modal" data-target="#conceptSummary" data-to-pass="my_value" onclick="setCentralConcept(this.text);">'+manualConcepts[c]+'</a>';
            }
            tempScroll2.innerHTML += '<span id="pnIndicator2" class="pn-ProductNav_Indicator"></span>';

        }
        */

        insertedRelations = result["savedInsertedRelations"];
        //console.log(result["savedManualConceptsFirstToks"]);

        // populate the horizontal scroll bar with added manualConcepts
        var tempScroll2 = document.getElementById("pnProductNavContents2");
        manualConceptsFirstToks = result["savedManualConceptsFirstToks"];
        for (let conceptToAdd in result["savedManualConceptsFirstToks"]) {
            manualConcepts.push(conceptToAdd);
            //console.log(conceptToAdd);
            let toksIndexes = result["savedManualConceptsFirstToks"][conceptToAdd];
            tempScroll2.innerHTML += '<a href="#" class="pn-ProductNav_Link" ' + 'id="scroll2_' + manualConcepts.indexOf(conceptToAdd) +'"' + ' aria-selected="true" data-toggle="modal" data-target="#conceptSummary" data-to-pass="my_value" onclick="setCentralConcept(this.text);">'+conceptToAdd+'</a>';
            for (let t of toksIndexes) {
                updateText(parseInt(t), conceptToAdd.split(" ").length, manualConcepts.indexOf(conceptToAdd));
            }
        }
        tempScroll2.innerHTML += '<span id="pnIndicator2" class="pn-ProductNav_Indicator"></span>';
        highlightText();
        //populate the full table of relations
        renderHTML();

        //show icon on every target concept in the right sentence of the text
        for (let rel of insertedRelations) {
            var icona = document.createElement("img");
            icona.src = '../static/images/transfer.svg';

            $('sent[sent_id='+rel["sent"]+']').find('concept[concept_id=' + rel["advanced_id"] + ']').each(function (){
                if($(this).find("img").length == 0)
                    this.appendChild(icona)
            });
        }
    };

function submit(){

    var data1 = {}
    data1['savedInsertedRelations'] = insertedRelations;
    data1['savedManualConceptsFirstToks'] = manualConceptsFirstToks;
    
    var entry = {
        data : JSON.stringify(data1),
        cap : $cap,
        bid : $bid
    };
    
    fetch('/final_annotation_upload', {
        method: "POST",
        credentials: "include",
        body: JSON.stringify(entry),
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    
    })
    .then(function (response) {
    
        document.body.classList.remove("loading");
        if (response.status !== 200) {
        
            document.getElementById('bootstrap-alert').style.display = 'block';
            setTimeout(function(){document.getElementById('bootstrap-alert').style.display = 'none'}, 1700);
  
            //THIS IS JS ALERT
            
                   
          }
        
        response.json().then(function(data) {
        
            document.getElementById('bootstrap-alert').style.display = 'block';
            setTimeout(function(){document.getElementById('bootstrap-alert').style.display = 'none'}, 1700);
  
            //THIS IS JS ALERT
            alert(data)
            
        })
    })
}


/** Initialization
 *
 */
/*initiate the autocomplete function on the "concept" element, and pass along the autoConcepts array as possible autocomplete values:*/
/*FIXME: delete (old)
autocomplete(document.getElementById("advanced1"), $autoConcepts);
autocomplete(document.getElementById("prerequisite1"), $autoConcepts);
*/
makeContextMenu();

/*
document.addEventListener("keydown", function(e) {
    if ($('.modal').hasClass('in') && e.keyCode === 27) {
        console.log("keypress");
        $(".modal").modal("hide");
        //$(".modal").modal("toggle");
        //$(".modal").fadeOut(500);
    }
});
*/

/** Helper function for creating ranges (javascript has not native function for that)
 *
 * @param start
 * @param end
 * @returns {any[]}
 */
function range (start, end) {
    return new Array(end - start).fill().map((d, i) => i + start);
}