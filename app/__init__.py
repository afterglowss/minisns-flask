import os
from flask import Flask, render_template
from .extensions import db, login_manager, bcrypt
from .routes.auth import auth_bp
from dotenv import load_dotenv

load_dotenv()  # .env 지원 (없어도 동작)

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 확장 초기화
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # 블루프린트 등록
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # 기본 페이지
    @app.route("/")
    def index():
        return render_template("base.html")

    # DB 생성
    with app.app_context():
        db.create_all()

    return app
