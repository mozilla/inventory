$(document).ready(function () {
  $('.service-auto-complete').each(function (i, el) {
    console.log("Service auto complete");
    var u = $(el);
    u.autocomplete({
      minLength: 0,
      source: u.data('autocomplete')
    }).focus(function () {
      if (this.value === "") {
        $(this).autocomplete("search");
      }
    });
 });
});
