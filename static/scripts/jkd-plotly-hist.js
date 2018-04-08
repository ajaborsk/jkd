class JkdPlotlyHistChart {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;


        this.duration = 3600 * 3; // in seconds
        this.start_date = null; // computed from end_date and length
        this.end_date = null; // default => Date.now()

        var self = this;

        // The chart
        Plotly.newPlot(this.prefix + "-chart", [], {}, {displaylogo: false});

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

//        self.jkd_env.on_connect[self.prefix] = {'cb':self.update, 'client':self};
        self.jkd_env.on_connect[self.prefix] = {'cb':self.connect, 'client':self};

        self.jkd_env.on_disconnect[self.prefix] = {'cb':function(client){
            self=client;
            $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-close");
            $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-refresh");
            $("#" + self.prefix + "-update > span.ui-icon").addClass("ui-icon-cancel");
            $("#" + self.prefix + "-update > span.ui-text").text("Disconn.");
            }, 'client':self};

        self.jkd_env.on_resize[self.prefix] = {'cb':function(self) {
                Plotly.Plots.resize(self.prefix + "-chart");
            }, 'client':self};
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

      if (!('before' in args)) {
          args['after'] = - self.duration;
      }

      $("#" + this.prefix + "-update > span.ui-icon").removeClass("ui-icon-refresh");
      $("#" + this.prefix + "-update > span.ui-icon").removeClass("ui-icon-cancel");
      $("#" + this.prefix + "-update > span.ui-icon").addClass("ui-icon-close");
      $("#" + this.prefix + "-update > span.ui-text").text("Cancel");

      self.jkd_env.get(self.data_addr,
            args,
            function (msg, client) {
                var data = [];
                var layout = {};
                if ('layout' in msg.reply) {
                    //self.chart.options = Object.assign({}, msg.reply.options);
                    layout = msg.reply.layout;
                    console.log(layout);
                    Plotly.relayout(self.prefix + "-chart", layout);
                }
                if ('data' in msg.reply) {
                    //self.chart.data = Object.assign({}, msg.reply.data);
                    data = msg.reply.data;
                    console.log(data);
                    Plotly.deleteTraces(self.prefix + "-chart", Array.apply(null, Array(document.getElementById(self.prefix + "-chart").data.length)).map(function (_, i) {return i;}));
                    Plotly.addTraces(self.prefix + "-chart", data);
                }
               //Plotly.update(self.prefix + "-chart", data, layout);
               $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-close");
               $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-cancel");
               $("#" + self.prefix + "-update > span.ui-icon").addClass("ui-icon-refresh");
               $("#" + self.prefix + "-update > span.ui-text").text("Refresh");
            },
            null);
      $("#" + self.prefix + "-duration").text(self.duration + " s");

     }

    chart_update(self, obj) {
        var data = [];
        var layout = {};
        if ('layout' in obj) {
            //self.chart.options = Object.assign({}, msg.reply.options);
            layout = obj.layout;
            console.log(layout);
            Plotly.relayout(self.prefix + "-chart", layout);
        }
        if ('data' in obj) {
            //self.chart.data = Object.assign({}, msg.reply.data);
            data = obj.data;
            console.log(data);
            Plotly.deleteTraces(self.prefix + "-chart", Array.apply(null, Array(document.getElementById(self.prefix + "-chart").data.length)).map(function (_, i) {return i;}));
            Plotly.addTraces(self.prefix + "-chart", data);
        }
    }

    connect(client) {
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

        if (!('before' in args)) {
            args['after'] = - self.duration;
        }

        console.log('plotly: Connection asked...', args);
        self.lcid = self.jkd_env.query(
            self.data_addr,
            args,
            function (msg, client) {
                self = client;
                console.log('plotly: response received !', msg);
                self.chart_update(self, msg.reply);
                //if ('data' in msg.reply)
                 //{
                    //console.log('plotly: data received !', msg.reply.data);
                 //}
            },
            client
        );
    }
    addData(label, data) {
        //this.chart.data.labels.push(label);
        //this.chart.data.datasets.forEach((dataset) => {
        //    dataset.data.push(data);
        //});
        //this.chart.update(0);
    }

    removeData() {
        //this.chart.data.labels.shift();
        //this.chart.data.datasets.forEach((dataset) => {
        //    dataset.data.shift();
        //});
        //this.chart.update(0);
    }
}


