# Модель Белла–ЛаПадули з категоріями (варіант 3).
# Рівні секретності + множини категорій. Право власника — окрема перевірка.

LEVELS = {
    "UNCLASSIFIED": 0,
    "CONFIDENTIAL": 1,
    "SECRET": 2,
    "TOP_SECRET": 3,
}

LEVEL_NAMES = {v: k for k, v in LEVELS.items()}

# Не менше 4 прав, включно з правом власника.
RIGHTS = ("OWN", "READ", "WRITE", "APPEND")


def parse_level(value) -> int:
  if isinstance(value, int):
    return value
  key = str(value).upper().replace(" ", "_")
  if key not in LEVELS:
    raise ValueError(f"Невідомий рівень секретності: {value}")
  return LEVELS[key]


def dominates(high_level: int, high_cats, low_level: int, low_cats) -> bool:
  """(L_h, C_h) домінує над (L_l, C_l), якщо L_h >= L_l і C_l ⊆ C_h."""
  return high_level >= low_level and set(low_cats).issubset(set(high_cats))


def check_right(subject: dict, obj: dict, right: str) -> tuple[bool, str]:
  """
  Повертає (дозволено, пояснення).

  ss-властивість (немає читання вгору):
      READ  — суб'єкт домінує над об'єктом.
  *-властивість (немає запису вниз):
      WRITE / APPEND — об'єкт домінує над суб'єктом.
  OWN — лише власник об'єкта (видалення).
  """
  right = right.upper()
  if right not in RIGHTS:
    return False, f"Невідоме право: {right}"

  s_level = parse_level(subject["level"])
  o_level = parse_level(obj["level"])
  s_cats = set(subject.get("categories") or [])
  o_cats = set(obj.get("categories") or [])

  if right == "OWN":
    if subject["username"] == obj.get("owner"):
      return True, "Право власника: суб'єкт є власником об'єкта."
    return False, "Відмовлено: суб'єкт не є власником об'єкта."

  if right == "READ":
    if dominates(s_level, s_cats, o_level, o_cats):
      return True, (
          "ss-властивість: рівень і категорії суб'єкта домінують "
          "над міткою об'єкта (немає читання вгору)."
      )
    if s_level < o_level:
      return False, (
          "Порушення ss-властивості (no read-up): рівень суб'єкта "
          f"{LEVEL_NAMES[s_level]} нижчий за {LEVEL_NAMES[o_level]}."
      )
    return False, (
        "Порушення ss-властивості: категорії об'єкта не є підмножиною "
        "категорій суб'єкта."
    )

  # WRITE та APPEND
  if dominates(o_level, o_cats, s_level, s_cats):
    return True, (
        "*-властивість: мітка об'єкта домінує над суб'єктом "
        "(немає запису вниз)."
    )
  if o_level < s_level:
    return False, (
        "Порушення *-властивості (no write-down): рівень об'єкта "
        f"{LEVEL_NAMES[o_level]} нижчий за рівень суб'єкта "
        f"{LEVEL_NAMES[s_level]}."
    )
  return False, (
      "Порушення *-властивості: категорії суб'єкта не є підмножиною "
      "категорій об'єкта (запис розширив би «need-to-know»)."
  )


def allowed_rights(subject: dict, obj: dict) -> list[str]:
  return [r for r in RIGHTS if check_right(subject, obj, r)[0]]
