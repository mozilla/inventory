    <script type="text/javascript">
        $(function() {
            $('#new_owner').click(function() {
		var old_content = $(this).parent().parent().clone(true);
                $(this).parent().remove();
                var form = $('<div class="sub_form">' +
                                        'Name: <input type="text" name="js_owner_name" /> <br />' + 
                                        'User Location: <input type="text" name="js_owner_user_location" /> <br />' + 
                                        'Email: <input type="text" name="js_owner_email" /> <br />' + 
                                        'Note: <input type="textarea" rows="15" cols="20" name="js_owner_note" /> <br />' + 
                                        ' <a class="cancel" href="">Cancel</a>' + 
                                        '</div>');

                form.find('a.cancel').click(function() {
                    $('#owner_formline').replaceWith(old_content); 
                    return false;
                });

                $('#id_owner').replaceWith(form);
                return false;
            });
        });
    </script>
