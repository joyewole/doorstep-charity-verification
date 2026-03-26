# FYP-2026
Doorstep Charity Verification

A web-based system for verifying doorstep charity collection campaigns using secure, cryptographically signed QR code tokens.

## Overview
This project was developed as part of a Final Year Project CS4501 (Undergraduate).  
The system allows members of the public to scan a QR code presented by a charity collector and instantly verify:

- The registered charity
- The active campaign
- The authorised collector
- Token validity (not expired or revoked)

The goal is to improve transparency, increase public trust and reduce fraudulent charity impersonation.

## Key Features

### Admin Interface
- Create and manage registered charities
- Create time bound campaigns
- Register and manage collectors (with badge ids and optional photos)
- Issue QR codes with cryptographically signed tokens
- Revoke issued tokens instantly
- View and manage public reports/feedback from the public
- View scan activity logs for monitoring suspicious behaviour

### Public Interface
- Scan QR code using a mobile browser camera
- Perform secure server-side token verification
- Validate expiry, revocation and campaign status
- Display clear verification resuls and status messages to users

### Advanced Fraud Detection Features
To extend beyond basic verification, the system includes additional safety mechanisms:
- **Duplicate Badge Detection**  
    - Flags when multiple collectors share the same badge number  
- **Scan Activity Monitoring**  
    - Logs all QR scans with timestamp and IP address  
- **High-Frequency Scan Detection**  
    - Detects unusually frequent scans within short time periods, indicating possible QR code copying or sharing  
- **Scan Count Transparency**  
    - Displays total scan count to help identify abnormal usage  
These features provide an additional layer of protection against misuse and fraud.

### Community Safety Features
- Report suspicious collectors
- Submit feedback on verified collectors
- Separate reporting for:
    - Suspicious activity
    - Genuine collector confirmation
- View community submitted warnings and alerts

## Technology Stack
- Python (Flask)
- SQLAlchemy
- Flask-Migrate
- SQLite 
- HTML/CSS
- JavaScript
- html5-qrcode (camera scanning - https://github.com/mebjas/html5-qrcode)

## Database & Migrations
- SQLite database used for development
- Flask-Migrate (Alembic) used for schema version control
- Versioned migrations stored in `/migrations`

## Security Measures
- Cryptographically signed QR tokens
- Token expiry enforcement
- Database backed token validation
- Token hashing for secure storage
- Token revocation support
- Protection against reused or tampered QR codes
