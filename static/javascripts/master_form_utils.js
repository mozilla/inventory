$(function() {
    String.prototype.startsWith = function(needle)
    {
        return(this.indexOf(needle) == 0);
    };
    if(typeof(String.prototype.strip) === "undefined")
    {
        String.prototype.strip = function()
        {
            return String(this).replace(/^\s+|\s+$/g, '');
        };
    }
    $('#rec_type_select').find(":selected").click();
    String.prototype.format = function() {
        var args = arguments;
        return this.replace(/{(\d+)}/g, function(match, number) {
            return typeof args[number] != 'undefined'
            ? args[number]
            : match
            ;
        });
    };

});
$(document).ready(function (){
});

function make_smart_name_get_domains(element, append){
    $.get('/mozdns/domain/get_all_domains/', function(domains) {
        console.log(domains.sort);
        make_smart_name(element, $.parseJSON(domains), append);
    });
}


function make_smart_name(element, domains, append){
    $(element).autocomplete({
        focus: function(event, ui) {
            // We saved the matching part to ui.item.value
            var name = $(element).val(); // The name the user entered
            if(!append) {
                $(element).attr('value', ui.item.label);
            } else if (ui.item.value !== ''){
                var foo =  name.substring(0,name.lastIndexOf(ui.item.value));
                $(element).attr('value', foo + ui.item.label);
            } else {
                if (name.lastIndexOf('.') == name.length - 1) {
                    $(element).attr('value',  name + ui.item.label);
                } else {
                    $(element).attr('value',  name + '.' + ui.item.label);
                }
            }
            return false;
        },
        select: function(event, ui) {
            return false;
        },
        autoFocus: false,
        source: function (li, callback) {
            labels = li.term.split('.')

            var suggested_domains = [];
            var domain_name = '';
            var search_name = '';
            while (labels) {
                search_name = labels.join('.');
                for (var domain in domains.sort(function(a,b) {return (a.length < b.length) ? 0 : 1; })){
                    domain_name = domains[domain];
                    if (domain_name.startsWith(search_name)){
                        suggested_domains.push({label: domain_name, value: search_name});
                    }
                }
                if (suggested_domains.length === 0){
                    labels.shift();
                } else {
                    return callback(suggested_domains.slice(0, 20)); // The list is too long sometimes
                }
            }
            return callback([]);
        }
    });

}
