import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from user_profile.forms import ProfileForm, ChangePasswordForm

user_profile_bp = Blueprint("user_profile", __name__, template_folder="../templates/user_profile")

AVATAR_FOLDER = os.path.join("static", "uploads", "avatars")


@user_profile_bp.route("/", methods=["GET", "POST"])
@login_required
def edit_profile():
    profile = current_user.profile
    form = ProfileForm(obj=profile)

    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        profile.bio = form.bio.data.strip() if form.bio.data else None
        profile.skills = form.skills.data.strip() if form.skills.data else None
        profile.portfolio_url = form.portfolio_url.data.strip() if form.portfolio_url.data else None
        profile.phone = form.phone.data.strip() if form.phone.data else None
        profile.location = form.location.data.strip() if form.location.data else None
        profile.hourly_rate = form.hourly_rate.data

        avatar_file = form.avatar.data
        if avatar_file and avatar_file.filename:
            ext = secure_filename(avatar_file.filename).rsplit(".", 1)[-1].lower()
            filename = f"user_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"

            upload_dir = os.path.join(current_app.root_path, AVATAR_FOLDER)
            os.makedirs(upload_dir, exist_ok=True)
            avatar_file.save(os.path.join(upload_dir, filename))

            profile.avatar_path = f"uploads/avatars/{filename}"

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("user_profile.edit_profile"))

    if request.method == "GET":
        form.name.data = current_user.name

    return render_template("user_profile/edit.html", form=form, profile=profile)


@user_profile_bp.route("/password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return render_template("user_profile/password.html", form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("user_profile.edit_profile"))

    return render_template("user_profile/password.html", form=form)
