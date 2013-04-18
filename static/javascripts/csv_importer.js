$(document).ready(function () {
    alert("This importer is still being tested. Try running your import on https://inventory-dev2.allizom.org/csv/ to confirm things are working before running the import in production.");
    $("#clear-csv-data").click(function() {
        console.log("clearing");
        $('#csv-data').val('');
    });

    $("#csv-form").submit(function( event ) {
        $('#csv-results').empty();
        $.ajax({
            type: "POST",
            url: "/en-US/csv/ajax_csv_importer/",
            data: $('#csv-form').serialize(),
            success: function (data) {
                console.log('data')
                $('#csv-results').append(data);
            },
            error: function (e) {
            //error: function (xhr, ajaxOptions, thrownError) {
                //alert(xhr.status);
                //alert(thrownError);
                console.log(e)
                var newDoc = document.open("text/html", "replace");
                newDoc.write(e.responseText);
                newDoc.close();
            }
        });
        return false;
    });
});
