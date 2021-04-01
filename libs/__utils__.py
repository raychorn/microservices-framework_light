import os
import enum
import logging

from datetime import datetime

from logging.handlers import RotatingFileHandler
from os.path import dirname

is_really_something = lambda s,t:s and t(s)
something_greater_than_zero = lambda s:(s > 0)

default_timestamp = lambda t:t.isoformat().replace(':', '').replace('-','').split('.')[0]

is_uppercase = lambda ch:''.join([c for c in str(ch) if c.isupper()])

def get_stream_handler(streamformat="%(asctime)s:%(levelname)s:%(message)s"):
    stream = logging.StreamHandler()
    stream.setLevel(logging.INFO)
    stream.setFormatter(logging.Formatter(streamformat))
    return stream

    
def setup_rotating_file_handler(logname, logfile, max_bytes, backup_count):
    assert is_really_something(backup_count, something_greater_than_zero), 'Missing backup_count?'
    assert is_really_something(max_bytes, something_greater_than_zero), 'Missing max_bytes?'
    ch = RotatingFileHandler(logfile, 'a', max_bytes, backup_count)
    l = logging.getLogger(logname)
    l.addHandler(ch)
    return l

production_token = 'production'

def get_logger():
    base_filename = os.path.splitext(os.environ.get('LOGGER_NAME', os.path.dirname(os.path.dirname(__file__)).split(os.sep)[-1]))[0]

    log_filename = '{}{}{}{}{}{}{}_{}.log'.format('logs', os.sep, base_filename, os.sep, production_token, os.sep, base_filename, default_timestamp(datetime.utcnow()))

    if not os.path.exists(os.path.dirname(log_filename)):
        os.makedirs(os.path.dirname(log_filename))

    if (os.path.exists(log_filename)):
        os.remove(log_filename)

    log_format = ('[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        filename=(log_filename),
    )

    logger = setup_rotating_file_handler(base_filename, log_filename, (1024*1024*1024), 10)
    logger.addHandler(get_stream_handler())
    
    return logger

class ServerMode(enum.Enum):
    use_none = 0
    use_flask = 1
    use_fastapi = 2
    use_django = 4


def get_server_mode(environ={}):
    __server_mode__ = ServerMode.use_none
    if (environ.get('use_flask', False)):
        __server_mode__ = ServerMode.use_flask
        assert not environ.get('use_fastapi', False), 'Cannot use flask and fastapi so choose one of them, not more than one.'
        assert not environ.get('use_django', False), 'Cannot use both flask and django so choose one of them, not more than one.'

    if (environ.get('use_fastapi', False)):
        __server_mode__ = ServerMode.use_fastapi
        assert not environ.get('use_flask', False), 'Cannot use both flask and fastapi so choose one of them, not more than one.'
        assert not environ.get('use_django', False), 'Cannot use both fastapi and django so choose one of them, not more than one.'

    if (environ.get('use_django', False)):
        __server_mode__ = ServerMode.use_django
        assert not environ.get('use_flask', False), 'Cannot use both flask and django so choose one of them, not more than one.'
        assert not environ.get('use_fastapi', False), 'Cannot use both fastapi and django so choose one of them, not more than one.'
        
    return __server_mode__

__is_serverMode_flask = lambda sm: sm == ServerMode.use_flask
__is_serverMode_fastapi = lambda sm: sm == ServerMode.use_fastapi
__is_serverMode_django = lambda sm: sm == ServerMode.use_django
