# Платформы и среды языков программирования — лабораторная № 1

## Файлы для проверки

- [answers.md](answers.md) — ответы на вопросы, ассемблерный код функций и результаты выполнения команд.
- [simple.cpp](simple.cpp) — исходный код задачи A из условия.
- [legacy.c](legacy.c) — читаемая работающая программа проверки для задачи B.
- [flag.txt](flag.txt) — восстановленный флаг с переводом строки.
- [legacy_original.c](legacy_original.c) — исходный артефакт задачи B без изменений.
- [recover_flag.py](recover_flag.py) — скрипт восстановления флага из исходного артефакта.
- [build.sh](build.sh) — этапы сборки и проверки.

## Сборка и проверка

Окружение эксперимента: Linux x86_64, GCC 14.4.0. Нужны GCC/G++ и Bash; для скрипта восстановления — Python 3. Intel-синтаксис ассемблера требует x86.
```bash
bash build.sh
python3 recover_flag.py
```
Либо через Docker, включая macOS и ARM:
```bash
docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work gcc:14 bash build.sh
```
