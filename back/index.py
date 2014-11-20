from bisect import bisect_left
from ply.lex import lex

# Lexer rules
terminators = '.?,!:;'
literals = terminators + '/='
tokens = (
   'AMP',
   'EN_DASH',
   'EM_DASH',
   'ELLIPSIS',
   'WORD',
)
t_AMP      = r'&'
t_EN_DASH  = r'--'
t_EM_DASH  = r'---'
t_ELLIPSIS = r'\.\.\.'
t_WORD     = r'\w+-\w+|\w+\'\w+|\w+'  # Allow all words, contractions, and dashed words.
t_ignore  = ' \t\n()[]"*-\''

# Locate the leftmost value in 'a' exactly equal to 'x'
def index(a, x):
   i = bisect_left(a, x)
   if i != len(a) and a[i] == x:
      return i
   raise ValueError

# Error handling rule.
def t_error(t):
    print "  Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

# Returns the part of 'path' after the last '/' character in 'path'.
def getBaseFilename(path):
   while '/' in path:
      path = path[(path.index('/')+1):]
   return path

# Given a map with string-type integer keys and values, returns a new map with identical
# integer-type key/values.
def strMapToInt(strMap):
   intMap = {}
   for key in strMap:
      intMap[int(key)] = int(strMap[key])
   return intMap

# given a list of string, returns a map with a key for every string in 'list', mapped
# to index. assumes that returned map is an injection
def invertedMap(list):
   res = {}
   for i in range(0, len(list)):
      res[list[i]] = i
   return res

"""
a text Index backed by a peristent store, according to scheme laid out in persistent.py
"""
class SerialIndex:
   """
   'sourceKey' is the key for the source text in the provided persistent 'store'
   """
   def __init__(self, sourceKey, store):
      if not store.isIndexed(sourceKey):
         raise ValueError(sourceKey + ' not found in store! Remember: use the base name.')
      self.sourceKey = sourceKey
      self.store = store
      self.successorCache = {}

   # Index documentation
   def getFirstId(self):
      return self.store.firstId(self.sourceKey)

   # Index documentation
   def getSuccessors(self, termId):
      # fast path: cache hit
      if termId in self.successorCache:
         return self.successorCache[termId]

      # convert Redis HASH (string keys/values) to integer python dict
      strMap = self.store.successors(termId, self.sourceKey)
      intMap = strMapToInt(strMap)

      # update cache with successor map
      self.successorCache[termId] = intMap
      return intMap

   # Index documentation
   def isLegalSeed(self, termId):
      return len(self.store.successors(termId, self.sourceKey).keys()) != 0

   # Index documentation
   def getSourceKey(self):
      return self.sourceKey

"""
A pre-parsed version of the source text contained in 'filename'. Each whitespace separated
unique word in the source is given an ID, and for any given word-id w, a collection of
words that follow w can be retrived in the form of a frequency distribution.

'filename' should be a path referencing the actual file to open. If serialized, the new
source's key is the base of this filename.
"""
class Index:
   def __init__(self, filename):
      tokens = self.__getTokens(open(filename))
      self.dictionary = list(set(tokens))
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
   Writes the index to the provided persistent store. Uses the *base* filename provided
   to the Index' constructor as a key. Raises ValueError if the store already has an
   entry with this filename key.
   """
   def serialize(self, store):
      if store.isIndexed(self.filename):
         raise ValueError('There is already an index for file: ' + self.filename)

      # the canonical id is the word's id in the Redis store, which may be different
      # from the one used internally. getCanonicalId will return the one and only
      # (potentially brand new) ID for the term referenced by the given instanceId.
      tokenToId = invertedMap(self.dictionary)
      canonMemo = {}  # avoid repeated Redis lookups for a bagillian 'the's
      def getCanonicalId(instanceId):
         if instanceId in canonMemo:
            return canonMemo[instanceId]
         canonKey = store.id(self.dictionary[instanceId])
         if canonKey == None:
            canonKey = store.getNewId()
            store.setIdTermPair(canonKey, self.dictionary[instanceId])
         canonMemo[instanceId] = str(canonKey)
         return str(canonKey)

      # store source term list
      store.setSourceList(self.filename, map(getCanonicalId, self.sourceText))

      # store successors
      for first in self.successors:
         canonFirst = getCanonicalId(first)
         for second in self.successors[first]:
            canonSecond = getCanonicalId(second)
            fileCount = self.successors[first][second]
            store.setSuccessorCount(self.filename, canonFirst, canonSecond, fileCount)

      # store positions
      positions = {}
      pos = 0
      for termId in self.sourceText:
         if not termId in positions:
            positions[termId] = []
         positions[termId].append(pos)
         pos += 1
      for termId in positions:
         store.setPositionList(getCanonicalId(termId), self.filename, positions[termId])

   """
   returns the source key used in serialization of the Index (see persistent.py docs).
   """
   def getSourceKey(self):
      return self.filename

   """
   returns the whitespace tokens from the file, making each terminator punctuator its own
   token and removing all quotes (double and single)
   """
   def __getTokens(self, file):
      lexer = lex()
      tokenized = []
      for line in file:
         lexer.input(line.lower())
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
