from datetime import datetime, timezone
from app import db 

class Charity(db.Model):
    __tablename__ = "charities"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    registration_number = db.Column(db.String(100), unique=True, nullable=False)
    website = db.Column(db.String(255), nullable=True)

    campaigns = db.relationship("Campaign", backref="charity", lazy=True)

class Campaign(db.Model):
    __tablename__ = "campaigns"
    id = db.Column(db.Integer, primary_key=True)
    charity_id = db.Column(db.Integer, db.ForeignKey("charities.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.String(20), default="active", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def computed_status(self):
        now = datetime.utcnow()

        if self.starts_at and self.starts_at > now:
            return "UPCOMING"
        elif self.ends_at and self.ends_at < now:
            return "EXPIRED"
        return "ACTIVE"

class IssuedQR(db.Model):
    __tablename__ = "issued_qr"
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False)
    collector_id = db.Column(db.Integer, db.ForeignKey("collectors.id"), nullable=False)

    token = db.Column(db.Text, nullable=False)
    token_hash = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    campaign = db.relationship("Campaign", backref="issued_qrs")
    

class Collector(db.Model):
    __tablename__ = "collectors"
    id = db.Column(db.Integer, primary_key=True)

    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False)

    full_name = db.Column(db.String(200), nullable=False)
    badge_number = db.Column(db.String(100), nullable=False)
    photo_filename = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    campaign = db.relationship("Campaign", backref="collectors")