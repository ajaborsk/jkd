
class JkdDynTable {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;
        var self = this;
        
        $("#" + this.prefix + "-container").tabulator({layout:"fitColumns", columns:["a"]});

        $("#" + this.prefix + "-update").click(function (evt) {
            self.update(self);
        });

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
                if ('columns' in msg.reply)
                 {
                  $("#" + self.prefix + "-container").tabulator("destroy");
                  $("#" + self.prefix + "-container").tabulator({layout:"fitColumns", columns:msg.reply.columns});
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

