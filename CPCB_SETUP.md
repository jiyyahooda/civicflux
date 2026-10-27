# Connect official CPCB data to CivicFlux

Project folder: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux`.

## What you are connecting

CPCB publishes air-quality station reports. The Government of India's Open Government Data platform, data.gov.in, provides an API for a CPCB resource. CivicFlux already contains the backend connector. You need your own data.gov.in account and API key; you do not need to add a new frontend API or retrain a model.

The data path is:

`data.gov.in API → backend/integrations/cpcb.py → city/station/time validation → SQLite response cache → /api/observations?city_id=delhi → CPCB source card`

IMD weather and CAMS air estimates are separate connections. A successful CAMS connection does not mean CPCB is connected.

## 1. Obtain an account and key

1. Open [data.gov.in](https://data.gov.in/), the official OGD portal.
2. Use its Login / registration flow. If you do not have an account, register and complete the verification steps the portal actually presents.
3. Sign in. Look in your account/dashboard for API key generation or API access. The exact menu wording can change; the [official Help page](https://data.gov.in/help) includes **How to operate My Account** and **How to use Datasets APIs**. It confirms API-key generation is available to registered portal users.
4. Generate/copy your personal API key. Keep it locally; do not paste it into this chat or a frontend input. CivicFlux has no browser-side key field by design.

If the portal is unavailable, shows an incomplete resource page or identifies itself as a sandbox, wait for the normal official portal/account service rather than supplying credentials to a demonstration page. During this implementation, a Help request intermittently returned HTTP 503 and the resource's rendered page was incomplete. Those provider-side problems cannot be repaired by changing the CivicFlux key.

## 2. Find the correct CPCB resource

Search the portal for **Real time Air Quality Index from various locations**, published by the Central Pollution Control Board. Open its [resource page](https://www.data.gov.in/resource/real-time-air-quality-index-various-locations).

The connector currently uses resource ID:

```text
3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69
```

API endpoint:

```text
https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69
```

Use the resource's API explorer/documentation to confirm its active endpoint, field names and access requirements before testing your key. Do not use a copied public/demo key. The existing connector sends these query parameters server-side:

| Parameter | Value |
| --- | --- |
| `api-key` | Your own secret key |
| `format` | `json` |
| `filters[city]` | `Delhi`, `Chandigarh` or `Chennai` |
| `limit` | `1000` |

The raw records are expected to include `country`, `state`, `city`, `station`, `latitude`, `longitude`, `last_update`, `pollutant_id` and `pollutant_avg`. Field/filter names and city spelling must match the resource. A HTTP 200 response alone does not establish that usable station records were returned.

## 3. Save the key locally

Open PowerShell in the project folder:

```powershell
Set-Location 'C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux'
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
notepad .env
```

Set these lines, preserving your other settings:

```dotenv
CIVICFLUX_PUBLIC_FEEDS=1
DATA_GOV_IN_API_KEY=YOUR_PERSONAL_KEY
CIVICFLUX_CPCB_URL=
```

Replace `YOUR_PERSONAL_KEY` with the actual key; do not leave the placeholder. Keep `CIVICFLUX_CPCB_URL` blank for the standard OGD connector. That variable is only for an already verified canonical gateway override. Never put the key in a `VITE_` variable, React file, public folder or Git commit. `.env` is excluded by the project's `.gitignore`.

`backend/config.py` loads `.env` from the central project root. Existing process environment variables take precedence over `.env`, so an old inherited `DATA_GOV_IN_API_KEY` or `CIVICFLUX_PUBLIC_FEEDS=0` can override the file. Open a fresh terminal after updating system-level variables.

## 4. Test the connector without exposing the key

Run the supplied diagnostic from the project root:

```powershell
.\.venv-windows\Scripts\python.exe scripts/check_cpcb.py --city delhi
```

You can repeat with `--city chandigarh` and `--city chennai`. It reads the local configuration, requests the official API and reports station identity, source time, freshness and publisher values. It does not print the key or the key-bearing request URL. A missing key prints setup guidance without making an external request.

Exit code 0 means fresh validated data; code 1 means missing configuration or an unsuccessful verification; code 2 means a response was returned but is not fresh. Do not share a shell/debug log containing an API request URL: query parameters can contain the key even though CivicFlux's own diagnostic omits them.

## 5. Restart and verify the website

After saving `.env`, double-click `RESTART-CIVICFLUX.cmd` or run:

```powershell
.\RESTART-CIVICFLUX.cmd
```

The restart helper verifies the executable belongs to this project's Windows environment and the command is CivicFlux on port 8000 before stopping it. It then uses the normal launcher in the current terminal. If process inspection is unavailable, close the existing server terminal with Ctrl+C and run `START-CIVICFLUX.cmd` manually. Leave that server running and open [CivicFlux locally](http://127.0.0.1:8000/). Opening `frontend/dist/index.html` directly will not run the API. If you use Vite during development, the FastAPI backend must still be running on port 8000.

Select Delhi. In the dashboard's connected sources, inspect **CPCB · official pollutant reports**. Expect a station, source timestamp and fresh/stale state rather than the missing-key message. Independently inspect the local endpoint:

```powershell
$observations = Invoke-RestMethod 'http://127.0.0.1:8000/api/observations?city_id=delhi'
$observations.feeds | Where-Object source -eq 'CPCB' |
    Select-Object source,status,station_name,observed_at,reason,readings
```

This local request does not include the key. The backend keeps provider credentials off the frontend. Successful raw responses are cached for 15 minutes to avoid repeated provider requests. The UI background refresh therefore does not mean every refresh makes a fresh upstream request.

## 6. Understand station mappings and values

The connector verifies the provider's city/state/country identity, station coordinates near the configured city reference, and timestamp. It does not invent station IDs. For CPCB, a station's actual provider name acts as its identifier; it is not an IMD station number. The response records how the station was selected and whether the first API page was complete.

`last_update` currently lacks an explicit timezone, so the connector declares an Asia/Kolkata interpretation. Reports older than three hours are stale. A network-failure cache fallback remains marked stale and preserves the old source time.

The resource name contains AQI, but that does not establish that each `pollutant_avg` is an overall city AQI, or that all reported pollutants share a concentration unit. The current connector deliberately shows **publisher value; unit unverified** for these raw reports. Before displaying a CPCB PM2.5 concentration or calculating an Indian AQI, verify the resource's pollutant-specific units and averaging periods with the publisher's documentation. Do not substitute the CAMS **US AQI** value for an Indian AQI. This unit-verification step is separate from making the API request succeed.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Missing-key message | Save the real key in project-root `.env`; restart FastAPI; check inherited environment overrides. |
| HTTP 401/403 from provider | Confirm key activation, resource access and exact endpoint in the official API explorer. |
| HTTP 429 | Observe provider rate limits; wait. Keep backend caching enabled. |
| Timeout, network failure or provider 5xx | Check connectivity/provider availability and retry later. Do not disable TLS verification. |
| HTTP 200 but no usable station | Check `records`, city/state spelling, missing pollutant values and actual resource field names. |
| Wrong city or coordinate validation failure | Verify the real station and geographic mapping; do not disable validation to force it through. |
| Stale source | Inspect the source timestamp. Restarting CivicFlux cannot make an old station observation current. |
| No concentration/overall Indian AQI | Publisher units/averaging semantics are still unverified; connecting a key alone does not resolve them. |
| Website cannot reach backend | Run `START-CIVICFLUX.cmd`; use the HTTP app URL, not a local HTML file. |

For a future hosted deployment, put `DATA_GOV_IN_API_KEY` into the backend host's secret/environment settings and restart that backend. Keep the frontend calling the application's `/api/observations` route. A static-only deployment cannot run the Python connector.

No personal key was available during implementation, so successful authenticated CPCB access has not been claimed or fabricated.
