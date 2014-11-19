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
      return self.store.lrange(key + 'src', start, end)

   def firstId(self, sourceKey):
      return self.store.lindex(sourceKey + ':src', 0)

   def term(self, id):
      return self.store.get(str(id))

   def id(self, term):
      id = self.store.get(str(term) + ':id')
      return None if id == None else int(id)

   def positions(self, id):
      return self.store.hgetall(str(id) + ':positions')

   def successors(self, id):
      return self.store.hgetall(str(id) + ':succ')

   def getNewId(self):
      return self.store.incr('last_term_id')

   def setSourceList(self, filename, idList):
      for id in idList:
         self.store.rpush(filename + ':src', id)

   def setPositionList(self, filename, id, positions):
      return self.store.hset(str(id) + ':positions', filename, positions)

   def setIdTermPair(self, id, term):
      self.store.set(id, term)
      self.store.set(term + ':id', id)

   def increaseSuccessorCount(self, first, second, amount):
      key = first + ':succ'
      field = second
      prev = self.store.hget(key, field)
      if prev == None:
         prev = 0
      else:
         prev = int(prev)
      self.store.hset(key, field, prev + amount)
