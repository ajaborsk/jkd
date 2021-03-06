Chart.pluginService.register({
    beforeDraw: function (chart, easing) {
        if (chart.config.options.chartArea && chart.config.options.chartArea.backgroundColor) {
            var ctx = chart.chart.ctx;
            var chartArea = chart.chartArea;

            ctx.save();
            ctx.fillStyle = chart.config.options.chartArea.backgroundColor;
            ctx.fillRect(chartArea.left, chartArea.top, chartArea.right - chartArea.left, chartArea.bottom - chartArea.top);
            ctx.restore();
        }
    }
});

class JkdHistoryChart {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;


        this.duration = 36 * 24; // in seconds
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
                tooltips: {
                    intersect:false,
                },
                scales: {
                    xAxes:[{
                        minRotation:45,
                        type: 'time',
                        time:{
                            displayFormats:{
                                millisecond:'HH:mm:ss.S',
                                second:'HH:mm:ss',
                                minute:'DD-MM HH:mm',
                                hour:'DD-MM HH:mm',
                                day:'DD-MM HH:mm',
                                week:'DD-MM-YYYY',
                                month:'MM-YYYY',
                                quarter:'MM-YYYY',
                                year:'YYYY'
                            },
                            tooltipFormat:'DD-MM-YYYY HH:mm:ss.S'
                        }
                    }],
                },
                zoom:{
                    enabled:true,
                    mode:'y',
                },
                pan:{
                    enabled:true,
                    mode:'y',
                },
                chartArea: {
                    backgroundColor: 'rgb(255, 255, 255)'
                }
            },


        });

    $("#" + this.prefix + "-update").click(function (evt) {
        self.update(self);
    });

    $("#" + this.prefix + "-zreset").click(function (evt) {
        self.chart.resetZoom();
    });

    $("#" + this.prefix + "-unzoom").click(function (evt) {
        self.duration *= 2;
        self.update(self);
    });

    $("#" + this.prefix + "-zoom").click(function (evt) {
        self.duration /= 2;
        self.update(self);
    });

    $("#" + this.prefix + "-prev").click(function (evt) {
        if (self.end_date)
         {
          self.end_date -= self.duration / 2;
         }
        else
         {
          self.end_date = Date.now() / 1000 - self.duration / 2;
         }
        self.update(self);
    });

    $("#" + this.prefix + "-next").click(function (evt) {
        if (self.end_date)
         {
          self.end_date += self.duration / 2;
          if (self.end_date > Date.now() / 1000)
           {
            self.end_date = null;
           }
         }
        self.update(self);
    });

//    $("#" + this.prefix + "-duration").text(self.duration + " s");

    $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-close");
    $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-refresh");
    $("#" + self.prefix + "-update > span.ui-icon").addClass("ui-icon-cancel");
    $("#" + self.prefix + "-update > span.ui-text").text("Disconn.");
    self.jkd_env.on_connect[self.prefix] ={'cb':self.update, 'client':self};
    self.jkd_env.on_disconnect[self.prefix] ={'cb':function(client){
        self=client;
        $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-close");
        $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-refresh");
        $("#" + self.prefix + "-update > span.ui-icon").addClass("ui-icon-cancel");
        $("#" + self.prefix + "-update > span.ui-text").text("Disconn.");
        }, 'client':self};
    //self.update();

    self.jkd_env.on_connect[self.prefix] = {'cb':self.connect, 'client':self};

    };

    connect(client) {
        var self = client;
        var args = {};
        console.log('Connection asked...');
        self.lcid = self.jkd_env.query(
            self.data_addr,
            args,
            function (msg, client) {
                self = client;
                console.log('response received !', msg);
                if ('data' in msg.reply)
                 {
                  console.log("data received.");
                 }
            },
            client
        );
    }

        update(client)
     {
      var self = client;
      var args = {};
      var end_date = null;

      if (self.end_date)
       {
        end_date = self.end_date;
        args['before'] = end_date;
       }
      else
       {
        end_date = Date.now()/ 1000;
       }

      if (self.start_date)
       {
        args['after'] = self.start_date;
        self.duration = end_date - self.start_date;
       }
      else
       {
        args['after'] = end_date - self.duration;
       }

      $("#" + this.prefix + "-update > span.ui-icon").removeClass("ui-icon-refresh");
      $("#" + this.prefix + "-update > span.ui-icon").removeClass("ui-icon-cancel");
      $("#" + this.prefix + "-update > span.ui-icon").addClass("ui-icon-close");
      $("#" + this.prefix + "-update > span.ui-text").text("Cancel");

      self.jkd_env.get(self.data_addr,
            args,
            function (msg, client) {
                if ('options' in msg.reply) {
                    self.chart.options = Object.assign({}, msg.reply.options);
                    console.log(self.chart.options);
                }
                if ('data' in msg.reply) {
                    self.chart.data = Object.assign({}, msg.reply.data);
                    console.log(self.chart.data);
                }
               self.chart.update(0);
               $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-close");
               $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-cancel");
               $("#" + self.prefix + "-update > span.ui-icon").addClass("ui-icon-refresh");
               $("#" + self.prefix + "-update > span.ui-text").text("Refresh");
            },
            null);
      $("#" + self.prefix + "-duration").text(self.duration + " s");
     }

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

