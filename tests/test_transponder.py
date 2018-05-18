from transponder import Transponder
from tornado.testing import AsyncTestCase, ExpectLog, gen_test
from tornado import gen
import pytest


class TestTransponder(AsyncTestCase):
    '''Transponder integration tests (requires running RabbitMQ instance)'''

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, mqparams):
        self._mqparams = mqparams

    @gen_test(timeout=10)
    def test(self):

        class MyClient(Transponder):
            def get_query_response(self, basic_deliver, properties, body):
                return "yup. it's me"

        # check that client connects to RabbitMQ
        with ExpectLog('mqclient', 'Channel opened'):
            client = MyClient(
                **self._mqparams
            )
            yield gen.sleep(1)

        # check that client can publish and receive messages
        with ExpectLog('mqclient', 'Acknowledging message 1'):
            client.publish('amqp.topic', 'ping', 'ping message')
            yield gen.sleep(1)

        # check that we can do RPC
        # asker--[question]-->rabbitmq->responder--[answer]-->rabbitmq->asker
        result = yield client.send_query(
            exchange="amqp.topic",
            routing_key="question",
            body="is anybody out there?",
        )
        assert result == b"yup. it's me"

        self.stop()
