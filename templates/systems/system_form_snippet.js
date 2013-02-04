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
                $('#expanded_keystore_inner').html('&nbsp;').load('/en-US/systems/get_expanded_key_value_store/' + system_id + '/');
            });




		function getURISegment(segment){
			var query = document.location.href;
			var split1 = query.split(/\/\//);
			var ret = split1[1].split(/\//);
			return (ret[segment - 1]);
		}

		var system_id = getURISegment(5);
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
                var form = $('<div id="server_model_sub_form" class="sub_form">' +
                                        '<label>Vendor:</label> <input type="text" name="js_server_model_vendor" id="js_server_model_vendor" /> <br />' + 
                                        '<label>Model:</label> <input type="text" name="js_server_model_model" id="js_server_model_model" /> <br />' + 
                                        '<a id="server_model_create_button" class="create" href="#">Create</a>&nbsp;<a class="cancel" href="">Cancel</a>' + 
                                        '</div>');

                form.find('a.cancel').click(function() {
                    $('#server_model_formline').replaceWith(old_content); 
                    return false;
                });

                $('#id_server_model').replaceWith(form);
                $("#server_model_create_button").click(function(){

                    server_model = $("#js_server_model_model").val();
                    server_vendor = $("#js_server_model_vendor").val();
                    if(!server_model || !server_vendor){
                        alert("You must provide both a server model and vendor");
                    } else {
                        $.ajax({ 
                            type: "POST", 
                            url: "/en-US/systems/server_models/create_ajax/",
                            data: {
                                'model': server_model,
                                'vendor': server_vendor
                            },
                            contentType: "application/json; charset=utf-8", 
                            dataType: "json", 
                            beforeSend: function(){ 
                                $('#server_model_formline').replaceWith(old_content); 
                                $("#id_server_model").get(0).options.length = 0; 
                                $("#id_server_model").get(0).options[0] = new Option("Loading...", "-1");
                            }, 
                            success: function(msg) { 
                                $("#server_model_sub_form").hide();
                                $("#id_server_model option[value='-1']").remove();
                                $.each(msg, function(index, item) { 
                                    $("#id_server_model").get(0).options[$("#id_server_model").get(0).options.length] = new Option(item.name, item.id);
                                }); 
                            }, 
                            error: function() { 
                                alert("Failed to load server models"); 
                            } 
                        });  
                    }

                    return false;

                });
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
                var form = $('<div id="operating_system_model_sub_form" class="sub_form">' +
                                        '<label>Name:</label> <input type="text" name="js_os_name" id="js_os_name" /> <br />' + 
                                        '<label>Version:</label> <input type="text" name="js_os_version" id="js_os_version" /> <br />' + 
                                        '<a id="operating_system_create_button" class="create" href="#">Create</a>&nbsp; <a class="cancel" href="">Cancel</a>' + 
                                        '</div>');

                $('#id_operating_system').replaceWith(form);
                $("#operating_system_create_button").click(function(){

                    name = $("#js_os_name").val();
                    version = $("#js_os_version").val();
                    if(!name || !version){
                        alert("You must provide both a name and version");
                    } else {
                        $.ajax({ 
                            type: "POST", 
                            url: "/en-US/systems/operating_system/create_ajax/",
                            data: {
                                'name': name,
                                'version': version
                            },
                            contentType: "application/json; charset=utf-8", 
                            dataType: "json", 
                            beforeSend: function(){ 
                                $('#os_formline').replaceWith(old_content); 
                                $("#id_operating_system").get(0).options.length = 0; 
                                $("#id_operating_system").get(0).options[0] = new Option("Loading...", "-1");
                            }, 
                            success: function(msg) { 
                                $("#operating_system_sub_form").hide();
                                $("#id_operating_system option[value='-1']").remove();
                                $.each(msg, function(index, item) { 
                                    $("#id_operating_system").get(0).options[$("#id_operating_system").get(0).options.length] = new Option(item.name, item.id);
                                }); 
                            }, 
                            error: function() { 
                                alert("Failed to load Operating Systems"); 
                            } 
                        });  
                    }

                    return false;

                });
                return false;
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
