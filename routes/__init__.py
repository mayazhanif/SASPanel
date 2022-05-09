from urllib.parse import urlparse
from flask import Blueprint,request

routes = Blueprint('routes', __name__)
@routes.app_context_processor
def server_host():
    o = urlparse(request.base_url)
    hosturl = o.hostname
    return dict(
        mainhost = hosturl,
    )