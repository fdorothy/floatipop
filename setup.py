import sys
from distutils.core import setup

# dependencies
try:
    import pygame
except ImportError:
    print 'pygame required'
    sys.exit(1)

try:
    import py2exe
except ImportError:
    pass

setup(name = 'floatipop',
      version = '0.1',
      description = 'Float-i-pop',
      author = 'Mark Dillavou',
      author_email = 'line72@users.sf.net',
      url = 'http://www.uab.edu/gamedev/',
      license = 'GPL',
      package_dir = {'floatipop': 'src'},
      packages = ['floatipop'],
      data_files = [('share/floatipop', ['AUTHORS', 'ChangeLog', 'LICENSE', 'README']),
                    ('share/floatipop/data', ['data/background.png', 'data/battleofsteel.xm', 'data/blank.png', 'data/clouds.png', 'data/highscores.png', 'data/menu.png', 'data/platform.png', 'data/player-0.png', 'data/player-1.png', 'data/player-2.png', 'data/player-3.png', 'data/star.png', 'data/water.png']),
                    ],
      scripts = ['floatipop'],
      options = {'py2exe': {'compressed' : 1,
                            },
                 },
      windows = ['floatipop'],
      )
                    
