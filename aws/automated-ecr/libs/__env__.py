import os
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
        def __init__(self, dotenv_path, is_ignoring=False, verbose=False, encoding=None, interpolate=True, override=True, callback=None, logger=None, environ=None):
            self.override = override
            self.callback = callback
            self.logger = logger
            self.is_ignoring = is_ignoring
            self.environ = environ if (environ is not None) else os.environ
            super().__init__(dotenv_path, verbose=verbose, encoding=encoding, interpolate=interpolate)
        
        def set_as_environment_variables(self):
            """
            Load the current dotenv as system environment variable.
            """
            for k, v in self.dict().items():
                if (not self.is_ignoring):
                    if k in os.environ and not self.override:
                        continue
                if (v is not None):
                    if (callable(self.callback)):
                        try:
                            k,v = parse_line('{}={}'.format(to_env(k), to_env(v)))
                            k,v = self.callback(key=k, value=v, logger=self.logger, is_ignoring=self.is_ignoring, environ=self.environ)
                            if (self.override):
                                os.environ[k] = v
                            continue
                        except Exception as ex:
                            if (self.verbose):
                                if (self.logger):
                                    self.logger.exception('Exception at %s', 'set_as_environment_variables', exc_info=ex)
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
    is_ignoring = kwargs.get('is_ignoring', False)
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
        if (not is_ignoring):
            __env__[k] = v
    if (__logger__):
        __logger__.info('\t{} -> {}'.format(k, environ.get(k)))
    return tuple([k,v])

def read_env(fpath=None, environ=None, is_ignoring=False, override=True, logger=None):
    fpath = fpath if (fpath is not None) and (os.path.exists(fpath) and os.path.isfile(fpath)) else find_dotenv()
    dotenv = MyDotEnv(fpath, environ=environ, is_ignoring=is_ignoring, verbose=True, interpolate=True, override=override, logger=logger, callback=get_environ_keys)
    dotenv.set_as_environment_variables()
    return __env__ if (environ is None) else environ
