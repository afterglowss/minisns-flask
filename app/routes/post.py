import os, uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps
from app.extensions import db
from app.models.post import Post
from app.models.like import Like

post_bp = Blueprint("post", __name__, template_folder="../templates/post")

ALLOWED_IMG = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_PIXELS = 4000 * 4000
MAX_SIDE = 1600

def allowed_image(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMG

@post_bp.get("/", endpoint="feed")
def feed():
    # 최신순
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("post/feed.html", posts=posts)

@post_bp.post("/post/new", endpoint="create")
@login_required
def create():
    text = request.form.get("text", "").strip()
    if not text:
        flash("내용을 입력하세요.", "danger")
        return redirect(url_for("post.feed"))

    image_path = None
    file = request.files.get("image")
    if file and file.filename:
        if not allowed_image(file.filename):
            flash("이미지 형식이 올바르지 않습니다. (png, jpg, jpeg, gif, webp)", "danger")
            return redirect(url_for("post.feed"))

        ext = file.filename.rsplit(".", 1)[1].lower()
        upload_dir = current_app.config.get("UPLOAD_DIR", "static/uploads")
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
                    img = img.resize((int(img.width*scale), int(img.height*scale)), Image.LANCZOS)

                final_name = secure_filename(f"{uuid.uuid4().hex}.jpg")
                final_path = os.path.join(save_dir, final_name)
                img.save(final_path, format="JPEG", quality=86, optimize=True)

        except Exception:
            try: os.remove(tmp_path)
            except OSError: pass
            flash("유효한 이미지 파일이 아닙니다.", "danger")
            return redirect(url_for("post.feed"))
        else:
            try: os.remove(tmp_path)
            except OSError: pass

            # DB에는 static 아래 상대경로만 저장
            rel_under_static = (
                f"{upload_dir.split('static/',1)[1]}/{final_name}"
                if "static/" in upload_dir else f"{upload_dir}/{final_name}"
            )
            image_path = rel_under_static

    post = Post(author_id=current_user.id, text=text, image_path=image_path)
    db.session.add(post)
    db.session.commit()
    flash("게시글이 등록되었습니다.", "success")
    return redirect(url_for("post.feed"))


@post_bp.post("/api/post/<int:post_id>/like", endpoint="toggle_like_api")
@login_required
def toggle_like_api(post_id):
    post = Post.query.get_or_404(post_id)

    existing = Like.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post_id))
        liked = True
    db.session.commit()

    # 최신 카운트 계산
    count = Like.query.filter_by(post_id=post_id).count()
    return jsonify({"ok": True, "liked": liked, "count": count, "post_id": post_id})