function setup_delete(zones, zone_delete_url){
    function display_zone(domain_name){
        $('#waiting-block').css('display', 'block');
        $('#results-block').css('display', 'none');

        $.get('/core/search/search_ajax/',
            {'search': 'zone=:' + domain_name},
            function update_results(data){
                $('#results-block').html(data);
                $('#waiting-block').css('display', 'none');
                $('#results-block').css('display', 'block');
            }).error(function(e) {
                console.log(e);
                if (e.statusText != "abort"){
                    var newDoc = document.open("text/html", "replace");
                    newDoc.write(e.responseText);
                    newDoc.close();
                } else {
                    $('#results-block').html('');
                }
            });
    }
    $('#zone_list').autocomplete({
        source: zones,
        select: function(event, ui) {
          display_zone(ui.item.value);
          $('delete-dialog').data('data-domain-name', ui.item.value);
        }
    });
    $('#delete_button').click(function (){
      var domain_name = $('#zone_list').val();
      if (domain_name) {
        $('#delete-dialog').dialog({
          buttons : {
            "Confirm" : function() {
              $('#waiting-to-delete-block').css('display', 'block');
              $.post(zone_delete_url,
                {'domain_name': domain_name},
                function delete_zone(data) {
                  var resp = $.parseJSON(data);
                  $('#waiting-to-delete-block').css('display', 'none');
                  if (resp.success) {
                    window.location = '/';
                  } else {
                    $('#results-block').css('display', 'block');
                    $('#results-block').html('' +
                      '<span style="color:red;">' +
                      'Sorry! There was an error. Please report the following message: "' +
                      resp.message +
                      '"</span>');
                  }
                });
              $(this).dialog('close');
            },
            "Cancel" : function() {
              $(this).dialog('close');
            }
          }
        });
      }
    });
}
