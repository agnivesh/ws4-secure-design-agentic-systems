#!/usr/bin/env python3
"""
Fetch CoSAI meeting minutes from Google Drive and GitHub, save as markdown.

Drive sources: Reads Gemini-generated meeting notes from shared Drive
folders, exports them as markdown. Uses OAuth credentials from
~/.config/mcp-gdrive/ (shared with the mcp-gdrive MCP server). Currently
covers WS4, the ADLC SIG (under WS4), WS3, the Code-Development SIG (under
WS3), and the Risk Management SIG (under WS3).

GitHub sources (TSC): Reads markdown meeting minutes committed to a public
GitHub repo directory. Uses the unauthenticated GitHub Contents API; honors
GITHUB_TOKEN env var if set to raise the rate limit.

Output goes under meeting_minutes/<subdir>/ in the WS4 repo.

Usage:
    # Fetch all meeting minutes
    python scripts/fetch_meeting_minutes.py

    # Fetch only new minutes (skip existing files)
    python scripts/fetch_meeting_minutes.py --skip-existing
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Meeting sources. Each source has:
#   type:    "drive" or "github"
#   subdir:  output subdirectory under meeting_minutes/
#   For drive sources: folder_id (parent containing per-meeting subfolders)
#   For github sources: repo (owner/name), path (directory in the repo)
SOURCES = [
    {
        "name": "WS4",
        "type": "drive",
        "folder_id": "1TJl4yqWIdfPc8fKWiTO0CsmsmuecGxWa",
        "subdir": "ws4",
        # Fallback when a per-meeting subfolder hasn't been filed yet:
        # match Gemini notes shared directly with the user.
        "shared_name_contains": "CoSAI WS4 recurring meeting",
        "shared_title_pattern": (
            r"^CoSAI WS4 recurring meeting - "
            r"(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2}) .* Notes by Gemini$"
        ),
        "shared_folder_name_template": "WS4 {y}{m}{d}",
    },
    {
        "name": "ADLC",
        "type": "drive",
        "folder_id": "1EkoOpMCtYahLu-sEhYrgNDmvPyTtgpit",
        "subdir": "adlc",
        "shared_name_contains": "WS4 SIG Security of Agent Development Lifecycle",
        "shared_title_pattern": (
            r"^WS4 SIG Security of Agent Development Lifecycle - "
            r"(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2}) .* Notes by Gemini$"
        ),
        "shared_folder_name_template": "{y}-{m}-{d}",
    },
    {
        "name": "WS3",
        "type": "drive",
        "folder_id": "1NFk_-2Plyi3qYr2qtrvt42AQhzJZB0Wf",
        "subdir": "ws3",
        # No shared-with-me fallback: the docs in WS3 per-meeting folders
        # aren't Gemini-tagged with a stable "Notes by Gemini" title, so
        # we can't reliably pattern-match unfiled shares. The folder-walk
        # pass picks them up via the find_notes_doc fallback.
    },
    {
        "name": "Code-SIG",
        "type": "drive",
        "folder_id": "1yKk-Mbbpowsk3gfRwGIT7UpMOJ-fDzdo",
        "subdir": "code-sig",
        "shared_name_contains": "CoSAI WS3 SIG: Security of AI-Assisted Code Development",
        "shared_title_pattern": (
            r"^CoSAI WS3 SIG: Security of AI-Assisted Code Development - "
            r"(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2}) .* Notes by Gemini$"
        ),
        "shared_folder_name_template": "{y}-{m}-{d}",
    },
    {
        "name": "RM-SIG",
        "type": "drive",
        "folder_id": "1tboOFAyYHnJRlXqMO3Kdh6KrcAVVIpiB",
        "subdir": "rm-sig",
        "shared_name_contains": "CoSAI WS3 CoSAI-RM SIG weekly meeting",
        "shared_title_pattern": (
            r"^CoSAI WS3 CoSAI-RM SIG weekly meeting - "
            r"(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2}) .* Notes by Gemini$"
        ),
        "shared_folder_name_template": "WS3 CoSAI-RM SIG {y}{m}{d}",
    },
    {
        "name": "Agent-Credentials",
        "type": "drive",
        "folder_id": "1Telz7CDwCgPNUyHlMwu9cBGl-keqP9z3",
        "subdir": "agent-credentials",
        "shared_name_contains": "CoSAI WS4: Agent Credentials",
        "shared_title_pattern": (
            r"^CoSAI WS4: Agent Credentials - "
            r"(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2}) .* Notes by Gemini$"
        ),
        "shared_folder_name_template": "{y}-{m}-{d}",
    },
    {
        "name": "TSC",
        "type": "github",
        "repo": "cosai-oasis/cosai-tsc",
        "path": "tsc-meeting-minutes",
        "subdir": "tsc",
    },
]

# Credentials path (shared with mcp-gdrive)
CREDS_DIR = Path.home() / ".config" / "mcp-gdrive"
CREDS_FILE = CREDS_DIR / ".gdrive-server-credentials.json"
OAUTH_KEYS_FILE = CREDS_DIR / "gcp-oauth.keys.json"

# Output directory
REPO_ROOT = Path.home() / "Github" / "ws4-secure-design-agentic-systems"
OUTPUT_DIR = REPO_ROOT / "meeting_minutes"


def load_credentials():
    """Load and refresh OAuth credentials."""
    if not CREDS_FILE.exists():
        print(f"Error: No credentials file at {CREDS_FILE}", file=sys.stderr)
        print("Run the mcp-gdrive auth flow first.", file=sys.stderr)
        sys.exit(1)

    with open(CREDS_FILE) as f:
        creds_data = json.load(f)

    with open(OAUTH_KEYS_FILE) as f:
        oauth_keys = json.load(f)
        installed = oauth_keys["installed"]

    creds = Credentials(
        token=creds_data.get("access_token"),
        refresh_token=creds_data.get("refresh_token"),
        token_uri=installed["token_uri"],
        client_id=installed["client_id"],
        client_secret=installed["client_secret"],
        scopes=creds_data.get("scope", "").split(),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save refreshed credentials
        new_creds = {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "scope": " ".join(creds.scopes or []),
            "token_type": "Bearer",
            "expiry_date": int(creds.expiry.timestamp() * 1000) if creds.expiry else None,
        }
        with open(CREDS_FILE, "w") as f:
            json.dump(new_creds, f, indent=2)

    return creds


def list_meeting_folders(drive_service, parent_folder_id):
    """List all meeting subfolders in a parent Drive folder."""
    folders = []
    page_token = None

    while True:
        response = drive_service.files().list(
            q=f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="nextPageToken, files(id, name)",
            pageSize=100,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

        folders.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return sorted(folders, key=lambda f: f["name"])


def find_notes_doc(drive_service, folder_id):
    """Find the Gemini notes document in a meeting folder.

    Returns a dict with id, name, and mimeType. If the match is a shortcut
    pointing to a Google Doc, the returned id is the shortcut's target id so
    the caller can export it directly.
    """
    response = drive_service.files().list(
        q=(
            f"'{folder_id}' in parents and trashed=false and "
            "(mimeType='application/vnd.google-apps.document' "
            "or mimeType='application/vnd.google-apps.shortcut')"
        ),
        fields="files(id, name, mimeType, shortcutDetails)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    files = response.get("files", [])

    def resolve(f):
        if f["mimeType"] == "application/vnd.google-apps.shortcut":
            sd = f.get("shortcutDetails") or {}
            if sd.get("targetMimeType") != "application/vnd.google-apps.document":
                return None
            return {"id": sd["targetId"], "name": f["name"], "mimeType": sd["targetMimeType"]}
        return f

    # Prefer "Notes by Gemini" matches, fall back to any resolvable doc
    for f in files:
        if "Notes by Gemini" in f["name"]:
            resolved = resolve(f)
            if resolved:
                return resolved
    for f in files:
        resolved = resolve(f)
        if resolved:
            return resolved
    return None


def export_doc_as_markdown(drive_service, file_id):
    """Export a Google Doc as markdown text."""
    content = drive_service.files().export(
        fileId=file_id,
        mimeType="text/plain",
    ).execute()

    if isinstance(content, bytes):
        return content.decode("utf-8")
    return content


def folder_name_to_filename(folder_name):
    """Convert folder name like 'WS4 20260402' to 'WS4-20260402.md'."""
    # Normalize whitespace and replace spaces with hyphens
    name = re.sub(r"\s+", "-", folder_name.strip())
    return f"{name}.md"


def fetch_drive_source(source, output_dir, drive_service, skip_existing):
    """Fetch all Gemini meeting notes from a Drive source.

    Returns (fetched, skipped, no_notes, errors).
    """
    fetched = skipped = no_notes = errors = 0

    print(f"\n[{source['name']}] Listing meeting folders...")
    folders = list_meeting_folders(drive_service, source["folder_id"])
    print(f"[{source['name']}] Found {len(folders)} meeting folders")

    for folder in folders:
        filename = folder_name_to_filename(folder["name"])
        output_path = output_dir / filename

        if skip_existing and output_path.exists():
            skipped += 1
            continue

        notes_doc = find_notes_doc(drive_service, folder["id"])
        if not notes_doc:
            print(f"  {folder['name']}: no notes document found")
            no_notes += 1
            continue

        print(f"  {folder['name']}: fetching '{notes_doc['name']}'...")
        try:
            content = export_doc_as_markdown(drive_service, notes_doc["id"])
        except HttpError as e:
            # Listing surfaces shortcuts whose target doc may be in a
            # restricted Drive the user can't export from. Don't let one
            # bad doc kill the whole run.
            print(
                f"  {folder['name']}: export failed ({e.resp.status} "
                f"{e.resp.reason}); skipping",
                file=sys.stderr,
            )
            errors += 1
            continue

        header = f"# {folder['name']}\n\n"
        header += f"**Source:** {notes_doc['name']}\n\n---\n\n"

        with open(output_path, "w") as f:
            f.write(header + content)

        fetched += 1

    return fetched, skipped, no_notes, errors


def fetch_drive_shared_fallback(source, output_dir, drive_service, skip_existing):
    """Catch Gemini notes that are shared with the user but not yet filed
    into a per-meeting subfolder. Matches by title pattern; writes to the
    same canonical filename the folder pass would produce.

    Returns (fetched, skipped, errors).
    """
    name_contains = source.get("shared_name_contains")
    pattern = source.get("shared_title_pattern")
    template = source.get("shared_folder_name_template")
    if not (name_contains and pattern and template):
        return 0, 0, 0

    fetched = skipped = errors = 0
    pat = re.compile(pattern)

    safe_contains = name_contains.replace("'", "\\'")
    q = (
        "sharedWithMe = true and trashed = false and "
        "mimeType = 'application/vnd.google-apps.document' and "
        f"name contains '{safe_contains}'"
    )

    print(f"\n[{source['name']}] Scanning shared-with-me for unfiled Gemini notes...")
    candidates = []
    page_token = None
    while True:
        resp = drive_service.files().list(
            q=q,
            fields="nextPageToken, files(id, name, mimeType)",
            pageSize=100,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        candidates.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    for f in candidates:
        m = pat.match(f["name"])
        if not m:
            continue
        synthetic = template.format(**m.groupdict())
        output_path = output_dir / folder_name_to_filename(synthetic)

        if skip_existing and output_path.exists():
            skipped += 1
            continue

        print(f"  [shared] {synthetic}: fetching '{f['name']}'...")
        try:
            content = export_doc_as_markdown(drive_service, f["id"])
        except HttpError as e:
            print(
                f"  [shared] {synthetic}: export failed ({e.resp.status} "
                f"{e.resp.reason}); skipping",
                file=sys.stderr,
            )
            errors += 1
            continue
        header = (
            f"# {synthetic}\n\n"
            f"**Source:** {f['name']} (via shared-with-me fallback)\n\n---\n\n"
        )
        with open(output_path, "w") as out:
            out.write(header + content)
        fetched += 1

    return fetched, skipped, errors


def _github_request(url):
    """Open a GitHub API/raw URL with optional bearer auth from GITHUB_TOKEN."""
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "fetch_meeting_minutes",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    return urllib.request.urlopen(req, timeout=30)


def fetch_github_source(source, output_dir, skip_existing):
    """Fetch markdown meeting minutes from a GitHub repo directory.

    Lists files via the GitHub Contents API and downloads .md files via
    each file's download_url. Returns (fetched, skipped).
    """
    fetched = skipped = 0
    api_url = f"https://api.github.com/repos/{source['repo']}/contents/{source['path']}"

    print(f"\n[{source['name']}] Listing GitHub directory {source['repo']}/{source['path']}...")
    try:
        with _github_request(api_url) as resp:
            listing = json.load(resp)
    except urllib.error.HTTPError as e:
        print(f"[{source['name']}] GitHub API error: {e.code} {e.reason}", file=sys.stderr)
        return fetched, skipped

    md_files = [f for f in listing if f.get("type") == "file" and f["name"].endswith(".md")]
    print(f"[{source['name']}] Found {len(md_files)} markdown files")

    for f in md_files:
        output_path = output_dir / f["name"]
        if skip_existing and output_path.exists():
            skipped += 1
            continue

        print(f"  {f['name']}: fetching...")
        with _github_request(f["download_url"]) as resp:
            content = resp.read().decode("utf-8")
        output_path.write_text(content, encoding="utf-8")
        fetched += 1

    return fetched, skipped


def main():
    parser = argparse.ArgumentParser(description="Fetch CoSAI meeting minutes from Drive and GitHub")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip meetings that already have a local file")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    drive_service = None
    if any(s["type"] == "drive" for s in SOURCES):
        print("Loading credentials...")
        creds = load_credentials()
        drive_service = build("drive", "v3", credentials=creds)

    total_fetched = 0
    total_skipped = 0
    total_no_notes = 0
    total_errors = 0

    for source in SOURCES:
        output_dir = OUTPUT_DIR / source["subdir"] if source["subdir"] else OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        if source["type"] == "drive":
            fetched, skipped, no_notes, errors = fetch_drive_source(
                source, output_dir, drive_service, args.skip_existing
            )
            total_no_notes += no_notes
            total_errors += errors
            f2, s2, e2 = fetch_drive_shared_fallback(
                source, output_dir, drive_service, args.skip_existing
            )
            fetched += f2
            skipped += s2
            total_errors += e2
        elif source["type"] == "github":
            fetched, skipped = fetch_github_source(source, output_dir, args.skip_existing)
        else:
            print(f"[{source['name']}] Unknown source type: {source['type']}", file=sys.stderr)
            continue

        total_fetched += fetched
        total_skipped += skipped

    print(
        f"\nDone: {total_fetched} fetched, {total_skipped} skipped, "
        f"{total_no_notes} without notes, {total_errors} export errors"
    )


if __name__ == "__main__":
    main()
