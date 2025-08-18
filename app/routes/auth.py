from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions import db, bcrypt, login_manager
from ..models.user import User

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.get("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("auth/register.html")

@auth_bp.post("/register")
def register_post():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # 간단 검증
    if not username or not email or not password:
        flash("모든 필드를 입력하세요.", "danger")
        return redirect(url_for("auth.register"))

    if User.query.filter((User.username == username) | (User.email == email)).first():
        flash("이미 존재하는 사용자명/이메일입니다.", "danger")
        return redirect(url_for("auth.register"))

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, email=email, password_hash=pw_hash)
    db.session.add(user)
    db.session.commit()

    flash("회원가입 성공! 로그인하세요.", "success")
    return redirect(url_for("auth.login"))

@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("auth/login.html")

@auth_bp.post("/login")
def login_post():
    email_or_username = request.form.get("email_or_username", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter(
        (User.email == email_or_username) | (User.username == email_or_username)
    ).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        flash("로그인 정보가 올바르지 않습니다.", "danger")
        return redirect(url_for("auth.login"))

    login_user(user, remember=True)
    flash("로그인 성공!", "success")
    #return redirect(url_for("index"))
    return redirect(url_for("profile.me"))

@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃 되었습니다.", "info")
    return redirect(url_for("index"))
