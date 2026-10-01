# Сервер ЛР7: автентифікація токеном (як у ЛР6) + політика Белла–ЛаПадули
# з категоріями. Об'єкти — текстові файли на серверному боці.

import hashlib
import json
import os
import socket
from datetime import datetime

from lab7_access import LEVEL_NAMES, RIGHTS, check_right, parse_level

# Для реальної лабораторної мережі: HOST = "0.0.0.0"
HOST = os.environ.get("LAB7_HOST", "127.0.0.1")
PORT = int(os.environ.get("LAB7_PORT", "9099"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OBJECTS_DIR = os.path.join(BASE_DIR, "server_objects")
META_FILE = os.path.join(OBJECTS_DIR, "objects_meta.json")
PROTOCOL_FILE = os.path.join(BASE_DIR, "protocol_lab7.log")

USERS_DB = {
    "student": hashlib.sha256(b"q123").hexdigest(),
    "admin": hashlib.sha256(b"admin123").hexdigest(),
    "Tetyana": hashlib.sha256(b"user_pass").hexdigest(),
}

# Рівень + категорії кожного суб'єкта (мандатна мітка).
SUBJECTS = {
    "admin": {
        "level": "TOP_SECRET",
        "categories": ["Фінанси", "Кадри", "Техніка"],
    },
    "Tetyana": {
        "level": "SECRET",
        "categories": ["Фінанси", "Кадри"],
    },
    "student": {
        "level": "CONFIDENTIAL",
        "categories": ["Техніка"],
    },
}

INITIAL_OBJECTS = [
    {
        "name": "public_notice.txt",
        "owner": "admin",
        "level": "UNCLASSIFIED",
        "categories": [],
        "content": "Оголошення: лабораторна робота з контролю доступу.\n",
    },
    {
        "name": "schedule.txt",
        "owner": "student",
        "level": "UNCLASSIFIED",
        "categories": ["Техніка"],
        "content": "Розклад занять з кібербезпеки: вівторок, 14:00.\n",
    },
    {
        "name": "lab_guide.txt",
        "owner": "student",
        "level": "CONFIDENTIAL",
        "categories": ["Техніка"],
        "content": "Методичка ЛР7: модель Белла-ЛаПадули з категоріями.\n",
    },
    {
        "name": "equipment.txt",
        "owner": "student",
        "level": "CONFIDENTIAL",
        "categories": ["Техніка"],
        "content": "Інвентар лабораторії: комутатори, робочі станції.\n",
    },
    {
        "name": "grades.txt",
        "owner": "Tetyana",
        "level": "CONFIDENTIAL",
        "categories": ["Кадри"],
        "content": "Оцінки групи: зберігаються як конфіденційні кадрові дані.\n",
    },
    {
        "name": "budget_2026.txt",
        "owner": "Tetyana",
        "level": "SECRET",
        "categories": ["Фінанси"],
        "content": "Проект бюджету підрозділу на 2026 рік (SECRET).\n",
    },
    {
        "name": "staff_salaries.txt",
        "owner": "Tetyana",
        "level": "SECRET",
        "categories": ["Кадри", "Фінанси"],
        "content": "Відомість нарахувань: кадри + фінанси.\n",
    },
    {
        "name": "crypto_notes.txt",
        "owner": "admin",
        "level": "SECRET",
        "categories": ["Техніка"],
        "content": "Нотатки щодо криптографічних протоколів лабораторії.\n",
    },
    {
        "name": "strategy.txt",
        "owner": "admin",
        "level": "TOP_SECRET",
        "categories": ["Фінанси"],
        "content": "Стратегія фінансування захищеної інфраструктури.\n",
    },
    {
        "name": "personnel_secret.txt",
        "owner": "admin",
        "level": "TOP_SECRET",
        "categories": ["Кадри"],
        "content": "Оперативні кадрові рішення найвищого рівня.\n",
    },
    {
        "name": "incident_plan.txt",
        "owner": "admin",
        "level": "TOP_SECRET",
        "categories": ["Техніка", "Фінанси"],
        "content": "План реагування на інциденти (техніка + фінанси).\n",
    },
    {
        "name": "ts_full.txt",
        "owner": "admin",
        "level": "TOP_SECRET",
        "categories": ["Фінанси", "Кадри", "Техніка"],
        "content": "Зведення TOP_SECRET з повним набором категорій.\n",
    },
]


def log_event(text: str) -> None:
  line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {text}"
  print(line)
  with open(PROTOCOL_FILE, "a", encoding="utf-8") as f:
    f.write(line + "\n")


def load_meta() -> dict:
  if not os.path.exists(META_FILE):
    return {}
  with open(META_FILE, "r", encoding="utf-8") as f:
    return json.load(f)


def save_meta(meta: dict) -> None:
  os.makedirs(OBJECTS_DIR, exist_ok=True)
  with open(META_FILE, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)


def object_path(name: str) -> str:
  return os.path.join(OBJECTS_DIR, name)


def seed_objects() -> None:
  os.makedirs(OBJECTS_DIR, exist_ok=True)
  meta = load_meta()
  if meta:
    return
  for item in INITIAL_OBJECTS:
    name = item["name"]
    with open(object_path(name), "w", encoding="utf-8") as f:
      f.write(item["content"])
    meta[name] = {
        "owner": item["owner"],
        "level": item["level"],
        "categories": item["categories"],
    }
  save_meta(meta)
  log_event(f"[INIT] Створено {len(meta)} об'єктів даних на сервері.")


def recv_json(conn) -> dict | None:
  buf = b""
  while b"\n" not in buf:
    chunk = conn.recv(4096)
    if not chunk:
      return None
    buf += chunk
    if len(buf) > 1_000_000:
      raise ValueError("Занадто велике повідомлення")
  line = buf.split(b"\n", 1)[0]
  return json.loads(line.decode("utf-8"))


def send_json(conn, payload: dict) -> None:
  conn.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))


def subject_record(username: str) -> dict:
  info = SUBJECTS[username]
  return {
      "username": username,
      "level": info["level"],
      "categories": list(info["categories"]),
  }


def handle_list(subject: dict) -> dict:
  meta = load_meta()
  items = []
  for name, info in sorted(meta.items()):
    obj = {"owner": info["owner"], "level": info["level"],
           "categories": info["categories"]}
    rights = [r for r in RIGHTS if check_right(subject, obj, r)[0]]
    items.append({
        "name": name,
        "owner": info["owner"],
        "level": info["level"],
        "categories": info["categories"],
        "rights": rights,
    })
  return {"status": "OK", "message": f"Об'єктів: {len(items)}", "objects": items}


def handle_read(subject: dict, name: str) -> dict:
  meta = load_meta()
  if name not in meta:
    return {"status": "ERROR", "message": "Об'єкт не знайдено."}
  allowed, reason = check_right(subject, meta[name], "READ")
  log_event(f"[ACL] {subject['username']} READ {name}: "
            f"{'ALLOW' if allowed else 'DENY'} ({reason})")
  if not allowed:
    return {"status": "DENIED", "message": reason, "right": "READ"}
  with open(object_path(name), "r", encoding="utf-8") as f:
    content = f.read()
  return {"status": "OK", "message": "Читання дозволено.", "content": content,
          "right": "READ"}


def handle_write(subject: dict, name: str, content: str, append: bool) -> dict:
  meta = load_meta()
  if name not in meta:
    return {"status": "ERROR", "message": "Об'єкт не знайдено."}
  right = "APPEND" if append else "WRITE"
  allowed, reason = check_right(subject, meta[name], right)
  log_event(f"[ACL] {subject['username']} {right} {name}: "
            f"{'ALLOW' if allowed else 'DENY'} ({reason})")
  if not allowed:
    return {"status": "DENIED", "message": reason, "right": right}
  mode = "a" if append else "w"
  with open(object_path(name), mode, encoding="utf-8") as f:
    f.write(content)
    if append and not content.endswith("\n"):
      f.write("\n")
  return {"status": "OK", "message": f"{right} виконано.", "right": right}


def handle_create(subject: dict, name: str, content: str) -> dict:
  meta = load_meta()
  if not name or "/" in name or "\\" in name or name == "objects_meta.json":
    return {"status": "ERROR", "message": "Некоректне ім'я об'єкта."}
  if name in meta:
    return {"status": "ERROR", "message": "Об'єкт з таким ім'ям уже існує."}
  # Новий об'єкт отримує мітку творця (запис «на своєму рівні»).
  meta[name] = {
      "owner": subject["username"],
      "level": subject["level"],
      "categories": list(subject["categories"]),
  }
  with open(object_path(name), "w", encoding="utf-8") as f:
    f.write(content)
  save_meta(meta)
  log_event(f"[ACL] {subject['username']} CREATE {name} "
            f"(власник, {subject['level']}, {subject['categories']})")
  return {
      "status": "OK",
      "message": "Об'єкт створено. Ви є власником.",
      "right": "OWN",
      "object": meta[name],
  }


def handle_delete(subject: dict, name: str) -> dict:
  meta = load_meta()
  if name not in meta:
    return {"status": "ERROR", "message": "Об'єкт не знайдено."}
  allowed, reason = check_right(subject, meta[name], "OWN")
  log_event(f"[ACL] {subject['username']} DELETE/OWN {name}: "
            f"{'ALLOW' if allowed else 'DENY'} ({reason})")
  if not allowed:
    return {"status": "DENIED", "message": reason, "right": "OWN"}
  os.remove(object_path(name))
  del meta[name]
  save_meta(meta)
  return {"status": "OK", "message": "Об'єкт видалено власником.", "right": "OWN"}


def handle_command(subject: dict, req: dict) -> dict:
  action = (req.get("action") or "").upper()
  name = req.get("name") or ""
  content = req.get("content") or ""

  if action == "LIST":
    return handle_list(subject)
  if action == "READ":
    return handle_read(subject, name)
  if action == "WRITE":
    return handle_write(subject, name, content, append=False)
  if action == "APPEND":
    return handle_write(subject, name, content, append=True)
  if action == "CREATE":
    return handle_create(subject, name, content)
  if action == "DELETE":
    return handle_delete(subject, name)
  if action == "PROFILE":
    return {
        "status": "OK",
        "message": "Профіль суб'єкта",
        "subject": subject,
        "rights_model": list(RIGHTS),
        "level_order": LEVEL_NAMES,
    }
  if action == "QUIT":
    return {"status": "BYE", "message": "Сеанс завершено."}
  return {"status": "ERROR", "message": f"Невідома дія: {action}"}


def handle_client(conn, addr) -> None:
  auth = recv_json(conn)
  if not auth:
    return
  username = auth.get("username")
  client_hash = auth.get("password_hash")
  log_event(f"[AUTH] Запит від {addr}: користувач '{username}'")

  if username not in USERS_DB or USERS_DB[username] != client_hash:
    send_json(conn, {
        "status": "FAILED",
        "message": "Помилка автентифікації! Невірний токен.",
    })
    log_event(f"[AUTH] ВІДХИЛЕНО: {username}")
    return
  if username not in SUBJECTS:
    send_json(conn, {
        "status": "FAILED",
        "message": "Користувача автентифіковано, але немає мандатної мітки.",
    })
    return

  subject = subject_record(username)
  send_json(conn, {
      "status": "SUCCESS",
      "message": f"Автентифікація успішна. Політика: Белла–ЛаПадула з категоріями.",
      "subject": subject,
  })
  log_event(
      f"[AUTH] УСПІХ: {username} "
      f"level={subject['level']} cats={subject['categories']}"
  )

  while True:
    req = recv_json(conn)
    if not req:
      log_event(f"[SESSION] {username} відключився.")
      break
    response = handle_command(subject, req)
    send_json(conn, response)
    if response.get("status") == "BYE":
      break


def start_server() -> None:
  seed_objects()
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  server_socket.bind((HOST, PORT))
  server_socket.listen(5)
  print(f"[*] Сервер ЛР7 запущено на {HOST}:{PORT}")
  print("[*] Політика: Белла–ЛаПадула з категоріями (варіант 3)")
  print("[*] Очікування клієнтів...")

  while True:
    conn, addr = server_socket.accept()
    print(f"\n[+] З'єднання: {addr}")
    try:
      handle_client(conn, addr)
    except Exception as e:
      log_event(f"[!] Помилка: {e}")
    finally:
      conn.close()


if __name__ == "__main__":
  start_server()
