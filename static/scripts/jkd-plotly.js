class JkdPlotlyChart {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;

        var self = this;

        // The chart
        Plotly.newPlot(this.prefix + "-chart", [], {}, {displaylogo: false});

        self.jkd_env.on_connect[self.prefix] = {'cb':self.connect, 'client':self};

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
            },
            null);
     }

    connect(client) {
        var self = client;
        var args = {};
        console.log('plotly: Connection asked...');
        self.lcid = self.jkd_env.query(
            self.data_addr,
            args,
            function (msg, client) {
                self = client;
                console.log('plotly: response received !', msg);
                if ('layout' in msg.reply) {
                    //self.chart.options = Object.assign({}, msg.reply.options);
                    var layout = msg.reply.layout;
                    console.log(layout);
                    Plotly.relayout(self.prefix + "-chart", layout);
                }
                if ('data' in msg.reply)
                 {
                    console.log('plotly: data received !', msg.reply.data);
                    var data = msg.reply.data;
                    console.log(data);
                    Plotly.deleteTraces(self.prefix + "-chart", Array.apply(null, Array(document.getElementById(self.prefix + "-chart").data.length)).map(function (_, i) {return i;}));
                    Plotly.addTraces(self.prefix + "-chart", data);
                 }
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


