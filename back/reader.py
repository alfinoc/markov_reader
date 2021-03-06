from json import loads
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
      return self.last

   """
   returns the last value returned from next, or, if next has not been called, returns
   the initial seed
   """
   def previous(self):
      return self.last

   """
   seeds the reader with a starting phrase 'start'
   after a call to seed(start), subsequent next() calls will behave as if the previous
   call to next() returned start
   raises ValueError if 'start' is not a known term, or 'start' has no successors within
   this Reader's source
   """
   def seed(self, start):
      if not self.index.isLegalSeed(start):
         raise ValueError('Term ID {0} has no successors.'.format(start))
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

"""
A scanner for reading simultaneously from multiple Index objects. At any given time, the
MultiReader is "reading" one Index in the sense that calls to next() return successors
in that Index.
"""
class MultiReader:
   """
   builds a scanner around all of the provided Index objects. initially, calls to next()
   will read from the first Index in the provided list.
   """
   def __init__(self, indices):
      if len(indices) == 0:
         raise ValueError('provide at least one Index')
      self.readers = map(Reader, indices)
      self.sourceKeys = map(lambda i : i.getSourceKey(), indices)
      self.current = 0
      # We need to store last again here since the client could switch the index any
      # number of times between calls to next and previous.
      self.last = self.__getCurrentReader().previous()

   """
   returns the next term from the current Index (see Reader doc)
   """
   def next(self):
      self.last = self.__getCurrentReader().next()
      return self.last

   """
   returns the last term returned by next() (see Reader doc)
   """
   def previous(self):
      return self.last

   """
   seeds the reader with a starting phrase 'start' (see Reader doc). if the seed is not
   a known term in the current index, switches the index to the first
   raises ValueError if 'start' is not a known term in *any* stored Index.
   """
   def seed(self, start):
      for i in range(len(self.readers)):
         try:
            self.__getCurrentReader().seed(start)
            #self.last = start
            return
         except ValueError:
            self.__progressCurrentReader()
      raise ValueError('No term with ID {0} in any of the indices.'.format(start))

   """
   attempts to switch the current Index to another, seeding the new current Index with
   the previous term. if no other Index can be seeded this way, does not change the
   current Index. consecutive calls to switchIndex will cycle through the indices
   round robin with respect to the order provided to the constructor.
   """
   def switchIndex(self):
      self.__progressCurrentReader()
      self.seed(self.last)

   """
   returns the source key of the Index currently being read
   """
   def getCurrentSourceKey(self):
      return self.sourceKeys[self.current]

   """
   returns the Reader currently reading
   """
   def __getCurrentReader(self):
      return self.readers[self.current]

   """
   progresses the current Index index (lol) one more, mod the number of indices
   """
   def __progressCurrentReader(self):
      self.current += 1
      self.current %= len(self.readers)
