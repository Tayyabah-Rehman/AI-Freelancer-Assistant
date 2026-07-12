from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db, limiter
from models import GigDescription
from gigs.forms import GigDescriptionForm
from ai_service import call_groq, parse_ai_sections, AIGenerationError, has_credits, deduct_credit, user_api_key

gigs_bp = Blueprint("gigs", __name__, template_folder="../templates/gigs")

SECTION_KEYS = ["DESCRIPTION", "SEO_KEYWORDS", "FAQS"]


def _build_prompt(data):
    system_prompt = (
        "You are an expert freelance marketplace (Upwork/Fiverr) gig copywriter. "
        "Given the service details, respond using EXACTLY this format, keeping the "
        "### markers and nothing else before or after:\n\n"
        "### DESCRIPTION\n"
        "(a compelling 150-250 word gig description written in first person, ready to publish, no placeholders)\n\n"
        "### SEO_KEYWORDS\n"
        "(8-12 comma-separated SEO keywords relevant to this gig)\n\n"
        "### FAQS\n"
        "(exactly 3 short FAQ pairs a client might ask, each formatted as 'Q: ...' then 'A: ...' on the next line)"
    )
    user_prompt = (
        f"Service Category: {data['service_category']}\n"
        f"Skills: {data['skills']}\n"
        f"Experience Level: {data['experience_level']}\n"
        f"Delivery Time: {data['delivery_time']}\n"
        f"Features Included: {data['features']}\n"
        f"Revisions: {data['revisions']}\n"
    )
    return system_prompt, user_prompt


def _form_to_data(form):
    return {
        "service_category": form.service_category.data.strip(),
        "skills": form.skills.data.strip(),
        "experience_level": form.experience_level.data,
        "delivery_time": form.delivery_time.data.strip(),
        "features": form.features.data.strip(),
        "revisions": form.revisions.data.strip(),
    }


@gigs_bp.route("/")
@login_required
def list_gigs():
    gigs = (
        GigDescription.query.filter_by(user_id=current_user.id)
        .order_by(GigDescription.created_at.desc())
        .all()
    )
    return render_template("gigs/list.html", gigs=gigs)


@gigs_bp.route("/new", methods=["GET", "POST"])
@limiter.limit("20 per hour")
@login_required
def new_gig():
    form = GigDescriptionForm()
    if form.validate_on_submit():
        if not has_credits(current_user):
            flash("You're out of AI credits. Please top up to generate more content.", "danger")
            return redirect(url_for("gigs.list_gigs"))

        data = _form_to_data(form)
        system_prompt, user_prompt = _build_prompt(data)

        try:
            raw = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
        except AIGenerationError as e:
            flash(str(e), "danger")
            return render_template("gigs/form.html", form=form, mode="new")

        parsed = parse_ai_sections(raw, SECTION_KEYS)

        gig = GigDescription(
            user_id=current_user.id,
            generated_description=parsed["DESCRIPTION"],
            seo_keywords=parsed["SEO_KEYWORDS"],
            faq_suggestions=parsed["FAQS"],
            **data,
        )
        db.session.add(gig)
        deduct_credit(current_user)
        db.session.commit()

        if not parsed["SEO_KEYWORDS"] or not parsed["FAQS"]:
            flash("Gig generated, but the AI response didn't fully match the expected format - review it below.", "warning")
        else:
            flash("Gig description generated successfully.", "success")

        return redirect(url_for("gigs.view_gig", gig_id=gig.id))

    return render_template("gigs/form.html", form=form, mode="new")


@gigs_bp.route("/<int:gig_id>")
@login_required
def view_gig(gig_id):
    gig = GigDescription.query.filter_by(id=gig_id, user_id=current_user.id).first_or_404()
    return render_template("gigs/view.html", gig=gig)


@gigs_bp.route("/<int:gig_id>/edit", methods=["GET", "POST"])
@login_required
def edit_gig(gig_id):
    gig = GigDescription.query.filter_by(id=gig_id, user_id=current_user.id).first_or_404()
    form = GigDescriptionForm(obj=gig)

    if form.validate_on_submit():
        data = _form_to_data(form)
        for key, value in data.items():
            setattr(gig, key, value)
        db.session.commit()
        flash("Gig details updated. Regenerate to refresh the AI content.", "success")
        return redirect(url_for("gigs.view_gig", gig_id=gig.id))

    return render_template("gigs/form.html", form=form, mode="edit", gig=gig)


@gigs_bp.route("/<int:gig_id>/regenerate", methods=["POST"])
@limiter.limit("20 per hour")
@login_required
def regenerate_gig(gig_id):
    gig = GigDescription.query.filter_by(id=gig_id, user_id=current_user.id).first_or_404()

    if not has_credits(current_user):
        flash("You're out of AI credits. Please top up to regenerate.", "danger")
        return redirect(url_for("gigs.view_gig", gig_id=gig.id))

    data = {
        "service_category": gig.service_category,
        "skills": gig.skills,
        "experience_level": gig.experience_level,
        "delivery_time": gig.delivery_time,
        "features": gig.features,
        "revisions": gig.revisions,
    }
    system_prompt, user_prompt = _build_prompt(data)

    try:
        raw = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
    except AIGenerationError as e:
        flash(str(e), "danger")
        return redirect(url_for("gigs.view_gig", gig_id=gig.id))

    parsed = parse_ai_sections(raw, SECTION_KEYS)
    gig.generated_description = parsed["DESCRIPTION"]
    gig.seo_keywords = parsed["SEO_KEYWORDS"]
    gig.faq_suggestions = parsed["FAQS"]

    deduct_credit(current_user)
    db.session.commit()
    flash("Gig description regenerated.", "success")
    return redirect(url_for("gigs.view_gig", gig_id=gig.id))


@gigs_bp.route("/<int:gig_id>/save-content", methods=["POST"])
@login_required
def save_content(gig_id):
    gig = GigDescription.query.filter_by(id=gig_id, user_id=current_user.id).first_or_404()
    gig.generated_description = request.form.get("generated_description", gig.generated_description)
    gig.seo_keywords = request.form.get("seo_keywords", gig.seo_keywords)
    gig.faq_suggestions = request.form.get("faq_suggestions", gig.faq_suggestions)
    db.session.commit()
    flash("Your edits were saved.", "success")
    return redirect(url_for("gigs.view_gig", gig_id=gig.id))


@gigs_bp.route("/<int:gig_id>/delete", methods=["POST"])
@login_required
def delete_gig(gig_id):
    gig = GigDescription.query.filter_by(id=gig_id, user_id=current_user.id).first_or_404()
    db.session.delete(gig)
    db.session.commit()
    flash("Gig description deleted.", "info")
    return redirect(url_for("gigs.list_gigs"))
