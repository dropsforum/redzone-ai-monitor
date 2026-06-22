# Security And Publication Hygiene

Do not commit:

- `.env` files or deployment secrets
- Apple IDs, team credentials, app-specific passwords, notarization profiles, signing certificates, or private keys
- Local videos, screenshots, recordings, customer data, or incident footage
- Private notes, internal handoff notes, or personal machine paths
- Generated `.dmg`, `.app`, `build`, `dist`, `.next`, `.venv-mac`, `.pt`, or `.onnx` files

Before publishing a public branch, run a tracked-file scan for tokens, private keys, local paths, and model binaries. Publish only the intended cleaned branch; do not use `git push --all` from a clone that also has private or historical refs.
