import truststore
truststore.inject_into_ssl()

import requests
import time
import winsound
from collections import OrderedDict
import os
from dotenv import load_dotenv

load_dotenv()

LPU_ID = os.getenv("LPU_ID", "250")
SPECIALITY_ID = os.getenv("SPECIALITY_ID", "211")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SEC", "60"))
BASE = "https://gorzdrav.spb.ru/_api/api/v2/schedule"
LOG_FILE = "tickets.log"

seen_slots = set()

RED_BOLD = "\033[1;31m"
RESET = "\033[0m"

def big_red(text: str) -> str:
    return f"{RED_BOLD}{text}{RESET}"

def find_free_count(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = k.lower()
            if isinstance(v, (int, float)) and ("free" in kl or "count" in kl) and "ticket" in kl:
                return v
            if isinstance(v, (int, float)) and kl in ("countfree", "freecount", "freeticketcount"):
                return v
            res = find_free_count(v)
            if res is not None:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_free_count(item)
            if res is not None:
                return res
    return None

def get_speciality_summary():
    url = f"{BASE}/lpu/{LPU_ID}/specialties"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[!] Ошибка запроса specialties: {e}")
        return None

    items = data.get("result") or data.get("items") or data
    if not isinstance(items, list):
        print("[!] Не удалось разобрать список специальностей.")
        return None

    for spec in items:
        if not isinstance(spec, dict):
            continue
        spec_id = str(spec.get("id") or spec.get("Id") or spec.get("specialityId") or "")
        if spec_id != SPECIALITY_ID:
            continue
        free = find_free_count(spec)
        name = spec.get("name") or spec.get("specName") or spec.get("Name") or "?"
        return {"free": free, "name": name, "raw": spec}

    print(f"[i] Специальность {SPECIALITY_ID} не найдена в списке ЛПУ.")
    return None

def log_tickets(blocks):
    """Пишет найденные талоны в файл с отметкой времени обнаружения."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for doc_name, slots in blocks.items():
            for s in slots:
                f.write(
                    f"{ts} | {doc_name} | {s['start']} – {s['end']} | "
                    f"каб. {s['room']} | талон №{s['num']}\n"
                )

def check_doctors():
    url = f"{BASE}/lpu/{LPU_ID}/speciality/{SPECIALITY_ID}/doctors"
    try:
        data = requests.get(url, timeout=30).json()
    except Exception as e:
        print(f"    [!] Ошибка списка врачей: {e}")
        return False

    doctors = data.get("result", [])
    total_now = 0
    new_found = False
    # OrderedDict: ключ — имя врача, значение — список новых слотов
    new_by_doctor = OrderedDict()

    for doc in doctors:
        doc_id = doc["id"]
        name = doc.get("name", "?")
        appt_url = f"{BASE}/lpu/{LPU_ID}/doctor/{doc_id}/appointments"
        try:
            appt_data = requests.get(appt_url, timeout=30).json()
        except Exception as e:
            print(f"    [!] Ошибка appointments для {name}: {e}")
            continue

        if not appt_data.get("success", False):
            continue

        for s in appt_data.get("result", []):
            total_now += 1
            slot_id = s.get("id")
            if slot_id in seen_slots:
                continue
            seen_slots.add(slot_id)
            new_found = True
            new_by_doctor.setdefault(name, []).append({
                "start": s.get("visitStart", ""),
                "end": s.get("visitEnd", ""),
                "room": s.get("room") or "?",
                "num": s.get("number"),
            })

    if new_found:
        print()
        print(big_red("🚨🚨  ПОЯВИЛСЯ НОВЫЙ ТАЛОН!  🚨🚨"))
        for doc_name, slots in new_by_doctor.items():
            print(f"  👨‍⚕️ {doc_name}")
            for s in slots:
                print(f"     🗓  {s['start']} – {s['end']}   "
                      f"🚪 каб. {s['room']}   🎫 №{s['num']}")
        print()
        winsound.Beep(1000, 700)
        log_tickets(new_by_doctor)
        new_count = sum(len(v) for v in new_by_doctor.values())
        print(f"[{time.strftime('%H:%M:%S')}] Всего талонов сейчас: {total_now}, новых: {new_count}.")
    elif total_now == 0:
        print(f"[{time.strftime('%H:%M:%S')}] Талонов нет (appointments пусты).")
    else:
        print(f"[{time.strftime('%H:%M:%S')}] Всего талонов сейчас: {total_now}, новых: 0.")
    return new_found

def check():
    summary = get_speciality_summary()

    if summary is None:
        print(f"[{time.strftime('%H:%M:%S')}] Сводка недоступна, перехожу к перебору врачей.")
        check_doctors()
        return

    free = summary["free"]
    name = summary["name"]

    if free is None:
        print(f"[{time.strftime('%H:%M:%S')}] {name}: не удалось определить количество, перехожу к перебору врачей.")
        check_doctors()
        return

    if free == 0:
        print(f"[{time.strftime('%H:%M:%S')}] {name}: талонов нет (по сводке).")
        return

    print(f"[{time.strftime('%H:%M:%S')}] {name}: по сводке {free}, проверяю врачей…")
    check_doctors()

if __name__ == "__main__":
    try:
        while True:
            check()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")