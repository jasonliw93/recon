"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

from django.core.wsgi import get_wsgi_application
from werkzeug.wsgi import DispatcherMiddleware


import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recon_site.settings")
os.environ.setdefault("CELERY_LOADER", "django")
from django.conf import settings

from pywb.framework.wsgi_wrappers import init_app, start_wsgi_server
from pywb.webapp.pywb_init import create_wb_router
#from pywb.utils.loaders import load_yaml_config
from pywb.webapp.views import add_env_globals

#config = load_yaml_config('/var/www/recon/config.yaml')
add_env_globals({'static_path': settings.STATIC_URL})

application = DispatcherMiddleware(
    get_wsgi_application(),  # Django
    {
        '/warc': init_app(create_wb_router, load_yaml=True, config_file='/var/www/recon/warc/config.yaml'),
    }
)
