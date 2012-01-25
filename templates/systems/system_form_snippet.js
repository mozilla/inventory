    <script type="text/javascript">
        $(function() {
            $("ul.tabs").tabs("div.panes > div");
            $("#key_value_store_expansion").overlay();
            $("#key_value_store_expansion_help").overlay();
            $("#key_value_store_quick_add_adapter").overlay({
               onBeforeLoad: function(){
                    $("#quick_add_host_name").val($("#id_hostname").val());
               }
            });
                
            $("#key_value_store_expansion").click(function(){
                $('#expanded_keystore_inner').html('&nbsp;').load('/systems/get_expanded_key_value_store/' + system_id + '/');
            });




		function getURISegment(segment){
			var query = document.location.href;
			var split1 = query.split(/\/\//);
			var ret = split1[1].split(/\//);
			return (ret[segment - 1]);
		}

		var system_id = getURISegment(4);
        if(system_id == 'new'){
            $("#network_adapter_link").hide();
        }

			/*if($('#id_allocation').val() == 2){
				$('#releng_div_label').show();
				$('#releng_div').show();
			} else {
				$('#releng_div_label').hide();
				$('#releng_div').hide();
			}*/
            $('#new_allocation').click(function() {
                var old_content = $(this).parent().parent().clone(true);
                $(this).parent().remove();
                var form = $('<div class="sub_form">' +
                                        '<label>Name:</label> <input type="text" name="js_allocation_name" />' + 
                                        ' <a class="cancel" href="">Cancel</a>' + 
                                        '</div>');

                form.find('a.cancel').click(function() {
                    $('#allocation_formline').replaceWith(old_content); 
                    return false;
                });

                $('#id_allocation').replaceWith(form);
                return false;
            });

            $('#new_server_model').click(function() {
                var old_content = $(this).parent().parent().clone(true);
                $(this).parent().remove();
                var form = $('<div class="sub_form">' +
                                        '<label>Vendor:</label> <input type="text" name="js_server_model_vendor" /> <br />' + 
                                        '<label>Model:</label> <input type="text" name="js_server_model_model" /> <br />' + 
                                        ' <a class="cancel" href="">Cancel</a>' + 
                                        '</div>');

                form.find('a.cancel').click(function() {
                    $('#server_model_formline').replaceWith(old_content); 
                    return false;
                });

                $('#id_server_model').replaceWith(form);
                return false;
            });

            $('#id_allocation').change(function() {
				if($('#id_allocation').val() == 2){
					$('#releng_div_label').show();
					$('#releng_div').show();
				} else {
					$('#releng_div_label').hide();
					$('#releng_div').hide();
					
				}

			});

            $('#new_os').click(function() {
                var old_content = $(this).parent().parent().clone(true);
                $(this).parent().remove();
                var form = $('<div class="sub_form">' +
                                        '<label>Name:</label> <input type="text" name="js_os_name" /> <br />' + 
                                        '<label>Version:</label> <input type="text" name="js_os_version" /> <br />' + 
                                        ' <a class="cancel" href="">Cancel</a>' + 
                                        '</div>');

                form.find('a.cancel').click(function() {
                    $('#os_formline').replaceWith(old_content); 
                    return false;
                });

                $('#id_operating_system').replaceWith(form);
                return false;
            });
       
            
	$('#new_status').click(function() {
                var old_content = $(this).parent().parent().clone(true);
                $(this).parent().remove();
                var form = $('<div class="sub_form">' +
                                        '<label>Name:</label> <input type="text" name="js_status_name" /> <br />' + 
                                        '<label>Color:</label> <input type="text" name="js_status_color" /> <br />' + 
                                        '<label>Code:</label> <input type="text" name="js_status_code" /> <br />' + 
                                        ' <a class="cancel" href="">Cancel</a>' + 
                                        '</div>');

                form.find('a.cancel').click(function() {
                    $('#status_formline').replaceWith(old_content); 
                    return false;
                });

                $('#id_system_status').replaceWith(form);
                return false;
            });
	});

	$(".container").css("width","1100px");

    </script>
