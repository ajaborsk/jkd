

function partial(fn) { // `fn` is the original function
    // `args_a` are the arguments (barring `fn`) of the first call.
    var args_a = Array.prototype.slice.call(arguments, 1);

    // Now, we return a new function, with the first set of arguments already applied.
    return function partialApplicator() {
        // `args_b` are the arguments applied at the second call
        var args_b = Array.prototype.slice.call(arguments);

        // Now, concatenate both Arrays and apply them to the original function
        return fn.apply(undefined, args_a.concat(args_b));
    };
}

class JkdEnv
 {
  constructor(appname, ws_url, from)
   {
    this.appname = appname;
    this.next_lcid = 1000;
    this.ws_url = ws_url;
    this.from = from;
    this.channels = {};
    this.on_connect = {};
    this.on_disconnect = {};
   }

   // send a message
   //send(msg)
   //{
   //}

  get(url, args, callback, client)
   {
    var lcid = this.next_lcid;
    this.next_lcid++;

    this.channels[lcid] = {'cb':callback, 'client':client};

//    console.log(typeof(callback));
//    console.log(typeof(this.channels[lcid]['cb']));

    var msg = { 'url'   : '/' + this.appname + url,
                'src'   : '/chuap/homepage', // Unused ??
                'from'  : this.from, // Unused ??
                'lcid'  : lcid,
                'flags' : 'c',
                'method': 'get',
                'policy': 'immediate',
                'args' : args };
    this.websocket.send(JSON.stringify(msg));
    return lcid;
   }

  put(url, args, callback, client)
   {
    var lcid = this.next_lcid;
    this.next_lcid++;

    this.channels[lcid] = {'cb':callback, 'client':client};

//    console.log(typeof(callback));
//    console.log(typeof(this.channels[lcid]['cb']));

    var msg = { 'url'   : '/' + this.appname + url,
                'src'   : '/chuap/homepage', // Unused ??
                'from'  : this.from, // Unused ??
                'lcid'  : lcid,
                'flags' : 'c',
                'method': 'put',
                'policy': 'immediate',
                'args' : args };
    this.websocket.send(JSON.stringify(msg));
    return lcid;
   }

  query(url, args, callback, client)
   {
    var lcid = this.next_lcid;
    this.next_lcid++;

    this.channels[lcid] = {'cb':callback, 'client':client};

//    console.log(typeof(callback));
//    console.log(typeof(this.channels[lcid]['cb']));

    var msg = { 'url'   : '/' + this.appname + url,
                'src'   : '/demo/homepage', // Unused ??
                'from'  : this.from, // Unused ??
                'lcid'  : lcid,
                'flags' : 'c',
                'method': 'get',
                'policy': 'on_update',
                'args'  : args };
    this.websocket.send(JSON.stringify(msg));
    return lcid;
   }

  send_on_channel(lcid, msg)
   {
    msg['lcid'] = lcid;
    this.websocket.send(JSON.stringify(msg));
   }

  onmessage(self, evt)
   {
      var msg = JSON.parse(evt.data);
      if (msg.lcid == 'q1')
       {
        $("#result1").text("Response : " + JSON.stringify(msg));
       }
      else if (msg.lcid == 'q2')
       {
        $("#result2").text("Response : " + JSON.stringify(msg));
       }
      else
       {
        //$("#test1").text("Response : " + JSON.stringify(msg));
        var lcid = msg['lcid'];
        if (self.channels[lcid]['cb'])
         {
          self.channels[lcid]['cb'](msg, self.channels[lcid]['client']);
         }
        if (msg['eoq'] == true)
         {
          delete self.channels[lcid];
         }
       }
   }

  run()
   {
    var self = this;
   // First of all: launch websocket connection
    this.websocket = new WebSocket(this.ws_url);

    this.websocket.onopen = function(evt)
     {
      $("#conn_status").text("Connected");
      //send({"data":"Plikdf 1"});
      var keys = Object.keys(self.on_connect);
      for (var i = 0;i < keys.length ;i++)
       {
        self.on_connect[keys[i]].cb(self.on_connect[keys[i]].client);
       }
     };

    var p1 = partial(this.onmessage, this);

  // Message handling
    this.websocket.onmessage = p1;

    this.websocket.onclose = function(evt)
     {
      $("#conn_status").text("Unconnected");
      var keys = Object.keys(self.on_disconnect);
      for (var i = 0;i < keys.length ;i++)
       {
        self.on_disconnect[keys[i]].cb(self.on_connect[keys[i]].client);
       }
     };

//TODO:
// Error handling
//  websocket.onerror = function(evt) { onError(evt) };
   }
 }
