# Support-form follow-up emails

`backend.services.complaint_email.send_follow_up(recipient_email, issue_details)`
sends a receipt using dynamic recipient and issue data. It returns `status`,
`provider_accepted`, and `failure_code`; it does not raise delivery exceptions to
form handlers. Use a trusted backend caller, never an unrestricted public mail API.
The existing complaint confirmation workflow uses the same message builder and
retains its report-level deduplication, rate limits and persistent attempt status.

Set these privately in the root `.env` or deployment environment:

```dotenv
SENDER_EMAIL=civicflux10@gmail.com
SENDER_PASSWORD=YOUR_GOOGLE_APP_PASSWORD
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_SECURITY=ssl
SMTP_TIMEOUT=10
```

For STARTTLS use `SMTP_PORT=587` and `SMTP_SECURITY=starttls`. For a different
standard provider, change SMTP_HOST and its required encrypted port. Custom ports
are supported; plaintext authentication is refused. Certificate and hostname
verification remain enabled. Existing SMTP_USER / SMTP_PASS aliases still work.
Never commit credentials or use a normal Gmail account password here.
Restart the backend after editing `.env`; environment values are read per send.

```python
import logging
from backend.services.complaint_email import send_follow_up

logging.basicConfig(level=logging.INFO)
result = send_follow_up(
    recipient_email="civilian@example.org",
    issue_details={
        "report_id": "CF-2026-100",
        "title": "Blocked drain",
        "description": "Water is accumulating near the market.",
        "category": "drainage",
        "location": "Reported locality",
        "postal_code": "110001",
        "status": "submitted",
    },
)
# result['status'] == 'sent' means SMTP acceptance, not confirmed inbox delivery.
```

The professional plain-text and HTML messages acknowledge receipt into the review
queue, include report details and tracking instructions, and retain the existing
clarification that CivicFlux reports are not submissions to a government system.
HTML content is escaped; email addresses and report IDs are validated before
building headers. Logs include an error type/category and a reference, not SMTP
response bodies, passwords, contact addresses or issue contents. A timeout after
sending can leave acceptance uncertain, so automatic retries are not attempted.

Validation: 34 affected tests passed, including encryption-before-login ordering,
certificate verification, dynamic inputs, escaped HTML, success logging,
authentication/network/recipient failures and existing confirmation persistence.
No real email was sent and no private credentials were configured by this change.
