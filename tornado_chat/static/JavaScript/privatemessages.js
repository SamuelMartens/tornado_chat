

// Function get the name of some option in cookie and return in value or null if
//value does not exist
function getCookie(name) {
    var cookieValue=null;
    if (document.cookie && document.cookie!=''){
        var cookie = document.cookie.split(';');
        for (var i=0; i< cookie.length; i++){
            var cookie=jQuery.trim(cookie[i]);
            // Does this cookie name what we want?
            if (cookie.substring(0, name.length + 1)==(name + '=')){
                 //Substring extract a part of string in current diapason
                cookieValue = decodeURIComponent (cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
 }


// Function set key and value in cookie
function setCookie(key, value) {
    document.cookie = escape(key) + '=' + escape(value);
}


//Function get the number and the set of endings for string of this number
// it return the right ending for this number string
function getNumEnding( iNumber, aEndings) {
    var sEnding, i;
    iNumber = iNumber % 100;
    if (iNumber>=11 && iNumber<=19) {
        sEnding = aEndings[2];
    }
    else {
        i = iNumber % 10;
        switch(i){
            case (1): sEnding = aEndings[0]; break;
            // Cases when i == 2 or 3 will the same as if i == 4
            case (2):
            case (3):
            case (4): sEnding = aEndings[1]; break;
            default: sEnding = aEndings[2];
        }
    }
    return sEnding;
}

var timezone = getCookie('timezone');

if (timezone == null) {
    setCookie('timezone', jstz.determine().name());
}

function activate_chat( thread_id, user_name, number_of_messages){
    $("div.chat form.message_form div.compose textarea").focus();


    //Function scroll chat window to the top
    function scroll_chat_window() {
        $("div.chat div.conversation").scrollTop($("div.chat div.conversation")[0].scrollHeight);
    }

    scroll_chat_window();

    var ws;

    function start_chat_ws() {
        //Opening of WebSocket connection
        ws = new WebSocket("ws://127.0.0.1:8888/"+thread_id+"/");
        //Collback on getting data on this websocket
        ws.onmessage = function(event) {
            // JSON.parse converst JSON text into JavaScript onject
            var message_data = JSON.parse(event.data);
            // timestamp get the number of milliseconds since January 1, 1970
            var date = new Date(message_data.timestamp/1000);
            // $.map gets an array and work with in with callback function and then return new array
            var time = $.map([date.getHours(), date.getMinutes(), date.getSeconds()], function(val, i) {
                return (val<10) ? '0'+val : val;
            });
            // Adding of new message in chat window
            $("div.chat div.conversation").append('<div class="message"><p class="author ' + ((message_data.sender == user_name) ? 'we'
            : 'partner') + '"><span class="datetime">' + time[0] +':' + time[1] + ':' + time[2] + '</span> ' + message_data.sender + ':</p><p class="message">' +
            message_data.text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g, '<br />') + '</p></div>');

            scroll_chat_window();
            number_of_messages['total']++;
            if (message_data.sender == user_name) {
                number_of_messages['sent']++;
            }
            else {
                number_of_messages['received']++;
            }
            // $().html method change all content of choosen element
            $("div.chat p.messages").html('<span class="total">' + number_of_messages["total"] + '</span>' + getNumEnding(number_of_messages['total'],
            ['сообщение','сообщения','сообщений']) + ' (<span class="received">' + number_of_messages['received'] + '</span> получено, <span class="sent">' +
            number_of_messages['sent'] + '</span> отправлено)');

        };

        //Try to reconnect in the event of closing during the 5 seconds
        ws.onclose = fuction (){
            setTimeout(function() {start_chat_ws()}, 5000);
        };

    }

    // Are the webSocket allowed?
    if ("WebSocket" in window) {
        start_chat_ws();
    }
    else {
        $("form.message_form").html('<div class="outdated_browser_message"><p><em>Ой!</em> Вы используете устаревший браузер.' +
      'Пожалуйста, установите любой из современных:</p><ul><li>Для <em>Android</em>: <a href="http://www.mozilla.org/ru/mobile/">Firefox</a>,' +
      '<a href="http://www.google.com/intl/en/chrome/browser/mobile/android.html">Google Chrome</a>, <a href="https://play.google.com/store/apps/details?id=com.opera.browser">' +
      'Opera Mobile</a></li><li>Для <em>Linux</em>, <em>Mac OS X</em> и <em>Windows</em>: <a href="http://www.mozilla.org/ru/firefox/fx/">Firefox</a>, <a href="https://www.google.com/' +
      'intl/ru/chrome/browser/">Google Chrome</a>, <a href="http://ru.opera.com/browser/download/">Opera</a></li></ul></div>');

        return false;
    }
    //Function send message through the web socket
    function send_message() {
        var textarea = $("textarea#message_textarea");
        if (textarea.val() == ''){
            return false;
        }
        //Are the web scoket connection open?
        if (ws.readyState !=WebSocket.OPEN) {
            return false
        }

        ws.send(textarea.val());
        textarea.val('');
    }

    $("form.message_form div.send button").click(send_message);

    //Ctrt + Enter message send
    $("textarea#message_textarea").keydown( function (e){
        if (e.ctrlKey && e.keyCode == 13) {
            send_message();
        }
    });

}