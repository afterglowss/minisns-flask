from flask import redirect, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

login_manager.login_view = "auth.login"     # 로그인 필요시 이동할 엔드포인트
login_manager.login_message_category = "info"

@login_manager.unauthorized_handler
def unauthorized():
    # JSON 요청이면 401로 응답, 아니면 로그인 페이지로 리다이렉트
    if request.accept_mimetypes["application/json"] >= request.accept_mimetypes["text/html"]:
        return jsonify({"error": "login required"}), 401
    return redirect(url_for(login_manager.login_view))  # 기본 동작(리다이렉트)