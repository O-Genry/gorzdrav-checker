# gorzdrav-checker

Следит за появлением свободных талонов на gorzdrav.spb.ru и печатает их в консоль.

## Установка

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

## Настройка

Скопируйте `.env.example` в `.env` и при необходимости поменяйте:
- `LPU_ID` — ID поликлиники (из URL: `...lpu%22:%22250%22...`)
- `SPECIALITY_ID` — ID специальности (из URL: `...speciality%22:%22211%22...`)
- `CHECK_INTERVAL_SEC` — интервал проверки в секундах

## Запуск

    python checker.py

Найденные талоны пишутся в `logs/tickets.log`.