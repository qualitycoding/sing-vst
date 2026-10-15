#!/usr/bin/env bash
# Spike (C-055): what `cmake --build --parallel` passes to make with the Unix Makefiles generator.
# Usage: bash run.sh <empty dir>  > output.txt 2>&1
set -u
S=${1:?dir}; mkdir -p "$S/src"; cd "$S"
printf 'cmake_minimum_required(VERSION 3.22)\nproject(p C)\nadd_executable(a a.c)\n' > src/CMakeLists.txt
echo 'int main(void){return 0;}' > src/a.c
printf '#!/bin/sh\necho "MAKE ARGS: $*" >> %s/args.txt\nexec /usr/bin/make "$@"\n' "$S" > mk.sh; chmod +x mk.sh
cmake --version | head -1
cmake -S src -B b -G "Unix Makefiles" -DCMAKE_MAKE_PROGRAM="$S/mk.sh" > /dev/null
echo "== cmake --build b --parallel";   cmake --build b --parallel > /dev/null;   tail -1 args.txt
echo "== cmake --build b --parallel 4"; cmake --build b --parallel 4 > /dev/null; tail -1 args.txt
