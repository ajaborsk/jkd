
class JkdDynTable {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;
        var self = this;

        $("#" + this.prefix + "-container").tabulator({rowClick:partial(self.row_click, self), layout:"fitColumns", columns:["a"]});

        $("#" + this.prefix + "-update").click(function (evt) {
            self.update(self);
        });

        //$("#" + self.prefix + "-container").tabulator({rowClick:self.row_click});

        self.jkd_env.on_connect[self.prefix] = {'cb':self.connect, 'client':self};
    };

    row_click(self, event, row) {
        console.log('Row clicked', event, row);
        self.jkd_env.put("/mp0/input",{'value':"test"});
    }

    col_click(self, event, col) {
        console.log('Col clicked', event, col);
        self.jkd_env.put("/mp0/input",{'value':"test"});
    }

    connect(client) {
        var self = client;
        var args = {};
        console.log('DynTable: Connection asked...');
        self.lcid = self.jkd_env.query(
            self.data_addr,
            args,
            function (msg, client) {
                self = client;
                console.log('DynTable: response received !', msg);
                if ('columns' in msg.reply)
                 {
                  $("#" + self.prefix + "-container").tabulator("destroy");
                  msg.reply.columns[0].headerClick = partial(self.col_click, self);
                  $("#" + self.prefix + "-container").tabulator({
                      rowClick:partial(self.row_click, self),
                      layout:"fitColumns",
                      columns:msg.reply.columns
                  });
                  //$("#" + self.prefix + "-container").tabulator({});
                 }
                if ('data' in msg.reply)
                 {
                  $("#" + self.prefix + "-container").tabulator("setData", msg.reply.data)
                 }
            },
            client
        );
    }
}

