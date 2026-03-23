from flask import Blueprint, render_template, request
from datetime import datetime, timezone

from app.models import Campaign, Charity, IssuedQR, Collector, FraudAlert
from app.services.token_service import verify_token, token_hash

public_bp = Blueprint("public", __name__)

@public_bp.get("/")
def home():
    recent_alerts = (
        FraudAlert.query
        .filter_by(is_active=True)
        .order_by(FraudAlert.published_at.desc(), FraudAlert.created_at.desc())
        .limit(3)
        .all()
    )
    return render_template("home.html", recent_alerts=recent_alerts)

@public_bp.get("/scan")
def scan():
    return render_template("scan.html")

@public_bp.get("/verify")
def verify_page():
    token = request.args.get("token", "").strip()

    recent_alerts = (
        FraudAlert.query
        .filter_by(is_active=True)
        .order_by(FraudAlert.published_at.desc(), FraudAlert.created_at.desc())
        .limit(3)
        .all()
    )

    if not token:
        return render_template(
            "verify_result.html",
            status="NO TOKEN",
            details=None,
            recent_alerts=recent_alerts
        )

    try:
        payload = verify_token(token)
    except Exception:
        return render_template(
            "verify_result.html",
            status="INVALID",
            details=None,
            recent_alerts=recent_alerts
        )

    exp = int(payload.get("exp", 0))
    now = int(datetime.now(tz=timezone.utc).timestamp())
    if exp and now > exp:
        return render_template(
            "verify_result.html",
            status="EXPIRED",
            details=None,
            recent_alerts=recent_alerts
        )

    issued = IssuedQR.query.filter_by(token_hash=token_hash(token)).first()
    if not issued:
        return render_template(
            "verify_result.html",
            status="NOT ISSUED",
            details=None,
            recent_alerts=recent_alerts
        )

    if issued.revoked_at is not None:
        return render_template(
            "verify_result.html",
            status="REVOKED",
            details=None,
            recent_alerts=recent_alerts
        )

    cid = payload.get("cid")
    campaign = Campaign.query.get(cid)
    if not campaign:
        return render_template(
            "verify_result.html",
            status="CAMPAIGN NOT FOUND",
            details=None,
            recent_alerts=recent_alerts
        )

    if campaign.ends_at and datetime.now(tz=timezone.utc) > campaign.ends_at.replace(tzinfo=timezone.utc):
        return render_template(
            "verify_result.html",
            status="CAMPAIGN EXPIRED",
            details=None,
            recent_alerts=recent_alerts
        )

    charity = Charity.query.get(campaign.charity_id)
    if not charity:
        return render_template(
            "verify_result.html",
            status="CHARITY NOT FOUND",
            details=None,
            recent_alerts=recent_alerts
        )

    collector_id = payload.get("collector_id")
    collector = Collector.query.get(collector_id) if collector_id else None

    if not collector or collector.campaign_id != campaign.id:
        return render_template(
            "verify_result.html",
            status="COLLECTOR NOT FOUND",
            details=None,
            recent_alerts=recent_alerts
        )

    details = {
        "charity_name": charity.name,
        "charity_reg": charity.registration_number,
        "charity_website": charity.website,
        "campaign_title": campaign.title,
        "campaign_description": campaign.description,
        "campaign_start": campaign.starts_at.isoformat(sep=" "),
        "campaign_end": campaign.ends_at.isoformat(sep=" "),
        "collector_name": collector.full_name,
        "collector_badge": collector.badge_number,
        "collector_photo": collector.photo_filename,
        "token_expires_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat(sep=" "),
    }

    return render_template(
        "verify_result.html",
        status="VERIFIED",
        details=details,
        recent_alerts=recent_alerts
    )