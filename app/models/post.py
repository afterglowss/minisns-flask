from datetime import datetime
from app.extensions import db

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)  # static 기준 상대경로
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    author = db.relationship("User", backref=db.backref("posts", lazy="dynamic"))
