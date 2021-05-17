import requests
import json

import time

import base64
import zlib
import binascii
#data = zlib.decompress(base64.b64decode(compressed))


def conversion_task(item=None):
    h = item[-1].hex()
    hb = h.encode("utf-8")
    h_crc32 = binascii.crc32(hb)
    c1 = zlib.compress(hb)
    c = base64.b64encode(c1)
    n = len(c) - len(h)
    return {'indx': item[0], 'hex': h, 'compressed': c, 'diff': n, 'crc32':h_crc32}


def read_binary_file(fpath, datum=None, chunksize=16384):
    startTime = time.time()
    with open(fpath, 'rb') as fIn:
        num = 0
        while (data := fIn.read(chunksize)):
            if (isinstance(datum, list)):
                datum.append(conversion_task(item=[num, data]))
            num += 1
            
    print('{} chunks.'.format(len(datum)))
        
    assert num == len(datum), 'Something went wrong with the threaded thing because there should be {} chunks but there were {} chunks seen.'.format(num, len(datum))
    executionTime = (time.time() - startTime)
    print('Done. {:.2f}'.format(executionTime))
    return executionTime


normalize_bytecount = lambda v:v/(1024*1024*1024)

results = {}
datum = []

if (1):
    savings = 0
    total_bytes = 0
    compressed_bytes = 0
    results['dt-single-core'] = r = read_binary_file('/home/raychorn/projects/python-projects/securex.ai/data/docker-images/raychorn-appgenerator-dev-latest.tar.gz', datum=datum)
    for data in datum:
        savings += data.get('diff', 0)
        total_bytes += len(data.get('hex', ''))
        compressed_bytes += len(data.get('compressed', ''))
    print('Compression saved {} ({:.2f}%) of {:.2f} GB -> {:.2f} GB bytes.'.format(savings, (savings / total_bytes) * 100.0, normalize_bytecount(compressed_bytes), normalize_bytecount(total_bytes)))
else:
    the_results = []
    the_results_slower = []
    for chsiz in range(1, 16384):
        chunksize=chsiz*128
        print('BEGIN: {} -> {}'.format(chsiz, chunksize))
        results['dt-single-core-{}'.format(chunksize)] = r = read_binary_file('/home/raychorn/projects/python-projects/securex.ai/data/docker-images/raychorn-appgenerator-dev-latest.tar.gz', chunksize=chunksize)
        print('END!!! {} -> {}'.format(chsiz, chunksize))
        if (len(the_results) > 0) and (r > the_results[-1]):
            the_results_slower.append({'chsiz':chsiz, 'r':r, '-1':the_results[-1]})
            print('the_results_slower -> {}'.format(len(the_results_slower)))
            if (len(the_results_slower) >= 100):
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