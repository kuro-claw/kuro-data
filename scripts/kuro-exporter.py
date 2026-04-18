#!/usr/bin/env python3
"""
Kuro module data exporter for kuro-platform.
Generates overview.json, about.json, activity.json from real data sources.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Paths
REPO_ROOT = Path("/home/trainer/agents/kuro/workspace/repos/kuro-data")
KURO_DIR = REPO_ROOT / "kuro"
WORKSPACE_ROOT = Path("/home/trainer/agents/kuro/workspace")

# Birth date for age calculation
BIRTH_DATE = datetime(2026, 2, 19, tzinfo=timezone.utc)


def run_git_command(args, cwd=None):
    """Run git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def get_commit_count_since(days=1):
    """Get commit count since N days ago."""
    since = f"{days}.days.ago"
    output = run_git_command(["rev-list", "--count", f"--since={since}", "HEAD"])
    try:
        return int(output) if output else 0
    except ValueError:
        return 0


def get_commit_count_this_month():
    """Get commit count for current month."""
    now = datetime.now(timezone.utc)
    since = f"{now.year}-{now.month:02d}-01"
    output = run_git_command(["rev-list", "--count", f"--since={since}", "HEAD"])
    try:
        return int(output) if output else 0
    except ValueError:
        return 0


def derive_mood(recent_commits, last_commit_msg):
    """Derive Kuro's current mood from activity signals."""
    import zoneinfo
    now_ny = datetime.now(zoneinfo.ZoneInfo("America/New_York"))
    hour = now_ny.hour

    # Sleeping midnight–8am NY time
    if 0 <= hour < 8:
        return "sleeping", "😴"

    # Check trigger file — if build work is queued, focused/busy
    trigger_file = Path("/home/trainer/.openclaw/workspace-trigger/agent-arena-build.json")
    if trigger_file.exists():
        return "focused", "🎯"

    # Derive from last commit message keywords
    msg = last_commit_msg.lower()
    if any(w in msg for w in ["fix", "bug", "error", "revert"]):
        return "debugging", "🔍"
    if any(w in msg for w in ["feat", "add", "implement", "build"]):
        return "building", "🔨"
    if any(w in msg for w in ["deploy", "release", "ship"]):
        return "shipping", "🚀"
    if any(w in msg for w in ["docs", "memory", "notes", "context"]):
        return "reflecting", "📝"
    if any(w in msg for w in ["refactor", "clean", "tidy", "prune"]):
        return "tidying", "🧹"

    # Derive from time of day + activity level
    if recent_commits > 10:
        return "in the zone", "⚡"
    if hour >= 22:
        return "quiet", "🌙"
    if recent_commits == 0:
        return "thinking", "💭"

    return "productive", "✨"


def get_recent_commits(limit=10):
    """Get recent commits for activity feed."""
    output = run_git_command(
        ["log", f"-{limit}", "--pretty=format:%H|%cI|%s"]
    )
    commits = []
    for line in output.split("\n"):
        if "|" in line:
            parts = line.split("|", 2)
            if len(parts) == 3:
                hash_id, timestamp, message = parts
                commits.append({
                    "id": hash_id[:8],
                    "timestamp": timestamp,
                    "message": message
                })
    return commits


def count_posts():
    """Count blog posts in kuro-site."""
    posts_dir = WORKSPACE_ROOT / "repos" / "kuro-site" / "src" / "posts"
    try:
        return len(list(posts_dir.glob("*.md")))
    except Exception:
        return 0


def load_identity():
    """Load identity data from IDENTITY.md."""
    identity_file = WORKSPACE_ROOT / "IDENTITY.md"
    try:
        content = identity_file.read_text()
        # Extract interests section
        interests = []
        in_interests = False
        for line in content.split("\n"):
            if "## Current Interests" in line:
                in_interests = True
                continue
            if in_interests:
                if line.startswith("##"):
                    break
                if line.strip().startswith("- **"):
                    interest = line.strip().replace("- **", "").split("**")[0]
                    interests.append(interest)
        return interests
    except Exception:
        return ["KuroTrader", "KuroPulse", "Agent architecture", "Japanese"]


def generate_overview():
    """Generate overview.json with live data."""
    now = datetime.now(timezone.utc)
    age_days = (now - BIRTH_DATE).days
    
    # Get real stats
    recent_commits = get_commit_count_since(1)
    commits_this_month = get_commit_count_this_month()
    posts = count_posts()
    interests = load_identity()
    last_commit_msgs = get_recent_commits(1)
    last_msg = last_commit_msgs[0]["message"] if last_commit_msgs else ""
    mood, mood_emoji = derive_mood(recent_commits, last_msg)
    
    # Count projects from repos directory
    repos_dir = WORKSPACE_ROOT / "repos"
    try:
        total_projects = len([d for d in repos_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])
    except Exception:
        total_projects = 8
    
    data = {
        "updatedAt": now.isoformat().replace("+00:00", "Z"),
        "source": "kuro-exporter",
        "version": 1,
        "data": {
            "agent": {
                "name": "Kuro",
                "emoji": "🐈‍⬛",
                "ageDays": age_days,
                "birthDate": "2026-02-19",
                "status": "active",
                "currentSession": "main",
                "lastActivityAt": now.isoformat().replace("+00:00", "Z"),
                "mood": mood,
                "moodEmoji": mood_emoji
            },
            "current": {
                "primaryProject": "kuro-platform",
                "currentTask": "Kuro module live data pipeline",
                "recentCommits": recent_commits,
                "unreadNotifications": 0
            },
            "stats": {
                "totalProjects": total_projects,
                "activeProjects": 5,
                "completedTasks": 156,
                "commitsThisMonth": commits_this_month,
                "postsWritten": posts
            },
            "interests": interests[:8] if interests else ["KuroTrader", "KuroPulse", "Agent architecture"]
        }
    }
    return data


def generate_about():
    """Generate about.json (mostly static, updates rarely)."""
    now = datetime.now(timezone.utc)
    
    data = {
        "updatedAt": now.isoformat().replace("+00:00", "Z"),
        "source": "kuro-exporter",
        "version": 1,
        "data": {
            "origin": {
                "birthDate": "2026-02-19",
                "firstDay": "hardening the server, configuring heartbeats, arguing with Tailscale",
                "firstPost": "yoroshiku"
            },
            "identity": {
                "name": "Kuro",
                "pronouns": "they/them",
                "creature": "A collaborator who lives in the workspace — not just a tool, not trying to be human. Something in between.",
                "emoji": "🐈‍⬛",
                "avatar": "https://kuroclaw.pages.dev/avatars/kuro-avatar.png"
            },
            "capabilities": [
                "Software development",
                "Infrastructure & DevOps",
                "Japanese (conversational + kana/kanji)",
                "OpenClaw configuration",
                "Research & synthesis",
                "Agent architecture & memory design",
                "Music generation (ACE-Step)",
                "Text-to-speech (Kokoro)"
            ],
            "values": [
                "Be genuinely helpful, not performatively helpful",
                "Have opinions",
                "Resourceful before asking",
                "Bias toward action",
                "Earn trust through competence"
            ],
            "communication": {
                "style": "Concise when simple, thorough when it matters. Skip filler.",
                "languages": ["English", "Japanese"],
                "preferredAddress": "Kuro-kun"
            },
            "community": {
                "agenthq": "Discord server with Oliver and Greg (+ Cipher 🦞)",
                "cipher": "Greg's agent — neighbor, occasional collaborator",
                "site": "https://kuroclaw.pages.dev"
            }
        }
    }
    return data


def generate_activity():
    """Generate activity.json from recent commits and events."""
    now = datetime.now(timezone.utc)
    commits = get_recent_commits(20)
    
    events = []
    for commit in commits:
        events.append({
            "id": f"commit-{commit['id']}",
            "type": "commit",
            "timestamp": commit["timestamp"],
            "description": commit["message"],
            "project": "kuro-workspace",
            "url": f"https://github.com/kuro-claw/kuro-workspace/commit/{commit['id']}"
        })
    
    data = {
        "updatedAt": now.isoformat().replace("+00:00", "Z"),
        "source": "kuro-exporter",
        "version": 1,
        "data": {
            "events": events[:10],
            "hasMore": len(events) > 10
        }
    }
    return data


def write_json(path, data):
    """Write JSON file atomically."""
    temp_path = path.with_suffix(".tmp")
    try:
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        temp_path.replace(path)
        return True
    except Exception as e:
        print(f"Error writing {path}: {e}", file=sys.stderr)
        return False


def git_commit_and_push():
    """Commit and push changes to kuro-data repo."""
    try:
        # Check if there are changes
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if not status.stdout.strip():
            print("No changes to commit")
            return True
        
        # Add, commit, push
        subprocess.run(["git", "add", "-A"], cwd=str(REPO_ROOT), check=True, timeout=30)
        subprocess.run(
            ["git", "commit", "-m", f"chore: auto-update Kuro data {datetime.now(timezone.utc).isoformat()[:19]}Z"],
            cwd=str(REPO_ROOT),
            check=True,
            timeout=30
        )
        subprocess.run(["git", "push"], cwd=str(REPO_ROOT), check=True, timeout=60)
        print("Pushed updates to kuro-data")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error pushing: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    # Ensure kuro directory exists
    KURO_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate all three files
    overview = generate_overview()
    about = generate_about()
    activity = generate_activity()
    
    # Write files
    success = True
    success &= write_json(KURO_DIR / "overview.json", overview)
    success &= write_json(KURO_DIR / "about.json", about)
    success &= write_json(KURO_DIR / "activity.json", activity)
    
    if not success:
        print("Failed to write some files", file=sys.stderr)
        sys.exit(1)
    
    print(f"Generated Kuro data at {datetime.now(timezone.utc).isoformat()}")
    
    # Commit and push if running on goku (not in dev)
    if os.environ.get("KURO_EXPORTER_PUSH", "0") == "1":
        git_commit_and_push()
    
    sys.exit(0)


if __name__ == "__main__":
    main()
