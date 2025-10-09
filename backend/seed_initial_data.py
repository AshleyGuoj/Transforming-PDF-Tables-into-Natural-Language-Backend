"""
Seed initial data into the database.
Run this script to populate the database with test data.
"""

import asyncio
import sys
from pathlib import Path

# Add GrandscaleDB to path
grandscale_db_path = Path(__file__).parent / "GrandscaleDB"
sys.path.insert(0, str(grandscale_db_path))

from app.db.session import get_async_session
from models import Organization, User, Project

async def seed_data():
    """Seed initial data for testing."""
    async with get_async_session() as session:
        print("🌱 Seeding initial data...")
        
        # Create organization
        org = Organization(
            name="Grand Scale AI",
            description="Main organization for Grand Scale projects",
            is_active=True
        )
        session.add(org)
        await session.flush()  # Get org_id
        print(f"✅ Created organization: {org.name} (ID: {org.org_id})")
        
        # Create users
        users = [
            User(
                email="admin@grandscale.ai",
                org_id=org.org_id,
                skill_level="expert",
                is_active=True
            ),
            User(
                email="pm@grandscale.ai",
                org_id=org.org_id,
                skill_level="senior",
                is_active=True
            ),
            User(
                email="annotator@grandscale.ai",
                org_id=org.org_id,
                skill_level="intermediate",
                language_expertise=["en", "zh"],
                is_active=True
            )
        ]
        
        for user in users:
            session.add(user)
        
        await session.flush()
        print(f"✅ Created {len(users)} users")
        
        # Create a sample project
        project = Project(
            org_id=org.org_id,
            name="PDF Table Annotation Project",
            description="Transform PDF tables into natural language",
            requirements_text="Extract and annotate tables from PDF documents",
            status="draft",
            client_pm_id=users[0].user_id,
            our_pm_id=users[1].user_id,
            is_active=True
        )
        session.add(project)
        await session.flush()
        print(f"✅ Created project: {project.name} (ID: {project.project_id})")
        
        await session.commit()
        print("\n🎉 Database seeded successfully!")
        print("\n📊 Summary:")
        print(f"   Organizations: 1")
        print(f"   Users: {len(users)}")
        print(f"   Projects: 1")
        print("\n🔑 Test Credentials:")
        print(f"   Admin: admin@grandscale.ai")
        print(f"   PM: pm@grandscale.ai")
        print(f"   Annotator: annotator@grandscale.ai")

if __name__ == "__main__":
    asyncio.run(seed_data())

