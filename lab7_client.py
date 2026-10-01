# Клієнт ЛР7: зчитує токен (як у ЛР6), автентифікується і працює
# з текстовими об'єктами на сервері згідно з політикою доступу.

import json
import os
import socket
import sys

HOST = os.environ.get("LAB7_HOST", "127.0.0.1")
PORT = int(os.environ.get("LAB7_PORT", "9099"))
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


def recv_json(sock) -> dict:
  buf = b""
  while b"\n" not in buf:
    chunk = sock.recv(4096)
    if not chunk:
      raise ConnectionError("Сервер закрив з'єднання")
    buf += chunk
  line = buf.split(b"\n", 1)[0]
  return json.loads(line.decode("utf-8"))


def send_json(sock, payload: dict) -> dict:
  sock.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
  return recv_json(sock)


def print_objects(items: list) -> None:
  print("\n{:<22} {:<10} {:<14} {:<28} {}".format(
      "Об'єкт", "Власник", "Рівень", "Категорії", "Права"))
  print("-" * 100)
  for item in items:
    cats = ",".join(item.get("categories") or ["—"]) or "—"
    rights = ",".join(item.get("rights") or ["немає"])
    print("{:<22} {:<10} {:<14} {:<28} {}".format(
        item["name"], item["owner"], item["level"], cats, rights))


def menu() -> None:
  print("\n--- Меню роботи з об'єктами ---")
  print("1. Список об'єктів і дозволених прав")
  print("2. Читати (READ)")
  print("3. Перезаписати (WRITE)")
  print("4. Дописати (APPEND)")
  print("5. Створити об'єкт (OWN)")
  print("6. Видалити об'єкт (OWN)")
  print("7. Мій профіль / мітка")
  print("0. Вихід")


def main() -> None:
  print("Клієнт ЛР7 (Белла–ЛаПадула з категоріями)")
  if len(sys.argv) > 1:
    token_path = sys.argv[1]
  else:
    token_path = input("Вкажіть шлях до флешки / каталогу з токеном: ").strip()

  auth_data = read_token(token_path)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((HOST, PORT))
  sock.sendall((json.dumps(auth_data, ensure_ascii=False) + "\n").encode("utf-8"))
  response = recv_json(sock)

  print("\nСтатус:", response.get("status"))
  print("Відповідь:", response.get("message"))
  if response.get("status") != "SUCCESS":
    sock.close()
    return

  subject = response.get("subject") or {}
  print("Користувач:", subject.get("username"))
  print("Рівень:", subject.get("level"))
  print("Категорії:", ", ".join(subject.get("categories") or []))

  while True:
    menu()
    choice = input("Оберіть пункт: ").strip()
    try:
      if choice == "0":
        send_json(sock, {"action": "QUIT"})
        break
      if choice == "1":
        resp = send_json(sock, {"action": "LIST"})
        print_objects(resp.get("objects") or [])
        continue
      if choice == "2":
        name = input("Ім'я об'єкта: ").strip()
        resp = send_json(sock, {"action": "READ", "name": name})
      elif choice == "3":
        name = input("Ім'я об'єкта: ").strip()
        content = input("Новий вміст: ")
        resp = send_json(sock, {"action": "WRITE", "name": name, "content": content})
      elif choice == "4":
        name = input("Ім'я об'єкта: ").strip()
        content = input("Текст для дописування: ")
        resp = send_json(sock, {"action": "APPEND", "name": name, "content": content})
      elif choice == "5":
        name = input("Ім'я нового файлу: ").strip()
        content = input("Вміст: ")
        resp = send_json(sock, {"action": "CREATE", "name": name, "content": content})
      elif choice == "6":
        name = input("Ім'я об'єкта для видалення: ").strip()
        resp = send_json(sock, {"action": "DELETE", "name": name})
      elif choice == "7":
        resp = send_json(sock, {"action": "PROFILE"})
      else:
        print("Невірний пункт меню.")
        continue

      print("Статус:", resp.get("status"))
      print("Повідомлення:", resp.get("message"))
      if "content" in resp:
        print("--- Вміст ---")
        print(resp["content"])
      if "subject" in resp:
        print("Мітка:", resp["subject"])
      if "object" in resp:
        print("Створений об'єкт:", resp["object"])
    except Exception as e:
      print("[!] Помилка:", e)
      break

  sock.close()
  print("Сеанс завершено.")


if __name__ == "__main__":
  main()
