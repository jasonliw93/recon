(function($, hljs){

    "use strict";

    var Table = window.Table = {
        colorRow: function(nRow, aData, iDisplayIndex, iDisplayIndexFull) {
            var field = 'css_grade' in aData;
            switch(aData[field]) {
                case 'A':
                    $(nRow).addClass('success');
                    break;
                case 'C':
                    $(nRow).addClass('info');
                    break;
                case 'X':
                    $(nRow).addClass('error');
                    break;
                default:
                    break;
            }
        }
    };


    $(function() {
        // Render embed code
        $('pre:not([data-url])').each(function(i, el) {
            hljs.highlightBlock(el);
        });

        // Load and render external files
        $('pre[data-url]').each(function(i, el) {
            $.get($(this).data('url'), function(data){
                $(el).text(data);
                hljs.highlightBlock(el);
            }, "text");
        });
    });

    return Table;

}(window.jQuery, window.hljs));
