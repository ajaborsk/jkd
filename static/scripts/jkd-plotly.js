class JkdPlotlyChart {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;


        this.duration = 36 * 24; // in seconds
        this.start_date = null; // computed from end_date and length
        this.end_date = null; // default => Date.now()

        var self = this;

        // The chart
        Plotly.newPlot(this.prefix + "-chart", [],{});


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
                    console.log(layout);
                }
                if ('data' in msg.reply) {
                    //self.chart.data = Object.assign({}, msg.reply.data);
                    console.log(data);
                }
               Plotly.update(self.prefix + "-chart", data, layout);
               $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-close");
               $("#" + self.prefix + "-update > span.ui-icon").removeClass("ui-icon-cancel");
               $("#" + self.prefix + "-update > span.ui-icon").addClass("ui-icon-refresh");
               $("#" + self.prefix + "-update > span.ui-text").text("Refresh");
            },
            null);
      $("#" + self.prefix + "-duration").text(self.duration + " s");
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


