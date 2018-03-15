
class JkdHistoryChart {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;


        this.duration = 3600; // in seconds
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
                                minut:'HH:mm',
                            }
                        }
                    }],
                    yAxes: [
                      {
                        ticks: {
                            //beginAtZero:true
                        },
                       position:'right',
                      },
                      {
                        id:'temp',
                        scaleLabel:'Temperature (°C)',
                        type:'linear',
                        position:'left',
                      },
                      {
                        id:'voltage',
                        scaleLabel:'Voltage (V)',
                        type:'linear',
                        position:'left',
                      },
                      {
                        id:'intensity',
                        scaleLabel:'Intensity (mA)',
                        type:'linear',
                        position:'left',
                      }
                      ]
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

    self.jkd_env.on_connect[self.prefix] ={'cb':self.update, 'client':self};
    //self.update();
    };

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

      self.jkd_env.get(self.data_addr,
            args,
            function (msg, client) {
                self.chart.data = msg.reply;
                self.chart.update(0);
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

