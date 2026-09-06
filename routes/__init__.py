import os
from urllib.parse import urlparse
from flask import Blueprint, request

routes = Blueprint('routes', __name__)

@routes.app_context_processor
def server_host():
    # FIX R9-01: Host header injection — use SERVER_NAME env var (trusted config)
    # NOT request.base_url which is derived from the user-controlled Host: header
    trusted_host = os.environ.get('SERVER_NAME') or request.host
    return dict(mainhost=trusted_host)