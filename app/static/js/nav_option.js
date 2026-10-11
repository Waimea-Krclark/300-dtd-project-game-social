function toggleOptionMenu(){
    const element = document.getElementById("menuDrop");
    console.log(element.style.display)
    if (element.style.display=="flex"){
        element.style.display = "none";
    } else{
        element.style.display = "flex";
    }
}
