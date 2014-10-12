from bisect import bisect_left
from random import uniform
from collections import OrderedDict
from copy import copy
import redis

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

#DEBUG = False  # makes token indexing more transparent
TERMINATOR = list('.?,!:;')
BRIDGE = ['--', '---', '...', '/']
IGNORE = list('"()[]_\'')

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

"""
A pre-parsed version of the source text contained in 'filename'. Each whitespace separated
unique word in the source is given an ID, and for any given word-id w, a collection of
words that follow w can be retrived in the form of a frequency distribution.
"""
class Index:
   def parseFile(self, filename):
      tokens = self.__getTokens(open(filename))
      self.dictionary = list(set(tokens))
      #self.dictionary.sort()
      tokenToId = invertedMap(self.dictionary)
      self.sourceText = map(lambda str: tokenToId[str], tokens)
      self.successors = self.__getFrequencyMap(tokens, tokenToId)
      self.filename = filename

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
      filename:src -> list<id>
      filename:id -> term_string
      filename:id:succ -> HASH<id, count>
      filename:term -> id
   with id being the term id for every term stored in the index.
   """
   def serialize(self, store):
      def prefixWithFile(keyId):
         return self.filename + ':' + str(keyId)

      # filename:src -> list<id>
      for keyId in self.sourceText:
         store.rpush(self.filename + ':src', keyId)

      # filename:id -> term_string
      for i in range(0, len(self.dictionary)):
         store.set(prefixWithFile(i), self.dictionary[i])

      # filename:id:succ -> HASH<id, count>
      for keyId in self.successors:
         copy = dict()
         for succ in self.successors[keyId]:
            copy[str(succ)] = str(self.successors[keyId][succ])
         store.hmset(prefixWithFile(keyId) + ':succ', copy)

   """
   returns the whitespace tokens from the file, making each terminator punctuator its own
   token and removing all quotes (double and single)
   """
   def __getTokens(self, file):
      tokens = []
      for line in file:
         # handle terminators and the ignore blacklist specially
         line = list(line)
         line = filter(lambda char : not char in IGNORE, line)
         for i in range(len(line)):
            if line[i] in TERMINATOR:
               line.insert(i, ' ')
               i += 1
         line = ''.join(line)

         tokens += line.split()

      # TODO: correct capitalization on non-names

      return tokens

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
         first = tokenToId[tokens[i]]  #index(self.dictionary, tokens[i])      # (tokens[i], i)
         second = tokenToId[tokens[i + 1]] #index(self.dictionary, tokens[i + 1])  # (tokens[i + 1], i)
         if not first in result:
            result[first] = {}
         prevSuccessors = result[first]
         if not second in prevSuccessors:
            prevSuccessors[second] = 1
         else:
            prevSuccessors[second] += 1
      return result

"""
   notes:
   you're going to want to incorporate a dec english dictionary here. for capitalization,
   only store the lowercase version for dictionary words (exclude names).

   going to need to handle terminator punctuation in a special way
   fuck am i going to do with --? ...?

"""
