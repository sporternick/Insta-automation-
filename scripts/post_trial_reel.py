#!/usr/bin/env python3
"""Publish an Instagram trial reel through the official Instagram API (Instagram Login).

Trial reels are shown to non-followers first. Graduation (sharing to followers)
is set at publish time with --graduation (graduation itself happens in the app):
  MANUAL          you share it to followers yourself in the Instagram app
  SS_PERFORMANCE  Instagram shares it automatically if it performs well

Flow: create a REELS container with trial_params -> wait until the video is
processed -> publish. Without --publish it only prints what it would do.

Auth: an access token sent as "Authorization: Bearer <token>". In Claude cloud
sessions the network proxy injects the saved credential, so the token never
appears in this repo or in chat. Locally, set IG_ACCESS_TOKEN.

Usage:
  python3 scripts/post_trial_reel.py --video-url https://.../clip.mp4 \
      --caption-file caption.txt [--graduation MANUAL] [--publish]
  python3 scripts/post_trial_reel.py --whoami
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

VERSION = "v27.0"
# Instagram Login tokens (IG...) use graph.instagram.com; Facebook Login
# tokens (EAA...) use graph.facebook.com and reach the Instagram account
# through the Facebook Page it is linked to. Set with --api.
API = f"https://graph.instagram.com/{VERSION}"
# Placeholder when no token is set locally; the cloud proxy replaces it.
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "proxy-injected")


def call(method, path, params=None):
    url = f"{API}/{path}"
    data = None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if params and method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    elif params:
        data = json.dumps(params).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        sys.exit(f"API error {e.code} on {method} {path}: {body}")


def whoami(api):
    global API
    if api == "instagram":
        API = f"https://graph.instagram.com/{VERSION}"
        return call("GET", "me", {"fields": "user_id,username,account_type"})
    API = f"https://graph.facebook.com/{VERSION}"
    pages = call("GET", "me/accounts",
                 {"fields": "name,instagram_business_account{id,username}"}).get("data", [])
    linked = [p for p in pages if p.get("instagram_business_account")]
    if not linked:
        sys.exit("No Facebook Page with a linked Instagram account is visible to this token. "
                 f"Pages seen: {[p.get('name') for p in pages] or 'none'}. Link your Instagram "
                 "account to a Page and grant pages_show_list + instagram_content_publish.")
    ig = linked[0]["instagram_business_account"]
    return {"user_id": ig["id"], "username": ig.get("username"),
            "account_type": f"via Page '{linked[0].get('name')}'"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--whoami", action="store_true", help="check the token and print the account")
    ap.add_argument("--api", choices=["facebook", "instagram"], default="facebook",
                    help="facebook for EAA... tokens (default), instagram for IG... tokens")
    ap.add_argument("--video-url", help="public HTTPS URL of the .mp4 (Instagram fetches it)")
    ap.add_argument("--caption", default="")
    ap.add_argument("--caption-file")
    ap.add_argument("--cover-url", help="optional public URL of a cover image")
    ap.add_argument("--graduation", choices=["MANUAL", "SS_PERFORMANCE"], default="MANUAL")
    ap.add_argument("--ai-generated", action="store_true", help="add Instagram's AI-content disclosure")
    ap.add_argument("--publish", action="store_true", help="actually publish (default: dry run)")
    args = ap.parse_args()

    me = whoami(args.api)
    if args.whoami:
        print(json.dumps(me, indent=2))
        return
    if not args.video_url:
        ap.error("--video-url is required")

    caption = args.caption
    if args.caption_file:
        caption = open(args.caption_file, encoding="utf-8").read().strip()

    params = {
        "media_type": "REELS",
        "video_url": args.video_url,
        "caption": caption,
        "trial_params": {"graduation_strategy": args.graduation},
    }
    if args.ai_generated:
        params["is_ai_generated"] = True
    if args.cover_url:
        params["cover_url"] = args.cover_url

    print(f"account:    @{me.get('username')} ({me.get('account_type')})")
    print(f"video:      {args.video_url}")
    print(f"graduation: {args.graduation}")
    print(f"ai label:   {'yes' if args.ai_generated else 'no'}")
    limit = call("GET", f"{me['user_id']}/content_publishing_limit",
                 {"fields": "quota_usage,config"}).get("data", [{}])[0]
    print(f"quota:      {limit.get('quota_usage')} of "
          f"{limit.get('config', {}).get('quota_total', 100)} posts used in the last 24h")
    print(f"caption:\n{caption}\n")
    if not args.publish:
        print("DRY RUN - nothing posted. Re-run with --publish to post this trial reel.")
        return

    uid = me["user_id"]
    container = call("POST", f"{uid}/media", params)["id"]
    print(f"container {container} created, waiting for Instagram to process the video...")
    # Meta recommends checking once per minute for no more than 5 minutes.
    for _ in range(6):
        time.sleep(60)
        status = call("GET", container, {"fields": "status_code,status"})
        code = status.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            sys.exit(f"processing failed: {status}")
    else:
        sys.exit(f"still processing after 5 minutes. Container {container} stays "
                 "valid for 24h; publish later with POST media_publish creation_id.")

    media = call("POST", f"{uid}/media_publish", {"creation_id": container})
    link = call("GET", media["id"], {"fields": "permalink"}).get("permalink")
    print(f"PUBLISHED trial reel {media['id']} {link or ''}")


if __name__ == "__main__":
    main()
