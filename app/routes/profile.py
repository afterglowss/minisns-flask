from flask import Blueprint, render_template, abort, url_for, redirect
from flask_login import current_user, login_required
from app.models.user import User

profile_bp = Blueprint("profile", __name__, template_folder="../templates/profile")

@profile_bp.get("/me")
@login_required
def me():
    # 로그인한 내 프로필로 리다이렉트
    return redirect(url_for("profile.view", username=current_user.username))

@profile_bp.get("/u/<username>")
def view(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404, description="User not found")
    return render_template("profile/view.html", profile_user=user)
