# GitHub Publish Guide

Use this only after the code and documentation are final.

## Before pushing

- verify no secrets are stored in tracked files
- confirm `.env` is ignored
- confirm sample payloads do not contain live credentials
- review diffs for accidental token exposure

## Recommended auth flow

Prefer one of these:

1. `gh auth login`
2. set a PAT in a temporary local environment variable
3. use Git Credential Manager

Avoid:

- hardcoding PATs into scripts
- embedding PATs into remote URLs in committed files
- placing tokens in docs or examples

## Suggested sequence

```bash
git status
git add .
git commit -m "Add IR, metals monitoring, and Veris-ready simulation stack"
```

Then authenticate and push:

```bash
gh auth login
git push origin <branch-name>
```

## Security note

If a PAT has been pasted into any chat, notes file, screenshot, or shell history that you do not fully control, rotate it after use.

