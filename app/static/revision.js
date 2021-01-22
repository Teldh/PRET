// Stampo il testo
var textBox = document.getElementById("testo");
textBox.innerHTML = $tagged;

// Metto in grassetto i titoli
var chapterTitle = document.getElementsByTagName("chaptertitle");

for (i = 0; i < chapterTitle.length; i++) {
  chapterTitle[i].style.fontWeight = 'bold';
}

// In base al tipo di revisione cambia colore della riga e opzioni dei tag
function changeOptions(elem) {
  let rev_id = $(elem).attr('id');

  let tag_id = "#tag_" + rev_id.split("_")[1];

  let new_options = [];

  let selectedValue = document.getElementById(rev_id).value;

  if(selectedValue == 'Delete'){
      new_options = ['None',"Background knowledge", "Too far", "Annotation error", "Co-requisites", "Wrong direction"];
      elem.parentNode.parentNode.style.backgroundColor = "#FF5733";
  }
  else if(selectedValue == 'Confirm') {
      new_options = ['None','Lexical relation', 'Functional Relation', 'Definition', 'Example', 'In depth','Causal Relation']
      elem.parentNode.parentNode.style.backgroundColor = "lightgreen";
  }
  else if (selectedValue == 'None'){
      new_options = ['None'];
      elem.parentNode.parentNode.style.backgroundColor = "";
  }
  else{
      if(document.getElementById("weight_"+rev_id.split("_")[1]).textContent == "strong")
            new_options = ['Weak'];
      else
            new_options = ['Strong'];

      elem.parentNode.parentNode.style.backgroundColor = "#FAFF5A";
  }
  $(tag_id).empty();

  $.each(new_options, function(key,value) {
      $(tag_id).append($("<option></option>")
        .attr("value", value).text(value));
  });
}


//submit revision
function submitRevision(){

    var dataRevisioni = [];
    var revisions = document.getElementsByClassName("revision_values");

    var tags = document.getElementsByClassName("tag_values");

    //prendo tutte le revisioni fatte e i relativi tag
    for (i=0; i< revisions.length;i++){
      var ann_user_id = revisions[i].id.split("_")[1];
      var rev = revisions[i].value;
      var tag = tags[i].value;
      dataRevisioni.push({ann_user_id:ann_user_id, rev:rev, tag:tag});
    }

    console.log(dataRevisioni);
    console.log(typeof(dataRevisioni));

    //creo json da mandare a routes.py
    var entry = {
        data : JSON.stringify(dataRevisioni),
        cap : $cap,
        bid : $bid
    };

    fetch('/revision_upload', {
        method: "POST",
        credentials: "include",
        body: JSON.stringify(entry),
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })

    })
    .then(function (response) {

        //risposta da /revision_upload
        response.json().then(function(data) {
            console.log(data)
            if(data == "succeeded"){
                document.getElementById("alert_success").style.display = "block";
                document.getElementById("alert_warning").style.display = "none";
                document.getElementById("alert_fail").style.display = "none";
            }
            else if(data =="not finished"){
                 document.getElementById("alert_success").style.display = "none";
                 document.getElementById("alert_warning").style.display = "block";
                 document.getElementById("alert_fail").style.display = "none";

            }
            else{
                document.getElementById("alert_success").style.display = "none";
                 document.getElementById("alert_warning").style.display = "one";
                document.getElementById("alert_fail").style.display = "block";
            }

            $(function() {
               $('body').scrollTop(0);
            });

        })
    })
}
