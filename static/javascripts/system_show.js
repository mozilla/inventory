function display_inpage_search_results(query, results_selector){
    $.get('/en-US/core/search/search_ajax/',
        {
            'format': 'table',
            'search': query + ' AND (!type=:SYSTEM)',
        },
        function (data) {
            if (!data) {
                console.log("no dns data");
            } else {
                $(results_selector).empty();
                $(results_selector).append(data);
            }
        });
}
