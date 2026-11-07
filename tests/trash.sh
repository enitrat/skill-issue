#!/bin/bash
set -euo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
export HOME="$work/home" XDG_DATA_HOME="$work/data"
mkdir -p "$HOME" "$work/a" "$work/b" "$work/c"

for n in a b c; do printf '%s\n' "$n" >"$work/$n/file"; done
"$repo/tools/trash" "$work/a/file" "$work/b/file" "$work/c/file"
if [ "$(uname)" = Darwin ]; then
    trash="$HOME/.Trash"
else
    trash="$XDG_DATA_HOME/Trash/files"
fi
test "$(find "$trash" -name file -type f -exec cat {} \; | sort)" = "$(printf 'a\nb\nc')"

ln -s nowhere "$trash/link"
ln -s original "$work/link"
"$repo/tools/trash" "$work/link"
test "$(readlink "$trash/link")" = nowhere
test "$(readlink "$trash"/item.*/link)" = original

mkdir "$work/a/dir" "$work/b/dir"
printf a >"$work/a/dir/a"
printf b >"$work/b/dir/b"
"$repo/tools/trash" "$work/a/dir" "$work/b/dir"
test "$(find "$trash" -name a -type f -exec cat {} \;)" = a
test "$(find "$trash" -name b -type f -exec cat {} \;)" = b

printf already >"$trash/already"
"$repo/tools/trash" "$trash/already"
test "$(cat "$trash"/item.*/already)" = already

long_name=$(printf '%0250d' 0)
printf long >"$work/$long_name"
"$repo/tools/trash" "$work/$long_name"
test "$(cat "$trash"/item.*/"$long_name")" = long

mkdir "$work/d" "$work/e"
printf 'd\n' >"$work/d/race"
printf 'e\n' >"$work/e/race"
"$repo/tools/trash" "$work/d/race" &
first=$!
"$repo/tools/trash" "$work/e/race" &
second=$!
wait "$first" "$second"
test "$(find "$trash" -name race -type f -exec cat {} \; | sort)" = "$(printf 'd\ne')"
