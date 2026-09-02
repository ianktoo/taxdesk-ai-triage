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
UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "")
UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "5"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "3600"))

# User-uploaded documents ("try your own document" proof-of-concept flow).
# Files are processed in memory for a single request and never persisted.
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
ALLOWED_UPLOAD_CONTENT_TYPES = {"application/pdf", "image/png", "image/jpeg"}
