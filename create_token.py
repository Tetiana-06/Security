# Код допоміжного скрипта створення токена
# Цей скрипт генерує файл облікових даних, обчислює SHA-256 від пароля та накладає шифрування перед записом на токен.


import hashlib
import json
import os

# Секретний ключ для захисту вмісту токена (симетричне шифрування XOR/базовий рівень)
TOKEN_PROTECTION_KEY = 0xAA


def xor_crypt(data: bytes, key: int) -> bytes:
  """Просте апаратне шифрування файлу токена від прямого зчитування."""
  return bytes([b ^ key for b in data])


def main():
  print(" Створення токена безпеки ")

  # Якщо флешка зараз не вставлена, можна ввести '.' (поточна папка)
  path = input("Введіть шлях до флешки: ")
  username = input("Введіть ім'я користувача: ")
  password = input("Введіть пароль: ")

  # Обчислення хеш-образу пароля (SHA-256 з набору стандартів CryptoAPI)
  pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

  token_data = {"username": username, "password_hash": pwd_hash}

  token_bytes = json.dumps(token_data).encode("utf-8")
  protected_bytes = xor_crypt(token_bytes, TOKEN_PROTECTION_KEY)

  token_file = os.path.join(path, "security_token.dat")
  with open(token_file, "wb") as f:
    f.write(protected_bytes)

  print(f"[+] Токен безпеки успішно створено за шляхом: {token_file}")
  print(f"[i] Збережений SHA-256 хеш: {pwd_hash}")


if __name__ == "__main__":
  main()