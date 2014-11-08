from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, BadRequest
import redis
import json

from reader import *

REDIS_HOST = 'localhost'
REDIS_PORT = '6379'

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
      if not 'filename' in args:
         return BadRequest('Required param: filename.')

      try:
         seed = args['seed']
         length = int(defaultValue(args, 'length', 500))
         sequential = int(defaultValue(args, 'sequential', 1))
      except:
         return BadRequest('\'seed\', \'length\', \'sequential\' should all be integers')
      filename = args['filename']
      randomLength = 'random_sequential' in args

      # Load SerialIndex with the requested file.
      if self.store.exists(filename + ':src'):
         index = SerialIndex(filename, self.store)
      else:
         # TODO: Automatically generate index if the file is present; else, error.
         return Response('Unrecognized file name: \'{0}'.format(filename))

      # Attempt to seed reader with provided seed
      reader = Reader(index)
      try:
         reader.seed(self.store.get(seed + ':id'))
      except ValueError:
         # Silently default to Reader's default.
         pass

      # Compose a list of terms.
      generatedList = [reader.previous()]
      for i in range(length):
         generatedList.append(reader.next())
      return Response('\'generated\': ' + str(generatedList))

   def get_source(self, request):
      return Response('lol srcin')

   def get_source_list(self, request):
      nameToFile = {}
      files = self.store.keys('*:src')
      for key in files:
         file = key[:-len(':src')]
         name = self.store.get(file + ':name')
         # If there's no descriptive name stored, just use the filename
         if not name:
            name = file
         nameToFile[name] = file
      return Response('\'sources\': ' + json.dumps(nameToFile))

   """
   dispatch requests to appropriate functions above
   """
   def __init__(self):
      self.url_map = Map([
         Rule('/', endpoint='otherwise'),
         Rule('/generate', endpoint='text_block'),
         Rule('/source', endpoint='source'),
         Rule('/available', endpoint='source_list')
      ])
      self.store = redis.Redis(REDIS_HOST, port=REDIS_PORT)

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
      return Response('api coming soon...for now experiment with /available, /generate, /source')
