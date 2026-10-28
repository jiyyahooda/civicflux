# Render deployment verification — 2026-10-28

- Source deployed: d8854dc83130dcdb80b86190eead4b55fafe8167, personal repository main.
- Public address: https://civicflux.onrender.com/
- Free Docker web service: srv-dbh0pde1egvs73eb9dhg.
- Render build completed and service reported live; API health returned status ok.
- Homepage, built assets and burgundy-white favicon served successfully.
- Existing configured administrator signed in through the hosted browser UI;
  municipal Planning, Decisions and Review reports navigation appeared.
- Hosted model inventory returned all nine components.
- Google TrafficLayer rendered its map controls and Google attribution.
- WAQI map rendered Delhi station readings, names and observation timestamps.
- Local regression suite: 137 passed; frontend production build passed.
- Linux deployment image build, model inference checks and served frontend HTTP
  checks passed: https://github.com/jiyyahooda/civicflux/actions/runs/40710182230

Only the selected administrator and provider settings were entered individually
into Render. No complete local .env, local SQLite database, photos, or restricted
raw datasets were uploaded. No paid disk or compute plan was selected. The free
service has ephemeral records and cold starts. Historical examples requiring
original raw datasets can abstain until those inputs are supplied.
