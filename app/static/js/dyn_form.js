var counter = 1
function new_link(){
    if (counter < 6) {
        const parent_label = document.getElementById('store_links');
        const new_link = document.createElement('input');
        new_link.name = 'link'
        new_link.type = 'text'
        new_link.required = true;
        const link_remove = document.createElement('button');
        link_remove.textContent='X';
        link_remove.id = 'link_remove';
        link_remove.type = 'button';
        link_remove.addEventListener('click', () => remove_link(link_remove, new_link));


        parent_label.insertBefore(new_link, parent_label.lastElementChild);
        parent_label.insertBefore(link_remove, parent_label.lastElementChild);
        counter++;
    };
};

function remove_link(button, input){
    const parent_label = document.getElementById('store_links');
    if (counter > 1) {
        parent_label.removeChild(button)
        parent_label.removeChild(input)
        button.remove()
        input.remove()
        counter--;
    };
};

function remove_screenshot(btn){
    btn.closest('.screenshot_row').remove();
};

function remove_edit_link(btn){
    btn.closest('.link_row').remove();
};