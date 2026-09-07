"""
Seed Demo Data CLI for RakshakGIS.
Initializes the database with deterministic Himalayan pilot scenario and engine-derived results.
Permitted only in APP_ENV=development and DATA_MODE=demo.
"""

import os
import sys

# Ensure backend directory is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set environment variables for demo mode if not already set
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATA_MODE", "demo")

def main():
    print("=== RakshakGIS Demo Seeder ===")
    try:
        from app.core.config import get_settings
        from app.core.database import SessionLocal
        from app.data.seed import seed_himalayan_pilot_data

        settings = get_settings()
        print(f"Active Environment: {settings.APP_ENV} | Active Mode: {settings.DATA_MODE}")

        db = SessionLocal()
        try:
            results = seed_himalayan_pilot_data(db, force=("--force" in sys.argv))
            print(f"[SUCCESS] Seeding completed: {results}")
        finally:
            db.close()

    except Exception as e:
        print(f"[ERROR] Seeding failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
