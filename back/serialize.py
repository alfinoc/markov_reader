import sys
import os
from reader import *
from persistent import *

# Check arguments.
if len(sys.argv) < 2:
   sys.exit('Usage: provide the filename for the text you\'d like to index')
filename = sys.argv[1]
if not os.path.isfile(filename):
   sys.exit('Error: could not find file ' + filename)

# Attempt indexing.
print '  indexing \'{0}\''.format(filename)
try:
   store = RedisWrapper()
   ind = Index(filename)
   ind.serialize(store)
except IOError:
   sys.exit('Error: could not find open Redis server at')
print '  done'
