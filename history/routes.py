from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from models import Proposal, CoverLetter, GigDescription, PricingHistory, ClientReply, Invoice, Contract

history_bp = Blueprint("history", __name__, template_folder="../templates/history")

# Maps the filter slug used in the UI to (Model, display fields, view endpoint)
TYPE_CONFIG = {
    "proposal": {
        "model": Proposal,
        "label": "Proposal",
        "title_field": "project_title",
        "subtitle_field": "client_name",
        "endpoint": "proposals.view_proposal",
        "id_kwarg": "proposal_id",
    },
    "cover_letter": {
        "model": CoverLetter,
        "label": "Cover Letter",
        "title_field": "job_title",
        "subtitle_field": "company_name",
        "endpoint": "cover_letters.view_cover_letter",
        "id_kwarg": "letter_id",
    },
    "gig": {
        "model": GigDescription,
        "label": "Gig Description",
        "title_field": "service_category",
        "subtitle_field": "experience_level",
        "endpoint": "gigs.view_gig",
        "id_kwarg": "gig_id",
    },
    "pricing": {
        "model": PricingHistory,
        "label": "Pricing Calculation",
        "title_field": None,
        "subtitle_field": "complexity",
        "endpoint": "pricing.view_pricing",
        "id_kwarg": "entry_id",
    },
    "client_reply": {
        "model": ClientReply,
        "label": "Client Reply",
        "title_field": "client_message",
        "subtitle_field": "tone",
        "endpoint": "client_replies.view_reply",
        "id_kwarg": "reply_id",
    },
    "invoice": {
        "model": Invoice,
        "label": "Invoice",
        "title_field": "invoice_number",
        "subtitle_field": "client_name",
        "endpoint": "invoices.view_invoice",
        "id_kwarg": "invoice_id",
    },
    "contract": {
        "model": Contract,
        "label": "Contract",
        "title_field": "client_name",
        "subtitle_field": "timeline",
        "endpoint": "contracts.view_contract",
        "id_kwarg": "contract_id",
    },
}


def _title_for(item, config):
    if config["title_field"]:
        value = getattr(item, config["title_field"], None)
        if value:
            return str(value)[:80]
    if config["label"] == "Pricing Calculation" and getattr(item, "suggested_price", None) is not None:
        return f"${item.suggested_price:.2f} calculated"
    return config["label"]


@history_bp.route("/")
@login_required
def index():
    active_filter = request.args.get("type", "all")
    user_id = current_user.id

    items = []
    for slug, config in TYPE_CONFIG.items():
        if active_filter != "all" and active_filter != slug:
            continue
        rows = config["model"].query.filter_by(user_id=user_id).order_by(config["model"].created_at.desc()).all()
        for row in rows:
            items.append({
                "slug": slug,
                "label": config["label"],
                "title": _title_for(row, config),
                "subtitle": getattr(row, config["subtitle_field"], None) if config["subtitle_field"] else None,
                "time": row.created_at,
                "url_endpoint": config["endpoint"],
                "url_kwargs": {config["id_kwarg"]: row.id},
            })

    items.sort(key=lambda i: i["time"], reverse=True)

    filters = [("all", "All")] + [(slug, cfg["label"]) for slug, cfg in TYPE_CONFIG.items()]

    return render_template("history/index.html", items=items, filters=filters, active_filter=active_filter)
