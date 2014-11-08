from bisect import bisect_left
from random import uniform
from collections import OrderedDict
from copy import copy
import redis
import ply.lex as lex

"""
Locate the leftmost value in 'a' exactly equal to 'x'
"""
def index(a, x):
   i = bisect_left(a, x)
   if i != len(a) and a[i] == x:
      return i
   raise ValueError

"""
given a list of string, returns a map with a key for every string in 'list', mapped
to index. assumes that returned map is an injection
"""
def invertedMap(list):
   res = {}
   for i in range(0, len(list)):
      res[list[i]] = i
   return res

"""
A scanner for reading from a source text Index.
"""
class Reader:
   """
   builds a scanner around the provided index
   """
   def __init__(self, index):
      self.index = index
      self.last = self.index.getFirstId();

   """
   let p be the last phrase returned. a subsequent call to "next()" returns a successor s
   to p in the source text chosen according to the frequency with which s succeeds p
   relative to p's other successors
   """
   def next(self):
      self.last = self.__sample(self.index.getSuccessors(self.last))
      return self.index.getTerm(self.last)

   """
   returns the last value returned from next, or, if next has not been called, returns
   the initial seed
   """
   def previous(self):
      return self.index.getTerm(self.last)

   """
   seeds the reader with a starting phrase 'start'
   after a call to seed(start), subsequent next() calls will behave as if the previous
   call to next() returned start
   raises ValueError if 'start' is not a known term
   """
   def seed(self, start):
      if self.index.getTerm.getTerm(start) == None:
         raise ValueError
      self.last = start

   """
   given 'distribution', a map from choice to frequency of that choices, returns a sample
   from key with probability proportional to the key's frequency / (sum of all values)
   """
   def __sample(self, distribution):
      total = sum(distribution.values()) * 1.0

      # invert map to <frequency boundary -> choice>
      sumProb = 0
      probabilityThresholds = OrderedDict()
      for choice in distribution:
         sumProb += distribution[choice] / total
         probabilityThresholds[sumProb] = choice

      # make a weighted random choice
      roll = uniform(0, 1)
      for prob in probabilityThresholds:
         if prob >= roll:
            return probabilityThresholds[prob]

      raise ValueError

def strMapToInt(strMap):
   intMap = {}
   for key in strMap:
      intMap[int(key)] = int(strMap[key])
   return intMap

"""
a text index stored in a Redis database, according to scheme laid out in Index.serialize
"""
class SerialIndex:
   """
   filename should be the *base* filename for the source text. raises ValueError if 
   the filename is not in the store.
   """
   def __init__(self, filename, store):
      if store.exists(filename + ':src'):
         raise ValueError(filename + ' not found in store! Remember: use the base name.')
      # TODO: this is a difference between serialindex and index -- one has
      # an intrinsic filename and the other does not
      self.filename = filename
      self.store = store
      self.successorCache = {}

   # Index documentation
   def getFirstId(self):
      return self.store.lindex(self.filename + ':src', 0)

   # Index documentation
   def getSuccessors(self, termId):
      # fast path: cache hit
      if termId in self.successorCache:
         return self.successorCache[termId]

      # convert Redis HASH (string keys/values) to integer python dict
      strMap = self.store.hgetall(str(termId) + ':succ')
      intMap = strMapToInt(strMap)

      # update cache with successor map
      self.successorCache[termId] = intMap
      return intMap

   # Index documentation
   def getTerm(self, termId):
      return self.store.get(termId)

# Lexer rules
terminators = '.?,!:;'
literals = terminators + '/='
tokens = (
   'EN_DASH',
   'EM_DASH',
   'ELLIPSIS',
   'WORD',
)
t_EN_DASH  = r'--'
t_EM_DASH  = r'---'
t_ELLIPSIS = r'\.\.\.'
t_WORD     = r'\w+-\w+|\w+\'\w+|\w+'  # Allow all words, contractions, and dashed words.
t_ignore  = ' \t\n()[]"*-\''

# Error handling rule.
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

def getBaseFilename(path):
   while '/' in path:
      path = path[(path.index('/')+1):]
   return path

"""
A pre-parsed version of the source text contained in 'filename'. Each whitespace separated
unique word in the source is given an ID, and for any given word-id w, a collection of
words that follow w can be retrived in the form of a frequency distribution.

'filename' should be a path referencing the actual file to open. If serialized, the file's
key is the base of this filename (see serialize documentation).
"""
class Index:
   def __init__(self, filename):
      tokens = self.__getTokens(open(filename))
      self.dictionary = list(set(tokens))
      #self.dictionary.sort()
      tokenToId = invertedMap(self.dictionary)
      self.sourceText = map(lambda str: tokenToId[str], tokens)
      self.successors = self.__getFrequencyMap(tokens, tokenToId)
      self.filename = getBaseFilename(filename)

   """
   returns the id of the first token in the source text, or None if there are no tokens.
   """
   def getFirstId(self):
      return self.sourceText[0] if len(self.sourceText) != 0 else None

   """
   returns a map from id to count, where each id is a successor (appears immediately after
   'termId' in the source text) and the count is the number of times that the successor
   follows the argument term id.
   """
   def getSuccessors(self, termId):
      return self.successors[termId]

   """
   returns the string term with the given ID
   """
   def getTerm(self, termId):
      if 0 <= termId and termId < len(self.dictionary):
         return self.dictionary[termId]
      else:
         return None

   """
   writes the index to the provided Redis store with the following <k,v> format:
      last_term_id
      <id> -> term_string
      <term_string>:id -> <id>
      <filename>:src -> list<id>
      <id>:succ -> HASH<filename:<id>, count>
      <id>:positions -> LIST<filename:id>
   with id being the term id for every term stored in the index.

   Uses the *base* filename provided to the Index' constructor as a key. Raises
   ValueError if the store already has an entry with this filename key.
   """
   def serialize(self, store):
      if store.exists(self.filename + ':src'):
         raise ValueError('There is already an index for file: ' + self.filename)

      # the canonical id is the word's id in the Redis store, which may be different
      # from the one used internally. getCanonicalId will return the one and only
      # (potentially brand new) ID for the term referenced by the given instanceId.
      tokenToId = invertedMap(self.dictionary)
      canonMemo = {}  # avoid repeated Redis lookups for a bagillian 'the's
      def getCanonicalId(instanceId):
         if instanceId in canonMemo:
            return canonMemo[instanceId]
         canonKey = store.get(self.dictionary[instanceId] + ':id')
         if canonKey == None:
            canonKey = store.incr('last_term_id')
            # id -> term_string
            # term_string:id -> id
            store.set(canonKey, self.dictionary[instanceId])
            store.set(self.dictionary[instanceId] + ':id', canonKey)
         canonMemo[instanceId] = str(canonKey)
         return str(canonKey)

      def prefixWithFile(key):
         return self.filename + ':' + str(key)

      # filename:src -> list<id>
      for keyId in self.sourceText:
         store.rpush(prefixWithFile('src'), getCanonicalId(keyId))

      # id:succ -> HASH<filename:id, count>
      for keyId in self.successors:
         canonKey = getCanonicalId(keyId) + ':succ'
         counts = store.hgetall(canonKey)
         # TODO/huh!: you might want to retain some file information here, but for now
         # you just go ahead and merge count maps. makes you think: the words themselves
         # don't really make the text, but rather word pairs, the connections.
         for succ in self.successors[keyId]:
            canonSucc = getCanonicalId(succ)
            if not canonSucc in counts:
               counts[canonSucc] = 0
            counts[canonSucc] = str(int(counts[canonSucc]) + self.successors[keyId][succ])
         store.hmset(canonKey, counts)

   """
   returns the whitespace tokens from the file, making each terminator punctuator its own
   token and removing all quotes (double and single)
   """
   def __getTokens(self, file):
      lexer = lex.lex()
      tokenized = []
      for line in file:
         lexer.input(line)
         while True:
           tok = lexer.token()
           if not tok: break
           tokenized.append(tok.value)
      return tokenized

   """
   returns a map of token to successor map, where each successor map maps a successor
   to its number of occurrances in tokens. in other words, for every successive pair
   of tokens (a, b) and returned map m, m[a][b] is the number of times "a b" appears
   in immediate sequence in tokens.

   the returned map uses integer indices to identify tokens. bijection 'tokenToId'
   maps token strings to their respective ids.
   """
   def __getFrequencyMap(self, tokens, tokenToId):
      result = {}
      for i in range(len(tokens) - 1):
         first = tokenToId[tokens[i]]
         second = tokenToId[tokens[i + 1]]
         if not first in result:
            result[first] = {}
         prevSuccessors = result[first]
         if not second in prevSuccessors:
            prevSuccessors[second] = 1
         else:
            prevSuccessors[second] += 1
      return result
