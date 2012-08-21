    function add_quicksearch(input, result_div, url) {
        input.closest('form').submit(function() {
            result_div.load(url, {quicksearch: input.val()});
            return false;
        });
    }

    function add_tablesorter(table) {
        var table = $(table);
        var headers = new Object();
        headers[table.find('th').length - 1] = { sorter: false};
        table.tablesorter( 
            {
                widgets: ['zebra'],
                headers: headers
            }
        );
    }

    jQuery.fn.submit_rack_system_form = function(form_url) {
        var row = this;

        row.find(':submit').click(function() {
            $.post(form_url, row.find(':enabled').serialize(), function(data) {
                var new_row = $(data.payload);
                if(data.success) {
                    row.replaceWith(new_row);
                } else {
                    new_row.submit_rack_system_form(form_url, new_row);
                    row.replaceWith(new_row);
                }
            }, "json");
            return false;
        });
        return this;
    }

    jQuery.fn.new_system_from_rack = function() {
        // Attach click event to "System rack link"
        this.click(function() {
            var rack_table = $(this).closest('.rack');
            var rack_id = rack_table.attr('id').split('-')[1];
            var form_url = '/en-US/systems/racks/system/new/' + rack_id + '/';

            // Load rack row form
            $.get(form_url, {}, function(data) {
                var new_system_row = $(data.payload);

                new_system_row.submit_rack_system_form(form_url);
                rack_table.find('.new-system').closest('tr').before(new_system_row);
            }, "json");
            return false;
        });
        return this;
    }
    $(document).ready(function(){
        $("input, select").mouseover(function(){
            $(this).next('span.helptext').css('display','inline');
        });
        $("input, select").mouseout(function(){
            $(this).next('span.helptext').css('display','none');
        });
    });
