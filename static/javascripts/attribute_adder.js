// This code is from here: http://www.openjs.com/scripts/examples/addfield.php
// 
/*
function addField(area, field, limit) {
    if(!document.getElementById) return; //Prevent older browsers from getting any further.
    var field_area = document.getElementById(area);
    var all_inputs = field_area.getElementsByTagName("input"); //Get all the input fields in the given area.
    //Find the count of the last element of the list. It will be in the format '<field><number>'. If the 
    //      field given in the argument is 'friend_' the last id will be 'friend_4'.
    if(all_inputs.length > 0){
        var last_item = all_inputs.length - 1;
        var last = all_inputs[last_item].id;
        var count = Number(last.split("_")[1]) + 1;
        if(count > limit && limit > 0) return;
    } else {
        var last_item = 0;
        var count = 0;
    }


    //If the maximum number of elements have been reached, exit the function.
    //      If the given limit is lower than 0, infinite number of fields can be created.

    //field_area.innerHTML += " <li>Attribute: <input name='"+(field+count)+"' id='"+(field+count)+"' type='text' /> Value: <input name='"+(field+count)+"_value' id='"+(field+count)+"_value' type='text' /> <a style='cursor:pointer;color:blue;' onclick='remove(this)';>Remove</a> </li>";
    var li = document.createElement('li');

    var label1 = document.createElement('label');
    var input1 = document.createElement('input');
    label1.for = field+count;
    label1.innerHTML = "Attribute: ";
    label1.style.display = "inline";
    input1.id = field+count;
    input1.type = "text";
    input1.name = field+count;


    var label2 = document.createElement('label');
    var input2 = document.createElement('input');

    label2.for = field+count;
    label2.innerHTML = "Value: ";
    label2.style.display = "inline";
    input2.id = field+count;
    input2.type = "text";
    input2.name = field+count+"_value";

    var a = document.createElement('a');
    a.innerHTML = "Remove";
    a.style.cursor = "pointer";
    a.addEventListener('click',function (e) {
            e.target.parentNode.parentNode.removeChild(e.target.parentNode)
    });

    li.appendChild(label1);
    li.appendChild(input1);

    li.appendChild(label2);
    li.appendChild(input2);
    li.appendChild(a);
    field_area.appendChild(li);


}
function remove(link) {
        link.parentNode.parentNode.removeChild(link.parentNode);
}
*/
function addAttr(area, field, limit, aa) {
    var field_area = document.getElementById(area);
    var all_inputs = field_area.getElementsByTagName("input");

    if (all_inputs.length > 0) {
        var last_item = all_inputs.length - 1;
        var last = all_inputs[last_item].id;
        var count = Number(last.split("_")[1]) + 400;
        if (count > limit && limit > 0) return;
    } else {
        var last_item = 400;
        var count = 400;
    }


    var li = document.createElement('li');

    var select = document.createElement('select');
    var label1 = document.createElement('label');
    label1.innerHTML = "Attribute: ";
    label1.style.display = "inline";
    label1.for = field + count;
    label1.innerHTML = "Attribute: ";
    label1.style.display = "inline";
    select.id = field + count;
    select.name = field + count;
    for (i = 0; i < aa.length; i++) {
            select.options[select.options.length] = new Option(aa[i], aa[i]);
    }



    var label2 = document.createElement('label');
    label2.innerHTML = " Value: ";
    var input2 = document.createElement('input');
    label2.for = field+count;
    label2.innerHTML = " Value: ";
    label2.style.display = "inline";
    input2.id = field+count+"_value";
    input2.name = field+count+"_value";
    input2.type = "text";

    var a = document.createElement('a');
    a.innerHTML = "Remove";
    a.style.cursor = "pointer";
    a.addEventListener('click', function(e) {
                e.target.parentNode.parentNode.removeChild(e.target.parentNode)
                });

    li.appendChild(label1);
    li.appendChild(select);

    li.appendChild(label2);
    li.appendChild(input2);
    li.appendChild(a);
    field_area.appendChild(li);
}



function addField(area, field, limit, offset) {
    if(!document.getElementById) return;
    var field_area = document.getElementById(area);
    var all_inputs = field_area.getElementsByTagName("input");
    if(all_inputs.length > 0){
        var last_item = all_inputs.length - 1;
        var last = all_inputs[last_item].id;
        var count = Number(last.split("_")[1]) + 200;
        if(count > limit && limit > 0) return;
    } else {
        var last_item = 200;
        var count = 200;
    }


    //If the maximum number of elements have been reached, exit the function.
    //      If the given limit is lower than 0, infinite number of fields can be created.

    var li = document.createElement('li');

    var label1 = document.createElement('label');
    var input1 = document.createElement('input');
    label1.for = field+count;
    label1.innerHTML = "Attribute: ";
    label1.style.display = "inline";
    input1.id = field+count;
    input1.name = field+count;
    input1.type = "text";
    input1.size = "19";


    var label2 = document.createElement('label');
    var input2 = document.createElement('input');

    label2.for = field+count;
    label2.innerHTML = " Value: ";
    label2.style.display = "inline";
    input2.id = field+count+"_value";
    input2.name = field+count+"_value";
    input2.type = "text";

    var a = document.createElement('a');
    a.innerHTML = "Remove";
    a.style.cursor = "pointer";
    a.addEventListener('click',function (e) {
            e.target.parentNode.parentNode.removeChild(e.target.parentNode)
    });

    li.appendChild(label1);
    li.appendChild(input1);

    li.appendChild(label2);
    li.appendChild(input2);
    li.appendChild(a);
    field_area.appendChild(li);


}
function remove(link) {
        link.parentNode.parentNode.removeChild(link.parentNode);
}
function remove_attr(attr_id, post_url) {
    $.post(post_url)
    remove(document.getElementById(attr_id));

}
