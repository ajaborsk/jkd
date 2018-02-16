class JkdEnv
 {
  constructor(ws_url)
   {
    this.next_qid = 1000;
    this.ws_url = ws_url;
   }

   // send a message
   send(msg)
   {
   }

  query(url, query)
   {
    var qid = this.next_qid;
    this.next_qid++;

    var msg = { 'url' : '//demo' + url,
                'src' : '//demo/homepage',
                'qid' : qid,
                'query' : query };
    this.websocket.send(JSON.stringify(msg));
   }

  run()
   {
   // First of all: launch websocket connection
    this.websocket = new WebSocket(this.ws_url);

    this.websocket.onopen = function(evt)
     {
      $("#conn_status").text("Connected");
      //send({"data":"Plikdf 1"});
     };

  // Message handling
    this.websocket.onmessage = function(evt)
     {
      msg = JSON.parse(evt.data);
      if (msg.qid == 'q1')
       {
        $("#result1").text("Response : " + JSON.stringify(msg));
       }
      else if (msg.qid == 'q2')
       {
        $("#result2").text("Response : " + JSON.stringify(msg));
       }
      else
       {
        $("#test1").text("Response : " + JSON.stringify(msg));
       }
     };

    this.websocket.onclose = function(evt)
     {
      $("#conn_status").text("Unconnected");
     };

//TODO:
// Error handling
//  websocket.onerror = function(evt) { onError(evt) };
   }
 }
