import sys
import os
import redis
import json

IP = 'localhost'
PORT = '6379'

# Check arguments.
if len(sys.argv) < 3:
   sys.exit('Usage: <redis source key> <out file name>')
key = sys.argv[1]
out = sys.argv[2]

# Attempt indexing.
print '  building json for \'{0}\''.format(out)
try:
   store = redis.Redis(IP, PORT)
   key = key + ':src'
   if not store.exists(key):
      sys.exit('No source found with key {0).'.format(key))
   srcLen = store.llen(key)
   
   # Construct id list and term string map.
   sequence = store.lrange(key, 0, srcLen)
   terms = {}
   for t in sequence:
      terms[t] = store.get(t)

   # Dump the JSON to a file.
   result = { 'source': { 'sequence': sequence, 'terms': terms } }
   open(out, 'w').write(json.dumps(result))
except redis.ConnectionError:
   sys.exit('Error: could not find open Redis server at {0}:{1}'.format(IP, PORT))
print '  done'
