# Prism by Kaleidoscope

Turns YouTube links and uploaded videos into timestamped transcripts, summaries and goal-tailored action plans, all downloadable as Markdown. It's a personal Azure web app behind Microsoft sign-in.

- **Spec and build plan:** [docs/spec.md](docs/spec.md)
- **Setup, deploy and test checklist:** [docs/SETUP.md](docs/SETUP.md)

## Layout

```
frontend/   React + TypeScript (Vite), hosted on Azure Static Web Apps
backend/    Python Azure Functions (Durable Functions for jobs)
  prism/models.py          job record (jobs/{ownerId}/{jobId}.json)
  prism/providers/         transcription + generation interfaces, chosen by config
  prism/storage/           Blob clients (managed identity) and job store
infra/      Bicep: SWA, Function App, Storage, Key Vault, identity, monitoring
scripts/    deploy.sh, invite-owner.sh
```

## Status

| Milestone | State |
|---|---|
| M0 Foundation | Built, ready to test |
| M1 Upload → transcript | — |
| M2 YouTube → transcript | — |
| M3 Summary | — |
| M4 Action Plan | — |
| M5 Download and polish | — |
| M6 Real-world test | — |
