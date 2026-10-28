# Deploy CivicFlux on Render

Live site: https://civicflux.onrender.com/

Render dashboard: https://dashboard.render.com/web/srv-dbh0pde1egvs73eb9dhg

The initial service was created using the public repository connection. To deploy
subsequent main-branch commits, use **Manual Deploy > Deploy latest commit** in
Render. Automatic deployment requires configuring the GitHub provider integration
or linking this repository through a Blueprint.

The Dockerfile builds React using Node 24 and the locked pnpm version, installs
Python 3.13 serving dependencies and Linux OpenMP, then serves the frontend and
API from one FastAPI process. No local virtual environment or Node modules are
uploaded. It never retrains models or copies your local database/photos.

## Create the service

1. Sign in at https://dashboard.render.com/ and connect your GitHub account.
2. Choose **New > Blueprint** and select `jiyyahooda/civicflux`, branch `main`.
   Render reads `render.yaml`. Alternatively choose **New > Web Service**, the
   same repository, **Docker** language and root `Dockerfile`.
3. Enter `VITE_GOOGLE_MAPS_API_KEY` (a browser key
   restricted to Maps JavaScript API), and `WAQI_API_TOKEN` when prompted.
   Area login is `admin` plus a listed six-digit postal PIN; the previous `001` login is retired. No secrets are committed to this configuration.
   Optional `OPENWEATHERMAP_API_KEY` can be added in Environment for rain tiles.
4. Keep the Docker command unset: the image already runs
   `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT` (8001 locally).
   Health check path: `/api/health`. The free plan is selected; this configuration
   creates no paid disk or database.
5. Deploy, inspect the build/runtime logs, and open the HTTPS URL Render assigns.
6. Add `https://YOUR-SERVICE.onrender.com/*` to the Google key's allowed website
   referrers. Enable Maps JavaScript API and appropriate billing in its Google
   project. Rebuild/redeploy after changing `VITE_GOOGLE_MAPS_API_KEY`: Vite
   embeds this public browser key at build time. Server tokens stay runtime-only.

Verify `/`, `/api/health`, `/api/models`, a map, and admin login after deployment.
GitHub main pushes can deploy updates automatically; check Render's auto-deploy
setting. A successful GitHub push alone does not mean the site is deployed.

## Free plan and persistent records

Render Free has 512 MB RAM and sleeps after 15 minutes without inbound traffic.
All nine models have not been measured on that instance: an out-of-memory restart
means more memory is required. SQLite, accounts, reports and uploaded photos are
lost whenever the ephemeral filesystem is replaced. Do not rely on free storage
for municipal records. Do not run multiple service instances sharing this SQLite DB.

For durable records, choose a paid instance with sufficient memory, attach a
persistent disk at `/var/data`, and set `CIVICFLUX_DB=/var/data/civicflux.sqlite3`.
Uploads are automatically stored beside it at `/var/data/uploads`. Update the
Blueprint as well if you manage this service through it. A new disk starts empty:
no private local records are transferred automatically. Area accounts are seeded
from the committed postal reference. Use scripts/provision_admin.py on the trusted
server console to activate or deactivate an area.

## Data and feature availability

GitHub includes saved model artifacts, exported test results and reference data.
`data/raw` is deliberately excluded. Historical-example requests requiring those
original CSVs can abstain until you supply the inputs from DATASET_GUIDE.md.
Do not represent this as an identical copy of the Mac's private database/datasets.
Live provider features also depend on valid keys and upstream availability.
No automatic dataset download or credential publication is performed by deployment.

## Local Docker verification (requires Docker)

```sh
docker build -t civicflux .
docker run --rm -p 8001:8001 -e CIVICFLUX_PUBLIC_FEEDS=0 civicflux
```

Open http://127.0.0.1:8001/. To retain local Docker records, mount a writable
volume at `/app/var`. Add your credentials through runtime environment settings;
only the restricted browser Maps key is passed with `--build-arg` at image build.

Official references: https://render.com/docs/docker,
https://render.com/docs/blueprint-spec, https://render.com/docs/free,
https://render.com/docs/disks.
