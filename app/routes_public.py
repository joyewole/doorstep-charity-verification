from flask import Blueprint, render_template, request
from datetime import datetime, timezone

from app.models import Campaign, Charity, IssuedQR, Collector
from app.services.token_service import verify_token, token_hash

public_bp = Blueprint("public", __name__)

@public_bp.get("/")
def home():
    return render_template("home.html")

@public_bp.get("/scan")
def scan():
    return render_template("scan.html")

@public_bp.get("/verify")
def verify_page():
    token = request.args.get("token", "").strip()
    if not token:
        return render_template("verify_result.html", status="NO TOKEN", details=None)

    # 1) Verify signature
    try:
        payload = verify_token(token)
    except Exception:
        return render_template("verify_result.html", status="INVALID", details=None)

    # 2) Check expiry
    exp = int(payload.get("exp", 0))
    now = int(datetime.now(tz=timezone.utc).timestamp())
    if exp and now > exp:
        return render_template("verify_result.html", status="EXPIRED", details=None)

    # 3) Check token exists in DB and not revoked - prevents random signed tokens
    issued = IssuedQR.query.filter_by(token_hash=token_hash(token)).first()
    if not issued:
        return render_template("verify_result.html", status="NOT ISSUED", details=None)

    if issued.revoked_at is not None:
        return render_template("verify_result.html", status="REVOKED", details=None)

    # 4) Load campaign and charity details
    cid = payload.get("cid")
    campaign = Campaign.query.get(cid)
    if not campaign:
        return render_template("verify_result.html", status="CAMPAIGN NOT FOUND", details=None)

    charity = Charity.query.get(campaign.charity_id)
    if not charity:
        return render_template("verify_result.html", status="CHARITY NOT FOUND", details=None)
    
    # 5) Load collector details (from token)
    collector_id = payload.get("collector_id")
    collector = Collector.query.get(collector_id) if collector_id else None

    if not collector or collector.campaign_id != campaign.id:
        return render_template("verify_result.html", status="COLLECTOR NOT FOUND", details=None)
    
    return render_template(
        "verify_result.html",
        status="VERIFIED",
        details={
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
        },
    )