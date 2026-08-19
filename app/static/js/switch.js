document.addEventListener("DOMContentLoaded", () => {
    const posts = document.getElementById("posts");
    const games = document.getElementById("games");
    const text = document.getElementById("switchText");
    const element = document.getElementById("toggle")
    
    if (element.checked){
        games.style.display = "table-row";
        posts.style.display = "none";
        text.textContent = "Games";
    } else{
        games.style.display = "none";
        posts.style.display = "table-row";
        text.textContent = "Posts";
    }
});

function toggleSwitch(element) {
    const posts = document.getElementById("posts");
    const games = document.getElementById("games");
    const text = document.getElementById("switchText");
    
    if (element.checked){
        games.style.display = "table-row";
        posts.style.display = "none";
        text.textContent = "Games";
    } else{
        games.style.display = "none";
        posts.style.display = "table-row";
        text.textContent = "Posts";
    }
}

