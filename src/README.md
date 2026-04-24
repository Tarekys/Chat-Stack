

## SMTP Email Service (Gmail)

This project uses Gmail SMTP to send emails (e.g., account verification and password reset) via the SMTP protocol.

### Configuration:
- Uses Gmail with an **App Password** instead of the regular account password.
- Server: `smtp.gmail.com`
- Port: `587` with `TLS` enabled

### Limits:
- Up to **500 emails per day** for standard Gmail accounts.
- Maximum ~ **100 recipients per email**.
- No official monthly limit, but excessive usage may lead to temporary blocking.

### Notes:
- Suitable for development and small-scale projects.
- Not recommended for bulk or production-level email sending.
- For large-scale applications, consider using dedicated email services (Email APIs).