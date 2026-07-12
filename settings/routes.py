from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from settings.forms import SettingsForm

settings_bp = Blueprint("settings", __name__, template_folder="../templates/settings")


@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def edit_settings():
    profile = current_user.profile
    form = SettingsForm(obj=profile)

    if form.validate_on_submit():
        profile.theme = form.theme.data
        profile.language = form.language.data
        profile.groq_api_key = form.groq_api_key.data.strip() if form.groq_api_key.data else None
        profile.email_notifications = form.email_notifications.data
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("settings.edit_settings"))

    return render_template("settings/edit.html", form=form)
