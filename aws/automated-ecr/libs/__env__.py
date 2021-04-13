import sys
from dotenv import find_dotenv


def parse_line(l, splitters=None):
    import re
    aLine = l.strip()
    key, value = tuple(['', ''])
    if (len(aLine) > 0):
        toks = aLine.split('=')
        key = toks[0]
        value = '='.join(toks[1:]).strip()
        toks = re.split(',|\\||\\;|\\#', value)
        if (len(toks) > 1):
            value = [str(t).strip() for t in toks]
    return tuple([key, value])


try:
    from dotenv.main import DotEnv
    from dotenv.compat import to_env

    class MyDotEnv(DotEnv):
        def __init__(self, dotenv_path, verbose=False, encoding=None, interpolate=True, override=True, callback=None, logger=None, environ=None):
            self.override = override
            self.callback = callback
            self.logger = logger
            self.environ = environ if (environ is not None) else os.environ
            super().__init__(dotenv_path, verbose=verbose, encoding=encoding, interpolate=interpolate)
        
        def set_as_environment_variables(self):
            """
            Load the current dotenv as system environment variable.
            """
            for k, v in self.dict().items():
                if k in os.environ and not self.override:
                    continue
                if v is not None:
                    if (callable(self.callback)):
                        try:
                            k,v = parse_line('{}={}'.format(to_env(k), to_env(v)))
                            k,v = self.callback(key=k, value=v, logger=self.logger, environ=self.environ)
                            if (self.override):
                                os.environ[k] = v
                            continue
                        except Exception as ex:
                            if (self.verbose):
                                extype, ex, tb = sys.exc_info()
                                #formatted = traceback.format_exception_only(extype, ex)[-1]
                                formatted = _utils.formattedException(details=ex)
                                if (self.logger):
                                    self.logger.error(formatted)
                                else:
                                    print(formatted)
                    else:
                        os.environ[to_env(k)] = to_env(v)

            return True
except ImportError:
    print('ImportError :: Cannot import dotenv.\npip install -U python-dotenv')
    

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
