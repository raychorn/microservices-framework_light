import os
from mujson import json

from vyperlogix.decorators import expose

normalize_query_params = lambda r : dict([tuple([k,v]) for k,v in r.items()])


def __response_handler__(the_response, request=None, response_handler=None, dictutils=None, is_serverMode_django=None, mimetype='application/json', logger=None):
    __response__ = None
    if (callable(response_handler)):
        try:
            __response__ = response_handler(json.dumps(dictutils.json_cleaner(the_response)) if ((not callable(is_serverMode_django)) or (not is_serverMode_django())) else the_response, mimetype='application/json')
        except Exception as ex:
            logger.exception('EXCEPTION -> {}'.format(request.method), ex)
    return __response__
    

class CatchAllResponse(object):
    
    def __init__(self):
        ...

    def __call__(self, f):
        try:
            def wrapped_f(*args, **kwargs):
                the_response = f(*args, **kwargs)
                __kwargs = {}
                __kwargs['request'] = kwargs.get('request')
                __kwargs['response_handler'] = kwargs.get('response_handler')
                __kwargs['dictutils'] = kwargs.get('dictutils')
                __kwargs['is_serverMode_django'] = kwargs.get('is_serverMode_django')
                __kwargs['mimetype'] = kwargs.get('mimetype')
                __kwargs['logger'] = kwargs.get('logger')
                return __response_handler__(the_response, **__kwargs)
            return wrapped_f
        except Exception as ex:
            if (self.logger):
                self.logger.exception('EXCEPTION -> {}'.format(self.request.method), ex)


@CatchAllResponse()
def __catch_all__(path, request=None, response_handler=None, __json=None, logger=None, service_runner=None, is_serverMode_flask=None, is_serverMode_django=None, __env__=None, is_debugging=False, dictutils=None):
    def request_query_params(request, is_serverMode_flask=None, is_serverMode_django=None):
        return normalize_query_params(request.args if (is_serverMode_flask()) else request.query_params if ((not callable(is_serverMode_django)) or (not is_serverMode_django())) else request.GET)
    def request_get_json(request, is_serverMode_flask=None, is_serverMode_django=None):
        return request.get_json() if (is_serverMode_flask()) else __json if ((not callable(is_serverMode_django)) or (not is_serverMode_django())) else json.loads(request.body.decode("utf-8"))
    the_path = [p for p in path.split('/') if (len(str(p)) > 0)]
    the_response = {"path": '/'.join(the_path[1:])}
    __fp_plugins__ = [__env__.get('plugins')]
    if (request.method in ['POST', 'PUT', 'DELETE']):
        try:
            uuid = the_path[0] if (len(the_path) > 0) else None
            if (uuid == __env__.get('__uuid__')):
                d = request_get_json(request, is_serverMode_flask=is_serverMode_flask, is_serverMode_django=is_serverMode_django)
                logger.info(json.dumps(d, indent=3))
                logger.info('-'*30)
                d = service_runner.resolve(request, data=d, path=the_path, plugins=__fp_plugins__, request_query_params=request_query_params)
                if (d is not None):
                    the_response['response'] = d
                else:
                    return {'success':False}, 404, {'ContentType':'application/json'}
            else:
                return {'success':False}, 404, {'ContentType':'application/json'}
        except Exception as ex:
            logger.exception('EXCEPTION -> {}'.format(request.method), ex)
            return {'success':False, 'reason': str(ex)}, 404, {'ContentType':'application/json'}
            
    elif (request.method in ['GET']):
        try:
            the_response = {}
            uuid = the_path[0] if (len(the_path) > 0) else None
            module_name = the_path[1] if (len(the_path) > 1) else None
            if (uuid == __env__.get('__uuid__')):
                if (module_name == '__directory__'):
                    if (uuid == __env__.get('__uuid__')):
                        the_response['fpath'] = os.path.dirname(__file__)
                        the_response['__plugins__'] = {}
                        for fp_plugins in __fp_plugins__:
                            the_response['__plugins__'][fp_plugins] = {}
                            the_response['__plugins__'][fp_plugins]['has_plugins'] = has_plugins = os.path.exists(fp_plugins) and os.path.isdir(fp_plugins)
                            if (not has_plugins):
                                os.mkdir(fp_plugins)
                                the_response['__plugins__'][fp_plugins]['has_plugins'] = has_plugins = os.path.exists(fp_plugins) and os.path.isdir(fp_plugins)
                            fp_plugins_initpy = os.sep.join([fp_plugins, '__init__.py'])
                            if (not (os.path.exists(fp_plugins_initpy) and (os.path.isfile(fp_plugins_initpy)))):
                                with open(fp_plugins_initpy, 'w') as fOut:
                                    fOut.write('{}\n'.format('#'*40))
                                    fOut.write('# (c). Copyright, Vyper Logix Corp, All Rights Reserved.\n')
                                    fOut.write('{}\n'.format('#'*40))
                                    fOut.write('\n\n')
                                    fOut.flush()
                            __is__ = eval(request_query_params(request, is_serverMode_flask=is_serverMode_flask, is_serverMode_django=is_serverMode_django).get('DEBUG', False))
                            if (is_debugging or __is__):
                                the_response['__plugins__'][fp_plugins]['query_params'] = request_query_params(request, is_serverMode_flask=is_serverMode_flask, is_serverMode_django=is_serverMode_django)
                                the_response['__plugins__'][fp_plugins]['modules'] = service_runner.modules.get(fp_plugins)
                                the_response['__plugins__'][fp_plugins]['endpoints'] = expose.get_endpoints(for_root=fp_plugins)
                                the_response['__plugins__'][fp_plugins]['imports'] = service_runner.imports.get(fp_plugins)
                                the_response['__plugins__'][fp_plugins]['aliases'] = service_runner.aliases.get(fp_plugins)
                                the_response['__plugins__'][fp_plugins]['status'] = 'OK'
                else:
                    d = service_runner.resolve(request, path=the_path, plugins=__fp_plugins__, request_query_params=request_query_params)
                    if (d is not None):
                        the_response['response'] = d
                    else:
                        return {'success':False}, 404, {'ContentType':'application/json'}
            else:
                return {'success':False}, 404, {'ContentType':'application/json'}
        except Exception as ex:
            logger.exception('EXCEPTION -> {}'.format(request.method), ex)
            return {'success':False, 'reason': str(ex)}, 404, {'ContentType':'application/json'}
    #__response__ = __response_handler__(the_response, request=request, response_handler=response_handler, dictutils=dictutils, is_serverMode_django=is_serverMode_django, mimetype='application/json', logger=logger)
    return the_response

