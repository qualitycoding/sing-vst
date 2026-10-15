#!/usr/bin/env bash
# Spike (C-056): T-034 switches to a German locale; on Ubuntu 24.04 de_DE.UTF-8 must be generated first.
# Usage: bash run.sh <scratch dir>  > output.txt 2>&1   (needs root or sudo for localedef/locale-gen)
set -u
S=${1:?dir}; mkdir -p "$S"
echo "== before: $(locale -a | tr '\n' ' ')"
printf '#include <clocale>\n#include <cstdio>\nint main(){const char* n[]={"de_DE.UTF-8","de_DE.utf8"};for(auto s:n){if(std::setlocale(LC_ALL,s)){std::printf("setlocale %%s ok, decimal point [%%s]\\n",s,std::localeconv()->decimal_point);return 0;}}std::puts("setlocale failed");return 1;}\n' > "$S/l.cpp"
g++ -std=c++20 -o "$S/l" "$S/l.cpp" && "$S/l"; echo "exit before $?"
if [ "$(id -u)" = 0 ]; then localedef -i de_DE -f UTF-8 de_DE.UTF-8; else sudo locale-gen de_DE.UTF-8; fi; echo "localedef exit $?"
echo "== after: $(locale -a | tr '\n' ' ')"
"$S/l"; echo "exit after $?"
