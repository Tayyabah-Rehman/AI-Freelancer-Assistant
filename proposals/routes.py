from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user

from extensions import db, limiter
from models import Proposal
from proposals.forms import ProposalForm
from ai_service import call_groq, AIGenerationError, has_credits, deduct_credit, user_api_key
from pdf_service import generate_proposal_pdf

proposals_bp = Blueprint("proposals", __name__, template_folder="../templates/proposals")


def _build_prompt(data):
    system_prompt = (
        f"You are an expert freelance proposal writer. Write a persuasive, concise "
        f"client proposal (250-350 words) in a {data['tone']} tone. Write it ready "
        f"to send - no placeholders like [Your Name], no headings, just the proposal body."
    )
    user_prompt = (
        f"Client Name: {data['client_name']}\n"
        f"Project Title: {data['project_title']}\n"
        f"Project Description: {data['project_description']}\n"
        f"Relevant Skills: {data['skills']}\n"
        f"Budget: {data.get('budget') or 'Not specified'}\n"
        f"Timeline: {data.get('timeline') or 'Not specified'}\n\n"
        f"Write a proposal addressed to this client highlighting fit, approach, "
        f"and clear next steps."
    )
    return system_prompt, user_prompt


def _form_to_data(form):
    return {
        "client_name": form.client_name.data.strip(),
        "project_title": form.project_title.data.strip(),
        "project_description": form.project_description.data.strip(),
        "skills": form.skills.data.strip(),
        "budget": form.budget.data.strip() if form.budget.data else None,
        "timeline": form.timeline.data.strip() if form.timeline.data else None,
        "tone": form.tone.data,
    }


@proposals_bp.route("/")
@login_required
def list_proposals():
    proposals = (
        Proposal.query.filter_by(user_id=current_user.id)
        .order_by(Proposal.created_at.desc())
        .all()
    )
    return render_template("proposals/list.html", proposals=proposals)


@proposals_bp.route("/new", methods=["GET", "POST"])
@limiter.limit("20 per hour")
@login_required
def new_proposal():
    form = ProposalForm()
    if form.validate_on_submit():
        if not has_credits(current_user):
            flash("You're out of AI credits. Please top up to generate more content.", "danger")
            return redirect(url_for("proposals.list_proposals"))

        data = _form_to_data(form)
        system_prompt, user_prompt = _build_prompt(data)

        try:
            generated = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
        except AIGenerationError as e:
            flash(str(e), "danger")
            return render_template("proposals/form.html", form=form, mode="new")

        proposal = Proposal(user_id=current_user.id, generated_content=generated, **data)
        db.session.add(proposal)
        deduct_credit(current_user)
        db.session.commit()

        flash("Proposal generated successfully.", "success")
        return redirect(url_for("proposals.view_proposal", proposal_id=proposal.id))

    return render_template("proposals/form.html", form=form, mode="new")


@proposals_bp.route("/<int:proposal_id>")
@login_required
def view_proposal(proposal_id):
    proposal = Proposal.query.filter_by(id=proposal_id, user_id=current_user.id).first_or_404()
    return render_template("proposals/view.html", proposal=proposal)


@proposals_bp.route("/<int:proposal_id>/edit", methods=["GET", "POST"])
@login_required
def edit_proposal(proposal_id):
    proposal = Proposal.query.filter_by(id=proposal_id, user_id=current_user.id).first_or_404()
    form = ProposalForm(obj=proposal)

    if form.validate_on_submit():
        data = _form_to_data(form)
        for key, value in data.items():
            setattr(proposal, key, value)
        db.session.commit()
        flash("Proposal details updated. Regenerate to refresh the AI content.", "success")
        return redirect(url_for("proposals.view_proposal", proposal_id=proposal.id))

    return render_template("proposals/form.html", form=form, mode="edit", proposal=proposal)


@proposals_bp.route("/<int:proposal_id>/regenerate", methods=["POST"])
@limiter.limit("20 per hour")
@login_required
def regenerate_proposal(proposal_id):
    proposal = Proposal.query.filter_by(id=proposal_id, user_id=current_user.id).first_or_404()

    if not has_credits(current_user):
        flash("You're out of AI credits. Please top up to regenerate.", "danger")
        return redirect(url_for("proposals.view_proposal", proposal_id=proposal.id))

    data = {
        "client_name": proposal.client_name,
        "project_title": proposal.project_title,
        "project_description": proposal.project_description,
        "skills": proposal.skills,
        "budget": proposal.budget,
        "timeline": proposal.timeline,
        "tone": proposal.tone,
    }
    system_prompt, user_prompt = _build_prompt(data)

    try:
        generated = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
    except AIGenerationError as e:
        flash(str(e), "danger")
        return redirect(url_for("proposals.view_proposal", proposal_id=proposal.id))

    proposal.generated_content = generated
    deduct_credit(current_user)
    db.session.commit()
    flash("Proposal regenerated.", "success")
    return redirect(url_for("proposals.view_proposal", proposal_id=proposal.id))


@proposals_bp.route("/<int:proposal_id>/save-content", methods=["POST"])
@login_required
def save_content(proposal_id):
    proposal = Proposal.query.filter_by(id=proposal_id, user_id=current_user.id).first_or_404()
    proposal.generated_content = request.form.get("generated_content", proposal.generated_content)
    db.session.commit()
    flash("Your edits were saved.", "success")
    return redirect(url_for("proposals.view_proposal", proposal_id=proposal.id))


@proposals_bp.route("/<int:proposal_id>/delete", methods=["POST"])
@login_required
def delete_proposal(proposal_id):
    proposal = Proposal.query.filter_by(id=proposal_id, user_id=current_user.id).first_or_404()
    db.session.delete(proposal)
    db.session.commit()
    flash("Proposal deleted.", "info")
    return redirect(url_for("proposals.list_proposals"))


@proposals_bp.route("/<int:proposal_id>/pdf")
@login_required
def download_pdf(proposal_id):
    proposal = Proposal.query.filter_by(id=proposal_id, user_id=current_user.id).first_or_404()
    buffer = generate_proposal_pdf(proposal)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"proposal_{proposal.id}.pdf",
    )
