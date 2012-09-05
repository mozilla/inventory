$(function() {
    String.prototype.startsWith = function(needle)
    {
        return(this.indexOf(needle) == 0);
    };
    if(typeof(String.prototype.strip) === "undefined")
    {
        String.prototype.strip = function()
        {
            return String(this).replace(/^\s+|\s+$/g, '');
        };
    }
    $('#rec_type_select').find(":selected").click();

});
function reset_form(){
    rec_types = ['A', 'MX', 'NS', 'CNAME', 'SRV', 'TXT', 'PTR'];
    for (var i = 0; i < rec_types.length; i++){
        rec_type = rec_types[i];
        $('#' + rec_type + '_build').attr('pk', "");
        display_disable(rec_type + '_display');
    }
    // Clear any notifications
    $('#error_list').empty();
    $('#dns_success').empty();
    type_select = document.getElementById("rec_type_select");
    type_select_index = type_select.options.selectedIndex;
    document.getElementById("dns_form").reset();
    type_select.options[type_select_index].selected = true;
    var rec_type = type_select.value;
    $('#'+rec_type+'_build_name').attr('value', '');
    $('#'+rec_type+'_build_target_name').attr('value', '');
    display_enable(rec_type+"_display");
    /* Walk through and reset to default display values */
    final_display = document.getElementById(rec_type + "_final");
    arr = final_display.getElementsByClassName("inline");
    for (var i = 0; i < arr.length; i++){
        var element = $('#' + arr[i].id);
        if (element.attr('id') == rec_type + "_display_type" ) {
            // Do nothing
        } else if (element.attr('reset') == 'false') {
            element.attr('innerHTML', "<i>" + element.attr('value') + "</i>");
        } else if (element.attr('value') == "TTL"){
            // TTL is stupid
            element.attr('innerHTML', '');
        } else {
            element.attr('innerHTML', '');
        }
    }
}

function display_disable(element_id){
    var ele = document.getElementById(element_id);
    var text = document.getElementById(element_id);
    ele.style.display = "none";
}

function display_enable(element_id){
    var ele = document.getElementById(element_id);
    var text = document.getElementById(element_id);
    ele.style.display = "block";
}

function make_smart_name(rec_type, element_name, domains, append){
    element = $('#'+element_name);
    $(element).autocomplete({
        focus: function(event, ui) {
            // We saved the matching part to ui.item.value
            var name = $('#'+element_name).val(); // The name the user entered
            if(!append) {
                $('#'+element_name).attr('value', ui.item.label);
                console.log("In NS");
            } else if (ui.item.value !== ''){
                console.log("");
                var foo =  name.substring(0,name.lastIndexOf(ui.item.value));
                $('#'+element_name).attr('value', foo + ui.item.label);
            } else {
                $('#'+element_name).attr('value',  name + '.' + ui.item.label);
            }
            return false;
        },
        select: function(event, ui) {
            return false;
        },
        autoFocus: false,
        source: function (li, callback) {
            labels = li.term.split('.')

            var suggested_domains = [];
            var domain_name = '';
            var search_name = '';
            while (labels) {
                search_name = labels.join('.');
                for (var domain in domains.sort(function(a,b) {return (a.length < b.length) ? 0 : 1; })){
                    domain_name = domains[domain];
                    if (domain_name.startsWith(search_name)){
                        suggested_domains.push({label: domain_name, value: search_name});
                    }
                }
                if (suggested_domains.length === 0){
                    labels.shift();
                } else {
                    return callback(suggested_domains);
                }
            }

            return callback([]);
        }
    });

}
function do_MX(e){
    reset_form();
    display_enable('MX_display');
}
function do_NS(e){
    reset_form();
    display_enable('NS_display');
}
function do_PTR(e){
    reset_form();
    display_enable('PTR_display');
}
function do_CNAME(e){
    reset_form();
    display_enable('CNAME_display');
}
function do_SRV(e){
    reset_form();
    display_enable('SRV_display');
}
function do_TXT(e){
    reset_form();
    display_enable('TXT_display');
}
function do_A(e){
    reset_form();
    display_enable('A_display');
}
/*
   Either the Label or Domain changed.
*/
function get_fqdn(rec_type){
    if (rec_type != 'NS'){
        var fqdn = $('#' + rec_type + '_build_name').val();
    } else {
        var fqdn = $('#' + rec_type + '_build_domain').find(":selected").text();
    }
    return fqdn;
}
function update_text(rec_type){
    var text = $('#' + rec_type + '_build_text').val();
    var text_display = $('#' + rec_type + '_display_text');
    if (text == ""){
        text = "<i>" + text_display.attr('value') + "</i>";
    } else {
        text = '"' + text +'"';
    }
    document.getElementById(rec_type + '_display_text').innerHTML = text;

}
function update_view(view_name){
    // Nothing right now
    var ip = $('#' + rec_type + '_build_ip').val();
    if (ip !== undefined && ip.substring(0, "10.".length) === "10.") {
        // WTF JS? No startsWith in the string prototype?
        set_view('private', true);
        set_view('public', false);
    }
}
function set_view(rec_type, view_name, enabled){
    if(enabled === true){
        document.getElementById(rec_type + '_' + view_name + '_view').checked = true;
    } else {
        document.getElementById(rec_type + '_' + view_name + '_view').checked = false;
    }
}
function update_target_name(rec_type){
    var name = $('#' + rec_type + '_build_target_name').val();
    var target_name = $('#' + rec_type + '_display_target_name');
    if (name == ""){
        name = "<i>" + target_name.attr('value') + "</i>";
    } else {
        name = name + ".";
    }
    document.getElementById(rec_type + '_display_target_name').innerHTML = name;
}
function update_fqdn(rec_type){
    var fqdn = get_fqdn(rec_type);
    var rec_name = $('#' + rec_type + '_display_rec_name');
    rec_name.empty()
    // We put a '.' on the end to tell the user there is no ORIGIN being applied. The '.'
    // isn't actually sent during a POST
    if (fqdn == ""){
        fqdn = rec_name.attr('value');
    }
    document.getElementById(rec_type + '_display_rec_name').innerHTML = fqdn + "."
}
function update_ip(rec_type){
    var ip = $('#' + rec_type + '_build_ip').val();
    display_ip = $('#' + rec_type + '_display_ip');
    display_ip.empty();
    if (ip == "") {
        ip = "<i>IP</i>";
    } else if (ip.substring(0, "10.".length) === "10.") {
        // WTF JS? No startsWith in the string prototype?
        set_view(rec_type, 'private', true);
        set_view(rec_type, 'public', false);
    }
    document.getElementById(rec_type + '_display_ip').innerHTML = ip
}
function update_number(rec_type, number_name){
    var num = $('#' + rec_type + '_build_' + number_name).val();
    var display_num = $('#' + rec_type + '_display_' + number_name);
    //alert(rec_type + '_display_' + number_name);
    if (num == "" && display_num.attr('reset') == "true") {
        num = "<i>" + display_num.attr('value') + "</i>";
    }
    //display_num.empty();
    document.getElementById(rec_type + '_display_' + number_name).innerHTML = num
}
function update_comment(rec_type){
    var comment = $('#' + rec_type + '_build_comment').val();
    $('#' + rec_type + '_display_comment').empty();
    if (comment == "") {
        comment = "";
    } else {
        comment = "; " + comment
    }
    document.getElementById(rec_type + '_display_comment').innerHTML = comment
}
