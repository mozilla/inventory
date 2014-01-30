
function chosen_init(ctx){
  /*
   * Params:
   *    hints - When chosen_init is called, use the elements here to see if we can't
   *        guess which vlan/network a user is trying to create a record in. We can
   *        do this by looking at the <vlan>.<dc>.mozilla.<tld> pattern.
   *    dialog_div_id - The div that will contain the drop downs
   *    reset_button_id - The reset button id that will restart the entire process
   *    display_range_id - The div where range data will be displayed to the user
   *    find_related_url - The API endpoint for calculating new states
   *    reset_callback - A function that is called after a reset happens
   *    found_ip_callback - A function that is called if an ip is found
   */

  /* Helpers */

  function build_select_state(options, state_getter){
      var pks = [];
      options.each(function(i, option){
          if (state_getter){
            pks.push(state_getter(option));
          } else {
            if($(option).val()){
              pks.push(parseInt($(option).val(), 'base-ten'));
            }
          }
      });
      return pks;
  }

  function insert_options(select_id, values_and_labels){
    var select_el = $(select_id);
    $.each(values_and_labels, function(key, o) {
      if (o.disabled) {
        option = $("<option disabled></option>");
      } else {
        option = $("<option></option>");
      }
      console.log("inserted");
      select_el.append(
        option
          .attr("value", o.value)
          .attr("label", o.label)
          .attr('class', 'choice')
          .text(o.label)
      );
    });
    $(select_id).trigger("chosen:updated");
  }


  function gather_range_info(start, end, callback) {
    $.get("/core/range/usage_text/",
      {
        start: start,
        end: end,
        format: 'human_readable'
      },
      function(resp) {
        console.log(resp);
        var data = $.parseJSON(resp);
        console.log(data);
        if (!data.success) {
            alert("There was an error. Please report it: " + data.error_messages);
            return {};
        } else if (!data.unused) {
            callback({
              free_ip: undefined,
              percent_used: '100%'
            });
        } else {
            var percent_used = (data.used / (data.unused + data.used)).toFixed(2) + '%';
            console.log(percent_used);
            console.log(data);
            percent_used = percent_used.replace(/^0.(0|)/, '');
            callback({
              free_ip: data.free_ranges[0][0],
              percent_used: percent_used
            });
        }
      }).error(function (data) {
        console.log(data);
      });
  }

  function display_ranges(ranges){
    $.each(ranges, function (i, range){

      $('#choose-ip-display-ranges-area').css('height', '100%');
      $(ctx.display_range_id).append(
        $('<a></a>').attr('class', 'range-choice').html(
          $('<div></div>').attr('class', 'range').html(
            $('<span></span>').attr('class', 'range-info').text(
              range.start + ' - ' + range.end + '  (' + range.rtype + ')'
            ).data('start', range.start).data('end', range.end).data('name-fragment', range.name_fragment).append(
              $('<span></span>').attr('class', 'extra-text')
            )
          ).click(
            function (){
              // What to do when the user clicks on a range
              var that = this;
              var start = $(that).find('.range-info').data('start');
              var end = $(that).find('.range-info').data('end');
              var name_fragment = $(this).find('.range-info').data('name-fragment');
              console.log(start + ' - ' + end);
              gather_range_info(start, end, function (range_info){
                console.log(range_info);

                $('.range').each(function(i, el){
                  $(el).css('background-color', '#D8D8D8');
                  $(el).css('border-width', '1px');
                  $(el).css('font-weight', 'normal');
                });

                $(that).css('transition', 'border-width 0.5s linear 0s');
                $(that).css('border-width', '3px');

                $(that).css('transition', 'font-weight 0.5s linear 0s');
                $(that).css('font-weight', 'bold');

                if (typeof range_info.free_ip == 'undefined'){
                  $(that).css('transition', 'background-color 0.5s linear 0s');
                  $(that).css('background-color', 'red');
                  $(that).find('span .extra-text').text(
                    ' NO FREE IPS'
                  );
                } else {
                  $(that).find('span .extra-text').text(
                    ' ' + range_info.percent_used + ' addresses are used.'
                  );
                  $(that).css('transition', 'background-color 0.2s linear 0s');
                  $(that).css('background-color', '#00CC33');
                }
                ctx.found_ip_callback(range_info, name_fragment);
              });
            }
          )
        )
      );
    });
  }

  /* Code starts here */

  var config = {
      '.chosen-select'           : {},
      '.chosen-select-deselect'  : {allow_single_deselect:true},
      '.chosen-select-no-single' : {disable_search_threshold:10},
      '.chosen-select-no-results': {no_results_text:'Oops, nothing found!'},
      '.chosen-select-width'     : {width:"95%"}
  };

  for (var selector in config) {
      $(selector).chosen(config[selector]);
  }

  var initial_state = (function (){
    function state_getter(option){
        return {'value': $(option).val(), 'label': $(option).text()};
    }
    return {
      sites: build_select_state($('#choose-site .choice'), state_getter),
      networks: build_select_state($('#choose-network .choice'), state_getter),
      vlans: build_select_state($('#choose-vlan .choice'), state_getter)
    };
  })();

  $(ctx.reset_button_id).click(function (){
      $("#choose-network option").remove();
      $("#choose-site option").remove();
      $("#choose-vlan option").remove();
      insert_options('#choose-network', initial_state.networks);
      insert_options('#choose-site', initial_state.sites);
      insert_options('#choose-vlan', initial_state.vlans);

      $('#choose-ip-display-ranges-area').css('transition', 'height 1s linear 0s');
      $('#choose-ip-display-ranges-area').css('height', '0%');
      $('#choose-ip-display-ranges-area').empty();

      $('#choose-ip-errors').empty();

      ctx.reset_callback();
  });

  $(".chosen-select").chosen().change(function (el){
      var choice_option = $(el.target);
      var choice_type = $(el.target).data('choice-type');
      var choice_pk = $(el.target).find('option:selected').val();
      process_current_state(choice_option, choice_type, choice_pk);
  });

  function process_current_state(choice_option, choice_type, choice_pk, callback){
    var state = {
        choice: [choice_type, choice_pk],
        sites: build_select_state($('#choose-site .choice')),
        networks: build_select_state($('#choose-network .choice')),
        vlans: build_select_state($('#choose-vlan .choice'))
    };
    console.log("state: ");
    console.log(JSON.stringify(state));
    $.ajax({
      url: ctx.find_related_url,
      type: "POST",
      data: JSON.stringify(state),
      success: function(result){
        console.log("results: ");
        console.log(result);
        var new_state = $.parseJSON(result);

        function replace_options(select_id, values_and_labels, choice_option){
          var select_el = $(select_id);
          if(select_id == '#' + choice_option.attr('id')){
            $(select_id + " option:not(selected)").remove();
          } else if (values_and_labels.length == 1) {
            $(select_id + " option[label='']").remove();
            $(select_id + " option:not(selected)").remove();
          } else {
            $(select_id + " option:gt(0)").remove();
          }
          insert_options(select_id, values_and_labels);
        }

        replace_options('#choose-network', new_state.networks, choice_option);
        replace_options('#choose-site', new_state.sites, choice_option);
        replace_options('#choose-vlan', new_state.vlans, choice_option);
        if (new_state.ranges){
          if($('#choose-network').find('option:gt(0)').first()){
            // This is okay to do because the server will only return range
            // options when there is exactly one network.
            $('#choose-network').find('option:gt(0)').first().prop('selected', true);
            $('#choose-network').trigger("chosen:updated");
          }
          console.log("Ranges: " + new_state.ranges);
          display_ranges(new_state.ranges);
        } else if (!new_state.networks.length) {
          // The user has struck out and there are no options for them. Tell
          // them to reset the form.
          $('#choose-ip-errors').html(
            '<p>Oh no! There are no networks meeting your criteria. Reset the form and try again. </p>' +
            '<p>Contact #netops if you want more networks</p>'
          );
        }
        if (callback) {
          console.log("Callback supplied");
          console.log(callback);
          callback();
        } else {
          console.log("No callback supplied");
        }
      },
      error: function(e){
        var newDoc = document.open("text/html", "replace");
        newDoc.write(e.responseText);
        newDoc.close();
      }

    });
  }

  function truncate_options(select_id){
    $(select_id + " option:not(:selected)").remove();
  }

  /*
   * Do this once. Look at the hints and set sites and vlans if we can.
   * Strategy:
   *   * Look at each label, starting from left most, and see if we can find a vlan with a matching name.
   *   * If we do find a matching vlan, take everything to the right of that label
   *   * Strip the two right most labels off, search for a site with the remaining string
   *
   *   host1.not-a-vlan.vlan3.dc1.mozilla.com
   *    N       N        Y       (N=not a vlan, Y=a vlan)
   *                         |---------------|
   *                         |---| (strip the two right labels off)
   *                         dc1 <--- look for a site with this name
   */
  $(ctx.hints).each(function (i, hint_location) {
      function parse_hints(labels) {
        var site;
        var remainder;
        var search = "";
        var j;
        var i;
        for (i = labels.length; i >= 0; i--) {
          if (site) {
            break;
          }
          for (j=i; j >= 0; j--) {
            search = labels.slice(j, i).join('.');
            if ($('#choose-site option[label="' + search + '"]').val()) {
              site = $('#choose-site option[label="' + search + '"]');
              remainder = labels.slice(0, j);
            }
          }
        }

        var vlans;
        var vlan_suffix = "";
        if (typeof(remainder) === "undefined") {
          return {'site': site, 'vlans': vlans};
        }
        for (i=remainder.length; i >= 0; i--) {
          if (vlans) {
             break;
          }
          for (j=i; j >= 0; j--) {
            search = remainder.slice(j, i).join('.') + vlan_suffix;
            console.log("Searching for vlan: " + search);
            if ($('#choose-vlan option[label^="' + search + ':"]').val()) {
              vlans = $('#choose-vlan option[label^="' + search + ':"]');
              if (vlans.length == 1){
                  vlan_suffix = '.' + vlans.attr('label').replace(/:\d+$/, '');
              } else {
                  break;
              }
            }
          }
        }
        return {'site': site, 'vlans': vlans};
      }

      // Only call change once if there is a change.
      function update_site(callback) {
        var choice_option = $('#choose-site');
        var choice_type = 'site';
        var choice_pk = choice_option.find('option:selected').val();
        console.log("Update site with: " + choice_type + " " + choice_pk);
        console.log(callback);
        process_current_state(choice_option, choice_type, choice_pk, callback);
      }

      function update_vlan(callback) {
        var choice_option = $('#choose-vlan');
        var choice_type = 'vlan';
        var choice_pk = choice_option.find('option:selected').val();
        console.log("Update vlan with: " + choice_type + " " + choice_pk);
        process_current_state(choice_option, choice_type, choice_pk, callback);
      }

      function alert_more_action_needed(option_selector, chosen_selector){
        /*
         * If we auto assign some stuff and the user still needs to select
         * objects from the drop down, paint the drop down orange.
         */
        function do_animation(el) {
          // For some reason I can't get the style of this element with jquery, so I'm hard coding it. I
          // hate hard coding things but I can figure this out...
          el.css('transition', 'background 0.2s linear');
          el.css('background', 'orange');
          setTimeout(function (){
              console.log("called");
              el.css('transition', 'background 0.5s linear');
              el.css('background', 'white');
          }, 200);
          //el.attr('style', 'transition: background 2s linear 2s;' + 'background: white');
        }
        if ($(option_selector).length > 1) {
          do_animation($(chosen_selector));
        }
      }

      console.log("Looking for hints");
      var hint = $(hint_location).val();
      if (!hint) {
        console.log("No hint for " + hint);
        return;
      }

      var labels = hint.split('.');

      if (!labels.length) {
         console.log("labels has no length");
         return;
      }
      var h = parse_hints(labels);
      var found_vlan = false;
      var found_site = false;

      // Trigger events based on the things we parsed from the hints
      if (typeof h.vlans != "undefined" && h.vlans.length === 1) {
        found_vlan = true;
        h.vlans.prop('selected', true);
        truncate_options('#choose-vlan');
        $('#choose-vlan').trigger("chosen:updated");
      } else if (typeof h.vlans != "undefined" && h.vlans.length > 1) {
        var first_option = $('#choose-vlan').find(':first-child');
        $("#choose-vlan option:gt(0)").remove();
        $('#choose-vlan').append(h.vlans);
        $('#choose-vlan').trigger("chosen:updated");
      } else {
        console.log("No vlans found.");
      }

      if (typeof h.site != "undefined" && h.site.length) {
        found_site = true;
        h.site.attr('selected', 'selected');
        truncate_options('#choose-site');
      } else {
        console.log("No site found");
      }

      if (found_site) {
        update_site(function () {
          var choice_option = $('#choose-vlan');
          var choice_type = 'vlan';
          var choice_pk = choice_option.find('option:selected').val();
          if (choice_pk || found_vlan) {
            console.log("Update vlan with: " + choice_type + " " + choice_pk);
            process_current_state(choice_option, choice_type, choice_pk, function (){
              alert_more_action_needed('#choose-vlan option', '#choose_vlan_chosen > a');
            });
          }
        });
      } else if (found_vlan) {
        update_vlan(function (){
          alert_more_action_needed('#choose-vlan option', '#choose_vlan_chosen > a');
        });
      }
  });
}
