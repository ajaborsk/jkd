class JkdEntry {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;
        var self = this;

        $("#" + this.prefix + "-send").click(function (evt) {
            //TODO
        });

        $("#" + this.prefix + "-enter").click(function (evt) {
            //TODO
        });

        $("#" + this.prefix + "-leave").click(function (evt) {
            //TODO
        });

        self.jkd_env.on_connect[self.prefix] ={'cb':self.update, 'client':self};
    };

    update(client)
     {
      var self = client;
      var args = {};

      //TODO

      self.jkd_env.get(self.data_addr,
            args,
            function (msg, client) {
                //TODO...
            },
            null);
      //$("#" + self.prefix + "-duration").text(self.duration + " s");
     }
}


