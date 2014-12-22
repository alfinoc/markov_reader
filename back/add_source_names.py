names = [
   ('wutheringheights.txt', 'Wuthering Heights'),
   ('dracula.txt', 'Dracula'),
   ('prideandprejudice.txt', 'Pride and Prejudice'),
   ('countofmontecristo.txt', 'Count of Monte Cristo'),
   ('sherlockholmes.txt', 'Sherlock Holmes'),
   ('warandpeace.txt', 'War and Peace'),
   ('taleoftwocities.txt', 'Tale of Two Cities')
]

from persistent import RedisWrapper

r = RedisWrapper()
for key, name in names:
   r.setSourceName(key, name)
