from dotenv import find_dotenv

from vyperlogix.env.environ import MyDotEnv

def __escape(v):
    from urllib import parse
    return parse.quote_plus(v)

def __unescape(v):
    from urllib import parse
    return parse.unquote_plus(v)

__env__ = {}
env_literals = []
def get_environ_keys(*args, **kwargs):
    from expandvars import expandvars
    
    k = kwargs.get('key')
    v = kwargs.get('value')
    assert (k is not None) and (v is not None), 'Problem with kwargs -> {}, k={}, v={}'.format(kwargs,k,v)
    __logger__ = kwargs.get('logger')
    if (k == '__LITERALS__'):
        _v = eval(v)
        if (isinstance(_v, list)):
            for item in _v:
                env_literals.append(item)
        else:
            env_literals.append(_v)
    if (isinstance(v, str)):
        v = expandvars(v) if (k not in env_literals) else v
        v = __escape(v) if (k in __env__.get('__ESCAPED__', [])) else eval(v) if (k in __env__.get('__EVALS__', [])) else v
    ignoring = __env__.get('IGNORING', [])
    environ = kwargs.get('environ', None)
    if (isinstance(environ, dict)):
        environ[k] = v if (isinstance(v, str)) else str(v)
    if (k not in ignoring):
        __env__[k] = v
    if (__logger__):
        __logger__.info('\t{} -> {}'.format(k, environ.get(k)))
    return tuple([k,v])

def read_env(logger=None):
    dotenv = MyDotEnv(find_dotenv(), verbose=True, interpolate=True, override=True, logger=logger, callback=get_environ_keys)
    dotenv.set_as_environment_variables()
