import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from datetime import datetime, timezone, timedelta
from app import db
from app.models import Charity, Campaign, IssuedQR, Collector, PublicReport, ScanEvent
from app.services.token_service import sign_payload, token_hash
from app.services.qr_service import make_qr_png
from werkzeug.utils import secure_filename
from flask_login import login_required


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

admin_bp = Blueprint("admin", __name__)

@admin_bp.get("/")
@login_required
def dashboard():
    charities = Charity.query.order_by(Charity.name.asc()).all()
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return render_template("admin/dashboard.html", charities=charities, campaigns=campaigns)

# -------- For Charities --------

@admin_bp.get("/charities/new")
@login_required
def new_charity():
    return render_template("admin/create_charity.html")

@admin_bp.post("/charities/new")
@login_required
def create_charity():
    name = request.form.get("name", "").strip()
    reg = request.form.get("registration_number", "").strip()
    website = request.form.get("website", "").strip() or None

    if not name or not reg:
        flash("Name and registration number are required.", "error")
        return redirect(url_for("admin.new_charity"))

    existing = Charity.query.filter_by(registration_number=reg).first()
    if existing:
        flash("A charity with that registration number already exists.", "error")
        return redirect(url_for("admin.new_charity"))

    charity = Charity(name=name, registration_number=reg, website=website)
    db.session.add(charity)
    db.session.commit()

    flash("Charity created successfully.", "success")
    return redirect(url_for("admin.dashboard"))

# -------- For Campaigns --------

@admin_bp.get("/campaigns/new")
@login_required
def new_campaign():
    charities = Charity.query.order_by(Charity.name.asc()).all()
    return render_template("admin/create_campaign.html", charities=charities)

@admin_bp.post("/campaigns/new")
@login_required
def create_campaign():
    charity_id = request.form.get("charity_id", "").strip()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip() or None
    starts_at = request.form.get("starts_at", "").strip()
    ends_at = request.form.get("ends_at", "").strip()

    if not charity_id or not title or not starts_at or not ends_at:
        flash("Charity, title, start date, and end date are required.", "error")
        return redirect(url_for("admin.new_campaign"))

    try:
        start_dt = datetime.fromisoformat(starts_at)
        end_dt = datetime.fromisoformat(ends_at)
    except ValueError:
        flash("Invalid date format. Please use the date picker.", "error")
        return redirect(url_for("admin.new_campaign"))

    if end_dt <= start_dt:
        flash("End date must be after start date.", "error")
        return redirect(url_for("admin.new_campaign"))

    charity = Charity.query.get(int(charity_id))
    if not charity:
        flash("Selected charity not found.", "error")
        return redirect(url_for("admin.new_campaign"))

    campaign = Campaign(
        charity_id=charity.id,
        title=title,
        description=description,
        starts_at=start_dt,
        ends_at=end_dt,
        status="active",
    )
    db.session.add(campaign)
    db.session.commit()

    flash("Campaign created successfully.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.get("/campaigns/<int:campaign_id>/edit")
@login_required
def edit_campaign(campaign_id: int):
    campaign = Campaign.query.get_or_404(campaign_id)
    charities = Charity.query.order_by(Charity.name.asc()).all()
    return render_template("admin/edit_campaign.html", campaign=campaign, charities=charities)


@admin_bp.post("/campaigns/<int:campaign_id>/edit")
@login_required
def update_campaign(campaign_id: int):
    campaign = Campaign.query.get_or_404(campaign_id)

    charity_id = request.form.get("charity_id", "").strip()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip() or None
    starts_at = request.form.get("starts_at", "").strip()
    ends_at = request.form.get("ends_at", "").strip()
    status = request.form.get("status", "").strip() or "active"

    if not charity_id or not title or not starts_at or not ends_at:
        flash("Charity, title, start date, and end date are required.", "error")
        return redirect(url_for("admin.edit_campaign", campaign_id=campaign_id))

    try:
        start_dt = datetime.fromisoformat(starts_at)
        end_dt = datetime.fromisoformat(ends_at)
    except ValueError:
        flash("Invalid date format. Please use the date picker.", "error")
        return redirect(url_for("admin.edit_campaign", campaign_id=campaign_id))

    if end_dt <= start_dt:
        flash("End date must be after start date.", "error")
        return redirect(url_for("admin.edit_campaign", campaign_id=campaign_id))

    charity = Charity.query.get(int(charity_id))
    if not charity:
        flash("Selected charity not found.", "error")
        return redirect(url_for("admin.edit_campaign", campaign_id=campaign_id))

    campaign.charity_id = charity.id
    campaign.title = title
    campaign.description = description
    campaign.starts_at = start_dt
    campaign.ends_at = end_dt
    campaign.status = status

    db.session.commit()

    flash("Campaign updated successfully.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.post("/campaigns/<int:campaign_id>/delete")
@login_required
def delete_campaign(campaign_id: int):
    campaign = Campaign.query.get_or_404(campaign_id)

    issued = IssuedQR.query.filter_by(campaign_id=campaign_id).first()
    if issued:
        flash("Cannot delete this campaign because QR codes have already been issued.", "error")
        return redirect(url_for("admin.dashboard"))

    # Delete collectors linked to this campaign first
    Collector.query.filter_by(campaign_id=campaign_id).delete()

    db.session.delete(campaign)
    db.session.commit()

    flash("Campaign deleted successfully.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.post("/campaigns/<int:campaign_id>/issue-qr")
@login_required
def issue_qr(campaign_id: int):
    campaign = Campaign.query.get_or_404(campaign_id)
    now = datetime.utcnow()

    if campaign.starts_at > now:
        flash("QR codes cannot be issued before the campaign start date.", "error")
        return redirect(url_for("admin.dashboard"))

    if campaign.ends_at < now:
        flash("This campaign has already ended. QR codes cannot be issued.", "error")
        return redirect(url_for("admin.dashboard"))

    collector_id = request.form.get("collector_id")
    if not collector_id:
        flash("Please select a collector.", "error")
        return redirect(url_for("admin.issue_qr_page", campaign_id=campaign_id))

    collector = Collector.query.get(int(collector_id))
    if not collector or collector.campaign_id != campaign_id:
        flash("Invalid collector selected.", "error")
        return redirect(url_for("admin.issue_qr_page", campaign_id=campaign_id))

    default_expiry = now + timedelta(days=7)
    actual_expiry = min(default_expiry, campaign.ends_at)
    exp = int(actual_expiry.timestamp())

    payload = {
        "cid": campaign.id,
        "collector_id": collector.id,
        "exp": exp,
        "n": f"camp-{campaign.id}-col-{collector.id}-{int(now.timestamp())}"
    }

    token = sign_payload(payload)

    record = IssuedQR(
        campaign_id=campaign.id,
        collector_id=collector.id,
        token=token,
        token_hash=token_hash(token),
        expires_at=actual_expiry,
        revoked_at=None,
    )
    db.session.add(record)
    db.session.commit()

    flash("QR issued successfully.", "success")
    return redirect(url_for("admin.show_qr", issued_id=record.id))

@admin_bp.get("/campaigns/<int:campaign_id>/issued-qrs")
@login_required
def issued_qrs(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    issued_list = (
        IssuedQR.query
        .filter_by(campaign_id=campaign_id)
        .order_by(IssuedQR.created_at.desc())
        .all()
    )
    return render_template(
        "admin/issued_qrs_list.html",
        campaign=campaign,
        issued_list=issued_list
    )


@admin_bp.post("/issued-qrs/<int:issued_id>/revoke")
@login_required
def revoke_issued_qr(issued_id):
    issued = IssuedQR.query.get_or_404(issued_id)

    if issued.revoked_at is None:
        issued.revoked_at = datetime.utcnow()
        db.session.commit()
        flash("QR token revoked successfully.", "success")
    else:
        flash("This token is already revoked.", "error")

    return redirect(url_for("admin.issued_qrs", campaign_id=issued.campaign_id))

@admin_bp.get("/issued/<int:issued_id>")
@login_required
def show_qr(issued_id: int):
    issued = IssuedQR.query.get_or_404(issued_id)
    campaign = Campaign.query.get_or_404(issued.campaign_id)
    charity = Charity.query.get_or_404(campaign.charity_id)

    return render_template("admin/issued_qr.html", issued=issued, campaign=campaign, charity=charity)

@admin_bp.get("/reports")
@login_required
def reports_list():
    reports = (
        PublicReport.query
        .order_by(PublicReport.submitted_at.desc())
        .all()
    )
    return render_template("admin/reports_list.html", reports=reports)

@admin_bp.get("/scan-logs")
@login_required
def scan_logs():
    logs = (
        ScanEvent.query
        .order_by(ScanEvent.scanned_at.desc())
        .all()
    )
    return render_template("admin/scan_logs.html", logs=logs)

@admin_bp.post("/reports/<int:report_id>/status")
@login_required
def update_report_status(report_id: int):
    report = PublicReport.query.get_or_404(report_id)
    new_status = request.form.get("status", "").strip().lower()

    allowed_statuses = {"pending", "reviewed", "escalated", "dismissed"}
    if new_status not in allowed_statuses:
        flash("Invalid report status.", "error")
        return redirect(url_for("admin.reports_list"))

    report.status = new_status
    db.session.commit()

    flash("Report status updated successfully.", "success")
    return redirect(url_for("admin.reports_list"))

@admin_bp.get("/issued/<int:issued_id>/qr.png")
@login_required
def issued_qr_png(issued_id: int):
    issued = IssuedQR.query.get_or_404(issued_id)

    base = os.getenv("PUBLIC_BASE_URL", "http://172.20.10.2:5050")
    verify_url = f"{base}/verify?token={issued.token}"

    png_bytes = make_qr_png(verify_url)
    return Response(png_bytes, mimetype="image/png")

@admin_bp.get("/campaigns/<int:campaign_id>/collectors/new")
@login_required
def new_collector(campaign_id: int):
    campaign = Campaign.query.get_or_404(campaign_id)
    charity = Charity.query.get_or_404(campaign.charity_id)
    return render_template("admin/create_collector.html", campaign=campaign, charity=charity)

@admin_bp.post("/campaigns/<int:campaign_id>/collectors/new")
@login_required
def create_collector(campaign_id: int):
    campaign = Campaign.query.get_or_404(campaign_id)

    full_name = request.form.get("full_name", "").strip()
    badge_number = request.form.get("badge_number", "").strip()

    if not full_name or not badge_number:
        flash("Full name and badge number are required.", "error")
        return redirect(url_for("admin.new_collector", campaign_id=campaign_id))

    photo = request.files.get("photo")
    photo_filename = None

    if photo and photo.filename:
        if not allowed_file(photo.filename):
            flash("Photo must be PNG/JPG/JPEG/WEBP.", "error")
            return redirect(url_for("admin.new_collector", campaign_id=campaign_id))

        uploads_dir = os.path.join("app", "static", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        safe = secure_filename(photo.filename)
        photo_filename = f"campaign{campaign_id}_{int(datetime.utcnow().timestamp())}_{safe}"
        photo.save(os.path.join(uploads_dir, photo_filename))

    existing_badge = Collector.query.filter_by(badge_number=badge_number).first()
    duplicate_badge_detected = existing_badge is not None

    collector = Collector(
        campaign_id=campaign_id,
        full_name=full_name,
        badge_number=badge_number,
        photo_filename=photo_filename, 
    )
    db.session.add(collector)
    db.session.commit()

    if duplicate_badge_detected:
        flash("Collector added, but warning: this badge number is already assigned to another collector.", "error")
    else:
        flash("Collector added successfully.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.get("/campaigns/<int:campaign_id>/issue-qr")
@login_required
def issue_qr_page(campaign_id: int):
    campaign = Campaign.query.get_or_404(campaign_id)
    collectors = Collector.query.filter_by(campaign_id=campaign_id).all()
    charity = Charity.query.get_or_404(campaign.charity_id)
    return render_template("admin/issue_qr_select.html", campaign=campaign, charity=charity, collectors=collectors)
