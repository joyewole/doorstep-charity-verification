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
- Register collectors
- Issue QR codes with signed tokens
- Revoke issued tokens

### Public Interface
- Scan QR code using mobile browser camera
- Server-side token verification
- Expiry and revocation checks
- Clear verification status messages

## Technology Stack
- Python (Flask)
- SQLAlchemy
- Flask-Migrate
- SQLite 
- HTML/CSS
- html5-qrcode (camera scanning - https://github.com/mebjas/html5-qrcode)

## Security Measures
- Cryptographically signed tokens
- Expiry enforcement
- Database backed token validation
- Token hashing
- Revocation support
