$(document).ready(function () {
  $('.combine-button').click(function (){
    var that = this;
    var bundle = $(this).closest('.sreg-container').find('.bundle-data');
    var a_pk = bundle.data('a-pk');
    var ptr_pk = bundle.data('ptr-pk');
    var system_pk = bundle.data('system-pk');
    $.ajax({
      method: 'POST',
      url: '/' + $('html').attr('lang') + '/core/registration/static/combine/',
      data: { a_pk: a_pk, ptr_pk: ptr_pk, system_pk: system_pk },
    }).done(function (result){
      var data = $.parseJSON(result);
      console.log(result);
      console.log(data);
      if (data.success) {
        console.log(data.redirect_url);
        $(that).closest('.sreg-container').html(
          $('<a></a>').attr('href', data.redirect_url).text('View the new SREG!')
        );
      }
    }).fail(function (result){
    });
  });
});
