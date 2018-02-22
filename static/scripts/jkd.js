

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
  constructor(ws_url, from)
   {
    this.next_lcid = 1000;
    this.ws_url = ws_url;
    this.from = from;
    this.channels = {};
   }

   // send a message
   send(msg)
   {
   }

  query(url, query, callback, client)
   {
    var lcid = this.next_lcid;
    this.next_lcid++;

    this.channels[lcid] = {'cb':callback, 'client':client};

    console.log(typeof(callback));
    console.log(typeof(this.channels[lcid]['cb']));

    var msg = { 'url'   : '/demo' + url,
                'src'   : '/demo/homepage',
                'from'  : this.from,
                'lcid'  : lcid,
                'flags' : 'c',
                'query' : query };
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
        //if (!(self.queries[lcid]['cb'] === undefined))
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
     };

    var p1 = partial(this.onmessage, this);

  // Message handling
    this.websocket.onmessage = p1;

    this.websocket.onclose = function(evt)
     {
      $("#conn_status").text("Unconnected");
     };

//TODO:
// Error handling
//  websocket.onerror = function(evt) { onError(evt) };
   }
 }
