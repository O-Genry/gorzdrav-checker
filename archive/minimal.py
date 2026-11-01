import truststore
truststore.inject_into_ssl()

import requests
import time
import winsound

LPU_ID = "250"
SPECIALITY_ID = "211"          # ваша нужная специальность
BASE = "https://gorzdrav.spb.ru/_api/api/v2/schedule"

seen_slots = set()

# ANSI-коды для красного жирного текста в Windows Terminal / PowerShell
RED_BOLD = "\033[1;31m"
RESET = "\033[0m"

def big_red(text: str) -> str:
    return f"{RED_BOLD}{text}{RESET}"

def check():
    url = f"{BASE}/lpu/{LPU_ID}/speciality/{SPECIALITY_ID}/doctors"
    try:
        data = requests.get(url, timeout=30).json()
    except Exception as e:
        print(f"[!] Ошибка запроса списка врачей: {e}")
        return

    doctors = data.get("result", [])
    if not doctors:
        print(f"[{time.strftime('%H:%M:%S')}] Список врачей пуст.")
        return

    new_found = False
    total_now = 0
    new_count = 0
    new_blocks = []

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

        slots = appt_data.get("result", [])
        for s in slots:
            total_now += 1
            slot_id = s.get("id")
            if slot_id in seen_slots:
                continue
            seen_slots.add(slot_id)
            new_count += 1
            new_found = True

            start = s.get("visitStart", "")
            end = s.get("visitEnd", "")
            room = s.get("room") or "?"
            num = s.get("number")
            new_blocks.append(
                f"  👨‍⚕️ {name}\n"
                f"     🗓  {start} – {end}\n"
                f"     🚪 каб. {room}   🎫 талон №{num}"
            )

    if new_found:
        print()
        print(big_red("🚨🚨  ПОЯВИЛСЯ НОВЫЙ ТАЛОН!  🚨🚨"))
        for block in new_blocks:
            print(block)
        print()
        winsound.Beep(1000, 700)
        print(f"[{time.strftime('%H:%M:%S')}] Всего талонов сейчас: {total_now}, новых: {new_count}.")
    elif total_now == 0:
        print(f"[{time.strftime('%H:%M:%S')}] Талонов нет.")
    else:
        print(f"[{time.strftime('%H:%M:%S')}] Всего талонов сейчас: {total_now}, новых: 0.")

if __name__ == "__main__":
    try:
        while True:
            check()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")