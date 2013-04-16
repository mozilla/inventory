$(document).ready(function () {
    $("#csv-form").submit(function( event ) {
        console.log("foo");
        console.log( $('#csv-form').serialize() );
        /*
        $.post("/en-US/csv/ajax_csv_importer/", $('#csv-form').serialize(), function (data) {
            console.log('data')
            $('#csv-results').empty();
            $('#csv-results').append('<h3>Results</h3>');
            $('#csv-results').append(data);
        });
        */
        $.ajax({
            type: "POST",
            url: "/en-US/csv/ajax_csv_importer/",
            data: $('#csv-form').serialize(),
            success: function (data) {
                console.log('data')
                $('#csv-results').empty();
                $('#csv-results').append('<h3>Results</h3>');
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

$(document).ajaxError(function(e) {
    console.log(e)
    //var newDoc = document.open("text/html", "replace");
    //newDoc.write(e.responseText);
    //newDoc.close();
});
