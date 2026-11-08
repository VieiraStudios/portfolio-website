import os

# Use a throwaway in-memory database for tests. This must be set before the
# app is imported, because the app reads DATABASE_URL when it starts.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.pop("POSTGRES_URL", None)
os.environ.pop("VERCEL", None)
