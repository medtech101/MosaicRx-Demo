# MosaicRx — Investor Demo

A polished, front-end-only proof of concept for **MosaicRx**, a reverse-causal,
phenotype-conditioned clinical decision support layer for geriatric polypharmacy.

> **DEMO — synthetic data, simulated reasoning, not for clinical use.**
> This is not the production system. It uses only synthetic patients and scripted
> reasoning, and it is safe to show publicly. No backend, no network calls, no login.

## Open the demo

The whole app is bundled into a single self-contained file: [`index.html`](index.html).

- **Live page (no login):** once GitHub Pages is enabled for this repo, it is served at
  `https://medtech101.github.io/MosaicRx-Demo/`
- **Locally:** download `index.html` and open it in any browser.

## What it shows

MosaicRx reasons backward from a patient's phenotype, medication timeline, comorbidities,
labs, and presenting complaint to identify the specific existing medication most likely
driving a new symptom (a prescribing cascade), rather than flagging generic pairwise
drug interactions.

- **Reverse-causal attribution** — names the likely culprit agent for this symptom in
  this patient, with a confidence level and the temporal link between medication start
  and symptom onset.
- **Comorbidity-adjusted anticholinergic burden** — adjusts the burden score for the
  patient's own physiology (CKD stage, dialysis, BMI, cardiac failure, diabetes), shown
  next to the conventional static score.
- **Glass Box reasoning** — every output shows its evidence, temporal reasoning, a
  literature basis, an uncertainty level, and an explicit "considered and ruled out"
  list naming the other candidates it evaluated and why.
- **Clinician-in-the-loop** — surfaces a risk signal and a clinical question, never an
  automated directive. The clinician always decides.

### Walkthrough

1. **Maria R.** (hero, positive cascade) — open her encounter, expand the Glass Box, take
   a clinician action, and watch the drafted note and audit log update.
2. **Robert T.** (negative case) — MosaicRx correctly stays quiet: no cascade, briefly
   showing what it checked. This demonstrates anti-alert-fatigue specificity.
3. **Eleanor K.** (hidden OTC) — surfaces a self-reported over-the-counter anticholinergic
   not in the formal medication list.
4. **Point-of-care modes** — the same intelligence surfaces appropriately in pre-visit
   chart prep, at the moment of e-prescribing, and on opening the chart with the patient
   present.
5. **Investor Value View** — KPI stack and a before/after outcome trajectory. All numbers
   are clearly labeled illustrative estimates.

## Run the source locally

The React + Vite + Tailwind source lives in [`app/`](app/).

```bash
cd app
npm install
npm run dev      # http://localhost:3000
npm run build    # production build
```

## Enabling the live page (GitHub Pages)

Settings → Pages → Source: **Deploy from a branch** → Branch: **main**, folder: **/ (root)** → Save.
The page will be live at `https://medtech101.github.io/MosaicRx-Demo/` within a minute.
