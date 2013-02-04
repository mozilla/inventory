
        function get_id(field){
            return field.split('_')[0];
        }
        function get_type(field){
            return field.split('_')[1];
        }

        function get_validation_regex(field_name){
            input_regex_array = new Array();
            output_regex_array = new Array();
            validation_error_array = new Array();
            return_array = new Array();

            ipv4_regex = new RegExp(/^\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b$/);
            true_false_regex = new RegExp(/(^True$|^False$)/);
            ///REGEX for an adapter ip address
            input_regex_array.push(new RegExp(/nic\.\d+\.ipv4_address\.\d+/));
            output_regex_array.push(ipv4_regex);
            validation_error_array.push('Requires IP Address');

            input_regex_array.push(new RegExp(/^dhcp\.scope\.netmask$/));
            output_regex_array.push(ipv4_regex);
            validation_error_array.push('Requires Subnet Mask');

            input_regex_array.push(new RegExp(/^is_dhcp_scope$/));
            output_regex_array.push(new RegExp(true_false_regex));
            validation_error_array.push('Requires True|False');

            input_regex_array.push(new RegExp(/^dhcp\.scope\.start$/));
            output_regex_array.push(new RegExp(ipv4_regex));
            validation_error_array.push('Requires IP Address');
            
            input_regex_array.push(new RegExp(/^dhcp\.scope\.end$/));
            output_regex_array.push(new RegExp(ipv4_regex));
            validation_error_array.push('Requires IP Address');

            input_regex_array.push(new RegExp(/^dhcp\.pool\.start$/));
            output_regex_array.push(new RegExp(ipv4_regex));
            validation_error_array.push('Requires IP Address');

            input_regex_array.push(new RegExp(/^dhcp\.pool\.end$/));
            output_regex_array.push(new RegExp(ipv4_regex));
            validation_error_array.push('Requires IP Address');

            input_regex_array.push(new RegExp(/^dhcp\.option\.ntp_server\.\d+$/));
            output_regex_array.push(new RegExp(ipv4_regex));
            validation_error_array.push('Requires IP Address');

            input_regex_array.push(new RegExp(/^dhcp\.dns_server\.\d+$/));
            output_regex_array.push(new RegExp(ipv4_regex));
            validation_error_array.push('Requires IP Address');

            input_regex_array.push(new RegExp(/^dhcp\.option_router\.\d+$/));
            output_regex_array.push(new RegExp(ipv4_regex));
            validation_error_array.push('Requires IP Address');

            input_regex_array.push(new RegExp(/^dhcp\.option\.subnet_mask\.\d+$/));
            output_regex_array.push(new RegExp(ipv4_regex));
            validation_error_array.push('Requires IP Address');

            input_regex_array.push(new RegExp(/^dhcp\.pool\.allow_booting\.\d+$/));
            output_regex_array.push(new RegExp(true_false_regex));
            validation_error_array.push('Requires True|False');
            
            input_regex_array.push(new RegExp(/^dhcp\.pool\.allow_bootp\.\d+$/));
            output_regex_array.push(new RegExp(true_false_regex));
            validation_error_array.push('Requires True|False');

            input_regex_array.push(new RegExp(/^nic\.\d+\.mac_address\.\d+$/));
            output_regex_array.push(new RegExp(/^([0-9a-fA-F]{2}([-:]|$)){6}$/i));
            validation_error_array.push('Requires Mac Address XX:XX:XX:XX:XX:XX');

            for(var i=0;i<input_regex_array.length;i++){
                if(field_name.match(input_regex_array[i])){
                    return_array[0] = output_regex_array[i];
                    return_array[1] = validation_error_array[i];
                    return return_array;
                }

            }
            return_array[0] = false;
            return return_array;

        }

        function validate_field_input(input_field){
            id = get_id(input_field.name);
            type = get_type(input_field.name);
            the_return = Array();
            the_return[0] = true;
            the_return[1] = '';
            if(type == 'value'){
                value = $("#" + id + "_key").val();
            } else {
                value = input_field.value;
            }
            validation_regex = get_validation_regex(value);
            value_field_name = '#' + id + '_value';
            if(validation_regex[0] != false){
                if(validation_regex[0].test($(value_field_name).val()) == false){
                //if($(value_field_name).val().test(validation_regex) == false){
                    //console.log('Validation Failed'); 
                    the_return[0] = false;
                    the_return[1] = validation_regex[1];
                } else {
                    //console.log('Validation Passed');
                    the_return[0] = true;
                    the_return[1] = validation_regex[1];

                }

            }
            return the_return;
        }
