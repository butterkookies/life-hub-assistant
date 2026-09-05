"""Generate VAPID keys for Andrei's Life Hub Assistant Web Push notifications."""

import sys
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid import Vapid
from py_vapid.main import b64urlencode

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

def generate_keys():
    vapid = Vapid()
    vapid.generate_keys()
    
    # Private key in PEM format (escaped single line or multi-line)
    private_pem = vapid.private_pem().decode("utf-8").strip()
    # In .env, multi-line PEM can be stored with escaped newlines \n or raw
    private_escaped = private_pem.replace("\n", "\\n")
    
    # Public key raw uncompressed point encoded as base64url
    raw_public = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    public_b64 = b64urlencode(raw_public)
    
    return public_b64, private_escaped, private_pem

def main():
    pub, priv_escaped, _ = generate_keys()
    print("✅ VAPID Keys Generated Successfully:\n")
    print(f'WEB_PUSH_VAPID_PUBLIC_KEY="{pub}"')
    print(f'WEB_PUSH_VAPID_PRIVATE_KEY="{priv_escaped}"')
    print('WEB_PUSH_CONTACT="mailto:andrei@example.com"\n')
    print("Add these lines to your .env file.")

if __name__ == "__main__":
    main()
