    <script>
        $(function() {

            function getURISegment(segment){
                var query = document.location.href;
                var split1 = query.split(/\/\//);
                var ret = split1[1].split(/\//);
                return (ret[segment - 1]);
            }

            var kv_id = getURISegment(5);
            load_key_value_store(kv_id);
            function load_key_value_store(kv_id){
                $('#key_value_store_span').html('&nbsp;').load('/en-US/truth/get_key_value_store/' + kv_id + '/');
            }


        });

	    $(".container").css("width","1100px");

    </script>
