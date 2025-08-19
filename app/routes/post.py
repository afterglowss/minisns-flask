import os, uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps
from app.extensions import db
from app.models.post import Post
from app.models.like import Like
from app.models.comment import Comment

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

from datetime import timezone
from zoneinfo import ZoneInfo
KST = ZoneInfo("Asia/Seoul")

def _to_kst(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST)

def serialize_comment(c: Comment):
    return {
        "id": c.id,
        "post_id": c.post_id,
        "author_id": c.author_id,
        "author_username": c.author.username,
        "author_avatar": (f"/static/{c.author.profile_image}") if c.author.profile_image else "/static/img/avatar_default.png",
        "text": c.text,
        "created_at": _to_kst(c.created_at).strftime("%Y-%m-%d %H:%M"),
    }

@post_bp.post("/api/post/<int:post_id>/comment", endpoint="add_comment_api")
@login_required
def add_comment_api(post_id):
    post = Post.query.get_or_404(post_id)

    # 어떤 경우에도 안전하게 본문에서 text를 뽑아낸다
    data_json = request.get_json(silent=True) or {}
    text = (
        request.form.get("text")            # x-www-form-urlencoded, multipart
        or data_json.get("text")            # application/json
        or (request.data or b"").decode(errors="ignore")  # text/plain 대비
    ).strip()

    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    if len(text) > 500:
        return jsonify({"ok": False, "error": "too long"}), 400

    c = Comment(post_id=post.id, author_id=current_user.id, text=text)
    db.session.add(c)
    db.session.commit()
    return jsonify({"ok": True, "comment": serialize_comment(c)})

@post_bp.post("/api/comment/<int:comment_id>/delete", endpoint="delete_comment_api")
@login_required
def delete_comment_api(comment_id):
    c = Comment.query.get_or_404(comment_id)
    if c.author_id != current_user.id:
        return jsonify({"ok": False, "error": "forbidden"}), 403
    db.session.delete(c)
    db.session.commit()
    return jsonify({"ok": True, "comment_id": comment_id, "post_id": c.post_id})