import os
from flask import Flask, render_template
from .extensions import db, login_manager, bcrypt
from .routes.auth import auth_bp
from .routes.profile import profile_bp
from .routes.post import post_bp
from dotenv import load_dotenv

load_dotenv()  # .env 지원 (없어도 동작)

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["UPLOAD_DIR"] = os.getenv("UPLOAD_DIR", "static/uploads")
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5MB


    # 확장 초기화
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # 블루프린트 등록
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(profile_bp)
    app.register_blueprint(post_bp)

    # 기본 페이지
    @app.route("/")
    def index():
        return render_template("base.html")

    # 업로드 폴더가 없으면 생성
    with app.app_context():
        os.makedirs(os.path.join(app.root_path, app.config["UPLOAD_DIR"]), exist_ok=True)
        db.create_all()
        
    # DB 생성
    with app.app_context():
        db.create_all()

    return app

