"""Setup script — creates the initial owner account in Supabase.

Run once after setting up the database:
    python setup_owner.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

from app.services.auth import sign_up


def main() -> None:
    email = "josh@maticdigital.com"
    name = "Josh Fuller"
    role = "owner"
    password = "12345"

    print(f"Creating owner account: {email}")
    try:
        user = sign_up(email, password, name, role)
        print(f"Owner account created successfully!")
        print(f"  ID:    {user['id']}")
        print(f"  Email: {user['email']}")
        print(f"  Name:  {user['name']}")
        print(f"  Role:  {user['role']}")
        print()
        print("You can now sign in at the Retina web app.")
        print("IMPORTANT: Change your password after first login.")
    except ValueError as e:
        if "already" in str(e).lower():
            print(f"Account for {email} already exists.")
        else:
            print(f"Error: {e}")
    except Exception as e:
        print(f"Failed to create account: {e}")
        print()
        print("Make sure:")
        print("  1. SUPABASE_URL is set in .env")
        print("  2. SUPABASE_SERVICE_ROLE_KEY is set in .env")
        print("  3. The SQL schema has been applied (supabase_setup.sql)")


if __name__ == "__main__":
    main()
