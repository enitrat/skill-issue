# Workarounds for hosts that are snapshot/restore VMs rather than real machines:
# the filesystem comes back mid-session and the hostname is regenerated at every
# boot. Everything in this file is dead weight on a laptop, so it only lands on
# hosts that opt in -- see `ephemeral_host` in .chezmoidata/host.toml and the
# guard in .chezmoiignore. Retiring the last such host means setting the flag
# back to false; deleting this file removes the behaviour entirely.
#
# A restore leaves the shell holding a cwd whose inode is gone. zsh does not
# fail: it gives up on resolving an absolute path and sets PWD=".", which is the
# "Failed to get current directory: path invalid" message at startup. Every later
# fragment then breaks in its own way -- mise's chpwd hook warns on each prompt,
# starship cannot render $directory, zsh-syntax-highlighting errors on each
# keystroke -- so recover before any of them load.
#
# The absolute-path test is the load-bearing half. `-d $PWD` alone does not
# detect this: PWD is "." by then, and an unlinked directory still has a live
# inode, so `-d .` is true right up until the shell exits.
[[ $PWD == /* && -d $PWD ]] || cd "$HOME"
