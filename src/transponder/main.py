import tornado.ioloop
import transponder
import logging
import signal
import os


client = None


def sig_exit(signum, frame):
    logging.warning('App received exit signal')
    tornado.ioloop.IOLoop.instance().add_callback_from_signal(do_stop, signum, frame)


def do_stop(signum, frame):
    logging.warning('Exiting application')
    # tornado.ioloop.IOLoop.instance().add_callback(client.stop)
    # client.stop()
    logging.info("Application terminated")
    tornado.ioloop.IOLoop.instance().stop()


def main():
    global client
    FORMAT = ('%(asctime)s %(levelname) -10s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s')
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)

    logging.getLogger('pika').setLevel(logging.INFO)

    mqhost = os.environ.get('MQHOST')
    mqport = os.environ.get('MQPORT')
    mquser = os.environ.get('MQUSER')
    mqpass = os.environ.get('MQPASS')
    mqexcname = os.environ.get('MQEXCNAME')
    mqexctype = os.environ.get('MQEXCTYPE')
    mqrk = os.environ.get('MQRK')

    client = transponder.Transponder(
        mqhost=mqhost,
        mqport=mqport,
        mquser=mquser,
        mqpass=mqpass,
        mqexcname=mqexcname,
        mqexctype=mqexctype,
        routing_key=mqrk,
        client_properties=transponder.ClientProperties(
            product="TransponderTestClient",
            information="testing transponder client",
            version="0.0.1"
        )
    )

    signal.signal(signal.SIGINT, sig_exit)

    logging.info("Starting rabbitmq client")
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()


if __name__ == "__main__":
    main()
