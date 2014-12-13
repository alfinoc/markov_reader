import os
from werkzeug.wsgi import SharedDataMiddleware
from generator_service import GeneratorService

def create_app():
   return ForwardService()

if __name__ == '__main__':
   from werkzeug.serving import run_simple
   app = GeneratorService()
   app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
      '/play':  os.path.join(os.path.dirname(__file__), '../front'),
      #'/source':  os.path.join(os.path.dirname(__file__), '../books')
   })
   # for debugging/development, set use_debugger=True, use_reloader=True,
   run_simple('localhost', 5000, app, use_reloader=True)