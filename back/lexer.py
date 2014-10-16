# Lexer rules
terminators = '.?,!:;'
literals = terminators + '/'
tokens = (
   'EN_DASH',
   'EM_DASH',
   'ELLIPSIS',
   'WORD',
)
t_EN_DASH  = r'--'
t_EM_DASH  = r'---'
t_ELLIPSIS = r'\.\.\.'
t_WORD     = r'\w+-\w+|\w+\'\w+|\w+'  # Allow all words, contractions, and dashed words.
t_ignore  = ' \t\n()[]"*-\''