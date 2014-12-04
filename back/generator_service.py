from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, BadRequest
import json

from persistent import RedisWrapper
from reader import MultiReader, generateBlock
from index import SerialIndex

"""
returns the value in 'dict' for 'key', or 'default' if there is none.
"""
def defaultValue(dict, key, default):
   return dict[key] if key in dict else default

class GeneratorService(object):
   """
   generate a block of text according to the params of the provided 'request',
   returned BadRequest's for missing required arguments and bogus
   """
   def get_text_block(self, request):
      args = request.args
      try:
         seed = defaultValue(args, 'seed', '')
         length = int(defaultValue(args, 'length', 500))
         sequential = int(defaultValue(args, 'sequential', 1))
      except:
         return BadRequest('\'seed\', \'length\', \'sequential\' should all be integers.')
      
      if not 'sources' in args:
         return BadRequest('Required param: sources.')
      try:
         sources = filter(lambda s : len(s) > 0, request.args['sources'].split(','))
         if len(sources) < 1:
            return BadRequest('Provide at least one source.')
      except:
         return BadRequest('Malformed source list.')

      # Load SerialIndex for each requested file.
      for srcKey in sources:
         if not self.store.isIndexed(srcKey):
            # TODO: Automatically generate index if the file is present; else, error.
            return BadRequest('Unrecognized file name: \'{0}'.format(srcKey))

      # Attempt to seed reader with provided seed.
      indices = map(lambda srcKey : SerialIndex(srcKey, self.store), sources)
      reader = MultiReader(indices)
      try:
         reader.seed(self.store.id(seed))
      except ValueError:
         # Silently default to the Reader's good judgement. This usually means using
         # to the first term in the source text if the seed can't be found.
         pass

      block = generateBlock(seed, length, sequential, reader, self.store)
      return Response(json.dumps({ 'generated': block }))

   def get_source_list(self, request):
      nameToFile = {}
      files = self.store.stored()
      for key in files:
         name = self.store.sourceName(key)
         # If there's no descriptive name stored, just use the filename.
         if not name:
            name = key
         nameToFile[name] = key
      return Response(json.dumps(nameToFile))

   def get_meta_data(self, request):
      if 'terms' not in request.args:
         return BadRequest('Required param: terms.')
      try:
         #terms = json.loads(request.args['terms'])['terms']
         terms = filter(lambda s : len(s) > 0, request.args['terms'].split(','))
      except:
         return BadRequest('Malformed JSON term list.')
      try:
         ids = map(self.store.id, terms)
         resp = {}
         for i in range(len(ids)):
            resp[terms[i]] = { 'positions': self.store.allPositions(ids[i]) }
         return Response(json.dumps(resp))
      except:
         return BadRequest('Error retrieving term positions.')

   """
   dispatch requests to appropriate functions above
   """
   def __init__(self):
      self.url_map = Map([
         Rule('/generate', endpoint='text_block'),
         Rule('/meta', endpoint='meta_data'),
         Rule('/available', endpoint='source_list'),
         Rule('/<all>', redirect_to='play/api.html'),

      ])
      self.store = RedisWrapper()

   def wsgi_app(self, environ, start_response):
      request = Request(environ);
      response = self.dispatch_request(request);
      return response(environ, start_response);

   def __call__(self, environ, start_response):
      return self.wsgi_app(environ, start_response)

   def dispatch_request(self, request):
      adapter = self.url_map.bind_to_environ(request.environ)
      try:
         endpoint, values = adapter.match()
         return getattr(self, 'get_' + endpoint)(request, **values)
      except HTTPException, e:
         return e

   def get_otherwise(self, request):
      return Response('api coming soon...')
