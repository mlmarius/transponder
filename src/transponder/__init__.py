import pika
import tornado
from tornado import gen
import uuid
import logging
import datetime
from tornado.concurrent import Future
from . import mqclient

LOGGER = logging.getLogger('mqmanager')


class Transponder(object):

    def __init__(self, *args, **kwargs):
        self.queries = {}
        self._client = mqclient.MQClient(
            **kwargs,
            handler=self.handle_message
        )
        self._client.prepare()

    def handle_message(self, unused_channel, basic_deliver, properties, body):
        # routing_key = basic_deliver.routing_key
        if properties.reply_to:
            LOGGER.info('Message contains reply_to. It must be a rpc query')
            self.handle_query(basic_deliver, properties, body)
        elif properties.correlation_id:
            corr_id = properties.correlation_id
            # if the message has a correlation_id then we treat it like a rpc reply
            if corr_id in self.queries:
                LOGGER.info('this is a rpc response')
                self.handle_query_response(basic_deliver, properties, body)
            else:
                LOGGER.warning('Received response with invalid correlation_id')
        else:
            self.handle_notification(unused_channel, basic_deliver, properties, body)

    def handle_notification(self, unused_channel, basic_deliver, properties, body):
        LOGGER.info('Handling a normal notification received on topic {}'.format(basic_deliver.routing_key))
        # LOGGER.info(body)

    def handle_query(self, basic_deliver, properties, body):
        LOGGER.info('Handling RPC query')
        newprops = pika.BasicProperties(correlation_id=properties.correlation_id)
        # beware of the '' exchange. We use this in order to publish directly to the channel
        response = self.get_query_response(basic_deliver, properties, body)
        self.publish(exchange='', routing_key=properties.reply_to, properties=newprops, body=response)

    def get_query_response(self, basic_deliver, properties, body):
        raise Exception("Method not implemented")

    def handle_query_response(self, basic_deliver, properties, body):
        # respond to RPC queries
        LOGGER.info('handling query response')
        corr_id = properties.correlation_id
        if self.queries[corr_id].get('future'):
            self.queries[corr_id]['future'].set_result(body)
            del self.queries[corr_id]
        else:
            self.queries[corr_id]['results'].append((basic_deliver, properties, body))

    @gen.coroutine
    def send_query(self, *args, **kwargs):
        '''
            gather_timeout = int - seconds to wait for responses to arrive
            exchange = string - exchange on which to publish the question
            routing_key = string - routing_key to publish question on
            body = string - question to publish
        '''
        LOGGER.info('running query method')
        corr_id = uuid.uuid4().hex
        exchange = kwargs['exchange']
        # make them reply_to my own channel
        reply_to = self._client._queue_name
        LOGGER.info(f"corr_id id is {corr_id}")
        LOGGER.info(f"reply_to is {reply_to}")
        query_data = {
            'time': datetime.datetime.now(),
            'results': []
        }

        # query can hage the 'timeout' parameter set
        # for example when we query on the rabbitmq for results
        # from multiple listeners and we do not know how many replys there will be
        # therefore we will wait a short amount of time for all
        # listeners to reply

        future = Future()

        # if we are instructed to wait a certain time for results to gather
        # than we do that right here
        gather_timeout = kwargs.get('gather_timeout')
        if gather_timeout:
            del kwargs['gather_timeout']

        if not gather_timeout:
            # if no gather_timeout than the first response
            # that arrives will resolve this future
            query_data['future'] = future

        self.queries[corr_id] = query_data
        properties = pika.BasicProperties(correlation_id=corr_id, reply_to=reply_to)
        LOGGER.info(properties)

        # TMP publishing requests
        # this will have to be the user's request
        LOGGER.info(f"Sending query to {exchange} on {kwargs['routing_key']}: {kwargs['body']}")
        self.publish(
            exchange=kwargs['exchange'],
            routing_key=kwargs['routing_key'],
            properties=properties,
            body=kwargs['body'])
        LOGGER.info('query sent')

        # if gather_timeout was used then we should wait
        # the selected amount of time for the responses
        # to arive
        if gather_timeout:
            yield tornado.gen.sleep(gather_timeout)
            future.set_result(self.queries[corr_id]['results'])
            del self.queries[corr_id]

        LOGGER.info("Returning the future")
        result = yield future
        return result

    def publish(self, *args, **kwargs):
        self._client.publish(*args, **kwargs)
