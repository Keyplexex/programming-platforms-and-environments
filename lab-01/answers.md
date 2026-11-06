# Отчёт по лабораторной работе № 1

## Задача A. Do It Yourself

Окружение: Linux x86_64 в Docker (образ gcc:14), GNU g++ 14.4.0. Дата выполнения: 29 октября 2026 года. Исходный simple.cpp соответствует тексту задания. Значимый вывод выполненных команд приведён ниже.

### Вопрос 1

В simple.cpp было 23 строки, а после препроцессинга в simple.i стало 1100. Количество строк проверено командой wc -l.

### Вопрос 2

main начинается на строке 1095. Над ней находятся остальные функции программы и глобальные переменные. Большую часть файла занимают объявления из `<cstdio>` и других заголовков, которые он подключает. Препроцессор вставил их содержимое вместо #include, поэтому строк стало намного больше.

### Вопрос 3

Строка осталась внутри printf в main, на строке 1098. Её содержимое не изменилось, включая запись `\n`. Значения вместо %d подставляет printf уже при запуске программы.

### Вопрос 4

Без оптимизации файл занимает 2247 байт и 123 строки, с -O2 — 1439 байт и 76 строк. Получается, по размеру файла он стал короче примерно в 1,56 раза, а по числу строк — в 1,62 раза. Здесь сравниваются именно текстовые .s-файлы: помимо инструкций в них есть служебные директивы.

### Вопрос 5

В ассемблерном файле square называется _Z6squarei — так компилятор C++ кодирует имя функции и тип её аргумента. Умножение выполняет imul eax, eax. Перед этим аргумент из edi сохраняется на стек и загружается в eax. Результат функция тоже возвращает через eax.

### Вопрос 6

Перед вызовом sum_of_squares в main стоят инструкции:

```text
mov esi, 4
mov edi, 3
```

То есть первый аргумент, 3, передаётся через edi, а второй, 4, — через esi. Это соответствует соглашению System V AMD64 ABI, которое используется в Linux x86_64. Для аргументов типа int берутся младшие 32 бита rdi и rsi. Результат возвращается через eax.

### Вопрос 7

В полученном файле square сохранилась даже с -O2. У неё внешнее связывание, поэтому компилятор оставил отдельную функцию для возможных вызовов из других файлов. Но внутри sum_of_squares вызовов square уже нет: вместо них стоят два умножения и сложение. В main компилятор сразу подставил 25, потому что аргументы 3 и 4 известны заранее. Увеличение счётчика тоже выполняется прямо в main, без вызова bump_counter. Если сделать square статической, компилятор сможет убрать её отдельное тело, когда после встраивания оно больше не нужно.

### Вопрос 8

В выводе nm у MAGIC стоит строчная r, а не R:

```text
0000000000000000 r _ZL5MAGIC
```

Она находится в .rodata, потому что это константа. Буквы D/d обозначали бы инициализированные данные, которые можно менять. Строчная r объясняется тем, что глобальная const int в C++ по умолчанию имеет внутреннее связывание: эта константа доступна только внутри своего файла.

### Вопрос 9

Команда size показывает размеры основных групп секций объектного файла:

```text
text = 347 байт, data = 0, bss = 4 байта; всего 351 байт.
```

Больше всего занимает text: сюда входят код, данные только для чтения и служебная информация для раскрутки стека. В data здесь ничего нет, а 4 байта в bss отведены под global_counter с начальным значением 0. Это не полный размер файла .o: таблицы символов и другие служебные структуры в эту сумму целиком не входят.

### Вопрос 10

Программа вывела:

```text
Result: 25, Counter: 1, Magic: 42
```

Сумма квадратов 3 и 4 равна 25. После bump_counter счётчик стал равен 1, а значение MAGIC осталось 42.

Команды для этапов сборки:

```bash
g++ -E simple.cpp -o simple.i
g++ -S -masm=intel -O0 simple.cpp -o simple_O0.s
g++ -S -masm=intel -O2 simple.cpp -o simple_O2.s
g++ -c simple_O0.s -o simple.o
g++ simple.o -o simple
./simple
```

При запуске с -S g++ сам повторно выполняет препроцессинг исходного .cpp. Объектный файл собран из полученного simple_O0.s.

### Ассемблерный вывод функций

Фрагменты взяты из полученных simple_O0.s и simple_O2.s. Для читаемости опущены служебные директивы .cfi_* и локальные метки .LFB/.LFE; инструкции функций сохранены без изменений. Синтаксис Intel. .LC0 — метка строки формата для printf.

#### Без оптимизации (`-O0`)

**`square(int)`**

```asm
_Z6squarei:
    push    rbp
    mov rbp, rsp
    mov DWORD PTR [rbp-4], edi
    mov eax, DWORD PTR [rbp-4]
    imul    eax, eax
    pop rbp
    ret
```

**`sum_of_squares(int, int)`**

```asm
_Z14sum_of_squaresii:
    push    rbp
    mov rbp, rsp
    push    rbx
    sub rsp, 8
    mov DWORD PTR [rbp-12], edi
    mov DWORD PTR [rbp-16], esi
    mov eax, DWORD PTR [rbp-12]
    mov edi, eax
    call    _Z6squarei
    mov ebx, eax
    mov eax, DWORD PTR [rbp-16]
    mov edi, eax
    call    _Z6squarei
    add eax, ebx
    mov rbx, QWORD PTR [rbp-8]
    leave
    ret
```

**`bump_counter()`**

```asm
_Z12bump_counterv:
    push    rbp
    mov rbp, rsp
    mov eax, DWORD PTR global_counter[rip]
    add eax, 1
    mov DWORD PTR global_counter[rip], eax
    nop
    pop rbp
    ret
```

**`main()`**

```asm
main:
    push    rbp
    mov rbp, rsp
    sub rsp, 16
    mov esi, 4
    mov edi, 3
    call    _Z14sum_of_squaresii
    mov DWORD PTR [rbp-4], eax
    call    _Z12bump_counterv
    mov edx, DWORD PTR global_counter[rip]
    mov eax, DWORD PTR [rbp-4]
    mov ecx, 42
    mov esi, eax
    mov edi, OFFSET FLAT:.LC0
    mov eax, 0
    call    printf
    mov eax, 0
    leave
    ret
```

#### С оптимизацией (`-O2`)

**`square(int)`**

```asm
_Z6squarei:
    imul    edi, edi
    mov eax, edi
    ret
```

**`sum_of_squares(int, int)`**

```asm
_Z14sum_of_squaresii:
    imul    edi, edi
    imul    esi, esi
    lea eax, [rdi+rsi]
    ret
```

**`bump_counter()`**

```asm
_Z12bump_counterv:
    add DWORD PTR global_counter[rip], 1
    ret
```

**`main()`**

```asm
main:
    sub rsp, 8
    mov eax, DWORD PTR global_counter[rip]
    mov ecx, 42
    mov esi, 25
    mov edi, OFFSET FLAT:.LC0
    lea edx, [rax+1]
    xor eax, eax
    mov DWORD PTR global_counter[rip], edx
    call    printf
    xor eax, eax
    add rsp, 8
    ret
```

Сравнение:

- При -O0 square получает аргумент через edi, сохраняет его на стек, загружает в eax и выполняет imul eax, eax.
- При -O0 sum_of_squares дважды вызывает square и складывает результаты. В main перед вызовом sum_of_squares записаны edi=3 и esi=4.
- При -O2 square сохраняется как отдельная функция, но обходится без стека. sum_of_squares выполняет два умножения без вызовов square.
- При -O2 main сразу передаёт printf результат 25 через esi. Вызовов sum_of_squares и bump_counter в main нет; счётчик увеличивается прямо там. Отдельное тело bump_counter также сохраняется для внешних вызовов.

### Вывод команд

```text
$ wc -l simple.cpp simple.i
   23 simple.cpp
 1100 simple.i

$ wc -c -l simple_O0.s simple_O2.s
 123 2247 simple_O0.s
  76 1439 simple_O2.s

$ nm simple.o
000000000000003c T _Z12bump_counterv
000000000000000f T _Z14sum_of_squaresii
0000000000000000 T _Z6squarei
0000000000000000 r _ZL5MAGIC
0000000000000000 B global_counter
0000000000000052 T main
                 U printf

$ size simple.o
   text    data     bss     dec     hex filename
    347       0       4     351     15f simple.o

$ ./simple
Result: 25, Counter: 1, Magic: 42
```

## Задача B. Наследие

Флаг: `flag{i_considered_giving_only_the_binary_24412707}`

В legacy.c находится упрощённая версия программы проверки. Оригинал сохранён в legacy_original.c, а recover_flag.py восстанавливает из него флаг.

В оригинале числа спрятаны в длинах списков: каждый вызов z добавляет один узел. Всего таким способом записано 1024 числа. Функция df меняет входные данные группами по 7 элементов: XOR с 99, XOR с 48, умножение на 16, на 4, на 55, прибавление 97 и прибавление 44. Она делает 128 проходов, то есть обрабатывает 896 чисел, а последние 128 оставляет как есть. Если выполнить обратные преобразования, получается флаг с переводом строки и нулями после него. В legacy.c та же проверка записана через обычный массив, без списков и макросов, которые затрудняли чтение кода.

```text
$ gcc -std=c11 -Wall -Wextra -Werror legacy.c -o legacy
$ ./legacy < flag.txt; echo $?
0
$ printf 'wrong\n' | ./legacy; echo $?
1
$ ./legacy < /dev/null; echo $?
1
```

Программа ничего не печатает: 0 — верный ввод, 1 — неверный. Вход должен содержать перевод строки после флага (как в flag.txt).
