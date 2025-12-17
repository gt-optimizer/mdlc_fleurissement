import os
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_optimizer.settings')

application = get_wsgi_application()

venv = os.path.expanduser('~') + '/.venv/'
virtualenv = os.path.join(venv, 'bin/activate_this.py')
try:
    if sys.version.split(' ')[0].split('.')[0] == '3':
        exec(compile(open(virtualenv, "rb").read(), virtualenv, 'exec'), dict(__file__=virtualenv))
    else:
        execfile(virtualenv, dict(__file__=virtualenv))
except IOError:
    pass
sys.path.append(os.path.expanduser('~'))
sys.path.append(os.path.expanduser('~') + '/kichen_optimizer/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'kitchen_optimizer.settings'