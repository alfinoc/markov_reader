import os
from werkzeug.wsgi import SharedDataMiddleware
from generator_service import GeneratorService

def create_app():
   return ForwardService()

if __name__ == '__main__':
   from werkzeug.serving import run_simple
   app = GeneratorService()
   # for debugging/development, set use_debugger=True, use_reloader=True,
   run_simple('localhost', 5005, app, use_reloader=True)