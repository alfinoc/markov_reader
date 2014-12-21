from json import loads
from random import choice
from reader import MultiReader
from index import invertedMap

"""
a proto for a term with some extra information about that term.
   'term' is the whitespace-separated term as it would appear in a sentence
   'src' is the either the Redis source key or a local ID representing this key
   'lookup' is the name of the *persistently stored* term.

term and lookup may differ with respect to punctuation or capitalization. for
instance ['And,', 0, 'and'] is a legal proto.
"""
def getProto(term, src, lookup):
   return {
      'term': term,
      'src': src,
      'lookup': lookup
   }

"""
converts a proto dict to a list in the format [term, src, lookup].
"""
def serializeProto(protoDict):
   return [protoDict['term'], protoDict['src'], protoDict['lookup']]

"""
builds a list of terms based on the provided request parameters:
   seed: The first term in the returned list. Must be a term recognized by the
         provided reader.
   length: The length of the returned list. Any integer.
   sequential: The minimum length of a sequence read directly from a text. Any
         integer.
using the provided MultiReader 'reader' and the persistent 'store'.

terms are returned as protos (see dict above) identical 'term' and 'lookup'
attributes.
"""
def generateBlock(seed, length, sequential, reader, store):
   # Compose a list of generated terms.
   seed = reader.previous()
   generatedList = [getProto(seed, '', seed)]
   pos = 0
   for i in range(1, length + 1):
      if i % sequential == 0:
         # attempt a jump!
         # TODO: make it so this uses the correct interface. the issue is that
         # 'last' doesn't stay consistent after sequential next()s.
         reader.last = generatedList[len(generatedList) - 1]['term']
         reader.switchIndex()
         generatedList.append(getProto(reader.next(), '', ''))
         # avoid the position lookups if we're jumping on every term
         if sequential > 1:
            lastId = generatedList[len(generatedList) - 1]['term']
            srcKey = reader.getCurrentSourceKey()
            pos = choice(loads(store.positions(lastId, srcKey)))
      else:
         # read the next term sequentially
         sourceKey = reader.getCurrentSourceKey()
         pos += 1
         pos %= store.sourceLength(sourceKey)
         term = store.sourceAtPosition(sourceKey, pos)
         generatedList.append(getProto(term, sourceKey, ''))

   # Translate proto term IDs to term strings and assign identical lookups.
   for proto in generatedList:
      proto['term'] = store.term(proto['term'])
      proto['lookup'] = proto['term']
   return generatedList
