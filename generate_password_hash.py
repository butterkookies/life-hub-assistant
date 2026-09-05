"""Generate salted password hash for Andrei's Life Hub Assistant."""

import argparse
import hashlib
import hmac
import os
import secrets
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def hash_password(password: str, iterations: int = 600000) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 600,000 rounds and random 16-byte salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        iterations
    )
    return f"pbkdf2:sha256:{iterations}${salt}${derived.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored hash."""
    if not password or not hashed:
        return False
    try:
        # Check if Argon2 hash (if user supplied an argon2id hash)
        if hashed.startswith("$argon2"):
            try:
                import argon2
                ph = argon2.PasswordHasher()
                return ph.verify(hashed, password)
            except ImportError:
                return False
            except Exception:
                return False

        # PBKDF2 format: pbkdf2:sha256:iterations$salt$hash
        if not hashed.startswith("pbkdf2:sha256:"):
            return False
        header, salt, hash_hex = hashed.split("$")
        iterations = int(header.split(":")[2])
        test_derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            iterations
        )
        return hmac.compare_digest(test_derived.hex(), hash_hex)
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate salted password hash for Andrei's Life Hub Assistant")
    parser.add_argument("-p", "--password", help="Password to hash (prompts interactively if not provided)")
    args = parser.parse_args()

    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("Enter password to hash: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("❌ Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    hashed = hash_password(password)
    assert verify_password(password, hashed), "Self-check verification failed!"
    print("\n✅ Password hash generated successfully:")
    print(f"\nWEB_PASSWORD_HASH=\"{hashed}\"\n")
    print("Add this line to your .env file.")

if __name__ == "__main__":
    main()
