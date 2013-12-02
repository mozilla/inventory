// So if people paste links around.
console.log("Form loaded: I see rdtype=: {{record_type}} and pk=:{{record_pk}}");
function page_js_init(find_related_url) {
    if ($('#id_ip_str')){
        $("<input type='button' id='ffip' value='Automatically Assign'/>").insertAfter('#id_ip_str').css('margin-left', '0.7em');

        // Pull in find IP stuff
        $('#ffip').click(function () {
          $('#choose-ip-area').css('display', 'block');
          $('#choose-ip-area').css('visibility', 'hidden');
          $.get('/core/range/ajax_find_related/', function (data){
                $('#choose-ip').html(data);
                // This function was pulled into existance by this ajax request
                chosen_init({
                  hints: ['#id_fqdn', '#id_name'],
                  dialog_div_id: '#choose-ip',
                  target_el_id: '#id_ip_str',  // target_el_id
                  reset_button_id: '#choose-ip-reset',
                  display_range_id: '#choose-ip-display-ranges-area',
                  find_related_url: find_related_url,
                  reset_callback: function (){
                    if (!$('#dns-data').attr('record_pk')) {
                      $('#related-things').empty();
                      $('#related-help-text').empty();
                      $('#id_ip_str').val('');

                      if ($('#id_fqdn').data('auto-name') === $('#id_fqdn').val()) {
                          $('#id_fqdn').val('');
                      }
                      if ($('#id_name').data('auto-name') === $('#id_name').val()) {
                          $('#id_name').val('');
                      }
                      $('#id_views_0').attr('checked', false);
                      $('#id_views_1').attr('checked', false);
                    }
                  },
                  found_ip_callback: function (range, name_fragment){
                    if(typeof range.free_ip == 'undefined') {
                      $('#id_ip_str').val('');
                    } else {
                      $('#id_ip_str').val(range.free_ip).change();
                      $('#id_ip_str').focus();
                    }
                    function suggest_name(target) {
                        if (name_fragment.length && !$(target).val()) {
                          var auto_name = '.' + name_fragment + '.mozilla.com';
                          $(target).val(auto_name);
                          $(target).focus();
                          $(target).data('auto-name', auto_name);
                        }
                    }
                    if ($('#id_fqdn').val() === '') {
                      suggest_name('#id_fqdn');
                    }
                    if ($('#id_name').val() === '') {
                      suggest_name('#id_name');
                    }
                  }
                });
                $('#choose-ip-area').css('transition', 'visibility 0.5s linear 0s');
                $('#choose-ip-area').css('visibility', 'visible');
                $('#choose-ip-area').css('transition', 'height 0.5s linear 0s');
          });
        });
    }
    var possible_input_ids = [
        '#id_ip_str',
        '#id_target',
        '#id_fqdn',
    ];
    search_watcher(possible_input_ids, $('#related-things'), function (search){
        console.log("callback here");
        console.log(search);
        if (search !== '') {
            $('#related-help-text').css('display', 'block');
            $('#related-help-text').html(
                'Below are related objects found with the search <code>"' + search + '"</code>'
            );
        } else {
            $('#related-help-text').css('display', 'none');
        }
    });
}
