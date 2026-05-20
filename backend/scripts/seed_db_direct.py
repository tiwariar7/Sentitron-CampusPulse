"""
seed_db_direct.py
-----------------
Seeds 32 test accounts (8 per role) DIRECTLY into the SQLite database,
bypassing the API server entirely. Works even when the backend is offline.

Run from the workspace root:
    python backend/scripts/seed_db_direct.py
"""

import sys
import os
import asyncio
from pathlib import Path

# Make backend importable
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))

# Force UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{ROOT}/backend/campuspulse.db")


ACCOUNTS = {
    "admin": [
        {"username": "admin",         "email": "admin@campuspulse.edu",                   "password": "Admin@Secure1",  "department": "Management"},
        {"username": "superadmin",    "email": "superadmin@campuspulse.edu",               "password": "SuperAdmin@2",   "department": "Management"},
        {"username": "director_ops",  "email": "director.ops@campuspulse.edu",             "password": "Director@Ops3",  "department": "Operations"},
        {"username": "dean_academic", "email": "dean.academic@campuspulse.edu",            "password": "Dean@Acad4",     "department": "Academics"},
        {"username": "principal_mit", "email": "principal@campuspulse.edu",                "password": "Principal@5",    "department": "Management"},
        {"username": "cto_sentitron", "email": "cto@campuspulse.edu",                      "password": "CTOAdmin@6",     "department": "Technology"},
        {"username": "provost",       "email": "provost@campuspulse.edu",                  "password": "Provost@7",      "department": "Management"},
        {"username": "sys_admin",     "email": "sysadmin@campuspulse.edu",                 "password": "SysAdmin@8",     "department": "IT"},
    ],
    "moderator": [
        {"username": "mod_cse",       "email": "mod.cse@campuspulse.edu",                  "password": "Mod_CSE@1",      "department": "CSE"},
        {"username": "mod_ece",       "email": "mod.ece@campuspulse.edu",                  "password": "Mod_ECE@2",      "department": "ECE"},
        {"username": "mod_me",        "email": "mod.me@campuspulse.edu",                   "password": "Mod_ME@3",       "department": "ME"},
        {"username": "mod_hostel",    "email": "mod.hostel@campuspulse.edu",               "password": "Mod_Hostel@4",   "department": "Hostel"},
        {"username": "mod_academics", "email": "mod.academics@campuspulse.edu",            "password": "Mod_Acad@5",     "department": "Academics"},
        {"username": "mod_transport", "email": "mod.transport@campuspulse.edu",            "password": "Mod_Trans@6",    "department": "Transport"},
        {"username": "mod_security",  "email": "mod.security@campuspulse.edu",             "password": "Mod_Sec@7",      "department": "Security"},
        {"username": "mod_welfare",   "email": "mod.welfare@campuspulse.edu",              "password": "Mod_Welfare@8",  "department": "Student Welfare"},
    ],
    "user": [
        {"username": "student_arjun", "email": "arjun.kumar@student.campuspulse.edu",      "password": "Arjun@Student1", "department": "CSE"},
        {"username": "student_priya", "email": "priya.sharma@student.campuspulse.edu",     "password": "Priya@Student2", "department": "ECE"},
        {"username": "student_rahul", "email": "rahul.verma@student.campuspulse.edu",      "password": "Rahul@Student3", "department": "ME"},
        {"username": "student_ananya","email": "ananya.singh@student.campuspulse.edu",     "password": "Ananya@Stu4",    "department": "Civil"},
        {"username": "faculty_rajesh","email": "rajesh.prof@campuspulse.edu",              "password": "Rajesh@Fac5",    "department": "CSE"},
        {"username": "faculty_meena", "email": "meena.prof@campuspulse.edu",               "password": "Meena@Fac6",     "department": "ECE"},
        {"username": "staff_arun",    "email": "arun.staff@campuspulse.edu",               "password": "Arun@Staff7",    "department": "Administration"},
        {"username": "staff_lakshmi", "email": "lakshmi.staff@campuspulse.edu",            "password": "Lakshmi@Stf8",   "department": "Hostel"},
    ],
    "guest": [
        {"username": "visitor_1",     "email": "visitor1@external.com",                    "password": "Visitor@Gst1",   "department": "External"},
        {"username": "visitor_2",     "email": "visitor2@external.com",                    "password": "Visitor@Gst2",   "department": "External"},
        {"username": "reporter_john", "email": "reporter1@press.com",                      "password": "Reporter@Gst3",  "department": "Press"},
        {"username": "inspector_gov", "email": "inspector1@gov.in",                        "password": "Inspect@Gst4",   "department": "Government"},
        {"username": "auditor_ext",   "email": "auditor@audit.org",                        "password": "Auditor@Gst5",   "department": "Audit"},
        {"username": "parent_kumar",  "email": "parent.kumar@external.com",                "password": "Parent@Gst6",    "department": "External"},
        {"username": "alumni_2022",   "email": "alumni2022@alumni.campuspulse.edu",        "password": "Alumni@Gst7",    "department": "Alumni"},
        {"username": "press_media",   "email": "media@campuspress.com",                    "password": "Press@Gst8",     "department": "Media"},
    ],
}


async def seed():
    from services.db import engine, Base, AsyncSessionLocal, User
    from services.auth import hash_password
    from sqlalchemy.future import select

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    created, skipped, failed = [], [], []

    async with AsyncSessionLocal() as session:
        for role, accounts in ACCOUNTS.items():
            print(f"\n{'=' * 55}")
            print(f"  Seeding {len(accounts)} {role.upper()} accounts...")
            print(f"{'=' * 55}")

            for acc in accounts:
                try:
                    # Check username
                    res = await session.execute(
                        select(User).where(User.username == acc["username"])
                    )
                    if res.scalars().first():
                        print(f"  [--]  {acc['username']:<22} [{role}]  ->  already exists (skipped)")
                        skipped.append({**acc, "role": role})
                        continue

                    # Check email
                    res2 = await session.execute(
                        select(User).where(User.email == acc["email"])
                    )
                    if res2.scalars().first():
                        print(f"  [--]  {acc['username']:<22} [{role}]  ->  email conflict (skipped)")
                        skipped.append({**acc, "role": role})
                        continue

                    user = User(
                        username=acc["username"],
                        email=acc["email"],
                        hashed_password=hash_password(acc["password"]),
                        role=role,
                        department=acc["department"],
                    )
                    session.add(user)
                    await session.flush()
                    print(f"  [OK]  {acc['username']:<22} [{role}]  ->  created")
                    created.append({**acc, "role": role})

                except Exception as e:
                    await session.rollback()
                    print(f"  [XX]  {acc['username']:<22} [{role}]  ->  error: {e}")
                    failed.append({**acc, "role": role})

        await session.commit()

    await engine.dispose()
    return created, skipped, failed


async def main():
    print("\nSentitron CampusPulse -- Direct DB Account Seeder")
    print(f"  Database: {os.environ['DATABASE_URL']}\n")

    created, skipped, failed = await seed()

    total = sum(len(v) for v in ACCOUNTS.values())
    print(f"\n{'=' * 55}")
    print("  Seeding complete:")
    print(f"    [OK] Created : {len(created)}/{total}")
    print(f"    [--] Skipped : {len(skipped)}/{total}  (already existed)")
    print(f"    [XX] Failed  : {len(failed)}/{total}")
    print(f"{'=' * 55}")
    print(f"\n  Credentials file: {ROOT / 'test_accounts.txt'}\n")


if __name__ == "__main__":
    asyncio.run(main())
