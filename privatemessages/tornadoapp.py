#!/usr/bin/python3
import datetime
import json
import time
import urllib.parse

import tornadoredis
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.httpclient


from django.conf import settings
from django.utils.importlib import import_module


session_engine=import_module(settings.SESSION_ENGINE)


from django.contrib.auth.models import User


from privatemessages.models import Thread




class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'text/plain')
        self.write(' Tornado handle HTTP request ')
        print ("Tornado handle GET request")



class MessagesHandler(tornado.websocket.WebSocketHandler ):
    def __init__(self,*args,**kwargs):
        super(MessagesHandler, self).__init__(*args, **kwargs)
        self.client=tornadoredis.Client()
        self.client.connect()


    def open(self, thread_id):
        session_key = self.get_cookie(settings.SESSION_COOKIE_NAME)
        session = session_engine.SessionStore(session_key)
        try:
            self.user_id = session['_auth_user_id']
            self.sender_name = User.objects.get(id = self.user_id).username
        except (KeyError, User.DoesNotExist):
            self.close()
            return
        if not Thread.objects.filter(id = thread_id, participants__id = self.user_id).exists():
            self.close()
            return
        self.channel = "".join(['thread_', thread_id, '_messages'])
        self.client.subscribe(self.channel)
        self.thread_id = thread_id


    #In case if i will want to do something woth response
    def handle_request(self, response):
        pass


    def on_message(self, ws_response):
        """ Function get message form WebSocket client,
        and according to the context of "operation"
        will do the following action:
            - send message
            - add new recipient in the chat room
         """
        ws_response = json.loads(ws_response)


        if ws_response['operation'] == 'add_user':
            print (ws_response)
            username = ws_response['username']

            if not username:
                return
            try:
                User.objects.get(username= username)
            except User.DoesNotExist:
                return
            if username == str (self.sender_name):
                return


            http_client = tornado.httpclient.AsyncHTTPClient()
            request = tornado.httpclient.HTTPRequest(
                "".join([settings.USERSET_EDIT_API_URL,"/",self.thread_id,"/"]),
                method = "POST",
                body = urllib.parse.urlencode({
                    "operation":"add_user",
                    "username":username.encode("utf-8"),
                }))


            http_client.fetch (request, self.handle_request)

            message = ("{0} добавил нового пользователя {1}  ".format(self.sender_name, username))
            
            result = json.dumps({
                "timestamp": int(time.time()),
                "sender": self.sender_name,
                "text": message,
            })
            self.write_message(result)





        if ws_response['operation'] == 'send_message':
            message = ws_response["message"]


            if not message:
                return
            if len(message) > 1000:
                return

            http_client = tornado.httpclient.AsyncHTTPClient()
            request = tornado.httpclient.HTTPRequest(
                "".join([settings.SEND_MESSAGE_API_URL, "/", self.thread_id, "/"]),
                method="POST",
                body = urllib.parse.urlencode({
                    "message": message.encode ("utf-8"),
                    "sender_id": self.user_id,
                })
            )

            http_client.fetch(request, self.handle_request)
            result = json.dumps({
                "timestamp": int(time.time()),
                "sender": self.sender_name,
                "text": message,
            })
            self.write_message(result)






    def on_close(self):

        def check():
            if self.client.connection.in_progress:
                tornado.ioloop.IOLoop.instance().add_timeout(
                    datetime.timedelta(0.00001),
                    check
                )
            else:
                self.client.disconnect()
        tornado.ioloop.IOLoop.instance().add_timeout(
            datetime.timedelta(0.00001),
            check
        )

    def check_origin(self, origin):
        return True


application = tornado.web.Application([
    (r"/",MainHandler),
    (r"/(?P<thread_id>\d+)/", MessagesHandler),
    ])