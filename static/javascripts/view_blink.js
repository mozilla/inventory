function view_blink_init(private_id, public_id) {
    detect_no_views = function () {
        if (!($(private_id).prop('checked') || $(public_id).prop('checked'))) {
            $(private_id).parent('label').addClass('blink');
            $(public_id).parent('label').addClass('blink');
        } else {
            $(private_id).parent('label').removeClass('blink');
            $(public_id).parent('label').removeClass('blink');
        }
    };
    $(private_id).change(function(){
        detect_no_views();
    });
    $(public_id).change(function(){
        detect_no_views();
    });
}
