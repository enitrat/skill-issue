#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
export HOME="$tmp/home" GIT_CONFIG_NOSYSTEM=1
mkdir -p "$HOME" "$tmp/origin"
git init -q -b main "$tmp/origin"
git -C "$tmp/origin" config user.name Test
git -C "$tmp/origin" config user.email test@example.com
printf 'first\n' > "$tmp/origin/flake.nix"
git -C "$tmp/origin" add flake.nix
git -C "$tmp/origin" commit -qm first
first=$(git -C "$tmp/origin" rev-parse HEAD)
printf 'second\n' > "$tmp/origin/flake.nix"
git -C "$tmp/origin" commit -qam second
second=$(git -C "$tmp/origin" rev-parse HEAD)
export repo_url="$tmp/origin" repo_dir="$HOME/skill-issue"
log() { :; }
checkout=$(sed -n '/^if \[ ! -e "\$repo_dir\/flake.nix" \]; then/,/^git -C "\$repo_dir" reset --quiet --hard FETCH_HEAD/p' "$root/bootstrap/linux.sh")
revision=$first
eval "$checkout"
[ "$(git -C "$repo_dir" rev-parse HEAD)" = "$first" ]
revision=main
eval "$checkout"
[ "$(git -C "$repo_dir" rev-parse HEAD)" = "$second" ]
mkdir -p "$HOME/.nix-profile/bin" "$HOME/.agents"
ln -s "$(command -v jq)" "$HOME/.nix-profile/bin/jq"
cat > "$HOME/.nix-profile/bin/npx" <<'SCRIPT'
#!/usr/bin/env bash
if [ "$3" = add ]; then
    if [ "${FAIL_INSTALL:-}" = 1 ]; then printf '[{"name":"kept","status":"failed"}]\n'; exit 0; fi
    printf '%s\n' "$4" > "$HOME/source"
    printf '[{"name":"kept","status":"installed"}]\n'
else
    printf '%s\n' "$4" >> "$HOME/removed"
fi
SCRIPT
chmod +x "$HOME/.nix-profile/bin/npx"
cat > "$HOME/.agents/.skill-lock.json" <<JSON
{"skills":{"kept":{"source":"$repo_dir"},"stale":{"source":"$repo_dir"},"old":{"source":"enitrat/skill-issue","skillPath":"skills/old/SKILL.md"},"other":{"source":"someone/else"}}}
JSON
skills=$(sed -n '/^installed=$("\$HOME\/\.nix-profile\/bin\/npx"/,/^fi$/p' "$root/bootstrap/linux.sh")
eval "$skills"
[ "$(cat "$HOME/source")" = "$repo_dir" ]
[ "$(sort "$HOME/removed")" = "$(printf 'old\nstale')" ]

rm "$HOME/removed"
if FAIL_INSTALL=1 bash -e -o pipefail -c "$skills"; then exit 1; fi
[ ! -e "$HOME/removed" ]
