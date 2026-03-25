from datetime import datetime, timezone
from app import db 
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

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
    
    @property
    def has_duplicate_badges(self):
        seen = {}
        for collector in self.collectors:
            badge = collector.badge_number
            if not badge:
                continue
            if badge in seen:
                return True
            seen[badge] = True

        for collector in self.collectors:
            matches = Collector.query.filter(
                Collector.badge_number == collector.badge_number,
                Collector.campaign_id != self.id
            ).count()
            if matches > 0:
                return True

        return False

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
    
    @property
    def has_duplicate_badge(self):
        return Collector.query.filter(
            Collector.badge_number == self.badge_number,
            Collector.id != self.id
        ).count() > 0

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="charity_user", nullable=False)
    charity_id = db.Column(db.Integer, db.ForeignKey("charities.id"), nullable=True)

    charity = db.relationship("Charity", backref="users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FraudAlert(db.Model):
    __tablename__ = "fraud_alerts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=True)
    summary = db.Column(db.Text, nullable=False)
    article_url = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(80), nullable=False, default="fake_collector")
    published_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class PublicReport(db.Model):
    __tablename__ = "public_reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_name = db.Column(db.String(120), nullable=True)
    reporter_email = db.Column(db.String(120), nullable=True)
    location = db.Column(db.String(120), nullable=False)
    claimed_charity = db.Column(db.String(120), nullable=True)
    collector_description = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(40), default="pending", nullable=False)
    feedback_type = db.Column(db.String(20), default="suspicious", nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class ScanEvent(db.Model):
    __tablename__ = "scan_events"

    id = db.Column(db.Integer, primary_key=True)
    issued_qr_id = db.Column(db.Integer, db.ForeignKey("issued_qr.id"), nullable=True)
    token_hash = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(40), nullable=False)
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    issued_qr = db.relationship("IssuedQR", backref="scan_events")