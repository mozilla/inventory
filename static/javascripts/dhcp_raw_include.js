function hide_text_area(id){
    text_area = document.getElementById(id);
    if (text_area.style.display != 'none') {
        text_area.style.display = 'none';
    } else {
        text_area.style.display = 'inline';
    }

}
