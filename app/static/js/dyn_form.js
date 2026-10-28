var counter = 1
function new_link(){
    if (counter < 6) {
        const parent_label = document.getElementById('store_links');
        const link_div = document.createElement('div');
        link_div.className = 'link_row'
        const new_link = document.createElement('input');
        new_link.name = 'link'
        new_link.type = 'text'
        new_link.placeholder = 'Enter Link'
        new_link.required = true;
        const link_remove = document.createElement('button');
        link_remove.textContent='X';
        link_remove.id = 'link_remove';
        link_remove.type = 'button';
        link_remove.addEventListener('click', () => remove_link(link_div));

        parent_label.append(link_div);
        link_div.appendChild(new_link);
        link_div.appendChild(link_remove);
        counter++;
        checkCounter();
    };
};

function remove_link(link_div){
    const parent_label = document.getElementById('store_links');
    if (counter > 1) {
        parent_label.removeChild(link_div)
        counter--;
        checkCounter();
    };
};

function remove_screenshot(btn){
    btn.closest('.screenshot_row').remove();
};

function remove_edit_link(btn){
    btn.closest('.link_row').remove();
    counter--;
    checkCounter();
};

function checkCounter(){
    const button = document.getElementById('new_link_button');
    if (counter >= 6){
        button.className = 'invisible';
    } else {
        button.className = 'visible'
    }
}