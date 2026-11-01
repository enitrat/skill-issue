# Dev boxes are snapshot/restore VMs: the filesystem comes back under a running
# session. A restore leaves the shell holding a cwd whose inode is gone. zsh does
# not fail: it gives up on resolving an absolute path and sets PWD=".", which is
# the "Failed to get current directory: path invalid" message at startup. Every
# later integration then breaks in its own way -- starship cannot render
# $directory, zsh-syntax-highlighting errors on each keystroke -- so recover
# before any of them load.
#
# The absolute-path test is the load-bearing half. `-d $PWD` alone does not
# detect this: PWD is "." by then, and an unlinked directory still has a live
# inode, so `-d .` is true right up until the shell exits.
[[ $PWD == /* && -d $PWD ]] || cd "$HOME"
