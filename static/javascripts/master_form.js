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
    String.prototype.format = function() {
        var args = arguments;
        return this.replace(/{(\d+)}/g, function(match, number) {
            return typeof args[number] != 'undefined'
            ? args[number]
            : match
            ;
        });
    };

});
$(document).ready(function (){
    var do_selects = document.getElementsByClassName('do-select');
    console.log('Selects: ' + do_selects);
    for (var select_i in do_selects){
        var select = do_selects[select_i];
        select.onclick = do_functions['A'];
    }
    $('#foo').click(function foo(){
        //$("#full_name").setCustomValidity("The username you entered is already in use.");
        var validator = $("#dns_form").validate();
        validator.showErrors({'nights': 'Foo bar baz'});
    });

});


function reset_form(){
    rec_types = ['A', 'MX', 'NS', 'CNAME', 'SRV', 'TXT', 'PTR'];
    for (var i = 0; i < rec_types.length; i++){
        rec_type = rec_types[i];
        $('#' + rec_type + '_build').attr('resource_uri', "");
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
    var final_display = document.getElementById(rec_type + "_final");
    var arr = final_display.getElementsByClassName("inline");
    clear_errors();
    clear_notices();
    for (var i = 0; i < arr.length; i++){
        var element = $('#' + arr[i].id);
        if (element.attr('id') == rec_type + "_display_type" ) {
            // Do nothing
        } else if (element.attr('reset') == 'false') {
            element.html("<i>" + element.attr('value') + "</i>");
        } else if (element.attr('value') == "TTL"){
            // TTL is stupid
            element.html("")
        } else {
            element.html("")
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
            } else if (ui.item.value !== ''){
                var foo =  name.substring(0,name.lastIndexOf(ui.item.value));
                $('#'+element_name).attr('value', foo + ui.item.label);
            } else {
                if (name.lastIndexOf('.') == name.length - 1) {
                    $('#'+element_name).attr('value',  name + ui.item.label);
                } else {
                    $('#'+element_name).attr('value',  name + '.' + ui.item.label);
                }
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
                    return callback(suggested_domains.slice(0, 20)); // The list is too long sometimes
                }
            }
            return callback([]);
        }
    });

}
do_functions = {
    MX: function (){
            reset_form();
            display_enable('MX_display');
        },
    NS: function (){
            reset_form();
            display_enable('NS_display');
        },
    PTR: function (){
            reset_form();
            display_enable('PTR_display');
        },
    CNAME: function (){
            reset_form();
            display_enable('CNAME_display');
        },
    SRV: function (){
            reset_form();
            display_enable('SRV_display');
        },
    TXT: function (){
            reset_form();
            display_enable('TXT_display');
        },
    A: function (){
            reset_form();
            display_enable('A_display');
        }
};
/*
   Either the Label or Domain changed.
*/
function get_fqdn(rec_type){
    var fqdn = $('#' + rec_type + '_build_name').val();
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

function submit_record(){
    var type_select = document.getElementById("rec_type_select");
    var type_select_index = type_select.options.selectedIndex;
    var rec_type = type_select.value;
    var resource_uri = $('#' + rec_type + '_build').attr('resource_uri')  // If this is not '' we POST, else we PATCH
    var record_meta = get_record_meta_data(rec_type)
    var commit_data = get_post_patch_data(record_meta.fields)
    if (resource_uri === '') {
        record_meta.pre_send(commit_data)
        post(rec_type, commit_data, record_meta)
    } else {
        patch(rec_type, commit_data, record_meta, resource_uri)
    }
}

function clear_errors(){
    var errors = $('.field_errors');
    for (var i=0; i< errors.length; i ++){
        $(errors[i]).empty();
        $(errors[i]).css('display', 'none');
    }
}
function clear_notices(){
    var notices = $('.build_notice');
    for (var i=0; i< notices.length; i ++){
        $(notices[i]).empty();
        $(notices[i]).css('display', 'none');
    }
}
function handle_errors(resp, record_meta){
    var retdata = jQuery.parseJSON(resp)
    console.log(resp.responseText);
    var resp = jQuery.parseJSON(resp.responseText);
    var errors = jQuery.parseJSON(resp.error_messages);
    clear_notices();
    clear_errors();
    for (var error_type in errors) {
        console.log("Error: "+ error_type + " msg:" + errors[error_type]);
        var error_message = errors[error_type];
        if (String(error_type) == "__all__"){
            console.log("Selector is: dns_errors");
            var selector = $('#dns_form_errors'); // These are general errors
        } else {
            // Map the error_type (like 'fqdn' or 'ip_str' back to it's selector
            console.log("Selector is: " +'#' + record_meta.fields[error_type]+"_errors");
            var selector = $('#' + record_meta.fields[error_type]+"_errors"); // These are general errors
        }

        // Error Output
        selector.empty();
        selector.css("display", "inline");
        //selector.append("<div class='field_error'>"+error_message+"</div>");
        jQuery('<div/>', {
            click: function () {$(this).css('display','none');},
            text: error_message,
            alt: 'Click to hide.',
        }).appendTo(selector);
    }
};
function handle_success(resp, rec_type, http_status){
    clear_notices();
    clear_errors();
    // Set the resource_uri attribute in the <rec_type>_build div. This resource_uri will be
    // used for all PATCH methods.
    $('#'+rec_type+'_build').attr('resource_uri', resp.resource_uri);
    switch (http_status) {
        case 201:
            jQuery('<p/>', {
                click: function () {$(this).css('display','none');},
                text: 'Succusfully created. Make changes and press commit or reset the form to create a new record.',
                alt: 'Click to hide.',
            }).appendTo($('#build_status'));
            $('#build_status').css('display', 'block');
            break
        case 202: // Updated
            // Successfully updated.
            console.log(resp);
            jQuery('<p/>', {
                click: function () {$(this).css('display','none');},
                text: 'Succusfully updated. Make more changes and press commit or reset the form to create a new record.',
                alt: 'Click to hide.',
            }).appendTo($('#build_status'));
            $('#build_status').css('display', 'block');
            break
    }
};
function patch(rec_type, commit_data, record_meta, resource_uri) {
    // This is supposed to be an object that doesn't exist yet.
    console.log("Patching...");
    console.log(record_meta.resource_uri);
    console.log(JSON.stringify(commit_data));
    $.ajax({
        url:resource_uri, // Use the resource_uri passed to us that points to an object.
        type:"PATCH",
        data:JSON.stringify(commit_data),
        contentType:"application/json; charset=utf-8",
        dataType:"json",
        statusCode: {
            404:function() { alert("This page is misconfigured. Please tell sommeone. Error: 404"); },
            200:function(resp) { handle_success(resp, rec_type, 200); },
            201:function(resp) { handle_success(resp, rec_type, 201); },
            202:function(resp) { handle_success(resp, rec_type, 202); },
            500:function(resp) { handle_errors(resp, record_meta); },
            400:function(resp) { handle_errors(resp, record_meta); },
        },
    });
}

function post(rec_type, commit_data, record_meta) {
    // This is supposed to be an object that doesn't exist yet.
    console.log("Posting...");
    console.log(record_meta.resource_uri);
    console.log(JSON.stringify(commit_data));
    $.ajax({
        url:record_meta.resource_uri,
        type:"POST",
        data:JSON.stringify(commit_data),
        contentType:"application/json; charset=utf-8",
        dataType:"json",

        statusCode: {
            404:function() { alert("This page is misconfigured. Please tell sommeone. Error: 404"); },
            200:function(resp) { handle_success(resp, rec_type, 200); },
            201:function(resp) { handle_success(resp, rec_type, 201); },
            202:function(resp) { handle_success(resp, rec_type, 202); },
            500:function(resp) { handle_errors(resp, record_meta); },
            400:function(resp) { handle_errors(resp, record_meta); },
        },
    });
}

/*

    //commit_data = jQuery.extend(commit_data, get_views(rec_type));
    console.log(commit_data);
    $.post('/mozdns/commit_record/', JSON.stringify(commit_data), function(data) {
        var data = jQuery.parseJSON(data)
        $('#error_list').empty();
        $('#dns_success').empty();
        if (data.errors){
            for(var attr in data.errors) {
                if(data.errors.hasOwnProperty(attr))
                    console.log(attr + ":" + data.errors[attr]);
                    // If you want to override the name of an Error, do it here.
                    switch (attr) {
                        case "__all__":
                            error_name = "";
                            break
                        case "ip_str":
                            error_name = "IP:";
                            break
                        default:
                            error_name = attr + ": ";
                    }
                    // Error Output
                    $('#error_list').append("<li>" + error_name + data.errors[attr] + "</li>");
            }
        } else {
            // Success Output
            $('#' + rec_type + '_build').attr('pk', data.obj_pk)
            if (data.created) {
                $('#dns_success').append("<span><a href='" + data.success + "'>Click to see the new "+
                    rec_type +" record</a>" + "</span>");
            } else {
                $('#dns_success').append("<span><a href='" + data.success + "'>Click to see the updated "+
                    rec_type +" record</a>" + "</span>");
            }
        }
    });// end post
}
*/

function get_post_patch_data(fields){
    var data = {views:[]}
    for (var field in fields) {
        if (String(field) == 'private_view') {
            if ($('#'+fields[field]).attr('checked') === 'checked'){
                data.views.push('private')
            }
        } else if (String(field) == 'public_view') {
            if ($('#'+fields[field]).attr('checked') === 'checked'){
                data.views.push('public')
            }
        } else {
            data[field] = $('#'+fields[field]).attr('value');
        }
    }
    return data
}

function get_record_meta_data(rec_type){
    /*
     * New record:
     *  - get_record_mata(rec_type)
     *  - suck data from inputs using right side of fields
     *  - call presend() with fields as argument
     *  - get data and:
     *      - if 'resource_uri' is set in the DOM, PATCH to resource_uri in DOM
     *      - if 'rewource_url' is not set, POST to resource_uri in meta_data
     * Edit Existing record:
     *  - take json X for initial data. for every field in X that matches fields, but data into
     *      right side of fields.
     *  - fill in 'pk' attribute
     *
     */
    var base_api_url = "/mozdns/api/v1_dns/"
    switch (rec_type) {
        case 'A':
                return {
                        fields: {
                            comment: 'A_build_comment',
                            ttl: 'A_build_ttl',
                            ip_str: 'A_build_ip',
                            fqdn: 'A_build_name',
                            private_view: 'A_private_view',
                            public_view: 'A_public_view',
                        },
                        resource_uri: base_api_url + 'addressrecord/', // Append <pk>/ to get details
                                          // about an object.
                        pre_send: function (fields) {
                            // Add any existing fields or return false and update dns_errors
                            fields['ip_type'] = '4';
                        }

                    }
            break
        case 'AAAA': // TODO
                return {
                        fields: {
                            comment: 'AAAA_build_comment',
                            ttl: 'AAAA_build_ttl',
                            ip_str: 'AAAA_build_ip',
                            fqdn: 'AAAA_build_name',
                            private_view: 'AAAA_private_view',
                            public_view: 'AAAA_public_view',
                        },
                        resource_uri: base_api_url + 'addressrecord/',
                        pre_send: function (fields) {
                            // Add any existing fields or return false and update dns_errors
                            fields['ip_type'] = '6';
                        }
                    }
            break
        case 'PTR':
                return {
                        comment: 'PTR_build_comment',
                        ttl: 'PTR_build_ttl',
                        ip_str: 'PTR_build_ip',
                        fqdn: 'PTR_build_name',
                        private_view: 'PTR_private_view',
                        public_view: 'PTR_public_view',
                        resource_uri: base_api_url + 'ptr/'
                    }
            break
        case 'SRV':
                return {
                        comment: 'SRV_build_comment',
                        ttl: 'SRV_build_ttl',
                        fqdn: 'SRV_build_name',
                        port: 'SRV_build_Port',
                        weight: 'SRV_build_Weight',
                        priority: 'SRV_build_Priority',
                        target: 'SRV_build_target_name',
                        private_view: 'SRV_private_view',
                        public_view: 'SRV_public_view',
                        resource_uri: base_api_url + 'srv/'
                    }
            break
        case 'CNAME':
                return {
                        comment: 'CNAME_build_comment',
                        ttl: 'CNAME_build_ttl',
                        fqdn: 'CNAME_build_name',
                        data: 'CNAME_build_target_name',
                        private_view: 'CNAME_private_view',
                        public_view: 'CNAME_public_view',
                        resource_uri: base_api_url + 'cname/'
                    }
            break
        case 'NS':
                return {
                        comment: 'NS_build_comment',
                        ttl: 'NS_build_ttl',
                        domain: 'NS_build_name',
                        server: 'NS_build_target_name',
                        private_view: 'NS_private_view',
                        public_view: 'NS_public_view',
                        resource_uri: base_api_url + 'nameserver/'
                    }
            break
        case 'TXT':
                return {
                        comment: 'TXT_build_comment',
                        ttl: 'TXT_build_ttl',
                        fqdn: 'TXT_build_name',
                        txt_data: 'TXT_build_build_text',
                        private_view: 'TXT_private_view',
                        public_view: 'TXT_public_view',
                        resource_uri: base_api_url + 'txt/'
                    }
            break
        case 'MX':
                return {
                        comment: 'MX_build_comment',
                        ttl: 'MX_build_ttl',
                        fqdn: 'MX_build_name',
                        priority: 'MX_build_Priority',
                        server: 'MX_build_target_name',
                        private_view: 'MX_private_view',
                        public_view: 'MX_public_view',
                        resource_uri: base_api_url + 'mx/'
                    }
            break
    }
    return false  // What is None in javascript?
}
