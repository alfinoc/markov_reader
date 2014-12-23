import sys
import os
from index import *
from persistent import *

# Check arguments.
if len(sys.argv) < 2:
   sys.exit('Usage: provide the filename for the text you\'d like to index')


# Attempt indexing.
for i in range(1, len(sys.argv)):
   filename = sys.argv[i]
   if not os.path.isfile(filename):
      sys.exit('Error: could not find file ' + filename)
   print '  indexing \'{0}\''.format(filename)
   try:
      store = RedisWrapper()
      ind = Index(filename, Dictionary('data/dict'))
      ind.serialize(store)
   except IOError:
      sys.exit('Error: could not find open Redis server at')
   print '  done'
