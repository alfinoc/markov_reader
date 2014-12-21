from bisect import bisect_left
import redis

HOST = 'localhost'
PORT = '6379'

"""
Key scheme:
   last_term_id
   <id> -> term_string
   <term_string>:id -> <id>
   <filename>:src -> list<id>
   <id>:succ -> HASH<filename:<id>, count>
   <id>:positions -> HASH<filename, list<pos>>
"""
class RedisWrapper:
   def __init__(self):
      try:
         self.store = redis.Redis(HOST, port=PORT)
      except redis.ConnectionError:
         raise IOError

   def stored(self):
      return map(lambda s : s[:-len(':src')], self.store.keys('*:src'))

   def isIndexed(self, filename):
      return self.store.exists(filename + ':src')

   def sourceName(self, key):
      return self.store.get(key + ':name')

   def sourceLength(self, key):
      return self.store.llen(key + ':src')

   def source(self, key, start=0, end=-1):
      if end == -1:
         end = self.sourceLength(key)
      return self.store.lrange(key + ':src', start, end)

   def sourceAtPosition(self, key, index):
      return self.store.lindex(key + ':src', index)

   def firstId(self, sourceKey):
      return self.store.lindex(sourceKey + ':src', 0)

   def term(self, id):
      return self.store.get(str(id))

   def id(self, term):
      id = self.store.get(str(term) + ':id')
      return None if id == None else int(id)

   def positions(self, id, sourceKey):
      return self.store.hget(str(id) + ':positions', sourceKey)

   def allPositions(self, id):
      return self.store.hgetall(str(id) + ':positions')

   def successors(self, id, sourceKey):
      return self.store.hgetall('{0}:{1}:succ'.format(id, sourceKey))

   def getNewId(self):
      return self.store.incr('last_term_id')

   def setSourceList(self, filename, idList):
      for id in idList:
         self.store.rpush(filename + ':src', id)

   def setPositionList(self, id, filename, positions):
      return self.store.hset(str(id) + ':positions', filename, positions)

   def setIdTermPair(self, id, term):
      self.store.set(id, term)
      self.store.set(term + ':id', id)

   def setSuccessorCount(self, filename, first, second, count):
      self.store.hset('{0}:{1}:succ'.format(first, filename), second, count)

"""
An in-memory English dictionary loaded directly from a file
containing one word per line.
"""
class Dictionary:
   def __init__(self, filename):
      self.dict = set()
      f = open(filename)
      for line in f:
         self.dict.add(line.strip())
      self.__contains__ = self.dict.__contains__
