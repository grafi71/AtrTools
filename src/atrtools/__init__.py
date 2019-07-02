import os
import logging

logging.basicConfig(level=os.environ.get('PYTHON_LOGGING', 'ERROR'),
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M')


