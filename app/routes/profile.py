import os, uuid
from flask import Blueprint, render_template, abort, url_for, redirect, request, current_app, flash
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps
from app.models.user import User
from app.extensions import db

profile_bp = Blueprint("profile", __name__, template_folder="../templates/profile")

ALLOWED_EXTS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_PIXELS = 4000 * 4000
MAX_SIDE = 1024

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS

@profile_bp.get("/me", endpoint="me")  # ← endpoint 명시
@login_required
def me():
    return redirect(url_for("profile.view", username=current_user.username))

@profile_bp.get("/u/<username>", endpoint="view")
def view(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404, description="User not found")
    return render_template("profile/view.html", profile_user=user)

@profile_bp.post("/me/avatar", endpoint="upload_avatar")
@login_required
def upload_avatar():
    if "avatar" not in request.files:
        flash("파일이 없습니다.", "danger")
        return redirect(url_for("profile.me"))
    file = request.files["avatar"]
    if file.filename == "":
        flash("선택된 파일이 없습니다.", "danger")
        return redirect(url_for("profile.me"))
    if not allowed_file(file.filename):
        flash("허용되지 않는 파일 형식입니다.", "danger")
        return redirect(url_for("profile.me"))

    ext = file.filename.rsplit(".", 1)[1].lower()
    upload_dir = current_app.config["UPLOAD_DIR"]  # e.g. "static/uploads"
    save_dir = os.path.join(current_app.root_path, upload_dir)
    os.makedirs(save_dir, exist_ok=True)

    tmp_name = secure_filename(f"{uuid.uuid4().hex}.{ext}")
    tmp_path = os.path.join(save_dir, tmp_name)
    file.save(tmp_path)

    try:
        with Image.open(tmp_path) as img:
            w, h = img.size
            if w * h > MAX_PIXELS:
                raise ValueError("too large")
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "L", "P"):
                img = img.convert("RGB")
            if max(img.size) > MAX_SIDE:
                scale = MAX_SIDE / float(max(img.size))
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.LANCZOS)

            final_name = secure_filename(f"{uuid.uuid4().hex}.jpg")
            final_path = os.path.join(save_dir, final_name)
            img.save(final_path, format="JPEG", quality=88, optimize=True)
    except Exception:
        try: os.remove(tmp_path)
        except OSError: pass
        flash("유효한 이미지 파일이 아닙니다.", "danger")
        return redirect(url_for("profile.me"))

    try: os.remove(tmp_path)
    except OSError: pass

    rel_under_static = (
        f"{upload_dir.split('static/',1)[1]}/{final_name}"
        if "static/" in upload_dir else f"{upload_dir}/{final_name}"
    )
    current_user.profile_image = rel_under_static
    db.session.commit()

    flash("프로필 사진이 변경되었습니다.", "success")
    return redirect(url_for("profile.me"))
