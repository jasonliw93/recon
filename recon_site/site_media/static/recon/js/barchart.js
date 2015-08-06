(function($) {
	$.fn.barChart = function(options, data) {

		var settings = $.extend({
			width: 800,
			height: 600,
			color: "#0099FF",
            		ylabel: "",
			tooltip_data_name: "",
			tooltip_title: "",
        }, options);

		var xs = ['x'];
		var ys = [settings.tooltip_data_name];
		xs = xs.concat(data.x);
		ys = ys.concat(data.y);

		return c3.generate({
						size: {
							width: settings.width,
							height: settings.height
						},
						bindto: this.selector,
						color: { pattern: [settings.color] },
						data: {
							x: 'x',
							columns: [xs, ys],
							type: 'bar',
						},
						axis : {
							x : { type: 'categorized' },
							y: {
								label: {
									text: settings.ylabel,
									position: 'outer-middle',
								},
							},
						},
						legend: { show: false },
						tooltip: {
							format: {
								title: function (d) { return settings.tooltip_title + xs[d + 1]; },
								value: function (value, ratio, id) { return value; }
							}
						}
					});
	};
})(jQuery);
