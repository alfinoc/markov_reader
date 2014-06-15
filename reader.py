from bisect import bisect_left
from random import uniform
from collections import OrderedDict

"""
Locate the leftmost value in 'a' exactly equal to 'x'
"""
def index(a, x):
   i = bisect_left(a, x)
   if i != len(a) and a[i] == x:
      return i
   raise ValueError

#DEBUG = False  # makes token indexing more transparent
TERMINATOR = list('.?,!:;')
QUOTES = list('"')

class Reader:
   def __init__(self, filename):
      tokens = self.__getTokens(open(filename))
      self.dictionary = list(set(tokens))
      self.dictionary.sort()
      self.successors = self.__getFrequencyMap(tokens)
      self.last = index(self.dictionary, tokens[0]) if len(tokens) != 0 else None

   """
   let p be the last phrase returned. a subsequent call to "next()" returns a successor s
   to p in the source text chosen according to the frequency with which s succeeds p
   relative to p's other successors
   """
   def next(self):
      self.last = self.__sample(self.successors[self.last])
      return self.dictionary[self.last]

   """
   returns the last value returned from next, or, if next has not been called, returns
   the initial seed
   """
   def previous(self):
      return self.dictionary[self.last]

   """
   seeds the reader with a starting phrase 'start'
   after a call to seed(start), subsequent next() calls will behave as if the previous
   call to next() returned stat
   raises ValueError if 'start' is not a known term
   """
   def seed(self, start):
      if not start in self.dictionary:
         raise ValueError
      self.last = start

   def getSuccessors(self, term):
      pass

   """
   returns the whitespace tokens from the file, making each terminator punctuator its own
   token and removing all quotes (double and single)
   """
   def __getTokens(self, file):
      tokens = []
      for line in file:
         # handle terminators and quotes specially
         line = list(line)
         line = filter(lambda char : not char in QUOTES, line)
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
   of tokens (a, b) and returned map m, m[a][b] returns the number of times "a b" appears
   in immediate sequence in tokens

   the returned map uses integer indices to identify tokens. these indices correspond to
   the values stored in self.dictionary
   """
   def __getFrequencyMap(self, tokens):
      result = {}
      for i in range(len(tokens) - 1):
         first  = index(self.dictionary, tokens[i])      # (tokens[i], i)
         second = index(self.dictionary, tokens[i + 1])  # (tokens[i + 1], i)
         if not first in result:
            result[first] = {}
         prevSuccessors = result[first]
         if not second in prevSuccessors:
            prevSuccessors[second] = 1
         else:
            prevSuccessors[second] += 1
      return result

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
   notes:
   you're going to want to incorporate a dec english dictionary here. for capitalization,
   only store the lowercase version for dictionary words (exclude names).

   going to need to handle terminator punctuation in a special way
   fuck am i going to do with --? ...?

"""