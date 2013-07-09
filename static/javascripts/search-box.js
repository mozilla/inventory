$(document).ready(function() {
  // If we are on the search page, don't allow searches in the upper box
  if (window.location.pathname == '/en-US/core/search/') {
    $('#search-box input').css('visibility', 'hidden');
  }
  $('#search-box input').keydown(function(event) {
    if (event.keyCode == 13) {
      window.location = '/en-US/core/search/#q=' + $('#search-box input').val();
      return false;
    }
  });
  var search_cache = {};
  $('#search-box input').autocomplete({
    minLength: 1,
    appendTo: '#search-box-result',
    position: { my: 'right top', at: 'right bottom'},
    source: function(request, response) {
        var term = request.term;
        if (term in search_cache) {
          response(search_cache[term]);
          return;
        }
        $.getJSON('/en-US/core/search/ajax_type_search/',
          {'query': term, 'record_type': 'SYSTEM'},
          function(data, status, xhr) {
            search_cache[term] = data.SYSTEM;
            response(data.SYSTEM);
          });
      },
    select: function(event, ui) {
      window.location = '/en-US/systems/show/' + ui.item.pk + '/';
      return false;
    },
    focus: function(event, ui) {
      return false;
    }
  });
});
