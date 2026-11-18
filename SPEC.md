Prism by Kaleidoscope — V1 Spec & Build Plan

Nov 18, 2026 · @Carlton Matthews

Overview

Prism by Kaleidoscope turns a YouTube link or an uploaded video into a transcript, a summary and a goal-tailored action plan, all downloadable as Markdown. V1 is a personal web app on Azure behind your Microsoft sign-in. It's built so a saved library, a "retool for my business" feature and paying customers can be added later without a rebuild.

V1 goals

•	Paste a YouTube link and get a timestamped transcript, using free captions when they exist and Azure speech-to-text when they don't.
•	Upload a video or audio file (typical length 15–60 min) and get the same transcript.
•	Generate a Summary (short / standard / detailed) and an Action Plan tailored to a goal you type, laid out over 7 or 30 days.
•	Download the transcript and every output as Markdown.
•	Save every run as a job record behind the scenes, so V2 features build on data that already exists.

Not in V1: Instagram/TikTok links, a library screen, retooling scripts, Word/PDF export, other users, billing.

Decisions from the interview

Every V1 choice below came from the interview on Nov 18. Each row can be revisited.

Topic	V1 decision	Later
Audience	Personal use, designed to become a product	Sell to clients/customers
Form factor	Web app (phone + desktop browser)	Same app, more users
Stack	Azure	Same
Link sources	YouTube only	Instagram, TikTok, Facebook
Uploads	Video/audio files, mostly 15–60 min	Longer files
No captions on YouTube	Auto-transcribe the audio with Azure	Same
Outputs	Summary + Action Plan	Retool for my business, content repurposing
Summary style	TL;DR + key points and timestamped sections, length toggle	Same
Action Plan style	Tailored to a goal you type, time-boxed to 7 or 30 days	Same
Storage	One-off + download; each run saved quietly as a job record	Searchable library
Downloads	Markdown	Word (.docx), PDF
Sign-in	Microsoft sign-in, your account only	Customer accounts
Hosting	Visual Studio Azure credits	Pay-as-you-go or Kaleidoscope subscription
Budget	$10–30 per month	Covered by revenue

V1 features and user flows

V1 has one screen with two inputs and two actions; everything else is a download button.

Flow A — YouTube link

1.	Sign in with your Microsoft account.
2.	Paste a YouTube URL and press Transcribe. The app checks that the link is YouTube and reads the title and length.
3.	The backend fetches the video's captions. If captions exist, the transcript is ready in seconds.
4.	If there are no captions, or YouTube blocks the request, the backend pulls the audio and sends it to Azure speech-to-text. The screen shows progress.
5.	The transcript appears with timestamps; each timestamp links back to that moment on YouTube.

Flow B — Upload

1.	Choose or drag in a video or audio file (mp4, mov, m4a, mp3, wav).
2.	The browser uploads it straight to Azure Blob Storage, so large files don't pass through the web server.
3.	The backend extracts the audio, transcribes it and shows the timestamped transcript.

Actions on a transcript

•	Summary: pick Short, Standard or Detailed. Every length gives a TL;DR and key points; Standard and Detailed add timestamped sections.
•	Action Plan: type your goal (for example, "get my first 5 coaching clients") and pick 7 or 30 days. The plan adapts the video's advice to that goal, day by day or week by week, and notes which part of the video each step came from.
•	Download: transcript, summary and plan as separate .md files, or one combined .md.

Behind the scenes: every run writes a job record (see Data model), even though V1 has no screen to browse them.

Architecture on Azure

Everything runs through one Job API, so new sources (social links) and new outputs (Retool) plug into the same pipeline.

[embedded content: V1 architecture on Azure · 6 components]

The browser uploads files straight to Blob Storage and only asks the Job API to start and track jobs. The API fetches YouTube captions or audio, sends audio to Speech, sends transcripts to Azure OpenAI, and writes each job record back to Blob.

•	Libraries: youtube-transcript-api for captions, yt-dlp for audio fallback, ffmpeg to extract audio from uploads.
•	Secrets: Key Vault, with the Functions app reaching Speech and OpenAI through managed identity where possible.
•	Provider swap: transcription and generation each sit behind one interface, so moving to MAI-Transcribe-2 or another model is a config change.

Data model

One JSON job record per run, stored at jobs/{ownerId}/{jobId}.json in Blob Storage. Its fields already cover the library, multiple users and the retool feature, so V2 adds screens, not migrations.

{
  "jobId": "01JD...",
  "ownerId": "carlton",
  "createdAt": "2026-11-18T15:30:00Z",
  "status": "done",
  "source": {
    "type": "youtube",
    "url": "https://youtube.com/watch?v=...",
    "title": "...",
    "durationSec": 2700
  },
  "transcript": {
    "method": "captions",
    "language": "en",
    "segments": [{ "start": 0.0, "end": 6.2, "text": "..." }]
  },
  "outputs": [
    {
      "type": "summary",
      "options": { "length": "standard" },
      "promptVersion": "summary-v1",
      "model": "...",
      "markdown": "...",
      "createdAt": "..."
    },
    {
      "type": "actionPlan",
      "options": { "goal": "...", "days": 30 },
      "promptVersion": "plan-v1",
      "markdown": "..."
    }
  ],
  "tags": [],
  "usage": { "audioMinutes": 0, "inputTokens": 0, "outputTokens": 0 }
}

Why these fields matter later:

•	ownerId on every record means customer accounts only change who signs in.
•	outputs is a list with a type, so "retool" and "repurpose" are new types, not new tables.
•	promptVersion lets you improve prompts and still know which version made an old output.
•	tags is empty in V1 and ready for library folders.
•	usage tracks cost per job, which you'll need to price a paid plan.
•	Uploaded media is deleted after 7 days by a Blob lifecycle rule; job records stay.

Costs

Expected spend is about $3–8 per month, well under the $10–30 budget and covered by the Visual Studio credit. The estimate assumes 20 videos a month at about 45 minutes each (15 audio hours), with every video needing paid transcription. In practice, YouTube videos with captions cost nothing to transcribe.

Item	Unit price	Monthly estimate (15 hrs)
Azure Speech batch transcription	$0.18 / audio hour (source)	$2.70
Azure Speech fast transcription (quicker results)	$0.36 / audio hour (source)	$5.40
MAI-Transcribe-2 (promo price ends Dec 31, 2026)	$0.10 / audio hour (source)	$1.50
gpt-4o-mini-transcribe (Azure OpenAI)	$0.003 / minute (source)	$2.70
Summary + Action Plan (small GPT model)	approximate	under $1
Static Web Apps, Functions, Blob Storage	free tiers + cents	under $1

Recommendation: use Azure Speech fast transcription by default. A 45-minute video costs about $0.27, and results come back in one request with no batch polling. Switch to batch if spend creeps up.

Visual Studio credit: Visual Studio Enterprise includes $150 a month in Azure credit (source). It covers V1 many times over. The credit doesn't cover Marketplace products, so stay with first-party Azure services.

Risks and constraints

The biggest risk is YouTube blocking requests from Azure servers. The upload path is the built-in fallback, so V1 still works when that happens.

Risk	What happens	Mitigation
YouTube blocks cloud servers	Caption or audio requests from Azure fail intermittently	Retry once, then offer "Upload instead" with one tap. Log the block rate; if it's high, evaluate a transcript API in V1.5.
YouTube terms of service	Downloading audio is restricted; fine for personal research, riskier in a paid product	Personal use in V1. Before selling, get a legal review and consider a captions-only or "upload your own content" model for customers.
Visual Studio credit is dev/test only	No SLA, personal use only, and services stop when the month's credit runs out	Fine for V1. Move to pay-as-you-go or a Kaleidoscope subscription before anyone else uses the tool. If the subscription comes through your employer, check its policy on outside projects.
Long processing times	A 60-min file can take longer than a basic serverless function allows	Run jobs with Durable Functions (or the Flex Consumption plan) and show progress in the UI.
AI invents steps	The Action Plan adds advice that isn't in the video	Each step must cite a timestamp; the prompt forbids uncited claims; outputs are versioned so prompts can be tuned.
Promo pricing ends	MAI-Transcribe-2's $0.10/hr rate ends Dec 31, 2026	Keep the transcription provider behind one interface so it's a config switch.
Account mix-up	Work and personal identities get mixed	Sign in with a personal Microsoft account and keep this subscription separate from any work tenant.

Build plan

Build the upload path first: it exercises the whole pipeline without depending on YouTube, so the YouTube work becomes "just another source." Each milestone ends with something you can use.

M0 — Foundation

☐	Activate the Visual Studio Azure credit; create one resource group for the tool
☐	Create the GitHub repo (React + TypeScript frontend, Python Azure Functions backend)
☐	Deploy an empty Static Web App with sign-in limited to your Microsoft account
☐	Create the Storage account (uploads, audio and jobs containers) and Key Vault

M1 — Upload → transcript

☐	Browser uploads straight to Blob using a short-lived SAS link
☐	Function extracts audio with ffmpeg and sends it to Azure Speech fast transcription
☐	Save timestamped segments to the job record; show the transcript on screen

M2 — YouTube → transcript

☐	Validate the URL; read title and duration
☐	Fetch captions; on failure, pull audio and reuse the M1 pipeline
☐	Clickable timestamps that open YouTube at that second
☐	"Upload instead" fallback when YouTube blocks the request

M3 — Summary

☐	Deploy a small GPT model in Azure OpenAI
☐	Prompt summary-v1 with Short / Standard / Detailed
☐	Long transcripts split into chunks, summarized, then merged

M4 — Action Plan

☐	Goal box + 7 / 30-day toggle
☐	Prompt plan-v1; every step cites a timestamp

M5 — Download and polish

☐	Download each output as .md, or all of them as one combined .md
☐	"Send to Notion" for Action Plans (Notion internal integration token in Key Vault)
☐	Progress states, friendly errors, phone layout
☐	Usage logging per job; Blob rule that deletes media after 7 days

M6 — Real-world test

☐	Run 10 real videos (YouTube with captions, YouTube without, uploads)
☐	Check the month's cost against the estimate; tune prompts

V1 is done when: a 45-minute YouTube video or upload produces a transcript, summary and action plan you'd actually use, all downloadable, from your phone.

Roadmap

Each phase reuses the V1 job records, so later phases add screens and prompts rather than rework.

[embedded content: product roadmap · 4 phases, 1 gate]

V1.5 starts once V1 is in daily use. V3 starts only after the gate: a legal review of YouTube downloading and a move off the Visual Studio credit.

Open questions: round 2 answers

Round 2 on Nov 18 settled five of the seven questions. The name is Prism by Kaleidoscope; its domain and first price are still open.

Question	Decision	Lands in
Retool business profiles	Kaleidoscope coaching, hypnosis programs, podcast/content brand	V2
Speaker labels	Optional toggle per video	V1 (M1)
Sensitive uploads	Public content only; 7-day media deletion stays	V1
Languages	Any language, auto-detected	V1 (M1)
Output language	Pick per video, defaults to English	V1 (M3–M4)
Action Plan destination	Choose Markdown download or Send to Notion	V1 (M5)
First customers	Coaches, course creators, podcasters/YouTubers	V3

Still open

☐	Domain and trademark: check that a domain and the name "Prism by Kaleidoscope" are free to use; "Prism" on its own is a common product name.
☐	First price: what would coaches, course creators and podcasters pay per month? Decide before V3.