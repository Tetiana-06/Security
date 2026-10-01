# Сервер слухає порт 127.0.0.1:9099, зберігає еталонний хеш і перевіряє запити автентифікації від клієнта.

import hashlib
import json
import socket

HOST = "127.0.0.1"  # Інтерфейс loopback
PORT = 9099

# Еталонна серверна база реєстраційних даних (username: password_hash)
USERS_DB = {
    "student": hashlib.sha256(b"q123").hexdigest(),
    # Пароль за замовчуванням: admin123
    "admin": hashlib.sha256(b"admin123").hexdigest(),
    # Пароль за замовчуванням: user_secure_pass
    "Tetyana": hashlib.sha256(b"user_pass").hexdigest(),
}


def start_server():
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server_socket.bind((HOST, PORT))
  server_socket.listen(5)
  print(f"[*] Сервер запущено на {HOST}:{PORT}")
  print("[*] Очікування з'єднань від клієнтів...")

  while True:
    conn, addr = server_socket.accept()
    print(f"\n[+] Нове з'єднання: {addr}")

    data = conn.recv(4096)
    if not data:
      conn.close()
      continue

    try:
      payload = json.loads(data.decode("utf-8"))
      username = payload.get("username")
      client_hash = payload.get("password_hash")

      print(f"[*] Запит автентифікації для користувача: '{username}'")
      print(f"[*] Отриманий хеш токена: {client_hash}")

      # Перевірка наявності користувача та збігу хешів
      if username in USERS_DB and USERS_DB[username] == client_hash:
        response = {
            "status": "SUCCESS",
            "message": f"Автентифікація успішна! Ласкаво просимо, {username}.",
        }
        print(f"[✓] УСПІХ: Користувача '{username}' автентифіковано.")
      else:
        response = {
            "status": "FAILED",
            "message": (
                "Помилка автентифікації! Невірні дані токена або хеш пароля."
            ),
        }
        print(f"[✗] ВІДХИЛЕНО: Автентифікація для '{username}' неуспішна.")

      conn.sendall(json.dumps(response).encode("utf-8"))
    except Exception as e:
      print(f"[!] Помилка обробки запиту: {e}")
    finally:
      conn.close()


if __name__ == "__main__":
  start_server()