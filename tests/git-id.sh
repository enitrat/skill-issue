#!/usr/bin/env bash
set -euo pipefail
script=$(cd "$(dirname "$0")/.." && pwd)/tools/git-id
home=$(mktemp -d)
trap 'rm -rf "$home"' EXIT
export HOME="$home" GIT_CONFIG_NOSYSTEM=1
cd "$home"
git config --global include.path "$home/.gitconfig.local"
name='Jane "$(touch exploited)" Doe'
"$script" add work "$name" jane@example.com
"$script" list > /dev/null
[ ! -e exploited ]
"$script" work
[ "$(git config user.name)" = "$name" ]
[ "$(git config user.email)" = jane@example.com ]
printf 'GIT_NAME="$(touch legacy-exploited)"\nGIT_EMAIL="old@example.com"\nSSH_KEY=""\nSIGNING_KEY=""\n' > "$home/.git-identities/old.conf"
"$script" list > /dev/null
[ ! -e legacy-exploited ]
"$script" old
[ "$(git config user.name)" = '$(touch legacy-exploited)' ]
if "$script" add ../escape Name email; then exit 1; fi
if "$script" rm ../escape; then exit 1; fi
before=$(cat "$home/.gitconfig.local")
real_git=$(command -v git)
mkdir "$home/bin"
cat > "$home/bin/git" <<'WRAPPER'
#!/usr/bin/env bash
if [[ ${1-} = config && ${2-} = --file && ${4-} = --replace-all && ${5-} = user.email ]]; then exit 1; fi
exec "$REAL_GIT" "$@"
WRAPPER
chmod +x "$home/bin/git"
if REAL_GIT="$real_git" PATH="$home/bin:$PATH" "$script" work; then exit 1; fi
[ "$(cat "$home/.gitconfig.local")" = "$before" ]
mkdir -p "$home/.ssh"
ssh-keygen -q -t ed25519 -N '' -f "$home/.ssh/id_test"
"$script" add signed 'Signed User' signed@example.com '' id_test
"$script" signed
"$script" verify
before=$(cat "$home/.gitconfig.local")
git config --global user.email overridden@example.com
ssh-keygen -q -t ed25519 -N '' -f "$home/.ssh/id_other"
"$script" add other 'Other User' other@example.com '' id_other
signers_before=$(cat "$home/.config/git/allowed_signers")
if "$script" other; then exit 1; fi
[ "$(cat "$home/.config/git/allowed_signers")" = "$signers_before" ]
if "$script" work; then exit 1; fi
[ "$(cat "$home/.gitconfig.local")" = "$before" ]
git config --global --unset user.email
mv "$home/.config/git/allowed_signers" "$home/signers-backup"
mkdir "$home/.config/git/allowed_signers"
if "$script" other; then exit 1; fi
[ "$(cat "$home/.gitconfig.local")" = "$before" ]
rmdir "$home/.config/git/allowed_signers"
mv "$home/signers-backup" "$home/.config/git/allowed_signers"
git config --global tag.gpgsign false
if "$script" signed; then exit 1; fi
[ "$(cat "$home/.gitconfig.local")" = "$before" ]
git config --global --unset tag.gpgsign
"$script" add keyed 'Keyed User' keyed@example.com id_test
git config --global core.sshCommand 'ssh -i wrong-key'
if "$script" keyed; then exit 1; fi
[ "$(cat "$home/.gitconfig.local")" = "$before" ]
git config --global --unset core.sshCommand
mv "$home/.gitconfig.local" "$home/config-target"
ln -s "$home/config-target" "$home/.gitconfig.local"
if "$script" work; then exit 1; fi
[ -L "$home/.gitconfig.local" ]
[ "$(cat "$home/config-target")" = "$before" ]
rm "$home/.gitconfig.local"
mkdir "$home/.gitconfig.local"
if "$script" work; then exit 1; fi
