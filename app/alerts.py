from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import FraudAlert, PublicReport

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.get("/alerts")
def alerts_list():
    alerts = (
        FraudAlert.query
        .filter_by(is_active=True)
        .order_by(FraudAlert.published_at.desc(), FraudAlert.created_at.desc())
        .all()
    )
    return render_template("alerts.html", alerts=alerts)


@alerts_bp.route("/report-suspicious", methods=["GET", "POST"])
def report_suspicious():
    if request.method == "POST":
        report = PublicReport(
            reporter_name=request.form.get("reporter_name"),
            reporter_email=request.form.get("reporter_email"),
            location=request.form.get("location", "").strip(),
            claimed_charity=request.form.get("claimed_charity"),
            collector_description=request.form.get("collector_description"),
            description=request.form.get("description", "").strip(),
        )
        db.session.add(report)
        db.session.commit()
        flash("Thank you. Your report has been submitted for review.", "success")
        return redirect(url_for("alerts.report_suspicious"))

    return render_template("report_suspicious.html")