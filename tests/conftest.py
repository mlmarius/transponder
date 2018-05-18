import logging
import pytest

logging.basicConfig(level=logging.INFO)


@pytest.fixture
def mqparams():

    mqhost = 'localhost'
    mqport = 5672
    mquser = 'guest'
    mqpass = 'guest'
    mquri = f'amqp://{mquser}:{mqpass}@{mqhost}:{mqport}/%2F'
    mqexcname = 'amqp.topic'
    mqexctype = 'topic'
    mqrk = 'ping, quake.#, question, status'

    return {
        'mqhost': mqhost,
        'mqport': mqport,
        'mquser': mquser,
        'mqpass': mqpass,
        'mquri': mquri,
        'mqexcname': mqexcname,
        'mqexctype': mqexctype,
        'routing_key': mqrk
    }


def pytest_itemcollected(item):
    par = item.parent.obj
    node = item.obj
    pref = par.__doc__.strip() if par.__doc__ else par.__class__.__name__
    suf = node.__doc__.strip() if node.__doc__ else node.__name__
    if pref or suf:
        item._nodeid = "{} - {}".format(node.__name__, ' '.join((pref, suf)))
