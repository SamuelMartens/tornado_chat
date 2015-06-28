
import signal
import time

import tornado.httpserver
import tornado.ioloop

from django.core.management.base import BaseCommand, CommandError


from privatemessages.tornadoapp import application

class Command(BaseCommand):
    args = '[port_number]'
    help = 'Start the Tornado application for message handling.'

    def sig_handler(self, sig, frame):
        #Catch signal and init callback
        #According to the next string i/o loop will call callback function on the next iteration
        tornado.ioloop.IOLoop.instance().add_callback(self.shutdown)


    def shutdown(self):
        #Stop server and add callback to stop i/o loop
        self.http_server.stop()


        io_loop = tornado.ioloop.IOLoop.instance()
        io_loop.add_timeout(time.time()+2, io_loop.stop)


    def handle(self, *args, **options):
        if len(args) == 1:
            try:
                port = int(args[0])
            except ValueError:
                raise CommandError("Invalid port number specified")
        else:
            port = 8888


        self.http_server = tornado.httpserver.HTTPServer(application)
        self.http_server.listen(port, address = "127.0.0.1")


        #Init signal handler
        signal.signal(signal.SIGTERM, self.sig_handler)

        #This will also catch KeyboardException
        signal.signal(signal.SIGINT, self.sig_handler)


        tornado.ioloop.IOLoop.instance().start()
