$(document).ready(function () {
    alert("FYI: You may run your import on https://inventory-dev.allizom.org/csv/ to confirm things are working before running an import on production.");
    $("#clear-csv-data").click(function() {
        console.log("clearing");
        $('#csv-data').val('');
    });

    $("#csv-form").submit(function( event ) {
        $('#id_waiting').css('display', 'block');
        $('#csv-results').empty();
        $.ajax({
            type: "POST",
            url: "/en-US/csv/ajax_csv_importer/",
            data: $('#csv-form').serialize(),
            success: function (data) {
                $('#id_waiting').css('display', 'none');
                $('#csv-results').append(data);
            },
            error: function (e) {
                $('#id_waiting').css('display', 'none');
                $('#csv-results').append(e.responseText);
            }
        });
        return false;
    });
});
