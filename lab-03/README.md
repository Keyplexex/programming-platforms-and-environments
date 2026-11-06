# Лабораторная № 3. Статические и динамические библиотеки

Платформы и среды языков программирования. Среда: Linux x86_64, Debian 12, GCC/G++ 12.2.0, GNU binutils 2.40.

## 1. Статическая библиотека

Сборка:
```bash
gcc -c vector_math.c -o vector_math.o
ar rcs libmath_static.a vector_math.o
g++ -c main.cpp -o main.o
g++ main.o -L. -lmath_static -o app_static
```
Все команды завершились успешно. При запуске получен результат:
```text
$ ./app_static
Library version: v2.4.1-release
Dot product result: 32
```
Скалярное произведение равно `1·4 + 2·5 + 3·6 = 32`. Здесь статически подключена именно `libmath_static.a`; это не полностью статический исполняемый файл, поскольку системные библиотеки по-прежнему подключаются динамически.

### 1.1. Флаги `ar` и повторный запуск

- `r` — добавляет объектный файл в архив или заменяет существующий элемент с тем же именем.
- `c` — подавляет предупреждение о создании нового архива; при обновлении отсутствующего архива он создаётся и без этого флага.
- `s` — создаёт или обновляет индекс символов, используемый компоновщиком.

После повторного выполнения `ar rcs libmath_static.a vector_math.o` объект заменяется, а не добавляется второй раз. Остальные элементы архива сохраняются. Проверка после двух запусков:
```text
$ ar t libmath_static.a
vector_math.o
```
### 1.2. Почему `main` не подверглась name mangling

```text
$ nm main.o
                 U _GLOBAL_OFFSET_TABLE_
000000000000011e t _GLOBAL__sub_I_main
00000000000000cc t _Z41__static_initialization_and_destruction_0ii
                 U _ZNSolsEPFRSoS_E
                 U _ZNSolsEi
                 U _ZNSt8ios_base4InitC1Ev
                 U _ZNSt8ios_base4InitD1Ev
                 U _ZSt4cout
                 U _ZSt4endlIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_
0000000000000000 b _ZStL8__ioinit
                 U _ZStlsISt11char_traitsIcEERSt13basic_ostreamIcT_ES5_PKc
                 U __cxa_atexit
                 U __dso_handle
                 U dot_product
                 U get_lib_version
0000000000000000 T main
```
`main` имеет специальное назначение: её вызывает код запуска программы. В используемом GCC/Linux для неё сохраняется имя `main`, которое ожидает стартовый код. При этом точка входа ELF обычно называется `_start`, а не `main`.
Обычные функции C++ кодируют в имени сведения о функции и типах параметров, что позволяет различать перегрузки. Имена `dot_product` и `get_lib_version` в этом выводе тоже не изменены, но уже по другой причине — их объявления находятся в блоке `extern "C"`.

## 2. Динамическая библиотека

### 2.1. Сборка без `-fPIC`

Выполнены команды из условия:
```bash
gcc -c vector_math.c -o vector_math_nopic.o
gcc -shared -o libmath_broken.so vector_math_nopic.o
```
В этой среде обе команды завершились с кодом 0, без сообщений об ошибке. Поэтому привести ожидаемую в условии ошибку для исходного файла нельзя: она не возникла.
Причина в конкретном коде: `LIB_VERSION` объявлена как `static`, то есть имеет внутреннее связывание, а `dot_product` работает с переданными указателями и локальными переменными. На x86_64 получившиеся обращения к локальным данным подходят для разделяемой библиотеки и без явно указанного `-fPIC`.
В выводе `readelf -rW vector_math_nopic.o` видны, в частности, такие перемещения:
```text
Relocation section '.rela.text' at offset 0x240 contains 1 entry:
    Offset             Info             Type               Symbol's Value  Symbol's Name + Addend
0000000000000007  0000000400000002 R_X86_64_PC32          0000000000000000 .data.rel.local - 4

Relocation section '.rela.data.rel.local' at offset 0x258 contains 1 entry:
    Offset             Info             Type               Symbol's Value  Symbol's Name + Addend
0000000000000000  0000000300000001 R_X86_64_64            0000000000000000 .rodata + 0
```
Первое обращение относительно счётчика команд разрешается внутри библиотеки, а адрес строки находится в секции данных. Перемещений, требующих правки машинного кода при загрузке, здесь не появилось: у готовой библиотеки нет тега `TEXTREL`.
Для `.so` всё равно следует использовать `-fPIC`: он явно задаёт генерацию позиционно-независимого кода. Успешная сборка этого небольшого примера не означает, что любой код можно собирать без него.

Для дополнительной проверки в отдельной копии `vector_math_global.c` убрано только слово `static` перед `LIB_VERSION`. Исходный файл задания не менялся. После `gcc -c vector_math_global.c -o vector_math_global.o` попытка собрать `.so` уже дала ошибку:
```text
$ gcc -shared -o libmath_global.so vector_math_global.o
/usr/bin/ld: vector_math_global.o: warning: relocation against `LIB_VERSION' in read-only section `.text'
/usr/bin/ld: vector_math_global.o: relocation R_X86_64_PC32 against symbol `LIB_VERSION' can not be used when making a shared object; recompile with -fPIC
/usr/bin/ld: final link failed: bad value
collect2: error: ld returned 1 exit status
```
Перекомпиляция этой копии с `-fPIC` устранила ошибку. Этот вывод относится к дополнительному опыту, а не к исходному коду задания.

### 2.2. Сборка с `-fPIC` и сравнение размеров

```bash
gcc -c -fPIC vector_math.c -o vector_math_pic.o
gcc -shared -o libmath_dynamic.so vector_math_pic.o
g++ main.o -L. -lmath_dynamic -o app_dynamic
```
Сборка прошла успешно. Для запуска указана папка с библиотекой:
```text
$ LD_LIBRARY_PATH=. ./app_dynamic
Library version: v2.4.1-release
Dot product result: 32
```
Флаг `-L.` задаёт путь поиска на этапе компоновки, но сам по себе не добавляет его в пути поиска загрузчика. Поэтому при запуске здесь используется `LD_LIBRARY_PATH=.`.
```text
$ size app_static app_dynamic
   text	   data	    bss	    dec	    hex	filename
   2649	    664	    280	   3593	    e09	app_static
   2594	    688	    280	   3562	    dea	app_dynamic
```
Столбец `text` уменьшился с 2649 до 2594 байт, то есть на 55 байт. Это суммарный размер кода и учитываемых `size` данных только для чтения, а не только секции `.text`.
В статическом варианте код функций скопирован из архива в исполняемый файл. В динамическом он остаётся в `libmath_dynamic.so`, которую загружает ОС. В исполняемом файле остаются ссылки на функции и служебные структуры динамического связывания. Поэтому разность размеров не обязана совпадать с размером машинного кода двух функций.
Проверка символов:
```text
$ nm app_static | grep -E 'dot_product|get_lib_version'
00000000000012b9 T dot_product
00000000000012ac T get_lib_version
$ nm -D app_dynamic | grep -E 'dot_product|get_lib_version'
                 U dot_product
                 U get_lib_version
$ nm -D libmath_dynamic.so | grep -E 'dot_product|get_lib_version'
0000000000001106 T dot_product
00000000000010f9 T get_lib_version
```
`T` означает определение в секции кода, а `U` — отсутствие определения в данном файле. В динамическом варианте определения обеих функций находятся в `.so`.

## 3. Порядок компоновки

При размещении библиотеки перед объектным файлом получена ошибка:
```text
$ g++ -L. -lmath_dynamic main.o -o app_wrong_order
/usr/bin/ld: main.o: in function `main':
main.cpp:(.text+0x50): undefined reference to `get_lib_version'
/usr/bin/ld: main.cpp:(.text+0xa1): undefined reference to `dot_product'
collect2: error: ld returned 1 exit status
```
Правильный порядок:
```bash
g++ main.o -L. -lmath_dynamic -o app_correct
```
```text
$ LD_LIBRARY_PATH=. ./app_correct
Library version: v2.4.1-release
Dot product result: 32
```
Для объяснения используются множества:

- `U` — неразрешённые ссылки;
- `D` — уже найденные определения символов;
- `E` — объектные файлы, включённые в результат, в том числе извлечённые из архивов.

Рассмотрим только символы нашей библиотеки. Когда `main.o` стоит первым, он включается в `E`, его определения добавляются в `D`, а `get_lib_version` и `dot_product` попадают в `U`. При последующем просмотре библиотеки находятся нужные определения, и эти ссылки разрешаются.
Если первой стоит библиотека, ссылок на её функции в `U` ещё нет. В используемой конфигурации G++ включён `--as-needed` — это подтверждено выводом `g++ -###`. Поэтому `libmath_dynamic.so` на этом шаге не сохраняется как необходимая зависимость. Когда затем обрабатывается `main.o`, обе ссылки добавляются в `U`, но библиотека автоматически повторно не рассматривается. В конце они остаются неразрешёнными.
Для статического архива модель `E` буквальная: компоновщик извлекает из `.a` объектные файлы, удовлетворяющие текущим ссылкам из `U`. Из `.so` объектные файлы не извлекаются: здесь похожий результат связан с отбором динамических зависимостей через `--as-needed`.
Без этой настройки обратный порядок для данной `.so` сработал:
```bash
g++ -Wl,--no-as-needed -L. -lmath_dynamic main.o -o app_no_as_needed
```
Команда завершилась успешно; программа также вывела версию `v2.4.1-release` и результат `32`. Таким образом, для динамической библиотеки ошибка порядка зависит от настроек линкера. Правило «сначала объектные файлы, затем библиотеки» позволяет избежать этой проблемы.

## 4. Name mangling и `extern "C"`

Для опыта в папке `noextern` созданы копии `main.cpp` и `vector_math.h`. Из копии заголовка удалены оба блока `#ifdef __cplusplus`: открывающий `extern "C" {` и закрывающий `}`. Объявления функций и защита от повторного включения оставлены. Затем заново скомпилирован именно C++-файл:
```bash
cd noextern
g++ -c main.cpp -o main.o
g++ main.o -L.. -lmath_dynamic -o app_no_extern
```
Вывод последней команды:
```text
$ g++ main.o -L.. -lmath_dynamic -o app_no_extern
/usr/bin/ld: main.o: in function `main':
main.cpp:(.text+0x50): undefined reference to `get_lib_version()'
/usr/bin/ld: main.cpp:(.text+0xa1): undefined reference to `dot_product(int const*, int const*, int)'
collect2: error: ld returned 1 exit status
```
Имена в новом объектном файле:
```text
$ nm main.o | grep dot
                 U _Z11dot_productPKiS0_i
```
```text
$ nm main.o | grep get_lib_version
                 U _Z15get_lib_versionv
```
Имена в библиотеке, собранной компилятором C:
```text
$ nm ../libmath_dynamic.so | grep dot
0000000000001106 T dot_product
```
```text
$ nm ../libmath_dynamic.so | grep get_lib_version
00000000000010f9 T get_lib_version
```
После удаления `extern "C"` компилятор C++ ожидает `_Z11dot_productPKiS0_i` и `_Z15get_lib_versionv`, а библиотека экспортирует `dot_product` и `get_lib_version`. Для линкера это разные имена.
В `_Z11dot_productPKiS0_i` закодированы имя `dot_product` и параметры `const int*`, `const int*`, `int`. В `_Z15get_lib_versionv` число `15` — длина имени, а `v` означает отсутствие параметров. Команда `nm -C` показывает имена в читаемом виде:
```text
$ nm -C main.o | grep -E 'dot_product|get_lib_version'
                 U dot_product(int const*, int const*, int)
                 U get_lib_version()
```
`extern "C"` задаёт C-связывание объявленным функциям, благодаря чему C++-код использует те же имена, что и библиотека на C. Обычное ключевое слово `extern` перед `get_lib_version` не заменяет `extern "C"`.
Для исправления нужно вернуть оба блока `#ifdef __cplusplus` в заголовок и перекомпилировать `main.cpp`. В основной папке сохранены исходные файлы с рабочим `extern "C"`; опыты с удалением выполнялись только в копии.
