import os
from generator_service import GeneratorService
from werkzeug.wsgi import SharedDataMiddleware

def create_app():
   app = GeneratorService()
   app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
      '/api.html':  os.path.join(os.path.dirname(__file__), '../front/api.html'),
      '/api.css':  os.path.join(os.path.dirname(__file__), '../front/api.css'),
      '/main.css':  os.path.join(os.path.dirname(__file__), '../front/main.css'),

      #'/play':  os.path.join(os.path.dirname(__file__), '../front/index_vulc.html'),
      '/play':     os.path.join(os.path.dirname(__file__), '../front'),
   })
   return app