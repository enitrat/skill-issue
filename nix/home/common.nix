# Everything a macOS client and a Linux dev box share. Platform files
# (darwin.nix, linux.nix) add only what truly differs.
{
  config,
  lib,
  pkgs,
  ...
}:
let
  inherit (pkgs.stdenv.hostPlatform) isDarwin;
  repo = config.skillIssue.repo;
in
{
  options.skillIssue.repo = lib.mkOption {
    type = lib.types.str;
    description = "Absolute path of this repository's checkout on the machine. tools/ is linked from it, so edits there are live.";
  };

  config = {
    home.stateVersion = "26.05";

    home.packages = with pkgs; [
      # Search and files. Agents call these more than people do.
      ripgrep
      fd
      jq

      # Runtimes and package managers. Project-specific versions belong in the
      # project's own devShell, not here.
      nodejs
      pnpm
      bun
      uv

      # Agents and their tooling
      herdr
      agent-browser

      # Everything else in daily use
      tmux
      ffmpeg-headless # full ffmpeg pulls in SDL, GTK and gstreamer
      foundry
      linear-cli

      # Nix itself: `nh` switches with a diff, `nvd` diffs two generations.
      nh
      nvd
    ];

    home.sessionVariables = {
      EDITOR = "vim";
      LANG = "en_US.UTF-8";
      CLAUDE_CODE_DISABLE_AUTO_MEMORY = "1";
      # ripgrep reads no config file unless this points at one. Exported (not an
      # alias) so the rg that agents and editors spawn picks it up too.
      RIPGREP_CONFIG_PATH = "${config.xdg.configHome}/ripgrep/config";
      # Where `pnpm add -g` links binaries.
      PNPM_HOME = if isDarwin then "$HOME/Library/pnpm" else "${config.xdg.dataHome}/pnpm";
    };
    home.sessionPath = [
      "$HOME/.local/bin"
      "$PNPM_HOME"
    ];

    # --- Shell ----------------------------------------------------------------
    programs.zsh = {
      enable = true;
      # Ubuntu's /etc/zsh/zshrc runs compinit before user config can add its
      # completion paths. This has to be set in .zshenv to keep one user-owned pass.
      envExtra = "skip_global_compinit=1";
      autosuggestion.enable = true;
      syntaxHighlighting.enable = true;
      enableCompletion = true;
      completionInit = ''
        autoload -Uz compinit
        compinit -d "''${XDG_CACHE_HOME:-$HOME/.cache}/zsh/zcompdump-$ZSH_VERSION"
      '';
      shellAliases = {
        cat = "bat";
        ls = "eza";
        ll = "eza -la --git";
        tree = "eza --tree";

        ".." = "cd ..";
        "..." = "cd ../..";
        "...." = "cd ../../..";
        "-" = "cd -";

        gp = "git push origin $(git branch --show-current)";
        gc = "git commit";
        gco = "git checkout";
        gcb = "git checkout -b";

        df = "df -h";
        du = "du -h";

        myip = "curl -s ifconfig.me";
        reload = "exec zsh";
        json = "uv run --no-project python -m json.tool";
        zf = "z $(zoxide query -l | fzf)";
        please = "sudo $(fc -ln -1)";
        starkup = "curl --proto '=https' --tlsv1.2 -sSf https://sh.starkup.sh | sh -s --";
      };
      initContent = lib.mkMerge [
        (builtins.readFile ./zsh/functions.zsh)
        (builtins.readFile ./zsh/worktree.zsh)
        (builtins.readFile ./zsh/completions.zsh)
        # Group header in the completion menu, e.g. "Completing file".
        "zstyle ':completion:*' format $'\\e[2;37mCompleting %d\\e[m'"
      ];
    };

    programs.starship = {
      enable = true;
      settings = lib.importTOML ./files/starship.toml;
    };
    programs.zoxide.enable = true;
    programs.fzf = rec {
      enable = true;
      defaultCommand = "fd --type f --hidden --exclude .git";
      fileWidget = {
        command = defaultCommand;
        options = [ "--preview 'bat --color=always --line-range :200 {}'" ];
      };
      changeDirWidget.options = [ "--preview 'eza --tree --level=2 {}'" ];
      # Atuin owns Ctrl-R: its history is searchable and can sync across machines.
      historyWidget.command = "";
    };
    programs.atuin.enable = true;
    programs.carapace = {
      enable = true;
      # Only zsh's own completions as a fallback; the default also bridges fish and
      # bash, which is slower and was never wanted.
      environment.CARAPACE_BRIDGES = "zsh";
    };
    programs.eza.enable = true;
    programs.bat.enable = true;
    programs.direnv = {
      enable = true;
      nix-direnv.enable = true;
      silent = true;
    };

    # --- Git ------------------------------------------------------------------
    programs.git = {
      enable = true;
      lfs.enable = true;
      ignores = [
        ".DS_Store"
        ".AppleDouble"
        "Thumbs.db"
        "*.swp"
        "*.swo"
        "*~"
        ".idea/"
        ".vscode/"
        "!.vscode/extensions.json"
        ".direnv/"
        ".env.local"
      ];
      settings = {
        core = {
          # Native filesystem watcher and untracked cache: `git status` in a big
          # checkout becomes a query instead of a tree walk.
          fsmonitor = true;
          untrackedCache = true;
        };
        # Most recently committed first.
        branch.sort = "-committerdate";
        column.ui = "auto";
        diff = {
          colorMoved = "default";
          algorithm = "histogram";
        };
        # Shows the common ancestor in conflicts.
        merge.conflictstyle = "zdiff3";
        fetch = {
          prune = true;
          writeCommitGraph = true;
        };
        rebase = {
          autosquash = true;
          autostash = true;
          # Move every branch pointing into the rebased range, so stacks survive.
          updateRefs = true;
        };
        rerere.enabled = true;
        push.autoSetupRemote = true;
        init.defaultBranch = "main";
        credential = lib.mkIf isDarwin { helper = "osxkeychain"; };
        alias = {
          rebase-last-five = ''!b="$(git rev-parse --abbrev-ref HEAD)" ; h="$(git rev-parse $b)" ; echo "Current branch: $b $h" ; c="$(git rev-parse $b~4)" ; echo "Recreating $b branch with initial commit $c ..." ; git checkout --orphan new-start $c ; git commit -C $c ; git rebase --onto new-start $c $b ; git branch -d new-start ; git gc'';
          # Catch up to the default branch, read from origin/HEAD rather than assumed.
          fomo = ''!f() { b=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null); b=''${b#origin/}; git fetch origin "''${b:=main}" && git rebase "origin/$b" --autostash; }; f'';
        };
      };
      # Identity and signing live in ~/.gitconfig.local, written by `git-id` and never
      # in the Nix store. Included last so it overrides everything above.
      includes = [ { path = "~/.gitconfig.local"; } ];
    };
    programs.delta = {
      enable = true;
      enableGitIntegration = true;
      options = {
        navigate = true;
        line-numbers = true;
        # Matches the starship prompt palette.
        syntax-theme = "gruvbox-dark";
      };
    };
    programs.mergiraf = {
      enable = true;
      enableGitIntegration = true;
    };
    programs.gh = {
      enable = true;
      gitCredentialHelper.enable = true;
      settings = {
        git_protocol = "https";
        aliases.co = "pr checkout";
      };
    };

    # --- SSH client -----------------------------------------------------------
    programs.ssh = {
      enable = true;
      enableDefaultConfig = false;
      # Machine-local Host blocks (work hosts). Included first because ssh keeps
      # the first value it sees for each option.
      includes = [ "~/.ssh/config.local" ];
      settings."*" = {
        # Reuse one authenticated connection per host. %C keeps the socket path
        # under the macOS 104-character limit.
        ControlMaster = "auto";
        ControlPath = "~/.ssh/sockets/%C";
        ControlPersist = "10m";
        ServerAliveInterval = 30;
        ServerAliveCountMax = 3;
        TCPKeepAlive = "yes";
        HashKnownHosts = "yes";
        AddKeysToAgent = "yes";
      }
      // lib.optionalAttrs isDarwin { UseKeychain = "yes"; };
    };
    # ssh creates neither the ControlMaster socket directory nor a missing Include.
    home.activation.sshDirs = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run mkdir -p "$HOME/.ssh/sockets"
      run chmod 700 "$HOME/.ssh" "$HOME/.ssh/sockets"
      if [ ! -e "$HOME/.ssh/config.local" ]; then
        run install -m 600 /dev/null "$HOME/.ssh/config.local"
      fi
    '';

    # --- Other config files ---------------------------------------------------
    xdg.configFile."ripgrep/config".source = ./files/ripgrep.conf;
    home.file = {
      ".tmux.conf".source = ./files/tmux.conf;
      # Herdr UI is a GUI app without the shell's PATH, and `herdr --remote` probes
      # this path on the other host: both find herdr at its default install location.
      ".local/bin/herdr".source = lib.getExe pkgs.herdr;
    }
    # Repo tools stay live-linked to the checkout, so editing one needs no switch.
    // lib.mapAttrs' (
      name: _:
      lib.nameValuePair ".local/bin/${name}" {
        source = config.lib.file.mkOutOfStoreSymlink "${repo}/tools/${name}";
      }
    ) (builtins.readDir ../../tools);

    # Claude Code rewrites its own settings file, so it cannot be a read-only store
    # link. Each switch copies the repo version over it, keeping the previous one.
    home.activation.claudeSettings = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      target="$HOME/.claude/settings.json"
      if ! cmp -s ${./files/claude-settings.json} "$target"; then
        run mkdir -p "$HOME/.claude"
        [ -e "$target" ] && run cp "$target" "$target.bak"
        run install -m 644 ${./files/claude-settings.json} "$target"
      fi
    '';

    # agent-browser drives its own Chrome for Testing, downloaded once per version.
    home.activation.agentBrowserChrome = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      stamp="${config.xdg.stateHome}/agent-browser-chrome"
      want="${pkgs.agent-browser}"
      if [ "$(cat "$stamp" 2>/dev/null)" != "$want" ]; then
        run ${lib.getExe pkgs.agent-browser} install
        run mkdir -p "$(dirname "$stamp")"
        if [ -z "''${DRY_RUN:-}" ]; then echo "$want" > "$stamp"; fi
      fi
    '';
  };
}
