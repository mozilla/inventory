/*

function bind_record_search_box(){
    // We also need bind an auto complete to the search
    // field for this specifc record type.
    $( "#record_search" ).autocomplete({
        minLength: 2,
        source: '/mozdns/record/ajax_search/?record_type='
                + $('#rec_type_select option:selected').attr('value'),
        select: function( event, ui ) {
            // Save the selected pk so we can use it if
            // the user decides to edit the record.
            var data = $('dns-data').record_pk = ui.item.pk;
            $("#record_search").prop('disabled', true);
            $('#record_search_selected').html('Edit <font color="green"><code>'
                                              +ui.item.label+'</code></font> ?');
        }
    });
}

$('#launch-search').click(function(){
    var s_dialog = $( "#search-dialog" ).dialog({
        title: 'Search '+$('#rec_type_select option:selected').attr('value')+' records',
        // Click the selected record
        autoShow: false,
        minWidth: 520,
        buttons: {
            "Edit Record": function() {
                $.get('/mozdns/record/ajax_form/',
                    {
                        'record_type':$('#rec_type_select option:selected').attr('value'),
                        'record_pk': $('#search-dialog').attr('stage_pk'),
                    },
                    function (data) {
                        $('#current_form_data').empty();
                        $('#current_form_data').append(data);
                        // Notice how we don't call
                        // bind_smart_names here. We don't
                        // want the autocomplete to get in
                        // the way
                        // It's likely that they are just making a small change.
                    });
                $("#record_search").prop('disabled', false);
                $('#record_search_selected').html('');
                $("#record_search").val('');
                $(this).dialog("close");
            },
            cancel: function() {
                $('#search-dialog').attr('stage_pk', ''), // we don't want this anymore.
                $("#record_search").prop('disabled', false);
                $('#record_search_selected').html('');
                $("#record_search").val('');
                $(this).dialog("close");
            }
        }
    });
    s_dialog.show();
});

function populate_dns_form() {
    var data = $('dns-data');

    $.get('/mozdns/record/ajax_form/',
        {
            'record_type': data.record_type,
            'record_pk': data.record_pk,
        }, function (data) {
            $('#current-form-area').empty();
            $('#current-form-area').append(data);
            bind_smart_names();
            bind_record_search_box();
        })
}

function edit_clear(){
}
function bind_record_search_box(){
    // We also need bind an auto complete to the search
    // field for this specifc record type.
    $("#record_search").autocomplete({
        minLength: 2,
        source: '/mozdns/record/ajax_search/?record_type='
                + $('#rec_type_select option:selected').attr('value'),
        select: function(event, ui) {
            // Save the selected pk so we can use it if
            // the user decides to edit the record.
            var data = $('dns-data');
            var record_pk = data.record_pk;
            var record_type = data.record_type;
        }
    });
}

function get_form(record_type, record_pk) {
}
*/

function select_state(state) {
    function insert_new_form(record_type, record_pk, callback){
        console.log(record_type + " " + record_pk);
        $.get('/mozdns/record/record_ajax/',

            {
                'record_type': record_type,
                'record_pk': record_pk
            },
            function (data) {
                $('#current-form-area').empty();
                console.log("[DEBUG] Redrawing form");
                $('#current-form-area').append(data);
                $('#add-comment').attr('checked', true);
                bind_submit($('#current-form'));
                callback();
            }).error(function(e) {
                var newDoc = document.open("text/html", "replace");
                newDoc.write(e.responseText);
                newDoc.close();
            });
    }
    var data = $('#dns-data');
    switch (state) {
    /*
     *      create
     *          * clear pk
     *          * get rdtype
     *          * get form for rdtype
     *          * insert new form
     *          * hide search div
     *          * unhide form div
     */
        case 'create':
            console.log("[STATE] create");
            data.attr('record_pk', '');
            insert_new_form(data.attr('record_type'), data.attr('record_pk'), function (){
                bind_smart_names();
            });
            break;
    /*
     *      edit
     *          * if no pk -> do create. log a warning
     *          * get pk and rdtype
     *          * get form for rdtype
     *          * insert form
     *          * hide search div
     *          * unhide form div
     */
        case 'update':
            console.log("[STATE] update");
            console.log("[DEBUG] pk in update state: "+data.attr('record_pk'));
            if (!data.attr('record_pk')) {
                console.log("Tried to update without a record_pk. Going to create view.");
                insert_new_form(data.record_type, '', function (){
                    bind_smart_names();
                    return;
                });
                break;
            } else {
                insert_new_form(data.attr('record_type'), data.attr('record_pk'), function (){
                    fix_css();
                    return;
                });
            }
            break;
    }
}

function clear_commit_message(){
    $('#commit-message').val('');
}
function bind_submit(form) {
    console.log("[DEBUG] Binding submit");
    form.submit(function (){
        console.log("[DEBUG] Submit pressed");
        if ($('#add-comment').is(':checked')) {
            console.log("[DEBUG] Submit pressed");
            var c_dialog = $( "#commit-dialog" ).dialog({
                title: 'Comment on this commit? (A bug number would be nice)',
                autoShow: false,
                minWidth: 520,
                buttons: {
                    "Commit": function() {
                        if(/^\s*$/.test($('#commit-message').val())){
                            alert("Aborting commit due to empty commit message.");
                        } else {
                            $('#id_comment').val($('#commit-message').val());
                            submit_handler();
                        }
                        $(this).dialog("close");
                    },
                    Cancel: function() {
                        // pass
                        $(this).dialog("close");
                    }
                }
            });
        } else {
            console.log("[DEBUG] No commit message");
            submit_handler();
        }
        return false;
    }); // end submit()
}

function submit_handler(){
    $('#form-message').html("<p>Sending data...</p>");
    var start = new Date().getTime();
    $.post('/mozdns/record/record_ajax/',
        $('#current-form').serialize(),
        function (data) {
            $('#current-form-area').empty();
            $('#current-form-area').append(data);
            var end = new Date().getTime();
            var time = end - start;
            $('#action-time').html('('+time/1000+' seconds)');
            fix_css();  // Make names the correct length
            bind_submit($('#current-form'));  // It's a new form.
        }
        ).error(function(e) { console.log(e); alert(e);
            var newDoc = document.open("text/html", "replace");
            newDoc.write(e.responseText);
            newDoc.close();
            $('#form-message').html("<p>Error</p>");
        });
}

function fix_css(){
    // Look for inputs that have id = 'id_fqdn' | 'id_server' | 'id_name'
    // 'id_target' | server . Make these smart names.
    var inputs = $('input');
    for (var x = 0; x < inputs.length; x++){
        if(inputs[x].id === 'id_name' || inputs[x].id === 'id_fqdn'
                || inputs[x].id === 'id_target' || inputs[x].id === 'id_server'){
            $(inputs[x]).css('width', '400px');
        }
    }
}

function bind_smart_names(){
    // Look for inputs that have id = 'id_fqdn' | 'id_server' | 'id_name'
    // 'id_target' | server . Make these smart names.
    var inputs = $('input');
    for (var x = 0; x < inputs.length; x++){
        if(inputs[x].id === 'id_name' || inputs[x].id === 'id_fqdn'
                || inputs[x].id === 'id_target' || inputs[x].id === 'id_server'){
            make_smart_name_get_domains(inputs[x], true)
            $(inputs[x]).css('width', '400px');
        }
    }
}

function make_smart_name_get_domains(element, append){
    $.get('/mozdns/domain/get_all_domains/', function(domains) {
        console.log(domains.sort);
        make_smart_name(element, $.parseJSON(domains), append);
    });
}

function make_smart_name(element, domains, append){
    $(element).autocomplete({
        select: function(event, ui) {
            // We saved the matching part to ui.item.value
            var name = $(element).val(); // The name the user entered
            if(!append) {
                $(element).attr('value', ui.item.label);
            } else if (ui.item.value !== ''){
                var foo =  name.substring(0,name.lastIndexOf(ui.item.value));
                $(element).attr('value', foo + ui.item.label);
            } else {
                if (name.lastIndexOf('.') == name.length - 1) {
                    $(element).attr('value',  name + ui.item.label);
                } else {
                    $(element).attr('value',  name + '.' + ui.item.label);
                }
            }
            return false;
        },
        focus: function(event, ui) {
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

function setup_search_table(){
    var data = $('#dns-data');
    var record_type = data.attr('record_type');
    switch (record_type) {
        case 'AAAA':
        case 'A': table_config = {
                sortList: [[0,1]],
                headers: {
                    0: { sorter:'hostname' },
                    1: { sorter:'ipAddress' },
                }
            };
            break;
        case 'PTR': table_config = {
                sortList: [[0,1],[2,1]],
                headers: {
                    0: { sorter:'ipAddress' },
                    1: { sorter:false },
                    2: { sorter:'hostname' },
                }
            };
            break
        case 'TXT':
        case 'SSHFP':
        case 'MX':
        case 'NS':
        case 'SRV':
        case 'CNAME': table_config = {
                sortList: [[0,1]],
                headers: {
                    0: { sorter:'hostname' },
                    1: { sorter:false },
                    2: { sorter:'hostname' },
                }
            };
            break
        case 'DOMAIN': table_config = {
                sortList: [[0,1]],
                headers: {
                    0: { sorter:'hostname' },
                    1: { sorter:'hostname' },
                }
            };
            break
    }
    $("#record-table").tablesorter(table_config);
    $("#record-table th:last-child").css('width', '30px');

    $("#record-table").on('sortEnd', function(e) {
        tableSorting = e.target.config.sortList;
        data.data('tableSorting', tableSorting); // Save how the table is sorted
    });
}

function do_search(){
    //console.log("searching" + $('#search-query').val());
    var data = $('#dns-data');
    var record_type = data.attr('record_type');

    $.get('/mozdns/record/search_ajax/',
        {
            'record_type': record_type,
            'query': $('#search-query').val(),
        },
        function (table) {
            $("#record-table").remove();
            $("#search-results").append(table);
            setup_search_table();
            // let the plugin know that we made a update

            $("#record-table").trigger("update");
            if (data.data('tableSorting')) {
                // http://stackoverflow.com/questions/2288655/jquery-tablesorter-sort-same-column-after-update
                $("#record-table").trigger("sorton", [data.data('tableSorting'),0]);
            }
        }).error(function(e) {
            var newDoc = document.open("text/html", "replace");
            newDoc.write(e.responseText);
            newDoc.close();
        });
    return false;
}
