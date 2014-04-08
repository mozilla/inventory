$(document).ready(function (){
  $('.chosen-select').chosen();
  $('#do-export').click(function(){
    console.log("selected class: " + $('.export-class').val());
    $('#id_waiting').css('display', 'block');
    $.ajax({
      url: '/en-US/csv/ajax_csv_full_exporter/',
      type: 'GET',
      data: {class_name: $('.export-class').val()},
      success: function (data){
        $('#csv-results').html(data);
        $('#id_waiting').css('display', 'none');
        $('#csv-results').css('display', 'block');
      }
    }).fail(function (data) {
      console.log(data);
      $('#csv-results').html(data.responseText);
      $('#id_waiting').css('display', 'none');
      $('#csv-results').css('display', 'block');
    });
  });
});
