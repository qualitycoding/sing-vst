#!/usr/bin/env bash
# Bootstraps the pinned C++ test environment outside the repository (PK-20, lesson L-20261009T161500Z).
# Usage: bash tools/bootstrap_test_env.sh <deps dir>     (idempotent; safe to re-run)
# Produces: <deps>/JUCE (tag 9.0.3), <deps>/Catch2 (tag v3.16.1), <deps>/ort (onnxruntime 1.31.0, SHA-256 checked),
# and prints the cmake configure line. Pins: plan/ENVIRONMENT.md.
set -euo pipefail
DEPS=${1:?usage: bootstrap_test_env.sh <deps dir>}; mkdir -p "$DEPS"; cd "$DEPS"
clone() { # dir url tag commit — the tag must still resolve to the pinned commit (else DR-02) and the clone must sit on it
  if [ ! -d "$1/.git" ]; then git clone -q --depth 1 --branch "$3" "$2" "$1"; fi
  tag=$(git ls-remote "$2" "refs/tags/$3^{}" | cut -f1); [ -n "$tag" ] || tag=$(git ls-remote "$2" "refs/tags/$3" | cut -f1)
  if [ "$tag" != "$4" ]; then echo "tag $3 of $2 now resolves to $tag, pinned $4: DR-02" >&2; exit 4; fi
  have=$(git -C "$1" rev-parse HEAD)
  if [ "$have" != "$4" ]; then echo "$1 is at $have, pinned $3 is $4: delete $DEPS/$1 and re-run" >&2; exit 3; fi
  echo "ok $1 @ $3 ($have)"
}
clone JUCE https://github.com/juce-framework/JUCE.git 9.0.3 be29c81492b6151c8ea8d14c840e1311963b3a83
clone Catch2 https://github.com/catchorg/Catch2.git v3.16.1 08092139210881f01a34e60c5f2fd6afa0ea4024
case "$(uname -s)" in
  Linux) PKG=onnxruntime-linux-x64-1.31.0.tgz; SHA=cc5c72baf5ae5c8238a6841f0897227be2d02826b9cf98eaf02fdefaeeb03a57 ;;
  *) echo "use the CI workflow on this platform" >&2; exit 2 ;;
esac
if [ ! -f ort/include/onnxruntime_c_api.h ]; then
  curl -sSfL -o "$PKG" "https://github.com/microsoft/onnxruntime/releases/download/v1.31.0/$PKG"
  echo "$SHA  $PKG" | sha256sum -c -
  rm -rf ort && mkdir ort && tar xzf "$PKG" -C ort --strip-components 1
fi
echo "JUCE $(git -C JUCE rev-parse HEAD)"; echo "Catch2 $(git -C Catch2 rev-parse HEAD)"; echo "ORT $(ls ort/lib/libonnxruntime.so.*.*.*)"
echo "configure: cmake -S <repo> -B <build> -DCMAKE_BUILD_TYPE=Release -DSINGVST_BUILD_PLUGIN=OFF -DFETCHCONTENT_SOURCE_DIR_JUCE=$DEPS/JUCE -DFETCHCONTENT_SOURCE_DIR_CATCH2=$DEPS/Catch2 -DSINGVST_ORT_DIR=$DEPS/ort"
