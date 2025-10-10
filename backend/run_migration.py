#!/usr/bin/env python3
"""
Database migration script to fix file unique constraint.
Allows reusing deleted file names within the same project.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings


async def run_migration():
    """Run the database migration."""
    settings = get_settings()

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
    )

    # Read migration SQL
    migration_file = Path(__file__).parent / "migrations" / "001_fix_file_unique_constraint.sql"
    with open(migration_file, 'r') as f:
        sql = f.read()

    print("🔧 Running database migration: Fix file unique constraint")
    print("=" * 60)

    async with engine.begin() as conn:
        # Execute migration
        try:
            # Split by semicolons and execute each statement
            statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

            for statement in statements:
                if statement:
                    print(f"\n📝 Executing:\n{statement}\n")
                    await conn.execute(text(statement))

            print("\n✅ Migration completed successfully!")
            print("\nChanges:")
            print("  - Dropped old constraint: uq_project_file_name")
            print("  - Created partial unique index: uq_project_file_name_active")
            print("  - Now allows reusing file names after deletion within same project")

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())
