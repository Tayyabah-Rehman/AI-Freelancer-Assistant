from flask import Blueprint, render_template
from flask_login import login_required

modules_bp = Blueprint("modules", __name__, template_folder="../templates/modules")

# Each entry: (url_slug, page_title, arriving_on_day)
# Day 2 replaced 'proposals' and 'cover_letters' with real blueprints - removed below.
# Day 3 replaces 'gigs' and 'pricing'. Day 4 replaces 'client_replies',
# 'invoices', 'contracts'. This keeps every Quick Action link on the
# dashboard working from Day 1 onward with zero broken buttons.
# All modules through Day 4 are now real blueprints. This dict is kept empty
# and the route below stays as a graceful fallback in case a future module
# needs a temporary placeholder page again.
COMING_SOON_PAGES = {}


@modules_bp.route("/<slug>")
@login_required
def coming_soon(slug):
    title, day = COMING_SOON_PAGES.get(slug, ("This Feature", "a future"))
    return render_template("modules/coming_soon.html", title=title, day=day, slug=slug)
