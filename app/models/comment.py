from datetime import datetime
from app.extensions import db

class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    author = db.relationship("User", backref=db.backref("comments", lazy="dynamic"))
    
    def __repr__(self):
        # content -> text 로 수정
        preview = (self.text or "")[:20]
        return f"<Comment {self.id} {preview!r}>"
