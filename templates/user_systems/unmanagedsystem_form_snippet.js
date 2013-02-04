    <script>
        var owner_list = {{ owner_json|safe }};
        $(function() {
            $('#id_owner').autocomplete(owner_list);
            $('#new_server_model').click(function() {
                var old_content = $(this).parent().parent().clone(true);
                $(this).parent().remove();
                var form = $('<div class="sub_form">' +
                                        'Vendor: <input type="text" name="js_server_model_vendor" /> <br />' + 
                                        'Model: <input type="text" name="js_server_model_model" /> <br />' + 
                                        ' <a class="cancel" href="">Cancel</a>' + 
                                        '</div>');

                form.find('a.cancel').click(function() {
                    $('#server_model_formline').replaceWith(old_content); 
                    return false;
                });

                $('#id_server_model').replaceWith(form);
                return false;
            });

            $('#new_os').click(function() {
                var old_content = $(this).parent().parent().clone(true);
                $(this).parent().remove();
                var form = $('<div class="sub_form">' +
                                        'Name: <input type="text" name="js_os_name" /> <br />' + 
                                        'Version: <input type="text" name="js_os_version" /> <br />' + 
                                        ' <a class="cancel" href="">Cancel</a>' + 
                                        '</div>');

                form.find('a.cancel').click(function() {
                    $('#os_formline').replaceWith(old_content); 
                    return false;
                });

                $('#id_operating_system').replaceWith(form);
                return false;
            });
        });
    </script>
