from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user

from extensions import db, limiter
from models import CoverLetter
from cover_letters.forms import CoverLetterForm
from ai_service import call_groq, AIGenerationError, has_credits, deduct_credit, user_api_key
from pdf_service import generate_cover_letter_pdf

cover_letters_bp = Blueprint("cover_letters", __name__, template_folder="../templates/cover_letters")


def _build_prompt(data):
    system_prompt = (
        "You are an expert career writer specializing in freelance and job "
        "application cover letters. Write a concise, compelling cover letter "
        "(200-300 words). Write it ready to send - no placeholders like "
        "[Your Name], no headings, just the letter body."
    )
    user_prompt = (
        f"Job Title: {data['job_title']}\n"
        f"Company Name: {data['company_name']}\n"
        f"Relevant Experience: {data['experience']}\n"
        f"Skills: {data['skills']}\n"
        f"Portfolio URL: {data.get('portfolio_url') or 'Not provided'}\n\n"
        f"Write a cover letter for this role that connects the candidate's "
        f"experience and skills directly to what the role likely needs."
    )
    return system_prompt, user_prompt


def _form_to_data(form):
    return {
        "job_title": form.job_title.data.strip(),
        "company_name": form.company_name.data.strip(),
        "experience": form.experience.data.strip(),
        "skills": form.skills.data.strip(),
        "portfolio_url": form.portfolio_url.data.strip() if form.portfolio_url.data else None,
    }


@cover_letters_bp.route("/")
@login_required
def list_cover_letters():
    letters = (
        CoverLetter.query.filter_by(user_id=current_user.id)
        .order_by(CoverLetter.created_at.desc())
        .all()
    )
    return render_template("cover_letters/list.html", letters=letters)


@cover_letters_bp.route("/new", methods=["GET", "POST"])
@limiter.limit("20 per hour")
@login_required
def new_cover_letter():
    form = CoverLetterForm()
    if form.validate_on_submit():
        if not has_credits(current_user):
            flash("You're out of AI credits. Please top up to generate more content.", "danger")
            return redirect(url_for("cover_letters.list_cover_letters"))

        data = _form_to_data(form)
        system_prompt, user_prompt = _build_prompt(data)

        try:
            generated = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
        except AIGenerationError as e:
            flash(str(e), "danger")
            return render_template("cover_letters/form.html", form=form, mode="new")

        letter = CoverLetter(user_id=current_user.id, generated_content=generated, **data)
        db.session.add(letter)
        deduct_credit(current_user)
        db.session.commit()

        flash("Cover letter generated successfully.", "success")
        return redirect(url_for("cover_letters.view_cover_letter", letter_id=letter.id))

    return render_template("cover_letters/form.html", form=form, mode="new")


@cover_letters_bp.route("/<int:letter_id>")
@login_required
def view_cover_letter(letter_id):
    letter = CoverLetter.query.filter_by(id=letter_id, user_id=current_user.id).first_or_404()
    return render_template("cover_letters/view.html", letter=letter)


@cover_letters_bp.route("/<int:letter_id>/edit", methods=["GET", "POST"])
@login_required
def edit_cover_letter(letter_id):
    letter = CoverLetter.query.filter_by(id=letter_id, user_id=current_user.id).first_or_404()
    form = CoverLetterForm(obj=letter)

    if form.validate_on_submit():
        data = _form_to_data(form)
        for key, value in data.items():
            setattr(letter, key, value)
        db.session.commit()
        flash("Cover letter details updated. Regenerate to refresh the AI content.", "success")
        return redirect(url_for("cover_letters.view_cover_letter", letter_id=letter.id))

    return render_template("cover_letters/form.html", form=form, mode="edit", letter=letter)


@cover_letters_bp.route("/<int:letter_id>/regenerate", methods=["POST"])
@limiter.limit("20 per hour")
@login_required
def regenerate_cover_letter(letter_id):
    letter = CoverLetter.query.filter_by(id=letter_id, user_id=current_user.id).first_or_404()

    if not has_credits(current_user):
        flash("You're out of AI credits. Please top up to regenerate.", "danger")
        return redirect(url_for("cover_letters.view_cover_letter", letter_id=letter.id))

    data = {
        "job_title": letter.job_title,
        "company_name": letter.company_name,
        "experience": letter.experience,
        "skills": letter.skills,
        "portfolio_url": letter.portfolio_url,
    }
    system_prompt, user_prompt = _build_prompt(data)

    try:
        generated = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
    except AIGenerationError as e:
        flash(str(e), "danger")
        return redirect(url_for("cover_letters.view_cover_letter", letter_id=letter.id))

    letter.generated_content = generated
    deduct_credit(current_user)
    db.session.commit()
    flash("Cover letter regenerated.", "success")
    return redirect(url_for("cover_letters.view_cover_letter", letter_id=letter.id))


@cover_letters_bp.route("/<int:letter_id>/save-content", methods=["POST"])
@login_required
def save_content(letter_id):
    letter = CoverLetter.query.filter_by(id=letter_id, user_id=current_user.id).first_or_404()
    letter.generated_content = request.form.get("generated_content", letter.generated_content)
    db.session.commit()
    flash("Your edits were saved.", "success")
    return redirect(url_for("cover_letters.view_cover_letter", letter_id=letter.id))


@cover_letters_bp.route("/<int:letter_id>/delete", methods=["POST"])
@login_required
def delete_cover_letter(letter_id):
    letter = CoverLetter.query.filter_by(id=letter_id, user_id=current_user.id).first_or_404()
    db.session.delete(letter)
    db.session.commit()
    flash("Cover letter deleted.", "info")
    return redirect(url_for("cover_letters.list_cover_letters"))


@cover_letters_bp.route("/<int:letter_id>/pdf")
@login_required
def download_pdf(letter_id):
    letter = CoverLetter.query.filter_by(id=letter_id, user_id=current_user.id).first_or_404()
    buffer = generate_cover_letter_pdf(letter)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"cover_letter_{letter.id}.pdf",
    )
