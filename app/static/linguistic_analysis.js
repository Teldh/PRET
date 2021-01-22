var concepts = [];
var insertedRelations = [];
var weights = [];
var sent_ids = [];
var clickedResult = {};




    var result = JSON.parse($json);

    insertedRelations = result["savedInsertedRelations"];

    if(insertedRelations) {
        for (let rel of insertedRelations) {
            if (!concepts.includes(rel["prerequisite"])) {
                concepts.push(rel["prerequisite"]);
            }
            if (!concepts.includes(rel["advanced"])) {
                concepts.push(rel["advanced"]);
            }
            //let currSent = $sentList[rel["sent"]-1]["text"];
        }
    }

    var metodo2= false;

    if(insertedRelations) {
        weights = Array.from(new Set(insertedRelations.map(x => x["weight"])));

        if(weights.length == 1 && weights[0] == undefined){

            $("#edge_weight").hide();
            $("#edge_weight_label").hide();
            metodo2=true;
        }
    
    }
    
    sent_ids = $sentList.map(x => x.sent_id);

        //populate the select inputs with options

    var options = "<option value='ANY CONCEPT'>ANY CONCEPT</option>";
    for(let i = 0; i < concepts.length; i++) {
        options += "<option value='" + concepts[i] + "'>" + concepts[i] + "</option>";
    }
    $('select[name="prerequisite_name"]').append(options);

    options = "<option value='ANY CONCEPT'>ANY CONCEPT</option>";
    for(let i = 0; i < concepts.length; i++) {
        options += "<option value='" + concepts[i] + "'>" + concepts[i] + "</option>";
    }
    $('select[name="advanced_name"]').append(options);

    options = "<option value='ANY WEIGHT'>ANY WEIGHT</option>";
    for(let i = 0; i < weights.length; i++) {
        options += "<option value='" + weights[i] + "'>" + weights[i] + "</option>";
    }
    $('select[name="edge_weight"]').append(options);

    options = "<option value='ANY SENTENCE'>ANY SENTENCE</option>";
    for(let i = 0; i < sent_ids.length; i++) {
        options += "<option value='" + sent_ids[i] + "'>" + sent_ids[i] + "</option>";
    }
    $('select[name="sent_id"]').append(options);


        function color_word_in_sentence(word,sent,color){
            var sentence = sent.toLowerCase();
            word = word.toLowerCase();
            var bigger_concepts = {}; // array con id dei concetti in una frase che includono la parola, ad esempio phone network include network
            // devo dividere la frase in: primo pezzo + parola + ultimo pezzo
            //in modo da evidenziare il concetto giusto ( se la parola è "network" e la frase è "phone network is a network" devo evidenziare il secondo network!)

            //rimpiazzo ogni concetto più grosso con "xxx"
            for(c in concepts){
                if(concepts[c].includes(word) && concepts[c] != word)
                    if(sent.includes(concepts[c])){
                        var re = new RegExp(concepts[c],"g");
                        sentence = sentence.replace(re, "xxx"+c);
                        bigger_concepts["xxx"+c] = concepts[c];
                    }
            }

            //splitto sul prerequisito
            if(sentence.includes(word)) { // il prerequisito potrebbe non essere nella frase
                sentence = sentence.split(word);
                //coloro prerequisito, se il prerequisito è presente più volte coloro solo la prima occorrenza

                var temp = sentence[0] + '<span style="background-color:'+color+'">' + word + '</span>';

                //se la frase non è finita
                if (sentence[1] != undefined) {
                    temp += sentence[1];
                    for (i = 2; i < sentence.length; i++)
                        temp += word + sentence[i];
                }
                sentence = temp;
            }


            //rimetto i concetti più grossi
            for(b in bigger_concepts){
                var re = new RegExp(b,"g");
                sentence = sentence.replace(re, bigger_concepts[b]);
            }


            return sentence.charAt(0).toUpperCase() + sentence.slice(1);
    }


$("#find").click(function () {
    //erase the paper from previous results and re-populate it
    //$('#paper').html("");
    $('#paper').empty();

    let selectedSentence = $('#sent_id').val();
    let selectedPrereq = $('#prerequisite_name').val();
    let selectedAdvanced = $('#advanced_name').val();
    let selectedWeight = $('#edge_weight').val();

    let no_relations_matched = true;

    for (let rel of insertedRelations) {
        if ((selectedPrereq === "ANY CONCEPT" || rel['prerequisite'] === selectedPrereq) &&
            (selectedAdvanced === "ANY CONCEPT" || rel['advanced'] === selectedAdvanced) &&
            ( metodo2 || (selectedWeight === "ANY WEIGHT" || rel['weight'] === selectedWeight) ) &&
            (selectedSentence === "ANY SENTENCE" || rel['sent'].toString() === selectedSentence)) {

            if(no_relations_matched)
                no_relations_matched = false;
            //append a text area for each relation
            let currSent = $sentList[rel["sent"]-1]["text"];

            // coloro prerequisito in giallo e target in verde
            var sentence = color_word_in_sentence(rel['prerequisite'], currSent, "#ff6666");
            sentence = color_word_in_sentence(rel['advanced'], sentence, "lightblue");





            $("#paper").append('' +
                '<div> ' +
                '     <span style="font-weight: bold;">Sentence:</span> ' + (rel['sent']) +
                '   <table class="table table-bordered">'+
                '       <tr><td>' + sentence +
                //'           ' + sentence[0] +'<span>'+ rel['prerequisite'] +'</span>'+ sentence[1] +'</td>' +
                '       </td></tr>'+
                '   </table>' +
                '   <div  style="float:right; margin-top: -15px;">' +
                '       <button type="button" class="btn btn-primary btn-sm result_text"' +
                ' data-rel_id="' + insertedRelations.indexOf(rel) + '"' +
                ' data-sent_id="' + rel['sent'] + '"' +
                ' data-prereq="' + rel['prerequisite'] + '"' +
                ' data-advanced="' + rel['advanced'] + '"' +
                ' data-weight="' + rel['weight'] + '"' +
                '">Show context</button>'+
                '   </div>' +
                '</div><br><br>');

        }
    }

    if(no_relations_matched)
        $("#paper").append('<div><span style="font-weight: bold;">No relations matched your critera</span></div> ');


    $('.result_text').click(function (e) {

        clickedResult = {
            rel_id: $(this).data( "rel_id" ),
            sent_id: $(this).data( "sent_id" ),
            prereq: $(this).data( "prereq" ),
            advanced: $(this).data( "advanced" ),
            weight: $(this).data( "weight" )
        };

        $('#modalAnalysis').modal('show');
    });
});

/* Show Context modal*/

var frase_mostrata;

$('#modalAnalysis').on('show.bs.modal', function(e) {


    let centralSent = $sentList[clickedResult.sent_id-1]["text"];
    frase_mostrata = clickedResult.sent_id-1;

    $('#next_button').css("display","block");
    $('#prev_button').css("display","block");

    //erase the paper from previous results and re-populate it
    $('#paper_modal').empty();
    $("#relation").empty();

    centralSent = color_word_in_sentence(clickedResult.prereq,centralSent,"#ff6666");
    centralSent = color_word_in_sentence(clickedResult.advanced,centralSent,"lightblue");
    $("#relation").append('<span style="font-weight: bold;">Prerequisite:  </span>'+ clickedResult.prereq + '<br><span style="font-weight: bold;">Target: </span> ' + clickedResult.advanced+'<br><br>');
    $("#paper_modal").append('<table class="table table-bordered result_text_modal" >'+ '<tr><td>'+centralSent + '</td></tr></table>');

    // populate the table in POS tab
    $("#table_pos").find("tr:not(:first)").remove();
    let tokens = $conll.filter(x => x.sent_id === clickedResult.sent_id);
    for (let tok of tokens) {
        //FIXME: highlighted_text += tok["forma"] + " ";
        let table = document.getElementById("table_pos");
        let row = table.insertRow(table.rows.length);
        let cell0 = row.insertCell(0);
        let cell1 = row.insertCell(1);
        let cell2 = row.insertCell(2);
        let cell3 = row.insertCell(3);
        let cell4 = row.insertCell(4);
        let cell5 = row.insertCell(5);
        cell0.innerHTML = tok["sent_id"];
        cell1.innerHTML = tok["tok_id"];
        cell2.innerHTML = tok["forma"];
        cell3.innerHTML = tok["lemma"];
        cell4.innerHTML = tok["pos_coarse"];
        cell5.innerHTML = tok["pos_fine"];
    }

    /*grafo: deve comprendere un livello prima e un livello dopo del target*/
    var target = clickedResult.advanced;
    var nodi_prima = [];
    var nodi_dopo = [];

    for (let rel of insertedRelations){
        if ( rel.advanced == target)
            nodi_prima.push(rel.prerequisite);
        else if(rel.prerequisite == target)
            nodi_dopo.push(rel.advanced)
    }

    var G = new jsnx.DiGraph();
    G.addNode(target,{color: 'lightblue'});
    G.addNodesFrom(nodi_prima, {color: '#ff6666'});
    G.addNodesFrom(nodi_dopo, {color: 'lightgreen'});

    for(var n in nodi_prima)
        G.addEdge(nodi_prima[n],target);
    for(var n in nodi_dopo)
        G.addEdge(target,nodi_dopo[n]);

    jsnx.draw(G, {
             element: '#canvas',
             withLabels: true,
             nodeStyle: {
                 fill: function (d) {
                     return d.data.color || '#AAA'; // any node without color is gray
                 },
                 stroke: 'none'
             },
             edgeStyle: {
                'stroke-width': 4,
                 fill: '#999'
             },
            labelStyle: {
                "font-size": '12px',
                'font-weight': 'bold',
                "font-family": "sans-serif",
                'text-anchor': 'middle',
                'dominant-baseline': 'text-after-edge',

                fill: 'black'
            },
            layoutAttr: {
                charge:function (d) {
                    if (d.data.color == "lightblue")
                        return 120;
                    else
                        return -300;
                 },
                linkDistance: 160
            },
            stickyDrag: true
    },false);
});





    $('#prev_button').click(function () {

        let prevSent = $sentList[frase_mostrata-1]["text"];
        frase_mostrata--;

        $('#paper_modal').empty();

        prevSent = color_word_in_sentence(clickedResult.prereq,prevSent,"#ff6666");
        prevSent = color_word_in_sentence(clickedResult.advanced,prevSent,"lightblue");

        $("#paper_modal").append('<table class="table table-bordered result_text_modal" >'+
                '                   <tr><td>'+ prevSent + '</td></tr></table>');

        if(frase_mostrata == clickedResult.sent_id-2)
            $('#prev_button').css("display","none");

        $('#next_button').css("display","block");
    });


    $('#next_button').click(function () {

        let nextSent = $sentList[frase_mostrata+1]["text"];
        frase_mostrata++;

        nextSent = color_word_in_sentence(clickedResult.prereq,nextSent,"#ff6666");
        nextSent = color_word_in_sentence(clickedResult.advanced,nextSent,"lightblue");

        $('#paper_modal').empty();
        $("#paper_modal").append('<table class="table table-bordered result_text_modal" >'+
                '                   <tr><td>'+ nextSent + '</td></tr></table>');

        if(frase_mostrata == clickedResult.sent_id)
            $('#next_button').css("display","none");
        $('#prev_button').css("display","block");
    });