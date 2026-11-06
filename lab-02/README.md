# Задание № 2. Анализ объектных файлов

Платформы и среды языков программирования.
Анализ и проверка сборки выполнены в Linux x86_64 с GCC 12.2.0 и GNU binutils 2.40. В предоставленных объектных файлах указана версия компилятора GCC 15.2.0 — это версия их исходной сборки.

## 1. Размеры секций

```text
$ size core.o legacy.o hotfix.o main.o
   text	   data	    bss	    dec	    hex	filename
    266	   4040	  50000	  54306	   d422	core.o
    172	      0	      4	    176	     b0	legacy.o
    127	      0	      0	    127	     7f	hotfix.o
    118	      0	      0	    118	     76	main.o
```

## 2. Почему `.bss` больше самого файла

У `core.o` секция `.bss` занимает 50 000 байт. В ней находится локальный буфер `large_buffer` такого же размера. При этом размер файла — всего 6200 байт:
```text
$ wc -c core.o legacy.o hotfix.o main.o
 6200 core.o
 1608 legacy.o
 1456 hotfix.o
 1448 main.o
10712 total
```
В выводе `readelf -SW core.o` у `.bss` указан тип `NOBITS`:
```text
[ 4] .bss NOBITS 0000000000000000 001048 00c350 00 WA 0 0 32
```
Данные этой секции не хранятся на диске: в файле записаны её размер и другие характеристики. При загрузке программы для неё выделяется область памяти с нулевым содержимым.
В условии неточно описан столбец `dec`: это сумма `text + data + bss`, а не размер файла на диске. Поэтому у `core.o` он равен 54 306 байт и включает все 50 000 байт `.bss`.
COMMON-символы в объектных файлах ещё не размещены в `.bss`. Поэтому у `hotfix.o` в этом столбце стоит 0, а 4 байта `.bss` в `legacy.o` относятся к `legacy_counter`, а не к `system_mode`.

## 3. Секция со строками

Искомая секция — `.rodata`. Она содержит данные только для чтения и есть в `core.o`, но отсутствует в `legacy.o` и `hotfix.o`. В `core.o` её номер — 5, размер — 76 байт.
```text
$ readelf -p .rodata core.o

String dump of section '.rodata':
  [     0]  System Initialized v1.0
  [    20]  FLAG{b1nary_4rch4eology_2026}
  [    3e]  %s, Mode: %d\n
```

## 4. Секретный токен

Токен: `FLAG{b1nary_4rch4eology_2026}`.
Он находится в `.rodata` по смещению `0x20`. Вывод команды извлечения строк:
```text
$ strings -a core.o
System Initialized v1.0
FLAG{b1nary_4rch4eology_2026}
%s, Mode: %d
GCC: (Ubuntu 15.2.0-16ubuntu1) 15.2.0
core.c
large_buffer
internal_cleanup
system_mode
config_table
welcome_msg
secret_token
print_status
printf
.symtab
.strtab
.shstrtab
.rela.text
.data
.bss
.rodata
.rela.data.rel.local
.comment
.note.GNU-stack
.note.gnu.property
.rela.eh_frame
```

## 5. Общие имена символов

```text
$ nm core.o legacy.o hotfix.o main.o

core.o:
0000000000000020 D config_table
0000000000000000 t internal_cleanup
0000000000000000 b large_buffer
0000000000000012 T print_status
                 U printf
0000000000000020 R secret_token
0000000000000000 D system_mode
0000000000000000 D welcome_msg

legacy.o:
000000000000001a T apply_legacy_patch
0000000000000000 b legacy_counter
0000000000000000 t legacy_helper
0000000000000004 C system_mode

hotfix.o:
0000000000000000 T apply_hotfix
0000000000000004 C system_mode

main.o:
                 U apply_hotfix
0000000000000000 T main
                 U print_status
```
В нескольких файлах встречаются:

- `system_mode` — в `core.o`, `legacy.o` и `hotfix.o`;
- `print_status` — в `core.o` и `main.o`;
- `apply_hotfix` — в `hotfix.o` и `main.o`.

## 6. Типы и секции общих символов

Номера секций получены командой `readelf -sW core.o legacy.o hotfix.o main.o`.

| Символ | Файл | Тип в `nm` | `Ndx` | Секция |
| --- | --- | --- | --- | --- |
| `system_mode` | `core.o` | `D` | `3` | `.data` |
| `system_mode` | `legacy.o` | `C` | `COM` | COMMON, секция ещё не назначена |
| `system_mode` | `hotfix.o` | `C` | `COM` | COMMON, секция ещё не назначена |
| `print_status` | `core.o` | `T` | `1` | `.text` |
| `print_status` | `main.o` | `U` | `UND` | Внешняя ссылка |
| `apply_hotfix` | `hotfix.o` | `T` | `1` | `.text` |
| `apply_hotfix` | `main.o` | `U` | `UND` | Внешняя ссылка |

У всех трёх записей `system_mode` размер равен 4 байтам. `D` означает определение в секции инициализированных данных, `C` — COMMON-символ, `T` — глобальный символ в секции кода, `U` — символ, не определённый в данном объектном файле.
COMMON здесь имеет привязку `GLOBAL`, а не `WEAK`. Его можно назвать «слабым» лишь условно: обычное определение получает приоритет при компоновке.

## 7. Конфликт `system_mode`

В `hotfix.c` переменная объявлена как `char system_mode[4]`. В `core.o` это четырёхбайтовый объект в `.data`, а в `legacy.o` — четырёхбайтовый COMMON-объект.
По одной таблице символов нельзя отличить `int` от `char[4]`. Но дизассемблирование командой `objdump -dr -Mintel core.o legacy.o hotfix.o` показывает, что:

- `core.o` читает `system_mode` как 32-битное число и выводит его через `%d`;
- `legacy.o` записывает в него 32-битное значение `42`;
- `hotfix.o` записывает четыре отдельных байта: `41 42 43 00`.

Начальное содержимое `system_mode` в `.data` — `01 00 00 00`. Следовательно, код `core` и `legacy` использует переменную как целочисленный режим, вероятнее всего `int`, тогда как `hotfix` использует то же имя для строки.
После компоновки все обращения попадают в одну область памяти. Строка `ABC` перезаписывает число. На x86_64 с порядком байтов little-endian последовательность `41 42 43 00` соответствует числу `4407873`. Это видно при запуске:
```text
$ ./app
System Initialized v1.0, Mode: 1
System Initialized v1.0, Mode: 4407873
```

## 8. Результат компоновки

```bash
gcc -fcommon core.o legacy.o hotfix.o main.o -o app
```
Команда завершилась успешно, без ошибок и предупреждений. Линкер выбрал определение `system_mode` из `core.o`, а COMMON-символы из остальных файлов связал с ним. Типы C при обычной компоновке этих объектных файлов не проверяются, поэтому конфликт массива и числа остался незамеченным.
С флагом `--warn-common` можно получить предупреждения:
```text
$ gcc -Wl,--warn-common core.o legacy.o hotfix.o main.o -o app_warn
/usr/bin/ld: legacy.o: warning: common of `system_mode' overridden by definition from core.o
/usr/bin/ld: hotfix.o: warning: common of `system_mode' overridden by definition from core.o
```

## 9. Секция `system_mode` после компоновки

```text
$ nm -S app | grep system_mode
0000000000004040 0000000000000004 D system_mode
```
Буква `D` означает, что символ оказался в `.data`. Линкер использовал инициализированное определение из `core.o`, которое имеет приоритет над COMMON. Если бы существовали только COMMON-символы, память для них обычно выделялась бы в `.bss`.

## 10. Сборка с `-fno-common` и исправление

Команда из условия:
```bash
gcc -fno-common main.o hotfix.o legacy.o core.o -o app_better
```
тоже завершилась без ошибки. Причина в том, что `-fno-common` влияет на компиляцию исходного кода, а готовые `.o` не изменяет. Чтобы увидеть конфликт определений, нужно сначала перекомпилировать `hotfix.c`:
```bash
gcc -O0 -fno-common -c hotfix.c -o hotfix_nocommon.o
```
Теперь `system_mode` становится обычным глобальным определением в `.bss`:
```text
$ nm -S hotfix_nocommon.o
0000000000000000 0000000000000023 T apply_hotfix
0000000000000000 0000000000000004 B system_mode
```
При компоновке возникает ошибка:
```text
$ gcc -fno-common main.o hotfix_nocommon.o legacy.o core.o -o app_rejected
/usr/bin/ld: warning: alignment 1 of symbol `system_mode' in hotfix_nocommon.o is smaller than 4 in legacy.o
/usr/bin/ld: core.o:(.data+0x0): multiple definition of `system_mode'; hotfix_nocommon.o:(.bss+0x0): first defined here
collect2: error: ld returned 1 exit status
```
Если строка должна храниться отдельно от общего числового режима, конфликт устраняется добавлением `static`, без изменения имени переменной:
```c
static char system_mode[4];

void apply_hotfix(void) {
    system_mode[0] = 'A';
    system_mode[1] = 'B';
    system_mode[2] = 'C';
    system_mode[3] = '\0';
}
```
Теперь массив доступен только внутри `hotfix.c` и не совпадает с глобальным числовым режимом из `core.o`. Исправленный код сохранён в [hotfix_fixed.c](hotfix_fixed.c).
Проверка:
```bash
gcc -O0 -Wall -Wextra -Werror -fno-common -c hotfix_fixed.c -o hotfix_fixed.o
gcc -fno-common main.o hotfix_fixed.o legacy.o core.o -o app_fixed
```
Обе команды завершились успешно. После запуска общий режим больше не меняется:
```text
$ ./app_fixed
System Initialized v1.0, Mode: 1
System Initialized v1.0, Mode: 1
```
Такой вариант подходит для отдельного строкового буфера. Если `hotfix` должен менять именно общий режим, нужно объявить `extern int system_mode` и присваивать допустимое числовое значение вместо строки. Замена на `extern char system_mode[4]` убрала бы повторное определение, но сохранила ошибку с перезаписью числа.
В готовом `legacy.o` COMMON-символ остаётся: успешная компоновка с `-fno-common` не означает его отсутствия. Для исправления на уровне исходного кода нужно также заменить определение в `legacy.c` согласованным `extern`-объявлением и перекомпилировать этот модуль; его исходник по условию недоступен.
