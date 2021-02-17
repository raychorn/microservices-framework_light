import sys
from flask import Flask, request, Response
from flask.ext.runner import Runner

pylib = '/home/raychorn/projects/python-projects/private_vyperlogix_lib3'
if (not any([f == pylib for f in sys.path])):
    sys.path.insert(0, pylib)
    
from vyperlogix.misc import _utils
from vyperlogix.iterators.dict import dictutils

import mujson as json


app = Flask(__name__)
runner = Runner(app)

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'], defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    the_response = {"path": path}
    the_path = path.split('/')
    print('request.method -> {}'.format(request.method))
    if (request.method in ['POST', 'PUT', 'DELETE']):
        try:
            d = request.get_json()
            print(json.dumps(d, indent=3))
            print('-'*30)
        except Exception as ex:
            print(_utils.formattedException(details=ex))
            
    elif (request.method in ['GET']):
        the_func = getattr(MongoClient.mongoClient, the_path[0])
        print('DEBUG: the_path -> {}, the_func -> {}'.format(the_path, the_func))
        if (callable(the_func)):
            try:
                resp = the_func({'args': the_path[1:]})
                print('DEBUG: resp -> {}'.format(resp))
                the_response['/'.join(the_path)] = resp
            except Exception as ex:
                print(_utils.formattedException(details=ex))
    return Response(json.dumps(dictutils.json_cleaner(the_response)), mimetype='application/json')

if (__name__ == '__main__'):
    #sys.argv.append('--help')
    if (not any([str(a).find('-p ') > -1 for a in sys.argv])):
        sys.argv.append('-p 27080')
    runner.run()
    