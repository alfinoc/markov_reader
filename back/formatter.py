from index import terminators, noLeftSpace
from generator import getProto

"""
returns 'src1' if both arguments are equal and non-empty; otherwise returns ''
"""
def _srcUnion(src1, src2):
   if src1 == src2 and src1 != '':
      return src1
   else:
      return ''  # two sources

"""
returns the union of two protos
"""
def _conjoinProto(p1, p2):
   return getProto(p1['term'] + p2['term'], _srcUnion(p1['src'], p2['src']), p1['term'])

"""
returns a new map where each (key, value) pair is a (value, key) pair in
provided dict. assumes the map is invertible (bijective)
"""
def _invert(dict):
   res = {}
   for k in dict:
      res[dict[k]] = k
   return res

"""
capitalizes the terms in the sequence that follow terminators immediately, modifying
argument list.
"""
def capitalize(sequence):
   lastWasTerminator = False
   for bundle in sequence:
      term = bundle['term']
      if len(term) > 0:
         if lastWasTerminator:
            term = term[0].upper() + term[1:]
      bundle['term'] = term
      lastWasTerminator = term in terminators

"""
conjoins adjacent protos where the second term is a puncatuator with no space to
its left (like ',' or '.'), modifying and potentially shortening argument list.
"""
def condensePunctuation(sequence):
   res = []
   i = 0
   while i + 1 < len(sequence):
      term1 = sequence[i]['term']
      term2 = sequence[i + 1]['term']
      if not term1 in noLeftSpace and term2 in noLeftSpace:
         sequence[i] = _conjoinProto(sequence[i], sequence[i + 1])
         del sequence[i + 1]
      i += 1

"""
adds a space after each term, modifying argument list.
"""
def spaces(sequence):
   for proto in sequence:
      proto['term'] += ' '

"""
returns a map from unique integer ID to redis source key, applying translating
the 'src' attribute of each proto in 'sequence' according to this encoding.
"""
def encodeSourceKeys(sequence):
   localSourceMap = {}
   localId = 0         
   for proto in sequence:
      if len(proto) > 1:
         srcKey = proto['src']
         if not srcKey in localSourceMap:
            localSourceMap[srcKey] = localId
            localId += 1
         proto['src'] = localSourceMap[srcKey]
      else:
         proto.append('')
   localSourceMap = _invert(localSourceMap);
   return localSourceMap
