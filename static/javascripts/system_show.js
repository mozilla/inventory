function display_inpage_search_results(query, results_selector, callback) {
  $.get('/en-US/core/search/search_ajax/',
    {
      'format': 'table',
      'search': query + ' AND !(type=:SYS OR type=:SREG)'
    },
    function(data) {
      if (!data) {
        console.log('no dns data');
      } else {
        $(results_selector).empty();
        $(results_selector).append(data);
      }
      callback();
    });
}


function goto_range(ip_str, ip_type) {
  $.get('/core/range/find_range/?ip_str=' +
        ip_str + '&ip_type=' + ip_type, do_redirect);
}

function do_redirect(e) {
  var obj = jQuery.parseJSON(e);
  if (obj.success) {
    window.open(obj.redirect_url);
  } else {
    alert(obj.message);
  }
}

$(document).ready(function() {
  // Pull in find IP stuff
  $('#ffip').click(function () {
    $('#choose-ip-area').css('display', 'block');
    $('#choose-ip-area').css('visibility', 'hidden');
    $.get('/core/range/ajax_find_related/', function (data){
          $('#choose-ip').html(data);
          // This function was pulled into existance by this ajax request
          chosen_init({
            hints: ['#id_sreg-fqdn'],
            dialog_div_id: '#choose-ip',
            target_el_id: '#id_sreg-ip_str',
            reset_button_id: '#choose-ip-reset',
            display_range_id: '#choose-ip-display-ranges-area',
            find_related_url: '/en-US/core/range/find_related/',
            reset_callback: function (){
              if ($('#id_sreg-fqdn').data('auto-name') === $('#id_sreg-fqdn').val()) {
                  $('#id_sreg-fqdn').val('');
              }
              $('#id_sreg-ip_str').val('');
              $('#id_sreg-views_0').attr('checked', false);
              $('#id_sreg-views_1').attr('checked', false);
            },
            found_ip_callback: function (range, name_fragment){
              function suggest_name(target) {
                  if (name_fragment.length && !$(target).val()) {
                    var auto_name = '.' + name_fragment + '.mozilla.com';
                    $(target).val(auto_name);
                    $(target).focus();
                    $(target).data('auto-name', auto_name);
                  }
              }
              if(typeof range.free_ip == 'undefined') {
                $('#id_sreg-ip_str').val('');
              } else {
                if ($('#id_sreg-fqdn').val() === '') {
                  suggest_name('#id_sreg-fqdn');
                }
                $('#id_sreg-ip_str').val(range.free_ip).change();
              }
            }
          });
          $('#choose-ip-area').css('transition', 'visibility 0.5s linear 0s');
          $('#choose-ip-area').css('visibility', 'visible');
          $('#choose-ip-area').css('transition', 'height 0.5s linear 0s');
    });
  });
  var system_id = $('#meta-data').attr('data-system-id');

  $('a.goto_range').click(function() {
    var args = $(this).attr('rel').split('|');
    var ip_str = args[0];
    var ip_type = args[1];
    $.get('/core/range/find_range/?ip_str=' +
          ip_str + '&ip_type=' + ip_type, do_redirect);
  });

  $('#add-sreg-dialog').dialog({
    title: 'Create new registration',
    autoShow: false,
    autoOpen: false,
    modal: true,
    width: 700,
    buttons: {
      'Save': function() {
        if (!$('#id_sreg-ip_str').val()) {
          alert('IP Address Required');
          return;
        }
        $.ajax({
          url: '/en-US/core/registration/static/create/',
          type: 'POST',
          data: $('#id-sreg-hwadapter-form').serialize(),
          success: function(data) {
            var result = jQuery.parseJSON(data);
            if (result.success === true) {
              self.location.reload();
            } else {
              // Clear errors
              $('.errors').remove();
              var field, error, error_list, error_el;
              if (result.errors.hw_adapters) {
                /*
                 * Here we look at the errors and try to tie them back to input
                 * fields.
                 *
                 * The order of the errors returned are in the same order as the
                 * the hw adapters that were submited.
                 */
                var blocks = $('#hwadapter-tables').find('.hwadapter-table');
                console.log(result.errors.hw_adapters);
                for (var i = 0; i < result.errors.hw_adapters.length; i++) {
                  error_list = $("<ul class='errors'></ul>");
                  $(error_list).css('color', 'red');
                  $(blocks[i]).prepend(error_list);
                  for (var j = 0;
                       j < result.errors.hw_adapters[i].length;
                       j++) {
                    field = result.errors.hw_adapters[i][j][0];
                    error = result.errors.hw_adapters[i][j][1];
                    if (field === '') {
                      message = error;
                    } else {
                      message = field + ': ' + error;
                    }
                    error_el = $(error_list).append(
                      '<li>' + message + '</li>'
                    );
                    $(error_el).css('color', 'red');
                  }
                }
              } else if (result.errors.sreg) {
                /*
                 * There was an error with creating the static reg. Display
                 * errors above appropriate inputs.
                 */
                error_list = $("<ul class='errors'></ul>");
                $(error_list).css('color', 'red');
                $('#id-sreg-hwadapter-form').prepend(error_list);
                for (var p = 0; p < result.errors.sreg.length; p++) {
                  field = result.errors.sreg[p][0];
                  for (var k = 0; k < result.errors.sreg[p][1].length; k++) {
                    error = result.errors.sreg[p][1][k];
                    if (field === '' || field == '__all__') {
                      message = error;
                    } else {
                      message = field + ': ' + error;
                    }
                    error_el = $(error_list).append(
                       '<li>' + message + '</li>');
                    $(error_el).css('color', 'red');
                  }
                }
              }
            }
          },
          error: function(e) {
            var newDoc = document.open('text/html', 'replace');
            newDoc.write(e.responseText);
            newDoc.close();
            $('#form-message').html('<p>Error</p>');
          }
        });
      },
      Cancel: function() {
          $(this).dialog('close');
      }
    },
    close: function(event, ui) {
    }
  }); // End dialog

  $('.add_new_sreg').click(function() {
    make_smart_name_get_domains($('#id_sreg-fqdn'), true);
    $('#add-sreg-dialog').dialog('open');
    return false;
  });

  // Default IP
  $('#id-auto-assign-ip').attr('checked', 'checked'); // Set it to auto assign
  bind_view_ip_type_detection('#id_sreg-ip_str', '#id_sreg-views_0', '#id_sreg-views_1');

  /*
   * Dynamically update option-hostname on hwadapter forms
   */

  $('#id_sreg-fqdn').on('change keypress paste focus textInput input', function (){
    var fqdn = $('#id_sreg-fqdn').val();
    $('.hw-option-hostname').each(function (i, el) {
      var option_hostname = $(el).val();
      if (option_hostname.length > 1 && fqdn === '') {
        // pass
      } else if (
        option_hostname.substring(0, fqdn.length) === fqdn || // startswith
        fqdn.substring(0, option_hostname.length) === option_hostname) { // startswith
        $(el).val(fqdn);
      }
    });
  });

  /*
   * Dynamically adding Hardware Adapters
   */

  $('#hwadapter-tables').find('.remove-hwadapter').css('visibility', 'hidden');
  $('#id_hwadapters-TOTAL_FORMS').val($('.hwadapter-table').length);

  $('#btnMore').click(function() {
    var hwtable, blocks, newBlock, newEntry, nextFree;
    var removeButton, newTTL;

    hwtable = $('#hwadapter-tables');
    nextFree = parseInt($('#id_hwadapters-TOTAL_FORMS').val(), 'base10');
    blocks = hwtable.find('.hwadapter-table');
    dhcp_scope_options = $(blocks.last()).find('.dhcp-scopes');
    newBlock = $(blocks.last()).clone();
    $($(newBlock).find('.dhcp-scopes')).each(function (i, el) {
      $(el).val(dhcp_scope_options.eq(i).val());
    });

    $(newBlock).find('input, select').each(function(i, el) {
      if ($(el).attr('class') === 'increment') {  // TODO make this a substring check
        $(el).val($(el).val().replace(/\d+$/, function(n){ return ++n; }));
      }
      if ($(el).attr('name')) {
        $(el).attr('name', $(el).attr('name').replace(nextFree - 1, nextFree));
      }
      if ($(el).attr('id')) {
        $(el).attr('id', $(el).attr('id').replace(nextFree - 1, nextFree));
      }
    });
    // Django starts at 0 when it numbers the forms, so we need to update
    // afterwards to fend off the off-by-one daemons
    nextFree = nextFree + 1;
    $('#id_hwadapters-TOTAL_FORMS').val(nextFree);

    // Bind remove handler
    removeButton = newBlock.find('.remove-hwadapter');
    $(removeButton).css('visibility', 'visible');
    removeButton.click(function() {
      $(this).closest('table').remove();
      // Do *NOT* decrement id_hwadapters-TOTAL_FORMS.
    });
    newBlock.insertAfter(blocks.last());
  });

  // Create/Delete Hardware Adapters
  $('.delete-hwadapter').click(function() {
    var hw_pk = $(this).attr('data-hwadapter-pk');
    if (confirm('Are you sure?')) {
      $.ajax({
        url: '/en-US/core/hwadapter/' + hw_pk + '/delete/',
        type: 'POST',
        data: {pk: hw_pk},
        success: function(data) {
          location.reload();
        },
        error: function(e) {
          var newDoc = document.open('text/html', 'replace');
          newDoc.write(e.responseText);
          newDoc.close();
          $('#form-message').html('<p>Error</p>');
        }
      });
    }
    return false;
  });

  $('.add-hwadapter').click(function() {
    var sreg_pk = $(this).attr('data-sreg-pk');
    $('#id_add-hw-sreg').val(sreg_pk);
    var d = $('#add-hwadapter-dialog').dialog({
        title: 'Create new registration',
        autoShow: true,
        width: 700,
        buttons: {
          'Save': function() {
              $.ajax({
                url: '/en-US/core/hwadapter/create/',
                type: 'POST',
                data: $('#add-hwadapter-form').serialize(),
                success: function(data) {
                  var res = jQuery.parseJSON(data);
                  if (res.success) {
                    location.reload();
                  } else {
                    $('#add-hwadapter-form').empty();
                    $('#add-hwadapter-form').append(res.form);
                    $('#id_add-hw-sreg').val(sreg_pk); // Re set the sreg pk
                  }
                },
                error: function(e) {
                  var newDoc = document.open('text/html', 'replace');
                  newDoc.write(e.responseText);
                  newDoc.close();
                  $('#form-message').html('<p>Error</p>');
                }
              });
              return false;
          },
          'Cancel': function() {
            $(this).dialog('close');
          }
        }
    }); // End dialog
    d.show();
    return false;
  });
});
