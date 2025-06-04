"""
WSGI config for mentoredd project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/

WSGI is a protocol, a standard of comunication between a web server and a web application.
(GUNICORN x DJANGO in this case)

******** https://www.fullstackpython.com/wsgi-servers.html ********
"""

import os

from django.core.wsgi import get_wsgi_application

"""
browser -> nginx -> gunicorn -> django
brower <- nginx <- gunicorn <- django

not necessarily this flow. example: if we want just to serve static files it can be handled by nginx

Nginx:
Acts as a reverse proxy.
Handles incoming HTTP/HTTPS requests from users.
Serves static files (e.g., CSS, JavaScript) and passes dynamic requests to Gunicorn.
Provides load balancing, caching, and SSL termination.

Gunicorn:
A WSGI server that runs your Django application.
Converts incoming HTTP requests from Nginx into a format Django understands (via the WSGI interface).
Runs the application code and returns the response to Nginx.

Django:
The actual web application framework that processes the requests.
Handles the business logic, interacts with the database, and generates dynamic HTML or JSON responses.
"""
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mentoreed.settings.production")

application = get_wsgi_application()
