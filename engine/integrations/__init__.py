"""External service clients for the AI CMO engine.

Every client in here is credential-gated: it reads credentials from the
environment and makes a live call ONLY when those credentials are present. With
no credentials set, the clients raise a clear "not configured" error so callers
fall back to the offline stub. Nothing here runs a network call by default.
"""
