# Git worktrees addressed by branch name instead of by path.
#
# The point is running several checkouts of one repo at once -- an agent on a
# feature branch, a review of someone else's PR, and main -- without stashing
# between them. `wt` creates one, `wtcd` jumps to one, `wtr` removes it and its
# branch together, which is the step that otherwise gets forgotten.
#
# Sorts after 40-completions on purpose: the compdefs at the bottom need
# compinit to have defined compdef already.

# Where worktrees live: $WT_DIR if set, otherwise beside the main checkout.
# Siblings rather than children, so a worktree is never inside the repo it
# belongs to -- git tolerates that, but every tool that walks the tree does not.
__wt_dir() {
    if [[ -n ${WT_DIR-} ]]; then
        print -r -- "${WT_DIR:A}"
        return
    fi

    local common
    common=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1

    # Bare-root layout: .bare/ and every worktree sit in one directory, so the
    # parent of .bare is already the right answer. Detecting it means the same
    # commands work in both layouts without a per-repo $WT_DIR.
    [[ ${common:t} == .bare ]] && { print -r -- "${common:h}"; return }

    local top
    top=$(git rev-parse --show-toplevel 2>/dev/null) || return 1
    print -r -- "${top:h}"
}

# What a new branch should be cut from, as something git can resolve.
#
# Preferring origin/<default> over the local branch is the point: branching
# from a local main that is fifty commits behind is the mistake this is here to
# avoid. But each candidate is tested rather than assumed -- a repo with no
# remote at all is a normal thing to be standing in, and guessing origin/main
# there fails with "not a valid object name" instead of doing the obvious.
__wt_base() {
    local b
    b=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
    b=${${b#origin/}:-main}

    local candidate
    for candidate in "origin/$b" "$b" HEAD; do
        if git rev-parse --verify --quiet "${candidate}^{commit}" >/dev/null; then
            print -r -- "$candidate"
            return
        fi
    done
    return 1
}

# Directory names cannot carry the slash in feat/foo without nesting a level
# that wtr then has to clean up, so flatten it.
__wt_slug() { print -r -- "${1//\//-}" }

# Absolute paths of the current repo's worktrees, for completion and fzf.
__wt_paths() {
    git worktree list --porcelain 2>/dev/null | awk '/^worktree /{print substr($0, 10)}'
}

# wt <branch> [base] -- new branch, new worktree, in one step.
wt() {
    local branch=${1-} base=${2-}
    [[ -n $branch ]] || { print -ru2 "usage: wt <branch> [base]"; return 1 }

    local dir
    dir=$(__wt_dir) || return 1
    [[ -n $base ]] || base=$(__wt_base) || return 1

    # --no-track is load-bearing. Branching from origin/main otherwise sets the
    # new branch's upstream to origin/main, and since push.autoSetupRemote only
    # fills in a *missing* upstream, a later bare `git push` would push the
    # feature branch straight at main. Without an upstream, autoSetupRemote
    # creates origin/<branch> on the first push, which is what was meant.
    git worktree add --no-track -b "$branch" "$dir/$(__wt_slug "$branch")" "$base"
}

# wtd <branch> [dir] -- detached checkout of a remote branch, for reading it.
# Detached and not tracking: reviewing a PR should not leave behind a local
# branch that then shows up in every branch listing and needs deleting.
wtd() {
    local branch=${1-} name=${2-}
    [[ -n $branch ]] || { print -ru2 "usage: wtd <branch> [dir]"; return 1 }

    local dir
    dir=$(__wt_dir) || return 1
    [[ -n $name ]] || name=$(__wt_slug "$branch")

    git fetch origin "$branch" || return 1
    git worktree add --detach "$dir/$name" "origin/$branch"
}

# wtcd [dir] -- jump to a worktree. Bare, it picks one interactively.
wtcd() {
    local dir target=${1-}
    dir=$(__wt_dir) || return 1

    if [[ -z $target ]]; then
        command -v fzf >/dev/null 2>&1 || {
            print -ru2 "usage: wtcd <dir>"
            return 1
        }
        target=$(__wt_paths | fzf --select-1 --exit-0 --header 'worktree') || return 1
        [[ -n $target ]] || return 1
        cd -- "$target"
        return
    fi

    # An absolute or relative path that exists wins over the name lookup, so
    # `wtcd .` and a tab-completed path both behave the way they read.
    [[ -d $target ]] && { cd -- "$target"; return }
    cd -- "$dir/$target"
}

# wtr [-k] <dir> -- remove a worktree, and its branch unless -k keeps it.
wtr() {
    local keep=0
    while [[ ${1-} == -* ]]; do
        case $1 in
            -k|--keep) keep=1; shift ;;
            --) shift; break ;;
            *) print -ru2 "wtr: unknown option $1"; return 1 ;;
        esac
    done

    [[ -n ${1-} ]] || { print -ru2 "usage: wtr [-k|--keep] <dir>"; return 1 }

    local dir tree
    dir=$(__wt_dir) || return 1
    if [[ $1 == /* || -d $1 ]]; then
        tree=${1:A}
    else
        tree=${dir}/$1
    fi

    # Read the branch before removing the worktree; afterwards there is nothing
    # left to ask. Empty for the detached checkouts wtd creates.
    local branch
    branch=$(git -C "$tree" symbolic-ref --quiet --short HEAD 2>/dev/null)

    git worktree remove "$tree" || return 1

    # -d and not -D: a branch with unmerged work should refuse to disappear
    # just because its worktree was cleaned up.
    (( keep )) || [[ -z $branch ]] || git branch -d "$branch"
}

wtl() { git worktree list "$@" }
wtp() { git worktree prune -v "$@" }

# Complete wtcd/wtr on the worktree directory names that actually exist.
_wt_dirs() {
    local -a dirs
    dirs=(${(f)"$(__wt_paths)"})
    compadd -- ${dirs:t}
}
# Guarded for the same half-provisioned case 40-completions allows for: with
# neither oh-my-zsh nor compinit, compdef is undefined and this would be the
# only line in the file that errors.
(( $+functions[compdef] )) && compdef _wt_dirs wtcd wtr
