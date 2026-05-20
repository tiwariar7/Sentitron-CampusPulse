"""
seed_accounts.py
----------------
Creates 7-8 test accounts for each role (admin, moderator, user, guest)
in the Sentitron CampusPulse database by calling the /api/auth/register endpoint.

Run while the backend server is running:
    python backend/scripts/seed_accounts.py
"""

import asyncio
import sys
import httpx
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

ACCOUNTS = {
    "admin": [
        {"username": "admin",         "email": "admin@campuspulse.edu",           "password": "Admin@Secure1",  "department": "Management"},
        {"username": "superadmin",    "email": "superadmin@campuspulse.edu",      "password": "SuperAdmin@2",   "department": "Management"},
        {"username": "director_ops",  "email": "director.ops@campuspulse.edu",    "password": "Director@Ops3",  "department": "Operations"},
        {"username": "dean_academic", "email": "dean.academic@campuspulse.edu",   "password": "Dean@Acad4",     "department": "Academics"},
        {"username": "principal_mit", "email": "principal@campuspulse.edu",       "password": "Principal@5",    "department": "Management"},
        {"username": "cto_sentitron", "email": "cto@campuspulse.edu",             "password": "CTOAdmin@6",     "department": "Technology"},
        {"username": "provost",       "email": "provost@campuspulse.edu",         "password": "Provost@7",      "department": "Management"},
        {"username": "sys_admin",     "email": "sysadmin@campuspulse.edu",        "password": "SysAdmin@8",     "department": "IT"},
    ],
    "moderator": [
        {"username": "mod_cse",       "email": "mod.cse@campuspulse.edu",         "password": "Mod_CSE@1",      "department": "CSE"},
        {"username": "mod_ece",       "email": "mod.ece@campuspulse.edu",         "password": "Mod_ECE@2",      "department": "ECE"},
        {"username": "mod_me",        "email": "mod.me@campuspulse.edu",          "password": "Mod_ME@3",       "department": "ME"},
        {"username": "mod_hostel",    "email": "mod.hostel@campuspulse.edu",      "password": "Mod_Hostel@4",   "department": "Hostel"},
        {"username": "mod_academics", "email": "mod.academics@campuspulse.edu",   "password": "Mod_Acad@5",     "department": "Academics"},
        {"username": "mod_transport", "email": "mod.transport@campuspulse.edu",   "password": "Mod_Trans@6",    "department": "Transport"},
        {"username": "mod_security",  "email": "mod.security@campuspulse.edu",    "password": "Mod_Sec@7",      "department": "Security"},
        {"username": "mod_welfare",   "email": "mod.welfare@campuspulse.edu",     "password": "Mod_Welfare@8",  "department": "Student Welfare"},
    ],
    "user": [
        {"username": "student_arjun", "email": "arjun.kumar@student.campuspulse.edu",   "password": "Arjun@Student1", "department": "CSE"},
        {"username": "student_priya", "email": "priya.sharma@student.campuspulse.edu",  "password": "Priya@Student2", "department": "ECE"},
        {"username": "student_rahul", "email": "rahul.verma@student.campuspulse.edu",   "password": "Rahul@Student3", "department": "ME"},
        {"username": "student_ananya","email": "ananya.singh@student.campuspulse.edu",  "password": "Ananya@Stu4",    "department": "Civil"},
        {"username": "faculty_rajesh","email": "rajesh.prof@campuspulse.edu",           "password": "Rajesh@Fac5",    "department": "CSE"},
        {"username": "faculty_meena", "email": "meena.prof@campuspulse.edu",            "password": "Meena@Fac6",     "department": "ECE"},
        {"username": "staff_arun",    "email": "arun.staff@campuspulse.edu",            "password": "Arun@Staff7",    "department": "Administration"},
        {"username": "staff_lakshmi", "email": "lakshmi.staff@campuspulse.edu",         "password": "Lakshmi@Stf8",   "department": "Hostel"},
    ],
    "guest": [
        {"username": "visitor_1",     "email": "visitor1@external.com",                 "password": "Visitor@Gst1",   "department": "External"},
        {"username": "visitor_2",     "email": "visitor2@external.com",                 "password": "Visitor@Gst2",   "department": "External"},
        {"username": "reporter_john", "email": "reporter1@press.com",                   "password": "Reporter@Gst3",  "department": "Press"},
        {"username": "inspector_gov", "email": "inspector1@gov.in",                     "password": "Inspect@Gst4",   "department": "Government"},
        {"username": "auditor_ext",   "email": "auditor@audit.org",                     "password": "Auditor@Gst5",   "department": "Audit"},
        {"username": "parent_kumar",  "email": "parent.kumar@external.com",             "password": "Parent@Gst6",    "department": "External"},
        {"username": "alumni_2022",   "email": "alumni2022@alumni.campuspulse.edu",     "password": "Alumni@Gst7",    "department": "Alumni"},
        {"username": "press_media",   "email": "media@campuspress.com",                 "password": "Press@Gst8",     "department": "Media"},
    ],
}


async def seed_accounts():
    results = {"created": [], "skipped": [], "failed": []}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:
        for role, accounts in ACCOUNTS.items():
            print(f"\n{'='*55}")
            print(f"  Seeding {len(accounts)} {role.upper()} accounts...")
            print(f"{'='*55}")
            for acc in accounts:
                payload = {
                    "username": acc["username"],
                    "email": acc["email"],
                    "password": acc["password"],
                    "role": role,
                    "department": acc["department"],
                }
                try:
                    res = await client.post("/api/auth/register", json=payload)
                    if res.status_code == 200:
                        print(f"  [OK]  {acc['username']:<22} [{role}]  ->  created")
                        results["created"].append({**acc, "role": role})
                    elif res.status_code == 400:
                        print(f"  [--]  {acc['username']:<22} [{role}]  ->  already exists (skipped)")
                        results["skipped"].append({**acc, "role": role})
                    else:
                        detail = res.json().get("detail", res.text)
                        print(f"  [XX]  {acc['username']:<22} [{role}]  ->  failed ({res.status_code}) {detail}")
                        results["failed"].append({**acc, "role": role})
                except Exception as e:
                    print(f"  [XX]  {acc['username']:<22} [{role}]  ->  error: {e}")
                    results["failed"].append({**acc, "role": role})

    return results


def write_credentials_file(results: dict):
    workspace_root = Path(__file__).parent.parent.parent  # backend/scripts -> root
    out_path = workspace_root / "test_accounts.txt"

    lines = [
        "=" * 65,
        "  SENTITRON CAMPUSPULSE -- TEST USER CREDENTIALS",
        "  Generated by: backend/scripts/seed_accounts.py",
        "=" * 65,
        "",
    ]

    all_accounts = results["created"] + results["skipped"]
    grouped: dict[str, list] = {}
    for acc in all_accounts:
        grouped.setdefault(acc["role"], []).append(acc)

    role_order = ["admin", "moderator", "user", "guest"]
    role_labels = {
        "admin":     "[ADMIN]      ADMINISTRATOR ACCOUNTS",
        "moderator": "[MODERATOR]  MODERATOR ACCOUNTS",
        "user":      "[USER]       STANDARD USER ACCOUNTS",
        "guest":     "[GUEST]      GUEST ACCOUNTS",
    }

    for role in role_order:
        accounts = grouped.get(role, [])
        if not accounts:
            continue
        lines.append(role_labels[role])
        lines.append("-" * 65)
        lines.append(f"{'USERNAME':<22}  {'EMAIL':<40}  {'PASSWORD':<20}  DEPARTMENT")
        lines.append("-" * 65)
        for acc in accounts:
            lines.append(
                f"{acc['username']:<22}  {acc['email']:<40}  {acc['password']:<20}  {acc['department']}"
            )
        lines.append("")

    lines += [
        "=" * 65,
        "  NOTES",
        "  - Backend login endpoint: POST http://localhost:8000/api/auth/login",
        '  - Body: {"username": "...", "password": "..."}',
        "  - Frontend login page:    http://localhost:3000/auth",
        "  - Admin panel controls:   Settings, Audit Logs, User Management",
        "  - Moderators can view all incidents but cannot edit settings.",
        "  - Standard Users see only their own incidents & notifications.",
        "  - Guests have read-only access to the reporting portal.",
        "=" * 65,
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[DONE]  Credentials saved -> {out_path}")
    return out_path


async def main():
    print("\nSentitron CampusPulse -- Account Seeder")
    print(f"    Target: {BASE_URL}")

    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=5.0) as c:
            res = await c.get("/health")
            if res.status_code != 200:
                raise ConnectionError()
        print("    Backend health check: OK\n")
    except Exception:
        print("\n  [ERROR]  Backend is not running. Start it with:")
        print("       cd backend && uvicorn api.main:app --reload")
        return

    results = await seed_accounts()
    write_credentials_file(results)

    total = len(ACCOUNTS["admin"]) + len(ACCOUNTS["moderator"]) + len(ACCOUNTS["user"]) + len(ACCOUNTS["guest"])
    print(f"\n{'='*55}")
    print(f"  Seeding complete:")
    print(f"    [OK] Created : {len(results['created'])}/{total}")
    print(f"    [--] Skipped : {len(results['skipped'])}/{total}  (already existed)")
    print(f"    [XX] Failed  : {len(results['failed'])}/{total}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    asyncio.run(main())
