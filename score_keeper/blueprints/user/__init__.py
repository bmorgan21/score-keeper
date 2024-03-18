from quart import Blueprint, current_app, redirect, request, url_for
from quart.templating import render_template
from quart_auth import current_user, login_required

from score_keeper import actions, enums
from score_keeper.lib.auth import Forbidden

blueprint = Blueprint(
    "user", __name__, template_folder="templates", static_folder="static"
)


@blueprint.route("/<int:id>/edit/")
@login_required
async def update(id):
    user = await current_user.get_user()
    obj = await actions.user.get(user, id=id)

    if not actions.user.has_permission(user, obj, enums.Permission.UPDATE):
        raise Forbidden()

    modal = 1 if "modal" in request.args else None

    return await render_template(
        "user/create.html",
        user=obj,
        base_template="modal_base.html" if modal else None,
    )
