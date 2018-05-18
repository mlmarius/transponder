from transponder import mqclient
from tornado.testing import AsyncTestCase, ExpectLog, gen_test
from tornado import gen
import pytest


class TestMQClient(AsyncTestCase):
    '''Integration test Testing MQClient connecting to RabbitMQ'''

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, mqparams):
        self._mqparams = mqparams

    @gen_test(timeout=10)
    def test(self):

        @gen.coroutine
        def handler(channel, basic_deliver, properties, body):
            print(body)

        client = mqclient.MQClient(
            **self._mqparams,
            handler=handler
        )

        # check that client connects to RabbitMQ
        with ExpectLog('mqclient', 'Channel opened'):
            client.prepare()
            yield gen.sleep(0.5)

        # check that client can publish and receive messages
        with ExpectLog('mqclient', 'Acknowledging message 1'):
            client.publish('amqp.topic', 'ping', 'ping message')
            yield gen.sleep(1)

        yield gen.sleep(1)
        self.stop()
