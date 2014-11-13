import redis

HOST = 'localhost'
PORT = '6379'

class RedisWrapper:
   def __init__(self):
      self.store = redis.Redis(HOST, port=PORT)

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
      return self.store.get(str(term) + ':id')

   def positions(self, id):
      return self.store.hgetall(str(id) + ':positions')

   def successors(self, id):
      return self.store.hgetall(str(id) + ':succ')

   def getNewId(self):
      return self.incr('last_term_id')
