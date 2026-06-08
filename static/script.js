function sendQuestion() {

let question =
document.getElementById("question").value;

fetch("/ask", {

method: "POST",

headers: {
"Content-Type":
"application/x-www-form-urlencoded"
},

body:
"question=" +
encodeURIComponent(question)

})

.then(response => response.json())

.then(data => {

document.getElementById(
"response"
).innerHTML = data.answer;

});

}