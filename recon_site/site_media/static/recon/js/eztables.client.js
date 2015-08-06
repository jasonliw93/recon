(function($, Django, Table){

    "use strict";

    $(function(){
        $('#browser-table').dataTable({
            "bPaginate": true,
            "sPaginationType": "bootstrap",
            "bScrollCollapse": true,
            "fnRowCallback": Table.colorRow
        });
    });

}(window.jQuery, window.Django, window.Table));