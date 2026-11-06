#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
g++ -E simple.cpp -o simple.i
g++ -S -masm=intel -O0 simple.cpp -o simple_O0.s
g++ -S -masm=intel -O2 simple.cpp -o simple_O2.s
g++ -c simple_O0.s -o simple.o
g++ simple.o -o simple
./simple
gcc -std=c11 -Wall -Wextra -Werror legacy.c -o legacy
./legacy < flag.txt
printf 'Correct flag: accepted\n'
if printf 'wrong\n' | ./legacy; then
    printf 'ERROR: wrong flag accepted\n'; exit 1
fi
if ./legacy < /dev/null; then
    printf 'ERROR: empty input accepted\n'; exit 1
fi
printf 'Wrong and empty input: rejected\n'
