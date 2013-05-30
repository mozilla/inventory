function display_inpage_search_results(query, results_selector, callback) {
  $.get('/en-US/core/search/search_ajax/',
    {
      'format': 'table',
      'search': query + ' AND !(type=:SYSTEM OR type=:SREG)'
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
  var system_id = $('#meta-data').attr('data-system-id');

  $('a.goto_range').click(function() {
    var args = $(this).attr('rel').split('|');
    var ip_str = args[0];
    var ip_type = args[1];
    $.get('/core/range/find_range/?ip_str=' +
          ip_str + '&ip_type=' + ip_type, do_redirect);
  });

  $('#id-show-all-ranges').click(function() {
    if ($(this).attr('checked')) {
      $('#id-sreg-range option').each(function() {
        $(this).css('display', '');
      });
    } else {
      $('#id-sreg-range option').each(function() {
        if ($(this).attr('relevant') === 'false') {
          $(this).css('display', 'none');
        }
      });
    }
  });
  $('#id-show-all-ranges').attr('checked', ''); // Default

  $('#add-sreg-dialog').dialog({
    title: 'Create new registration',
    autoShow: false,
    autoOpen: false,
    modal: true,
    width: 700,
    buttons: {
      'Save': function() {
        if (!$('#id_sreg-ip_str').val() &&
            !$('#id-sreg-range').val() &&
            $('#id-auto-assign-ip').is(':checked')) {
          alert('Select a range');
          return;
        }
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
            if (result.success == true) {
              self.location.reload();
            } else {
              // Clear errors
              $('.errors').remove();
              if (result.errors.hw_adapters) {
                /*
                 * Here we look at the errors and try to tie them back to input
                 * fields.
                 *
                 * The order of the errors returned are in the same order as the
                 * the hw adapters that were submited.
                 */
                var blocks = $('#hwadapter-tables').find('.hwadapter-table');
                var field, error, error_list, error_el;
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
                    if (field == '') {
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
                for (var i = 0; i < result.errors.sreg.length; i++) {
                  field = result.errors.sreg[i][0];
                  for (var k = 0; k < result.errors.sreg[i][1].length; k++) {
                    error = result.errors.sreg[i][1][k];
                    if (field == '' || field == '__all__') {
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
          $('#id-sreg-range').get(0).options.length = 0;
          $(this).dialog('close');
      }
    },
    close: function(event, ui) {
      $('#id-sreg-range').get(0).options.length = 0;
    }
  }); // End dialog

  $('.add_new_sreg').click(function() {
    make_smart_name_get_domains($('#id_sreg-fqdn'), true);
    $.ajax({
        type: 'GET',
        url: '/core/range/get_all_ranges_ajax/',
        data: {'system_pk': system_id},
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        beforeSend: function() {
            $('#id-sreg-range').get(0).options[0] = new Option(
              'Loading...', ''
            );
        },
        success: function(msg) {
            $('#id-sreg-range').get(0).options.length = 0;
            $('#id-sreg-range').get(0).options[0] = new Option(
              'Select Range', ''
            );
            $.each(msg, function(index, item) {
              var tld = $('#hostname_dd').html().split('.').pop();
              // Build a suggested FQDN and store it on the range option
              if (tld === 'com' || tld === 'net' || tld === 'org') {
                suggested_fqdn = 'mozilla.' + tld;
              } else {
                suggested_fqdn = 'mozilla.com';
              }
              if (item.site !== '') {
                suggested_fqdn = item.site + '.' + suggested_fqdn;
              }
              if (item.vlan !== '') {
                suggested_fqdn = item.vlan + '.' + suggested_fqdn;
              }
              suggested_fqdn = $(
                '#hostname_dd').html().split('.')[0] + '.' + suggested_fqdn;
              var option = new Option(item.display, item.id);
              $(option).attr('suggested_fqdn', suggested_fqdn);
              $(option).attr('relevant', item.relevant);
              if (!item.relevant) {
                $(option).css('display', 'none');
              }
              $('#id-sreg-range').get(0).options[
                $('#id-sreg-range').get(0).options.length] = option;
            });
            if ($('#id-show-all-ranges').attr('checked')) {
              $('#id-sreg-range option').each(function() {
                $(this).css('display', '');
              });
            } else {
              $('#id-sreg-range option').each(function() {
                if ($(this).attr('relevant') === 'false') {
                  $(this).css('display', 'none');
                }
              });
            }
        },
        error: function() {
          alert('Failed to load Ranges');
        }
      }); // End Ajax
      $('#add-sreg-dialog').dialog('open');
    return false;
  });

  // Use fqdn or auto creation options.
  $('#id-override-fqdn').click(function() {
    if ($(this).attr('checked') == 'checked') {
      $('#id_sreg-fqdn').removeAttr('readonly');
    } else {
      $('#id_sreg-fqdn').attr('readonly', 'readonly');
    }

  });
  // Defaults
  $('#id_sreg-fqdn').val('');
  $('#id_sreg-fqdn').attr('readonly', 'readonly');
  $('#id-override-fqdn').attr('checked', '');

  function auto_assign_ip(the_range) {
    if (the_range) {
      $.get('/core/range/get_next_available_ip_by_range/' + the_range + '/',
        function(data) {
          var obj = jQuery.parseJSON(data);
          if (obj.success == true) {
            $('#id_sreg-ip_str').val(obj.ip_str);
            $('#id_sreg-ip_str').keyup();  // Set the views!
          } else {
            alert(obj.error);
          }
      });
    } else {
      alert('Please select a range.');
      $('#id_sreg-ip_str').val('Auto Assign');
    }
  }

  $('#id-auto-assign-ip').click(function() {
      if ($('#id-auto-assign-ip').prop('checked')) {
        console.log('we are checked');
        var the_range = $('#id-sreg-range').val();
        auto_assign_ip(the_range);
        $('#id_sreg-ip_str').attr('readonly', 'readonly');
      } else {
        console.log('we are NOT checked');
        $('#id_sreg-ip_str').removeAttr('readonly');
        if ($('#id_sreg-ip_str').val() === 'Auto Assign') {
          $('#id_sreg-ip_str').val('');
        }
        // Reset the range select but don't clear the IP
        $('#id-sreg-range').attr('selectedIndex', 0);
      }

  });

  $('#id-sreg-range').change(function() {
    if ($('#id-auto-assign-ip').attr('checked')) {
      auto_assign_ip($(this).val());
    }
    if ($('#id-override-fqdn').attr('checked') === 'checked') {
      var suggested_fqdn = $(
        '#id-sreg-range option:selected').attr('suggested_fqdn');
      console.log('Suggesting: ' + suggested_fqdn);
      $('#id_sreg-fqdn').val(suggested_fqdn);
      $('.hw-option-hostname').val(suggested_fqdn);
    }
  });
  // Default IP
  $('#id-auto-assign-ip').attr('checked', 'checked'); // Set it to auto assign
  $('#id_sreg-ip_str').val('Auto Assign');
  $('#id_sreg-ip_str').attr('readonly', 'readonly');
  bind_view_ip_type_detection();

  /*
   * Dynamically adding Hardware Adapters
   */

  $('#hwadapter-tables').find('.remove-hwadapter').css('visibility', 'hidden');
  $('#id_hwadapters-TOTAL_FORMS').val($('.hwadapter-table').length);

  $('#btnMore').click(function() {
    var hwtable, blocks, newBlock, newEntry, nextFree;
    var removeButton, newTTL;

    hwtable = $('#hwadapter-tables');
    nextFree = parseInt($('#id_hwadapters-TOTAL_FORMS').val());
    blocks = hwtable.find('.hwadapter-table');
    newBlock = $(blocks.last()).clone();

    $(newBlock).find('input').each(function(i, el) {
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

  // gdmit this code is duplicate code!  static/javascripts/dns_form_utils.js

  function bind_view_ip_type_detection() {
    // If an ip starts with '10' automatically set the private view
    // If an ip starts with '63.245' automatically set the public view
    var public_prefixs = ['63.245', '2620:0101', '2620:101'];
    var private_prefixs = ['10'].concat(public_prefixs);
    var found = false; // Help us only do view detect once

    var i; // loop var

    $('#id_sreg-ip_str').keyup(function() {
      set_ip_type($('#id_sreg-ip_str').val());
      function do_detect(prefixs, view_el) {
        var ip_str = $('#id_sreg-ip_str').val();
        for (i = 0; i < prefixs.length; i++) {
          if (ip_str.substring(0, prefixs[i].length) === prefixs[i]) {
            $(view_el).attr('checked', 'checked');
            found = true;
            break;
          }
        }
      }
      if (!found) {  // Only do view detect if we havne't done it before
        do_detect(private_prefixs, '#id_sreg-views_0');
        do_detect(public_prefixs, '#id_sreg-views_1');
      }
    });

    function set_ip_type(ip) {
      if (ip.indexOf('.') > 0) {
        $('#id_ip_type option[value="4"]').attr('selected', 'selected');
        $('#id_ip_type option[value="6"]').removeAttr('selected');
      } else if (ip.indexOf(':') > 0) {
        $('#id_ip_type option[value="4"]').removeAttr('selected');
        $('#id_ip_type option[value="6"]').attr('selected', 'selected');
      }
    }
  }

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
