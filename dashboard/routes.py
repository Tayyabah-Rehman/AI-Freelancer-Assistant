from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models import Proposal, CoverLetter, Invoice, Contract, GigDescription, ClientReply, PricingHistory

dashboard_bp = Blueprint("dashboard", __name__, template_folder="../templates/dashboard")


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    user_id = current_user.id

    stats = {
        "proposals": Proposal.query.filter_by(user_id=user_id).count(),
        "cover_letters": CoverLetter.query.filter_by(user_id=user_id).count(),
        "invoices": Invoice.query.filter_by(user_id=user_id).count(),
        "contracts": Contract.query.filter_by(user_id=user_id).count(),
        "gig_descriptions": GigDescription.query.filter_by(user_id=user_id).count(),
        "client_replies": ClientReply.query.filter_by(user_id=user_id).count(),
        "pricing_calculations": PricingHistory.query.filter_by(user_id=user_id).count(),
    }

    # "Active Clients" = distinct client names seen across proposals + invoices + contracts
    proposal_clients = {
        p.client_name for p in Proposal.query.filter_by(user_id=user_id).all() if p.client_name
    }
    invoice_clients = {
        i.client_name for i in Invoice.query.filter_by(user_id=user_id).all() if i.client_name
    }
    contract_clients = {
        c.client_name for c in Contract.query.filter_by(user_id=user_id).all() if c.client_name
    }
    stats["active_clients"] = len(proposal_clients | invoice_clients | contract_clients)

    # Recent activity feed - merges the most recent item from each module
    activity = []
    for p in Proposal.query.filter_by(user_id=user_id).order_by(Proposal.created_at.desc()).limit(5):
        activity.append({"type": "Proposal", "title": p.project_title or "Untitled proposal", "time": p.created_at})
    for c in CoverLetter.query.filter_by(user_id=user_id).order_by(CoverLetter.created_at.desc()).limit(5):
        activity.append({"type": "Cover Letter", "title": c.job_title or "Untitled cover letter", "time": c.created_at})
    for inv in Invoice.query.filter_by(user_id=user_id).order_by(Invoice.created_at.desc()).limit(5):
        activity.append({"type": "Invoice", "title": inv.invoice_number or "Untitled invoice", "time": inv.created_at})
    for g in GigDescription.query.filter_by(user_id=user_id).order_by(GigDescription.created_at.desc()).limit(5):
        activity.append({"type": "Gig Description", "title": g.service_category or "Untitled gig", "time": g.created_at})
    for pr in PricingHistory.query.filter_by(user_id=user_id).order_by(PricingHistory.created_at.desc()).limit(5):
        activity.append({"type": "Pricing", "title": f"${pr.suggested_price:.2f} calculated", "time": pr.created_at})
    for ct in Contract.query.filter_by(user_id=user_id).order_by(Contract.created_at.desc()).limit(5):
        activity.append({"type": "Contract", "title": ct.client_name or "Untitled contract", "time": ct.created_at})
    for cr in ClientReply.query.filter_by(user_id=user_id).order_by(ClientReply.created_at.desc()).limit(5):
        activity.append({"type": "Client Reply", "title": (cr.client_message[:40] + "...") if cr.client_message else "Reply", "time": cr.created_at})

    activity.sort(key=lambda a: a["time"], reverse=True)
    activity = activity[:6]

    return render_template("dashboard/index.html", stats=stats, activity=activity)
