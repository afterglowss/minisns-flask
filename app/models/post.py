from datetime import datetime
from app.extensions import db
from app.models.like import Like
from flask_login import current_user

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)  # static 기준 상대경로
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    author = db.relationship("User", backref=db.backref("posts", lazy="dynamic"))

def likes_count(self) -> int:
    return Like.query.filter_by(post_id=self.id).count()

def is_liked_by(self, user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return Like.query.filter_by(post_id=self.id, user_id=user.id).first() is not None

Post.likes_count = likes_count
Post.is_liked_by = is_liked_by