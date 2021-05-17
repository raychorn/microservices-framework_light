import requests
import json

import time
from concurrent import futures

def conversion_task(item=None):
    return [item[0], item[-1].hex()]


def read_binary_file(fpath, chunksize=2048, max_workers=0, multiprocess=False):
    startTime = time.time()
    datum = []
    wait_for = []
    if (max_workers > 0):
        executor = futures.ThreadPoolExecutor(max_workers=max_workers)
    elif (multiprocess):
        executor = futures.ProcessPoolExecutor(max_workers=max_workers)
    with open(fpath, 'rb') as fIn:
        num = 0
        while (data := fIn.read(chunksize)):
            if (max_workers > 0):
                wait_for.append(executor.submit(conversion_task, [num, data]))
            else:
                datum.append([num, data.hex()])
            num += 1
            
    if (max_workers == 0):
        print('{} chunks.'.format(len(datum)))
    elif (max_workers > 0):
        for f in futures.as_completed(wait_for):
            datum.append(f.result())
        print('{} chunks.'.format(len(datum)))
        
    assert num == len(datum), 'Something went wrong with the threaded thing because there should be {} chunks but there were {} chunks seen.'.format(num, len(datum))
    executionTime = (time.time() - startTime)
    print('Done. {:.2f}'.format(executionTime))
    return executionTime

results = {}
the_results = []
the_results_slower = []
for chsiz in range(1, 8192):
    chunksize=chsiz*128
    print('BEGIN: {} -> {}'.format(chsiz, chunksize))
    results['dt1-single-core-{}'.format(chunksize)] = r = read_binary_file('/home/raychorn/projects/python-projects/securex.ai/data/docker-images/raychorn-appgenerator-dev-latest.tar.gz', chunksize=chunksize, max_workers=0, multiprocess=False)
    print('END!!! {} -> {}'.format(chsiz, chunksize))
    if (len(the_results) > 0) and (r > the_results[-1]):
        the_results_slower.append({'chsiz':chsiz, 'r':r, '-1':the_results[-1]})
        print('the_results_slower -> {}'.format(len(the_results_slower)))
        if (len(the_results_slower) >= 50):
            print('Stopping...')
            break
    the_results.append(r)
_min = min(results.items(), key=lambda x: x[1])
print('{} is faster'.format(_min))
print()

print('BEGIN: the_results (last 10)')
for r in the_results[-10:]:
    print('{}'.format(r))
print('END!!! the_results (last 10)')
print()

print('BEGIN: the_results_slower')
for r in the_results_slower:
    print('{}'.format(r))
print('END!!! the_results_slower')
print()

chunksize=8192
results['dt1-single-core'] = read_binary_file('/home/raychorn/projects/python-projects/securex.ai/data/docker-images/raychorn-appgenerator-dev-latest.tar.gz', chunksize=chunksize, max_workers=0, multiprocess=False)
results['dt2-multi-thread'] = read_binary_file('/home/raychorn/projects/python-projects/securex.ai/data/docker-images/raychorn-appgenerator-dev-latest.tar.gz', chunksize=chunksize, max_workers=1100, multiprocess=False)
results['dt3-multi-process'] = read_binary_file('/home/raychorn/projects/python-projects/securex.ai/data/docker-images/raychorn-appgenerator-dev-latest.tar.gz', chunksize=chunksize, max_workers=800, multiprocess=True)

_min = min(results.items(), key=lambda x: x[1])

print('{} is faster'.format(_min))

headers={'Content-Type':'application/gzip'}
f = open('/home/raychorn/projects/python-projects/securex.ai/data/docker-images/raychorn-appgenerator-dev-latest.tar.gz', 'rb')

files = {"file": f}

URL = 'http://172.19.152.76:9999/4a1bf01e-0693-48c5-a52b-fc275205c1d8/auto-ecr-rest-api-v1/submit-job-details/'

resp = requests.post(URL, files=files, headers=headers )

print(resp.text)

print("status code " + str(resp.status_code))

if resp.status_code == 200:
    print ("Success")
    print(resp.json())
else:
    print("Failure")