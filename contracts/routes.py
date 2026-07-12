from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user

from extensions import db, limiter
from models import Contract
from contracts.forms import ContractForm
from ai_service import call_groq, AIGenerationError, has_credits, deduct_credit, user_api_key
from pdf_service import generate_contract_pdf

contracts_bp = Blueprint("contracts", __name__, template_folder="../templates/contracts")


def _build_prompt(data):
    system_prompt = (
        "You are a contract drafting assistant for freelancers. Write a clear, professional "
        "freelance service agreement based on the details below. Include sections for Scope "
        "of Work, Timeline, Payment Terms, and Terms & Conditions. Write it ready to use - "
        "use the names given directly instead of placeholders like [Client Name]. Keep it "
        "well-structured with clear paragraph breaks, around 300-450 words."
    )
    user_prompt = (
        f"Freelancer: {data['freelancer_name']}\n"
        f"Client: {data['client_name']}\n"
        f"Project Scope: {data['project_scope']}\n"
        f"Timeline: {data['timeline']}\n"
        f"Payment Terms: {data['payment_terms']}\n"
        f"Additional Terms & Conditions: {data.get('terms_conditions') or 'None specified'}\n"
    )
    return system_prompt, user_prompt


def _form_to_data(form):
    return {
        "client_name": form.client_name.data.strip(),
        "freelancer_name": form.freelancer_name.data.strip(),
        "project_scope": form.project_scope.data.strip(),
        "timeline": form.timeline.data.strip(),
        "payment_terms": form.payment_terms.data.strip(),
        "terms_conditions": form.terms_conditions.data.strip() if form.terms_conditions.data else None,
    }


@contracts_bp.route("/")
@login_required
def list_contracts():
    contracts = (
        Contract.query.filter_by(user_id=current_user.id)
        .order_by(Contract.created_at.desc())
        .all()
    )
    return render_template("contracts/list.html", contracts=contracts)


@contracts_bp.route("/new", methods=["GET", "POST"])
@limiter.limit("20 per hour")
@login_required
def new_contract():
    form = ContractForm()
    if not form.freelancer_name.data:
        form.freelancer_name.data = current_user.name

    if form.validate_on_submit():
        if not has_credits(current_user):
            flash("You're out of AI credits. Please top up to generate more content.", "danger")
            return redirect(url_for("contracts.list_contracts"))

        data = _form_to_data(form)
        system_prompt, user_prompt = _build_prompt(data)

        try:
            generated = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
        except AIGenerationError as e:
            flash(str(e), "danger")
            return render_template("contracts/form.html", form=form, mode="new")

        contract = Contract(user_id=current_user.id, generated_content=generated, **data)
        db.session.add(contract)
        deduct_credit(current_user)
        db.session.commit()

        flash("Contract generated successfully.", "success")
        return redirect(url_for("contracts.view_contract", contract_id=contract.id))

    return render_template("contracts/form.html", form=form, mode="new")


@contracts_bp.route("/<int:contract_id>")
@login_required
def view_contract(contract_id):
    contract = Contract.query.filter_by(id=contract_id, user_id=current_user.id).first_or_404()
    return render_template("contracts/view.html", contract=contract)


@contracts_bp.route("/<int:contract_id>/edit", methods=["GET", "POST"])
@login_required
def edit_contract(contract_id):
    contract = Contract.query.filter_by(id=contract_id, user_id=current_user.id).first_or_404()
    form = ContractForm(obj=contract)

    if form.validate_on_submit():
        data = _form_to_data(form)
        for key, value in data.items():
            setattr(contract, key, value)
        db.session.commit()
        flash("Contract details updated. Regenerate to refresh the AI content.", "success")
        return redirect(url_for("contracts.view_contract", contract_id=contract.id))

    return render_template("contracts/form.html", form=form, mode="edit", contract=contract)


@contracts_bp.route("/<int:contract_id>/regenerate", methods=["POST"])
@limiter.limit("20 per hour")
@login_required
def regenerate_contract(contract_id):
    contract = Contract.query.filter_by(id=contract_id, user_id=current_user.id).first_or_404()

    if not has_credits(current_user):
        flash("You're out of AI credits. Please top up to regenerate.", "danger")
        return redirect(url_for("contracts.view_contract", contract_id=contract.id))

    data = {
        "client_name": contract.client_name,
        "freelancer_name": contract.freelancer_name,
        "project_scope": contract.project_scope,
        "timeline": contract.timeline,
        "payment_terms": contract.payment_terms,
        "terms_conditions": contract.terms_conditions,
    }
    system_prompt, user_prompt = _build_prompt(data)

    try:
        generated = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
    except AIGenerationError as e:
        flash(str(e), "danger")
        return redirect(url_for("contracts.view_contract", contract_id=contract.id))

    contract.generated_content = generated
    deduct_credit(current_user)
    db.session.commit()
    flash("Contract regenerated.", "success")
    return redirect(url_for("contracts.view_contract", contract_id=contract.id))


@contracts_bp.route("/<int:contract_id>/save-content", methods=["POST"])
@login_required
def save_content(contract_id):
    contract = Contract.query.filter_by(id=contract_id, user_id=current_user.id).first_or_404()
    contract.generated_content = request.form.get("generated_content", contract.generated_content)
    db.session.commit()
    flash("Your edits were saved.", "success")
    return redirect(url_for("contracts.view_contract", contract_id=contract.id))


@contracts_bp.route("/<int:contract_id>/delete", methods=["POST"])
@login_required
def delete_contract(contract_id):
    contract = Contract.query.filter_by(id=contract_id, user_id=current_user.id).first_or_404()
    db.session.delete(contract)
    db.session.commit()
    flash("Contract deleted.", "info")
    return redirect(url_for("contracts.list_contracts"))


@contracts_bp.route("/<int:contract_id>/pdf")
@login_required
def download_pdf(contract_id):
    contract = Contract.query.filter_by(id=contract_id, user_id=current_user.id).first_or_404()
    buffer = generate_contract_pdf(contract)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"contract_{contract.id}.pdf",
    )
