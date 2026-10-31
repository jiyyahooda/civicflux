# Civilian portal — 31 October 2026

## What is implemented

- Public visitors choose **Continue as guest** or **name + Indian mobile number + SMS OTP**. The choice is remembered for that tab session. An existing valid civilian session opens directly. The existing location prompt starts after the welcome choice, rather than competing with it.
- Separate civilian accounts, cookie sessions and private tables; the admin login and PIN jurisdiction are retained. Profile is absent from the admin navigation and admin content. A civilian session never grants admin access.
- Public **Profile** contains Details, My complaints, Places & routes, and Travel planner. Name, optional email/address, saved places and routes belong to the session owner. A verified mobile number identifies the account; it cannot be changed by editing the profile.
- Newly submitted complaints have a private `civilian_id` owner. My complaints selects by that ID. Existing anonymous complaints are preserved and are not claimed by matching an email. Public report responses omit civilian ownership and private contact fields.
- Guests can browse and track a report, but cannot submit one. Manual entry to Report a problem opens login automatically. The form is disabled for guests and the backend independently requires a civilian session. Expired login requests reopen civilian login. Changing accounts clears the previous account's report draft and camera component.
- The complaint UI has **Open camera → live preview → Capture photo → Stop camera**, with up to three photos, previews and removal. There is no gallery/file picker. Permission denial and missing camera/HTTPS have explicit errors. Tracks stop on exit and after the third capture. Photos are uploaded only on deliberate report submission; existing server-side image sanitization remains in force.
- Google map click or keyboard-friendly **Use map centre** selects a private place. Home/Work/Hotel are suggestions; custom labels work. Geocoding search is included but requires Google's Geocoding API/billing access. A shared loader avoids loading Maps JavaScript twice.
- Travel planner supports A, up to five intermediate stops, then B, in the chosen order. Saved places and saved usual routes can populate points. Google Routes `Route.computeRoutes` requests DRIVING / TRAFFIC_AWARE with path, distance, duration and static duration. Google's default departure time avoids device-clock drift. Requests have a deadline. Zero-length routes are rejected. Input changes clear old results; async generations prevent stale checks overwriting new selections. Regular city-data refreshes preserve route inputs.
- Route geometry is checked by the backend against active official-source notice imports for the selected city. Exact HTTPS police/municipal source-host allowlists are used. Located notices within 500 metres of route segments are separate from unlocated city notices. Expired, unrelated and nonofficial records are excluded. Citizen complaints are not recast as official reports.
- Private profile and travel topics extend onboarding to 106 steps / 29 topics. Guest/public tours explain the login/camera conditions. Private topics are available only to signed-in civilians. The tour pauses behind the login dialog, preserves progress and never sends OTPs, starts a camera or saves a place automatically.

## Provider setup and current limitations

The signed-in **Google Chrome** Fast2SMS account was inspected. Its Smart OTP template drawer reported **No DLT Entity found**. The account has Quick SMS enabled at ₹7/message; the user explicitly chose to wait for DLT approval instead. No paid SMS was sent, no template/entity identity was invented, no key was reset and no account security setting was changed.

After the user completes DLT registration:

1. Add the approved Entity ID, Sender ID and OTP content template to Fast2SMS.
2. Create an **SMS-channel-only Smart OTP template** and copy its OTP ID.
3. Set `FAST2SMS_API_KEY` and `FAST2SMS_OTP_TEMPLATE_ID` in the private root `.env` (or Render environment). Never use VITE_ for these secrets or commit them.
4. Restart the backend. `/api/civilian/session` exposes only `sms_configured`, never the secrets.
5. Test a real SMS to an expressly authorized recipient. Provider acceptance is not handset-delivery confirmation. No real delivery was tested in this implementation.

Until then the production/local normal server returns a setup-pending status and does not permit fabricated OTP login. Guest reporting is intentionally unavailable while SMS setup is pending.

Official Fast2SMS contract: https://docs.fast2sms.com/reference/send-otp . The app generates a cryptographically random six-digit code, sends it through `/dev/otp/send` with the approved OTP ID, and verifies its own HMAC digest. Five-minute expiry, five guesses, browser-bound challenge cookie, one-time use, 60-second resend cooldown, five sends/phone/hour and 20 sends/source-IP/hour are enforced in SQLite transactions. A failed provider request cannot create a session. Challenge retention is one day and expired sessions are cleaned when a new session is created. No OTP is returned to the browser or stored in plaintext. Civilian session tokens are stored as hashes, with seven-day expiry and a 24-hour idle timeout. Cookies are HTTP-only / SameSite Strict and Secure over HTTPS. Private responses are `Cache-Control: no-store`; same-origin checks protect writes.

The existing Google key rendered Maps and returned a **real 0.7 km / 3 minute traffic-aware driving route** in local browser QA. Geocoding address search returned Google's **billing must be enabled** error. Billing and Geocoding API access still need owner setup; Routes API access and allowed HTTP referrers should also be checked for the eventual deployed hostname. No billing setting or payment information was changed. Google Route and traffic are provider estimates, not guarantees.

There is no complete automatic police/municipal road-level waterlogging feed connected. The UI therefore shows **Waterlogging: unknown**, links official sources and never declares a route clear because no imported notice matched. Existing traffic/flood/rainfall research artifacts are historical or synthetic and have no validated route geography. They are deliberately not used to manufacture a live road risk score. This implementation does not retrain models or change Delhi datasets.

Camera-only is enforced in the supported website UI. A web server cannot independently attest that an arbitrary image sent by a custom API client came from physical camera hardware; browser capture is not forensic proof. Server validation checks authentication, file content, dimensions, size and sanitization.

Expired admin/civilian cookies are cleared safely. A stale admin cookie no longer forces a guest into admin login. Closing the admin login restores the public URL.

The existing Render free service uses ephemeral SQLite/uploads unless persistent storage is added. Civilian accounts and saved places need durable storage before relying on continuity across redeploys. Current work is saved locally, not pushed or redeployed by this task. The Round1 site is unchanged.

## Verification

- Production TypeScript/Vite build passed.
- Final full backend suite passed: 208 tests, including nine civilian security/workflow tests.
- Tour catalog passed: 9 tests; 106 steps / 29 topics, including civilian-only topic filtering.
- New backend tests cover guest denial, OTP hashing/browser binding/expiry/replay/guess limits/cooldown, provider failure/missing configuration, same-origin rejection, owner isolation across two accounts, complaint ownership and public redaction, logout, no administrator privilege, and official-route source/geometry/expiry filtering.
- Browser QA used a separate localhost-only service at 8011, a temporary database and a stub SMS transport. The normal 8001 backend has no test authentication shortcut and reports `sms_configured:false` pending setup. QA created no production complaints and sent no real SMS.
- Browser checks: welcome and guest choice; login popup on reporting; no file inputs; disabled guest form; real challenge/verification UI against the isolated stub; private profile save; empty owned-report list; direct Google map selection; saved-place and usual-route persistence; real Google route results and honest notice/coverage output; ordered stop insertion and stale-result clearing. At 375×812 there was no horizontal overflow, all six public items appeared in the animated dropdown, and profile arrow-key tabs changed the actual panel and focus. Admin login succeeded in isolated QA and neither the Profile navigation item nor civilian profile content appeared. The temporary QA service was stopped after testing. The normal 5173/8001 server was verified healthy and shows the honest SMS-setup-pending welcome.

Google contract references:
- https://developers.google.com/maps/documentation/javascript/routes/get-a-route
- https://developers.google.com/maps/documentation/javascript/routes/traffic-options
- https://developers.google.com/maps/documentation/javascript/reference/route


## Quick SMS approval and provider activation — 31 October 2026

The owner subsequently approved the INR 7 Quick SMS option and one test recipient.
The existing Kushagra account key was revealed by the owner after Fast2SMS account
verification and saved only in private `.env` (mode 0600). It was not printed or committed.
The selected mode is now `FAST2SMS_MODE=quick`, using the documented POST `/dev/bulkV2`,
route `q`, one recipient and a short ASCII OTP message. Smart OTP remains the default
when Quick mode is not explicitly selected. All existing challenge/session protections remain.

The local Quick mode is capped to one attempt using `FAST2SMS_QUICK_LIMIT=1` and a private
activation timestamp. Attempts reserve their budget slot transactionally before sending;
there are no automatic retries or a paid fallback. Verification of an accepted challenge
still works after the send budget is exhausted. Extra sends require separate owner approval.

The single authorized live request was rejected by Fast2SMS with HTTP 400 / code 999:
**You need to complete one transaction of 100 INR or more before using API route.**
The provider API log shows Failed, and the wallet still displayed INR 50. No OTP was sent.
The wallet top-up is a separate owner action; no payment or second send was performed.
A specific actionable activation error is now mapped without exposing provider payloads.
The conservative attempt cap remains consumed until the owner completes activation and
an authorized retry is prepared. Render has not been redeployed with these local changes.


## Prototype guest access update
Guest reporting no longer requires OTP. Valid guest submissions are saved without a
civilian account owner; registered-account profiles remain authenticated. The public
Profile tab opens a guest workspace with browser-local details, places and usual
routes. Only reports submitted as guest in this browser are listed there by their
public tracking IDs. Browser storage is shared by users of that browser and does
not establish verified identity or transfer ownership of registered accounts.
Travel advisory checks now read public official notices without requiring login.
Admin permissions and camera-only evidence are unchanged. OTP setup stays optional
and pending; no new SMS/WhatsApp delivery or payment is performed.


### SMS preparation — payment deferred (31 October 2026)
The local service now selects Fast2SMS Quick SMS using its private environment credential. One future send attempt is approved; no SMS was sent or payment made during preparation. The earlier provider response was HTTP 400/code 999, requiring a first transaction of INR 100 or more. After the owner completes activation, manually request a code from Login and enter the received SMS. Acceptance by the provider alone is not proof of delivery.

An explicit HTTP 400/code 999 is recorded as payment_required and does not consume the paid-send allowance; normal cooldown and request limits still apply. Other failures, including timeouts with uncertain delivery, consume the allowance to avoid accidental repeat charges. There is no automatic retry or route fallback. The next single attempt is enabled locally; further paid sends require owner approval.

Guest complaint submission and the browser-local guest profile remain enabled pending successful real SMS verification. Registered profile data remains authenticated and owner-only. Mandatory report login has not been restored prematurely. These changes are local, not a Render deployment.


Owner approved raising the local Quick SMS allowance to 10 total attempts on 31 October 2026. The activation timestamp and existing usage were retained. Attempt history is retained so OTP expiry does not reset this financial cap. Render has FAST2SMS_QUICK_LIMIT=10 saved only; its older deployed application has not been updated by this configuration change. No SMS was sent when applying this allowance.
