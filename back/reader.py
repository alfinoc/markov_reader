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
   """
   builds a reader around the provided index, 
   """
   def __init__(self, index):
      self.index = index
      # TODO: lol this won't work in general
      self.last = self.index.last
      print self.last, self.index.getTerm(self.last)

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
