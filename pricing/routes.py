from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db, limiter
from models import PricingHistory
from pricing.forms import PricingForm
from pricing_engine import calculate_price
from ai_service import call_groq, parse_ai_sections, AIGenerationError, has_credits, deduct_credit, user_api_key

pricing_bp = Blueprint("pricing", __name__, template_folder="../templates/pricing")

SECTION_KEYS = ["DELIVERY_TIME", "MARKET_ANALYSIS", "IMPROVEMENT_TIPS"]


def _build_prompt(data, calc):
    system_prompt = (
        "You are a freelance pricing strategist. Given a project's calculated price, "
        "respond using EXACTLY this format, keeping the ### markers and nothing else "
        "before or after:\n\n"
        "### DELIVERY_TIME\n"
        "(one short line - a recommended delivery timeframe, e.g. '5-7 business days')\n\n"
        "### MARKET_ANALYSIS\n"
        "(2-3 sentences on whether this price is competitive for this complexity/urgency combination)\n\n"
        "### IMPROVEMENT_TIPS\n"
        "(2-3 short tips, each on its own line starting with '-', to help justify or improve this pricing)"
    )
    user_prompt = (
        f"Hourly Rate: ${data['hourly_rate']}\n"
        f"Estimated Hours: {data['estimated_hours']}\n"
        f"Complexity: {data['complexity']}\n"
        f"Urgency: {data['urgency']}\n"
        f"Additional Charges: ${data['additional_charges']}\n"
        f"Tax: {data['tax_percent']}%\n"
        f"Calculated Total Price: ${calc['total']}\n"
    )
    return system_prompt, user_prompt


def _form_to_data(form):
    return {
        "hourly_rate": form.hourly_rate.data,
        "estimated_hours": form.estimated_hours.data,
        "complexity": form.complexity.data,
        "urgency": form.urgency.data,
        "additional_charges": form.additional_charges.data or 0,
        "tax_percent": form.tax_percent.data or 0,
    }


@pricing_bp.route("/")
@login_required
def list_pricing():
    entries = (
        PricingHistory.query.filter_by(user_id=current_user.id)
        .order_by(PricingHistory.created_at.desc())
        .all()
    )
    return render_template("pricing/list.html", entries=entries)


@pricing_bp.route("/new", methods=["GET", "POST"])
@limiter.limit("20 per hour")
@login_required
def new_pricing():
    form = PricingForm()
    if form.validate_on_submit():
        if not has_credits(current_user):
            flash("You're out of AI credits. Please top up to get AI suggestions.", "danger")
            return redirect(url_for("pricing.list_pricing"))

        data = _form_to_data(form)
        calc = calculate_price(
            data["hourly_rate"], data["estimated_hours"], data["complexity"],
            data["urgency"], data["additional_charges"], data["tax_percent"],
        )
        system_prompt, user_prompt = _build_prompt(data, calc)

        try:
            raw = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
        except AIGenerationError as e:
            flash(str(e), "danger")
            return render_template("pricing/form.html", form=form, mode="new")

        parsed = parse_ai_sections(raw, SECTION_KEYS)

        entry = PricingHistory(
            user_id=current_user.id,
            hourly_rate=data["hourly_rate"],
            estimated_hours=data["estimated_hours"],
            complexity=data["complexity"],
            urgency=data["urgency"],
            additional_charges=data["additional_charges"],
            tax=data["tax_percent"],
            suggested_price=calc["total"],
            recommended_delivery_time=parsed["DELIVERY_TIME"],
            market_analysis=parsed["MARKET_ANALYSIS"],
            service_improvement_tips=parsed["IMPROVEMENT_TIPS"],
        )
        db.session.add(entry)
        deduct_credit(current_user)
        db.session.commit()

        flash("Price calculated and AI suggestions generated.", "success")
        return redirect(url_for("pricing.view_pricing", entry_id=entry.id))

    return render_template("pricing/form.html", form=form, mode="new")


@pricing_bp.route("/<int:entry_id>")
@login_required
def view_pricing(entry_id):
    entry = PricingHistory.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    calc = calculate_price(
        entry.hourly_rate, entry.estimated_hours, entry.complexity,
        entry.urgency, entry.additional_charges, entry.tax,
    )
    return render_template("pricing/view.html", entry=entry, calc=calc)


@pricing_bp.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_pricing(entry_id):
    entry = PricingHistory.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    form = PricingForm(obj=entry, tax_percent=entry.tax)

    if form.validate_on_submit():
        if not has_credits(current_user):
            flash("You're out of AI credits. Please top up to recalculate with AI suggestions.", "danger")
            return redirect(url_for("pricing.view_pricing", entry_id=entry.id))

        data = _form_to_data(form)
        calc = calculate_price(
            data["hourly_rate"], data["estimated_hours"], data["complexity"],
            data["urgency"], data["additional_charges"], data["tax_percent"],
        )
        system_prompt, user_prompt = _build_prompt(data, calc)

        try:
            raw = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
        except AIGenerationError as e:
            flash(str(e), "danger")
            return render_template("pricing/form.html", form=form, mode="edit", entry=entry)

        parsed = parse_ai_sections(raw, SECTION_KEYS)

        entry.hourly_rate = data["hourly_rate"]
        entry.estimated_hours = data["estimated_hours"]
        entry.complexity = data["complexity"]
        entry.urgency = data["urgency"]
        entry.additional_charges = data["additional_charges"]
        entry.tax = data["tax_percent"]
        entry.suggested_price = calc["total"]
        entry.recommended_delivery_time = parsed["DELIVERY_TIME"]
        entry.market_analysis = parsed["MARKET_ANALYSIS"]
        entry.service_improvement_tips = parsed["IMPROVEMENT_TIPS"]

        deduct_credit(current_user)
        db.session.commit()
        flash("Pricing recalculated with updated AI suggestions.", "success")
        return redirect(url_for("pricing.view_pricing", entry_id=entry.id))

    return render_template("pricing/form.html", form=form, mode="edit", entry=entry)


@pricing_bp.route("/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_pricing(entry_id):
    entry = PricingHistory.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash("Pricing calculation deleted.", "info")
    return redirect(url_for("pricing.list_pricing"))
