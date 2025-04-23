$(function() {
    "use strict";

    // ============================================================== 
    // Sales ratio
    // ============================================================== 
    var chart = new Chartist.Line('.sales', {
        labels: [1, 2, 3, 4, 5, 6, 7],
        series: [
            [24.5, 28.3, 42.7, 32, 34.9, 48.6, 40],
            [8.9, 5.8, 21.9, 5.8, 16.5, 6.5, 14.5]
        ]
    }, {
        low: 0,
        high: 48,
        showArea: true,
        fullWidth: true,
        plugins: [
            Chartist.plugins.tooltip()
        ],
        axisY: {
            onlyInteger: true,
            scaleMinSpace: 40,
            offset: 20,
            labelInterpolationFnc: function(value) {
                return (value / 10) + 'k';
            }
        },
    });

    // ============================================================== 
    // Our Visitor
    // ============================================================== 
    function sparklineLogin(data) {
        $('#earnings').sparkline(data, {
            type: 'bar',
            height: '40',
            barWidth: '4',
            width: '100%',
            resize: true,
            barSpacing: '8',
            barColor: '#137eff'
        });
    }

    function fetchTemperaturesAndDisplaySparkline() {
        $.ajax({
            url: './data_get.php', // URL to the PHP script
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                sparklineLogin(data);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error fetching data: ' + textStatus + ', ' + errorThrown);
            }
        });
    }

    $(window).resize(function(e) {
        clearTimeout(sparkResize);
        sparkResize = setTimeout(fetchTemperaturesAndDisplaySparkline, 500);
    });

    // Initial call to fetch and display temperatures
    fetchTemperaturesAndDisplaySparkline();
});
