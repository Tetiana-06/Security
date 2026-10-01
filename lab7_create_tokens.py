# Створює три токени ЛР6/ЛР7 для користувачів admin, Tetyana, student.

import hashlib
import json
import os

TOKEN_PROTECTION_KEY = 0xAA
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USERS = [
    ("admin", "admin123"),
    ("Tetyana", "user_pass"),
    ("student", "q123"),
]


def xor_crypt(data: bytes, key: int) -> bytes:
  return bytes([b ^ key for b in data])


def main() -> None:
  for username, password in USERS:
    folder = os.path.join(BASE_DIR, "tokens", username)
    os.makedirs(folder, exist_ok=True)
    pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    token_data = {"username": username, "password_hash": pwd_hash}
    protected = xor_crypt(
        json.dumps(token_data).encode("utf-8"), TOKEN_PROTECTION_KEY
    )
    path = os.path.join(folder, "security_token.dat")
    with open(path, "wb") as f:
      f.write(protected)
    print(f"[+] {username}: {path}")


if __name__ == "__main__":
  main()
