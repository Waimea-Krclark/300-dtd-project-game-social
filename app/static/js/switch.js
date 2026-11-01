document.addEventListener("DOMContentLoaded", () => {
    const posts = document.getElementById("posts");
    const games = document.getElementById("games");
    const element = document.getElementById("toggle")
    if(element){
        if (element.checked){
            games.style.display = "block";
            posts.style.display = "none";
        } else{
            games.style.display = "none";
            posts.style.display = "block";
        }
    }

});

function toggleSwitch(element) {
    const posts = document.getElementById("posts");
    const games = document.getElementById("games");

    fetch('/save-checkbox', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ checked: element.checked })
    })
    .then(response => response.json())
    if (element.checked){
        games.style.display = "block";
        posts.style.display = "none";
    } else{
        games.style.display = "none";
        posts.style.display = "block";
    }
    
};

function toggleReplies(element){
    const parent = element.parentElement;
    const reply = parent.querySelector(".replies");

    if (reply.style.display == "block"){
        reply.style.display = "none";
    } else {
        reply.style.display = "block";
    };

};
