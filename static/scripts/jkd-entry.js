class JkdEntry {
    constructor(jkd_env, prefix, data_addr) {

        this.jkd_env = jkd_env;
        this.prefix = prefix;
        this.data_addr = data_addr;
        var self = this;

        $("#" + this.prefix + "-send").click(function (evt) {
            //TODO
            console.log(self.prefix+': Add event '+$("#"+self.prefix+"-constraint").val()+'=> '+$("#"+self.prefix+"-constraint-value").val()+' to "'+self.data_addr+'"');
            self.jkd_env.put(self.data_addr, {'value':{'mode':'ponctual', 'constraint':$("#"+self.prefix+"-constraint").val(), 'constraint-value':$("#"+self.prefix+"-constraint-value").val()}}, null, null);
        });

        $("#" + this.prefix + "-enter").click(function (evt) {
            //TODO
            console.log(self.prefix+': Enter event '+$("#"+self.prefix+"-constraint").val()+'=> '+$("#"+self.prefix+"-constraint-value").val()+' to "'+self.data_addr+'"');
            self.jkd_env.put(self.data_addr, {'value':{'mode':'enter', 'constraint':$("#"+self.prefix+"-constraint").val(), 'constraint-value':$("#"+self.prefix+"-constraint-value").val()}}, null, null);
        });

        $("#" + this.prefix + "-leave").click(function (evt) {
            //TODO
            console.log(self.prefix+': Leave event '+$("#"+self.prefix+"-constraint").val()+'=> '+$("#"+self.prefix+"-constraint-value").val()+' to "'+self.data_addr+'"');
            self.jkd_env.put(self.data_addr, {'value':{'mode':'leave', 'constraint':$("#"+self.prefix+"-constraint").val(), 'constraint-value':$("#"+self.prefix+"-constraint-value").val()}}, null, null);
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


