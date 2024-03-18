from quart import Blueprint
from quart.templating import render_template

blueprint = Blueprint(
    "marketing",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/marketing",
)


@blueprint.route("/")
async def index():
    return await render_template("marketing/index.html")
