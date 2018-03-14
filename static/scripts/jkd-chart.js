
class JkdHistoryChart {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;


        this.length = 3600; // in seconds
        this.start_date = null; // computed from end_date and length
        this.end_date = null; // default => Date.now()

        var ctx = $('#'+ this.prefix + '-canvas');
        var self = this;

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: '# of Votes',
                    data: [12, 19, 3, 5, 2, 3],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(255, 206, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                        'rgba(255, 159, 64, 0.2)'
                    ],
                    borderColor: [
                        'rgba(255,99,132,1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    xAxes:[{
                        minRotation:45,
                        type: 'time',
                        time:{
                            displayFormats:{
                                millisecond:'HH:mm:ss.S',
                                second:'HH:mm:ss',
                                minut:'HH:mm',
                            }
                        }
                    }],
                    yAxes: [{
                        ticks: {
                            //beginAtZero:true
                        }
                    }]
                },
                zoom:{
                    enabled:true,
                    mode:'y',
                },
                pan:{
                    enabled:true,
                    mode:'y',
                },
            },
        });

    $("#" + this.prefix + "-update").click(function (evt) {
        self.jkd_env.get(self.data_addr,
            {'after':Date.now() / 1000 - 3600 * 3},
            function (msg, client) {
                self.chart.data = msg.reply;
                self.chart.update();
            },
            null);
    });

    $("#" + this.prefix + "-zreset").click(function (evt) {
        self.chart.resetZoom();
    });

    };

    addData(label, data) {
        this.chart.data.labels.push(label);
        this.chart.data.datasets.forEach((dataset) => {
            dataset.data.push(data);
        });
        //this.chart.update(0);
    }

    removeData() {
        this.chart.data.labels.shift();
        this.chart.data.datasets.forEach((dataset) => {
            dataset.data.shift();
        });
        //this.chart.update(0);
    }
}


function addData(chart, label, data) {
    chart.data.labels.push(label);
    chart.data.datasets.forEach((dataset) => {
        dataset.data.push(data);
    });
    chart.update(0);
}

function removeData(chart) {
    chart.data.labels.shift();
    chart.data.datasets.forEach((dataset) => {
        dataset.data.shift();
    });
    //chart.update(0);
}

