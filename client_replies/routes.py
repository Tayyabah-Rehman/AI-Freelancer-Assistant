from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db, limiter
from models import ClientReply
from client_replies.forms import ClientReplyForm
from ai_service import call_groq, AIGenerationError, has_credits, deduct_credit, user_api_key

client_replies_bp = Blueprint("client_replies", __name__, template_folder="../templates/client_replies")


def _build_prompt(data):
    system_prompt = (
        f"You are an expert freelancer communications assistant. Write a clear, "
        f"{data['tone']} reply to the client's message below. Keep it concise "
        f"(80-150 words), ready to send, no placeholders."
    )
    user_prompt = f"Client's message:\n{data['client_message']}\n\nWrite an appropriate reply."
    return system_prompt, user_prompt


def _form_to_data(form):
    return {
        "client_message": form.client_message.data.strip(),
        "tone": form.tone.data,
    }


@client_replies_bp.route("/")
@login_required
def list_replies():
    replies = (
        ClientReply.query.filter_by(user_id=current_user.id)
        .order_by(ClientReply.created_at.desc())
        .all()
    )
    return render_template("client_replies/list.html", replies=replies)


@client_replies_bp.route("/new", methods=["GET", "POST"])
@limiter.limit("20 per hour")
@login_required
def new_reply():
    form = ClientReplyForm()
    if form.validate_on_submit():
        if not has_credits(current_user):
            flash("You're out of AI credits. Please top up to generate more content.", "danger")
            return redirect(url_for("client_replies.list_replies"))

        data = _form_to_data(form)
        system_prompt, user_prompt = _build_prompt(data)

        try:
            generated = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
        except AIGenerationError as e:
            flash(str(e), "danger")
            return render_template("client_replies/form.html", form=form, mode="new")

        reply = ClientReply(user_id=current_user.id, generated_reply=generated, **data)
        db.session.add(reply)
        deduct_credit(current_user)
        db.session.commit()

        flash("Reply generated successfully.", "success")
        return redirect(url_for("client_replies.view_reply", reply_id=reply.id))

    return render_template("client_replies/form.html", form=form, mode="new")


@client_replies_bp.route("/<int:reply_id>")
@login_required
def view_reply(reply_id):
    reply = ClientReply.query.filter_by(id=reply_id, user_id=current_user.id).first_or_404()
    return render_template("client_replies/view.html", reply=reply)


@client_replies_bp.route("/<int:reply_id>/edit", methods=["GET", "POST"])
@login_required
def edit_reply(reply_id):
    reply = ClientReply.query.filter_by(id=reply_id, user_id=current_user.id).first_or_404()
    form = ClientReplyForm(obj=reply)

    if form.validate_on_submit():
        data = _form_to_data(form)
        for key, value in data.items():
            setattr(reply, key, value)
        db.session.commit()
        flash("Message details updated. Regenerate to refresh the AI reply.", "success")
        return redirect(url_for("client_replies.view_reply", reply_id=reply.id))

    return render_template("client_replies/form.html", form=form, mode="edit", reply=reply)


@client_replies_bp.route("/<int:reply_id>/regenerate", methods=["POST"])
@limiter.limit("20 per hour")
@login_required
def regenerate_reply(reply_id):
    reply = ClientReply.query.filter_by(id=reply_id, user_id=current_user.id).first_or_404()

    if not has_credits(current_user):
        flash("You're out of AI credits. Please top up to regenerate.", "danger")
        return redirect(url_for("client_replies.view_reply", reply_id=reply.id))

    data = {"client_message": reply.client_message, "tone": reply.tone}
    system_prompt, user_prompt = _build_prompt(data)

    try:
        generated = call_groq(system_prompt, user_prompt, api_key_override=user_api_key(current_user))
    except AIGenerationError as e:
        flash(str(e), "danger")
        return redirect(url_for("client_replies.view_reply", reply_id=reply.id))

    reply.generated_reply = generated
    deduct_credit(current_user)
    db.session.commit()
    flash("Reply regenerated.", "success")
    return redirect(url_for("client_replies.view_reply", reply_id=reply.id))


@client_replies_bp.route("/<int:reply_id>/save-content", methods=["POST"])
@login_required
def save_content(reply_id):
    reply = ClientReply.query.filter_by(id=reply_id, user_id=current_user.id).first_or_404()
    reply.generated_reply = request.form.get("generated_reply", reply.generated_reply)
    db.session.commit()
    flash("Your edits were saved.", "success")
    return redirect(url_for("client_replies.view_reply", reply_id=reply.id))


@client_replies_bp.route("/<int:reply_id>/delete", methods=["POST"])
@login_required
def delete_reply(reply_id):
    reply = ClientReply.query.filter_by(id=reply_id, user_id=current_user.id).first_or_404()
    db.session.delete(reply)
    db.session.commit()
    flash("Reply deleted.", "info")
    return redirect(url_for("client_replies.list_replies"))
