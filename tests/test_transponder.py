from transponder import Transponder
from tornado.testing import AsyncTestCase, ExpectLog, gen_test
from tornado import gen
import json
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
                **self._mqparams,
                name="Name of actor",
                about="Description of this actor"
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
            routing_key="status",
            body="is anybody out there?",
        )

        def is_valid_result(result):
            assert 'exchange' in result
            assert 'queue' in result
            assert 'hostname' in result
            assert 'main' in result
            assert 'name' in result
            assert 'about' in result

        result = json.loads(result.decode('utf8'))
        is_valid_result(result)

        # check that we can do RPC and gather results from multiple publishers
        # asker--[question]-->rabbitmq->responder--[answer]-->rabbitmq->asker
        result = yield client.send_query(
            exchange="amqp.topic",
            routing_key="status",
            body="is anybody out there?",
            gather_timeout=1
        )
        results = []
        for basic_deliver, basic_propertis, body in result:
            results.append(json.loads(body.decode('utf8')))

        for result in results:
            is_valid_result(result)

        self.stop()
