# FYP-2026
Doorstep Charity Verification

A web-based system for verifying doorstep charity collection campaigns using secure QR code token validation.

## Overview
This project was developed as part of a Final Year Project CS4501 (Undergraduate).  
The system allows members of the public to scan a QR code presented by a charity collector and instantly verify:

- The registered charity
- The active campaign
- The authorised collector
- Token validity (not expired or revoked)

The goal is to improve transparency and reduce fraudulent charity impersonation.

## Key Features

### Admin Interface
- Create and manage charities
- Create time bound campaigns
- Register and manage collectors
- Issue QR codes with signed tokens
- Revoke issued tokens
- View and manage reports/feedback from the public

### Public Interface
- Scan QR code using mobile browser camera
- Server-side token verification
- Expiry and revocation checks
- Clear verification status messages

### Community Safety Features
- Report suspicious collectors
- Submit feedback on verification results
- View community warnings and alerts

## Technology Stack
- Python (Flask)
- SQLAlchemy
- Flask-Migrate
- SQLite 
- HTML/CSS
- html5-qrcode (camera scanning - https://github.com/mebjas/html5-qrcode)

## Database & Migrations
- SQLite database for development
- Flask-Migrate (Alembic) for schema version control
- Versioned migrations stored in `/migrations`

## Security Measures
- Cryptographically signed tokens
- Token expiry enforcement
- Database backed token validation
- Token hashing for secure storage
- Revocation support
- Protection against reused or tampered QR codes
