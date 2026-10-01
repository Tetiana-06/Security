# Автоматичний протокол: 3 користувачі, 10+ об'єктів, дозволи та відмови.

import json
import os
import socket
import sys

HOST = os.environ.get("LAB7_HOST", "127.0.0.1")
PORT = int(os.environ.get("LAB7_PORT", "9099"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PROTECTION_KEY = 0xAA


def xor_crypt(data: bytes, key: int) -> bytes:
  return bytes([b ^ key for b in data])


def read_token(username: str) -> dict:
  path = os.path.join(BASE_DIR, "tokens", username, "security_token.dat")
  with open(path, "rb") as f:
    data = xor_crypt(f.read(), TOKEN_PROTECTION_KEY)
  return json.loads(data.decode("utf-8"))


def recv_json(sock) -> dict:
  buf = b""
  while b"\n" not in buf:
    chunk = sock.recv(4096)
    if not chunk:
      raise ConnectionError("Сервер закрив з'єднання")
    buf += chunk
  return json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))


def send_json(sock, payload: dict) -> dict:
  sock.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
  return recv_json(sock)


def session(username: str, actions: list[dict]) -> list[str]:
  lines = [f"\n===== Сеанс користувача {username} ====="]
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((HOST, PORT))
  sock.sendall((json.dumps(read_token(username), ensure_ascii=False) + "\n")
               .encode("utf-8"))
  auth = recv_json(sock)
  lines.append(f"AUTH {auth.get('status')}: {auth.get('message')}")
  if auth.get("subject"):
    s = auth["subject"]
    lines.append(
        f"Мітка: {s['level']} | категорії: {', '.join(s['categories'])}"
    )
  if auth.get("status") != "SUCCESS":
    sock.close()
    return lines

  for act in actions:
    resp = send_json(sock, act)
    title = act.get("action")
    name = act.get("name", "")
    status = resp.get("status")
    msg = resp.get("message")
    extra = ""
    if title == "LIST":
      extra = "; ".join(
          f"{o['name']}[{','.join(o['rights']) or '-'}]"
          for o in resp.get("objects") or []
      )
    elif "content" in resp:
      extra = "вміст=" + repr(resp["content"][:80])
    lines.append(f"{title} {name} -> {status}: {msg} {extra}".rstrip())

  send_json(sock, {"action": "QUIT"})
  sock.close()
  return lines


def main() -> None:
  out_path = os.path.join(BASE_DIR, "protocol_demo.txt")
  all_lines = [
      "Протокол роботи програми ЛР7",
      "Політика: модель Белла–ЛаПадули з категоріями (варіант 3)",
      "Інтерфейс: 127.0.0.1:9099 (loopback)",
  ]

  all_lines += session("student", [
      {"action": "PROFILE"},
      {"action": "LIST"},
      {"action": "READ", "name": "public_notice.txt"},
      {"action": "READ", "name": "lab_guide.txt"},
      {"action": "READ", "name": "grades.txt"},
      {"action": "READ", "name": "strategy.txt"},
      {"action": "WRITE", "name": "lab_guide.txt",
       "content": "Оновлена методичка від student.\n"},
      {"action": "WRITE", "name": "public_notice.txt",
       "content": "Спроба знизити секретність.\n"},
      {"action": "APPEND", "name": "equipment.txt",
       "content": "Додано кабель UTP.\n"},
      {"action": "CREATE", "name": "student_notes.txt",
       "content": "Нотатки студента (CONFIDENTIAL / Техніка).\n"},
      {"action": "DELETE", "name": "budget_2026.txt"},
      {"action": "DELETE", "name": "student_notes.txt"},
  ])

  all_lines += session("Tetyana", [
      {"action": "PROFILE"},
      {"action": "LIST"},
      {"action": "READ", "name": "budget_2026.txt"},
      {"action": "READ", "name": "grades.txt"},
      {"action": "READ", "name": "incident_plan.txt"},
      {"action": "READ", "name": "lab_guide.txt"},
      {"action": "WRITE", "name": "budget_2026.txt",
       "content": "Уточнений бюджет (SECRET).\n"},
      {"action": "WRITE", "name": "public_notice.txt",
       "content": "Запис вниз заборонений.\n"},
      {"action": "APPEND", "name": "staff_salaries.txt",
       "content": "Коментар власника.\n"},
      {"action": "DELETE", "name": "grades.txt"},
      {"action": "CREATE", "name": "hr_memo.txt",
       "content": "Службова записка кадрів.\n"},
  ])

  all_lines += session("admin", [
      {"action": "PROFILE"},
      {"action": "LIST"},
      {"action": "READ", "name": "incident_plan.txt"},
      {"action": "READ", "name": "staff_salaries.txt"},
      {"action": "READ", "name": "public_notice.txt"},
      {"action": "WRITE", "name": "public_notice.txt",
       "content": "Адмін не може писати вниз (UNCLASSIFIED).\n"},
      {"action": "WRITE", "name": "strategy.txt",
       "content": "Оновлена стратегія TOP_SECRET.\n"},
      {"action": "WRITE", "name": "ts_full.txt",
       "content": "Оновлене зведення TOP_SECRET (усі категорії).\n"},
      {"action": "APPEND", "name": "crypto_notes.txt",
       "content": "Допис адміністратора.\n"},
      {"action": "CREATE", "name": "admin_ts.txt",
       "content": "Новий об'єкт TOP_SECRET.\n"},
      {"action": "DELETE", "name": "admin_ts.txt"},
      {"action": "DELETE", "name": "hr_memo.txt"},
  ])

  text = "\n".join(all_lines) + "\n"
  with open(out_path, "w", encoding="utf-8") as f:
    f.write(text)
  print(text)
  print(f"[+] Протокол збережено: {out_path}")


if __name__ == "__main__":
  try:
    main()
  except ConnectionRefusedError:
    print("Спочатку запустіть: python lab7_server.py", file=sys.stderr)
    sys.exit(1)
