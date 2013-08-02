function insert_search(query, target_div){
  return function (){
    $.get('/core/search/search_ajax/',
        {'search': 'zone=:' + query},
        function update_results(data){
          target_div.html(data);
          target_div.css('display', 'block');
        }).error(function(e) {
          var newDoc = document.open("text/html", "replace");
          newDoc.write(e.responseText);
          newDoc.close();
        });
  };
}

function search_watcher(possible_input_ids, target_div, callback){
  function calc_search(){
    return possible_input_ids.reduce(function(search, el) {
        if($(el) && $(el).val()) {
          if (el === '#id_ip_str' ) {
            if (is_valid_ip($(el).val())) {
              if (search !== '') {
                search = search + ' OR ';
              }
              return search + 'ip=:' + $(el).val();
            } else {
              return search;
            }
          } else {
            if (search !== '') {
              search = search + ' OR ';
            }
            return search + '/^' + $(el).val() + '$';
          }
        }
        return search;
    }, '');
  }

  function highlight_results(search){
    /*
     * Find every occurance of text we searched for in the results and highlight it with green.
     */
    callback(search);
    target_div.find('td').each(function (i, td_el){
      $(possible_input_ids).each(function(i, search_el) {
        if($(td_el).html().indexOf($(search_el).val()) != -1){
          $(td_el).html($(td_el).html().replace(
            $(search_el).val(),
            '<span style="background-color: #67ff5f;">' + $(search_el).val() + '</span>'
          ));
        }
      });
    });
  }

  search_watcher_helper(possible_input_ids, calc_search, target_div, highlight_results);
}

function search_watcher_helper(possible_input_ids, calc_search, target_div, callback){
  // First define what we are going to do then put it in a callback loop to watch target_el. When results are found they will be dumped into target_div.

  function insert_search(){
    var search = calc_search();
    $.get('/core/search/search_ajax/',
      {'search': search},
      function update_results(data){
        target_div.html(data);
        target_div.css('display', 'block');
        callback(search);
      }).error(function(e) {
        var newDoc = document.open("text/html", "replace");
        newDoc.write(e.responseText);
        newDoc.close();
    });
  }

  // If there is something already in the target_el, fire off a first search
  var initial_search = calc_search();
  console.log("initial search is :" + initial_search);
  if (initial_search){
    insert_search();
  }

  // A little bit of js to handle the timing of doing search results
  var timerHandle;
  var timeOutInterval = 200; // 2 seconds
  $(possible_input_ids).each(function (i, target_id){
    $(target_id).on('change keypress paste focus textInput input', function(){
      clearTimeout(timerHandle);
      search = calc_search();
      console.log("search is: " + search);
      if (calc_search()){
        timerHandle = setTimeout(insert_search, timeOutInterval);
      } else {
        target_div.css('display', 'none');
      }
    });
  });
}
