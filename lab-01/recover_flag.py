"""Recover list lengths and invert the seven operations in legacy_original.c."""
from pathlib import Path
import re

root = Path(__file__).resolve().parent
source = (root / 'legacy_original.c').read_text()
initializer = source.split('S*a[1024]={', 1)[1].split('};S*p;', 1)[0]
lengths = [len(re.findall(r'\bz\s*\(', item))
           for item in initializer.split(',') if item.strip()]
assert len(lengths) == 1024
operations = [lambda x: x ^ 99, lambda x: x ^ 48,
              lambda x: x * 16, lambda x: x * 4,
              lambda x: x * 55, lambda x: x + 97, lambda x: x + 44]
recovered = []
for index, value in enumerate(lengths[:896]):
    candidates = [x for x in range(128) if operations[index % 7](x) == value]
    assert len(candidates) == 1
    recovered.append(candidates[0])
assert all(value == 0 for value in lengths[896:])
print(bytes(recovered).split(b'\0', 1)[0].decode(), end='')
