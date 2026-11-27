import os

# Provide a safe in-memory fallback for test collection and unit tests
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
