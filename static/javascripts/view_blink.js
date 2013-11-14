function view_blink_init(private_id, public_id, callback) {
    /*
     * private_id - The dom id of the private view checkbox
     * public_id - The dom id of the public view checkbox
     * callback - A callback called after the blink class is added or removed. If the
     *      class was removed 'false' is passed to the function. If the class was added
     *      'true' is passed to the function.
     */
    detect_no_views = function () {
        if (!($(private_id).prop('checked') || $(public_id).prop('checked'))) {
            $(private_id).parent('label').addClass('blink');
            $(public_id).parent('label').addClass('blink');
            if (callback) {
                callback(true);
            }
        } else {
            $(private_id).parent('label').removeClass('blink');
            $(public_id).parent('label').removeClass('blink');
            if (callback) {
                callback(false);
            }
        }
    };
    $(private_id).change(function(){
        detect_no_views();
    });
    $(public_id).change(function(){
        detect_no_views();
    });
}
