from flask import Blueprint, render_template, request
from datetime import datetime, timezone, timedelta

from app import db
from app.models import Campaign, Charity, IssuedQR, Collector, FraudAlert, PublicReport, ScanEvent
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

    community_reports = (
        PublicReport.query
        .filter(
            PublicReport.status.in_(["reviewed", "escalated"]),
            PublicReport.feedback_type == "suspicious"
        )
        .order_by(PublicReport.submitted_at.desc())
        .limit(3)
        .all()
    )

    community_feedback = (
        PublicReport.query
        .filter(
            PublicReport.status == "reviewed",
            PublicReport.feedback_type == "genuine"
        )
        .order_by(PublicReport.submitted_at.desc())
        .limit(3)
        .all()
    )

    return render_template(
        "home.html",
        recent_alerts=recent_alerts,
        community_reports=community_reports,
        community_feedback=community_feedback
    )


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
        log_scan("NO_TOKEN")
        return render_template(
            "verify_result.html",
            status="NO_TOKEN",
            details=None,
            recent_alerts=recent_alerts
        )

    try:
        payload = verify_token(token)
    except Exception:
        log_scan("INVALID", token=token)
        return render_template(
            "verify_result.html",
            status="INVALID",
            details=None,
            recent_alerts=recent_alerts
        )

    issued = IssuedQR.query.filter_by(token_hash=token_hash(token)).first()
    if not issued:
        log_scan("NOT_ISSUED", token=token)
        return render_template(
            "verify_result.html",
            status="NOT_ISSUED",
            details=None,
            recent_alerts=recent_alerts
        )

    if issued.revoked_at is not None:
        log_scan("REVOKED", token=token, issued=issued)
        return render_template(
            "verify_result.html",
            status="REVOKED",
            details=None,
            recent_alerts=recent_alerts
        )
    
    exp = int(payload.get("exp", 0))
    now_ts = int(datetime.now(timezone.utc).timestamp())

    if exp and now_ts > exp:
        log_scan("EXPIRED", token=token)
        return render_template(
            "verify_result.html",
            status="EXPIRED",
            details=None,
            recent_alerts=recent_alerts
        )

    cid = payload.get("cid")
    campaign = db.session.get(Campaign, cid)
    if not campaign:
        log_scan("CAMPAIGN_NOT_FOUND", token=token)
        return render_template(
            "verify_result.html",
            status="CAMPAIGN_NOT_FOUND",
            details=None,
            recent_alerts=recent_alerts
        )

    now = datetime.now(timezone.utc)
    campaign_end = campaign.ends_at
    if campaign_end and campaign_end.tzinfo is None:
        campaign_end = campaign_end.replace(tzinfo=timezone.utc)

    if campaign_end and now > campaign_end:
        log_scan("CAMPAIGN_EXPIRED", token=token, issued=issued)
        return render_template(
            "verify_result.html",
            status="CAMPAIGN_EXPIRED",
            details=None,
            recent_alerts=recent_alerts
        )

    charity = db.session.get(Charity, campaign.charity_id)
    if not charity:
        log_scan("CHARITY_NOT_FOUND", token=token)
        return render_template(
            "verify_result.html",
            status="CHARITY_NOT_FOUND",
            details=None,
            recent_alerts=recent_alerts
        )

    collector_id = payload.get("collector_id")
    collector = db.session.get(Collector, collector_id) if collector_id else None

    if not collector or collector.campaign_id != campaign.id:
        log_scan("COLLECTOR_NOT_FOUND", token=token)
        return render_template(
            "verify_result.html",
            status="COLLECTOR_NOT_FOUND",
            details=None,
            recent_alerts=recent_alerts
        )

    duplicate_badge_warning = (
        Collector.query.filter(
            Collector.badge_number == collector.badge_number,
            Collector.id != collector.id
        ).count() > 0
    )

    details = {
        "charity_name": charity.name,
        "charity_reg": charity.registration_number,
        "charity_website": charity.website,
        "campaign_title": campaign.title,
        "campaign_description": campaign.description,
        "campaign_start": campaign.starts_at.isoformat(sep=" ") if campaign.starts_at else None,
        "campaign_end": campaign.ends_at.isoformat(sep=" ") if campaign.ends_at else None,
        "collector_name": collector.full_name,
        "collector_badge": collector.badge_number,
        "collector_photo": collector.photo_filename,
        "token_expires_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat(sep=" ") if exp else None,
    }

    log_scan("VERIFIED", token=token, issued=issued)

    recent_scan_count = ScanEvent.query.filter(
        ScanEvent.issued_qr_id == issued.id,
        ScanEvent.scanned_at >= datetime.now(timezone.utc) - timedelta(minutes=10)
    ).count()

    if recent_scan_count >= 10:
        scan_risk_level = "high"
    elif recent_scan_count >= 5:
        scan_risk_level = "medium"
    else:
        scan_risk_level = "low"

    total_scan_count = ScanEvent.query.filter(
        ScanEvent.issued_qr_id == issued.id
    ).count()

    return render_template(
        "verify_result.html",
        status="VERIFIED",
        details=details,
        recent_alerts=recent_alerts,
        duplicate_badge_warning=duplicate_badge_warning,
        recent_scan_count=recent_scan_count,
        total_scan_count=total_scan_count,
        scan_risk_level=scan_risk_level
    )


def log_scan(status, token=None, issued=None, latitude=None, longitude=None):
    event = ScanEvent(
        issued_qr_id=issued.id if issued else None,
        token_hash=token_hash(token) if token else None,
        status=status,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
        latitude=latitude,
        longitude=longitude,
    )
    db.session.add(event)
    db.session.commit()