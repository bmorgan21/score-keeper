from quart import Blueprint

from .auth import blueprint as auth_blueprint
from .event import blueprint as event_blueprint
from .post import blueprint as post_blueprint
from .team import blueprint as team_blueprint
from .token import blueprint as token_blueprint
from .user import blueprint as user_blueprint

blueprint = Blueprint("api", __name__)

blueprint.register_blueprint(auth_blueprint, url_prefix="/auth")
blueprint.register_blueprint(event_blueprint, url_prefix="/event")
blueprint.register_blueprint(post_blueprint, url_prefix="/post")
blueprint.register_blueprint(team_blueprint, url_prefix="/team")
blueprint.register_blueprint(token_blueprint, url_prefix="/token")
blueprint.register_blueprint(user_blueprint, url_prefix="/user")
