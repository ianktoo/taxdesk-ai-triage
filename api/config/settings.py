"""Environment config and active-adapter selection.

Nothing outside this module should read os.environ directly for
capability selection. Services and routes ask this module which
adapter is active, never a vendor SDK.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")
SAMPLE_DOCS_DIR = REPO_ROOT / "data" / "sample_docs"

# Which document-extraction adapter is active. "mock" needs no API key
# and is the default so the app runs end-to-end with no setup; set
# DOCUMENT_EXTRACTOR=nutrient once a real DWS API key is configured.
DOCUMENT_EXTRACTOR = os.environ.get("DOCUMENT_EXTRACTOR", "mock")

NUTRIENT_DWS_API_KEY = os.environ.get("NUTRIENT_DWS_API_KEY", "")
NUTRIENT_DWS_BASE_URL = os.environ.get(
    "NUTRIENT_DWS_BASE_URL", "https://api.nutrient.io"
)

# Confidence threshold: any extracted field below this routes the
# request to "Needs human review" instead of "Ready to auto-approve".
# Kept as a single tunable knob since it's central to the demo story.
AUTO_APPROVE_CONFIDENCE_THRESHOLD = float(
    os.environ.get("AUTO_APPROVE_CONFIDENCE_THRESHOLD", "0.85")
)

# Demo throttling: per-client-IP request cap, no login required.
# Falls back to a no-op limiter (unlimited) when Upstash creds are unset,
# so local dev needs no extra setup.
#
# One shared counter covers every metered route: triage, approve, speech,
# persona generation and upload. Reviewing a single request costs three
# (send, listen, decide), so the budget is sized in walkthroughs, not
# clicks: 30 per 5 minutes is roughly ten full reviews back to back,
# which no human demoing this will reach and a script will.
UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "")
UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "30"))
# Kept short on purpose: the window is also the worst-case lockout, and a
# demo recovering in five minutes beats one that allows a bigger burst
# and then locks someone out for ten.
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "300"))

# User-uploaded documents ("try your own document" proof-of-concept flow).
# Files are processed in memory for a single request and never persisted.
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
ALLOWED_UPLOAD_CONTENT_TYPES = {"application/pdf", "image/png", "image/jpeg"}

# AI-generated personas + voice narration. Falls back to mock adapters
# (canned persona text, a placeholder tone instead of real speech) when
# unset, so local dev needs no extra setup.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_TEXT_MODEL = os.environ.get("OPENAI_TEXT_MODEL", "gpt-4o-mini")
OPENAI_TTS_MODEL = os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
OPENAI_TTS_VOICE = os.environ.get("OPENAI_TTS_VOICE", "alloy")

# The agent pipeline. Every agent reasons through the Reasoning
# capability, so this one switch decides whether triage runs on a model
# or on the deterministic rules. Set AGENT_REASONER=mock to force the
# rules even when an OpenAI key is present, which is what the test
# suite and offline demos do.
AGENT_REASONER = os.environ.get("AGENT_REASONER", "openai")
OPENAI_REASONING_MODEL = os.environ.get("OPENAI_REASONING_MODEL", "gpt-4o-mini")

# Per-agent ceiling. Five agents run in sequence inside one serverless
# invocation, so this has to stay well under the platform's function
# timeout with room for the document extraction calls that precede them.
REASONING_TIMEOUT_SECONDS = float(os.environ.get("REASONING_TIMEOUT_SECONDS", "20"))
