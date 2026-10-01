# Клієнт зчитує зашифрований файл із флешки, дешифрує його на льоту та передає дані на сервер.

import json
import os
import socket

HOST = "127.0.0.1"
PORT = 9099
TOKEN_PROTECTION_KEY = 0xAA


def xor_crypt(data: bytes, key: int) -> bytes:
  return bytes([b ^ key for b in data])


def read_token(path: str) -> dict:
  token_file = os.path.join(path, "security_token.dat")
  if not os.path.exists(token_file):
    raise FileNotFoundError(f"Файл токена не знайдено: {token_file}")

  with open(token_file, "rb") as f:
    encrypted_data = f.read()

  decrypted_data = xor_crypt(encrypted_data, TOKEN_PROTECTION_KEY)
  return json.loads(decrypted_data.decode("utf-8"))


def main():
  print(" Клієнт автентифікації (Security Token) ")
  token_path = input(
      "Вкажіть шлях до флешки з токеном: "
  )

  try:
    auth_data = read_token(token_path)
    print(
        f"[+] Токен знайдено! Користувач: {auth_data.get('username')}, Хеш:"
        f" {auth_data.get('password_hash')[:16]}..."
    )

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    # Передача облікових даних на сервер
    client_socket.sendall(json.dumps(auth_data).encode("utf-8"))

    # Отримання вердикту
    response_data = client_socket.recv(4096)
    response = json.loads(response_data.decode("utf-8"))

    print("\n Результат автентифікації ")
    print(f"Статус:  {response.get('status')}")
    print(f"Відповідь сервера: {response.get('message')}")

    client_socket.close()
  except Exception as e:
    print(f"[!] Помилка виконання: {e}")


if __name__ == "__main__":
  main()