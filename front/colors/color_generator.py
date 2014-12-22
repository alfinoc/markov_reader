SRCS = ['wutheringheights.txt', 'dracula.txt', 'warandpeace.txt', 'prideandprejudice.txt',
        'taleoftwocities.txt', 'sherlockholmes.txt', 'countofmontecristo.txt']
COLORS = ['#C75646', '#218693', '#C8A0D1', '#8EB33B', '#D0B03C']
# RED, TEAL, PURPLE, GREEN, YELLOW

def triple(hex):
   if len(hex) < 6:
      raise ValueError('hex color must be at least 6 characters long')
   top = hex[-6:]
   r = int(top[:2], 16)
   g = int(top[2:4], 16)
   b = int(top[4:], 16)
   return '%d, %d, %d' % (r, g, b)

def rgb(hex):
   return 'rgb(%s)' % triple(hex)

def rgba(hex, a):
   return 'rgba(%s, %f)' % (triple(hex), a)

def getTemplateContents(filename):
   f = file(filename)
   res = ''
   for l in f:
      res += l
   return res

def getColorPairings():
   res = []
   last = 0
   for s in SRCS:
      c = COLORS[last]
      last += 1
      last %= len(COLORS)
      res.append({'srcKey': s, 'color': c})
   return res

from jinja2 import Template, Environment
env = Environment()
env.filters['rgb'] = rgb
env.filters['rgba'] = rgba
template = env.from_string(getTemplateContents('colors.template'))
print template.render(sources=getColorPairings())
