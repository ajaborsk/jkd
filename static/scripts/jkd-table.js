
class JkdTable {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;
        var self = this;
        
        $("#" + this.prefix + "-table").tabulator({layout:"fitColumns", columns:cols});

    }

    $("#" + this.prefix + "-update").click(function (evt) {
        self.update(self);
    });


//    $("#" + this.prefix + "-duration").text(self.duration + " s");

    self.jkd_env.on_connect[self.prefix] = {'cb':self.update, 'client':self};
    //self.update();
//#;

    update(client)
     {
      var self = client;
      var args = {};

      self.jkd_env.get(self.data_addr,
            args,
            function (msg, client) {
                //self.data = msg.reply;
            },
            null);
     }

}

