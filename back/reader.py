from random import uniform

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
      if self.index.getTerm(start) == None:
         raise ValueError('No term with ID ' + str(start))
      self.last = start

   """
   given 'distribution', a map from choice to frequency of that choices, returns a sample
   from key with probability proportional to the key's frequency / (sum of all values)
   """
   def __sample(self, distribution):
      total = sum(distribution.values()) * 1.0
      roll = uniform(0, total)

      thusFar = 0
      for choice in distribution:
         thusFar += distribution[choice]
         if thusFar >= roll:
            return choice
