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

class Index:
   def __init__(self, filename):
      tokens = self.__getTokens(open(filename))
      self.dictionary = list(set(tokens))
      self.dictionary.sort()
      self.successors = self.__getFrequencyMap(tokens)
      self.last = index(self.dictionary, tokens[0]) if len(tokens) != 0 else None

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
   of tokens (a, b) and returned map m, m[a][b] is the number of times "a b" appears
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
   notes:
   you're going to want to incorporate a dec english dictionary here. for capitalization,
   only store the lowercase version for dictionary words (exclude names).

   going to need to handle terminator punctuation in a special way
   fuck am i going to do with --? ...?

"""