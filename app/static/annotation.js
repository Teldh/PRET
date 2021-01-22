/*$('#content-target').mouseup(function(){

    if (window.getSelection().toString()) {
        var span = document.createElement("span");
        var sel = window.getSelection();

        console.log(sel.rangeCount);
        
        /*if (sel.rangeCount) {
            console.log("node");
            var range = sel.getRangeAt(0).cloneRange();
            var node = $(range.commonAncestorContainer);
            console.log(node);
            if(node.parent().is("span")) {
                node.unwrap();
        }
        else*/
       /* if (hasNumber(sel.toString())) {
            var range = sel.getRangeAt(0).cloneRange();

            var node = $(range.commonAncestorContainer);;

            if(node.parent()[0].id == "content-target"){
                range.surroundContents(span);
                 sel.removeAllRanges();
                 sel.addRange(range);
            }
            else if(node.parent().is('span')){
                node.unwrap();
            }

        }
    }
});*/

function hasNumber(myString) {
  return /\d/.test(myString);
}

function isSection(id) {

    if($('#' + id).is(":checked")) {
        var label = $('label[for="' + id + '"]').text();
        $('label[for="' + id + '"]').html('<span>' + label + '</span>');
    }
    else{
        var text = $('label[for="' + id + '"]').text();//get span content
        $('label[for="' + id + '"]').html(text);
    }
}

window.onload = function() {
    var fileInput = document.getElementById('customFile');
    var div_testo = document.getElementById('testo');
    var fileDisplayArea = document.getElementById('content-target');

    fileInput.addEventListener('change', function(e) {
    var file = fileInput.files[0];
    var textType = /text.*/;

    if (file.type.match(textType)) {
        var reader = new FileReader();

        document.getElementById("instructions").style.display = "";
        reader.onload = function(e) {
        //fileDisplayArea.innerText = reader.result;

        var text = reader.result;
        //var lines = text.split(/[\r\n]+/g);
        var lines = text.match(/[^\n]+(?:\r?\n|$)/g);

        fileDisplayArea.innerHTML = "";

        for(var i = 0; i < lines.length; i++){

            if (hasNumber(lines[i]) && lines[i].length < 200)
                fileDisplayArea.innerHTML += '<div class="class="float-left">' +
                    '<input type="checkbox" id="'+i+'" onclick="isSection(this.id);"></div><div class="class="float-right">'+
                        '<label for="'+i+'">'+ lines[i].replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')+'</label></div>'
            else
                fileDisplayArea.innerHTML += lines[i].replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        }

        };

        reader.readAsText(file);
    } else {
        //fileDisplayArea.innerText = "File not supported!"
        alert("File not supported");
      }
    });



}


//code to make the name of the file appear on select
$(".custom-file-input").on("change", function() {
    var fileName = $(this).val().split("\\").pop();
    $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
});



function getValue() {
$(function() {
    result = Array.prototype.filter.call(document.getElementsByTagName("span"),
                 function (elm) { return /\d/.test(elm.innerHTML) }
             ); 
    return result;
});
}


function submit_entry() {
    
    var book = document.getElementById("book");
    var author = document.getElementById("author");
    var year = document.getElementById("year");
    var cap = document.getElementById("cap");
    var category = document.getElementById("category");
    let language = document.getElementById("language");
    var text = document.getElementById("content-target");
    //var text = document.getElementById("testo");
    /*console.log(text2.outerText);
    var result = Array.prototype.filter.call(
             $("span"),
                 function (elm) { return /\d/.test(elm.innerHTML) }
             );

    result.forEach(function(part, index) {

      this[index] = this[index].innerHTML;
    }, result);
    console.log(result);*/

    var result2 = [];

    $('input:checked').filter(function() {
        console.log(this.id);
        result2.push($('label[for="'+this.id+'"]').text());
    });
    console.log(result2);

    var entry = {
        book: book.value,
        author: author.value,
        year: year.value,
        cap: cap.value,
        category: category.value,
        language: language.value,
        text: text.outerText,
        result: result2
    };
    document.body.classList.add("loading");
    
    fetch('/text_upload', {
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
            alert(data);
                   
          }
        
        response.json().then(function(data) {
        
            document.getElementById('bootstrap-alert').style.display = 'block';
            setTimeout(function(){document.getElementById('bootstrap-alert').style.display = 'none'}, 1700);
  
            //THIS IS JS ALERT
            alert(data);
            
        })
    })

}


 



