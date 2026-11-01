# macOS client laptops: the home-manager half. System settings and apps are in
# nix/darwin/default.nix.
{
  config,
  lib,
  pkgs,
  ...
}:
let
  # iTerm's own shell integration, pinned. Sourced only inside iTerm.
  itermIntegration = pkgs.fetchurl {
    url = "https://raw.githubusercontent.com/gnachman/iTerm2/v3.6.11/Resources/shell_integration/iterm2_shell_integration.zsh";
    sha256 = "91027c6d5221ee7123609e8e5aa8840ea218f98583e516c3d425d5f8a2b20e7a";
  };
in
{
  skillIssue.repo = "/Users/msaug/workspace/skill-issue";

  programs.zsh.profileExtra = ''
    # Homebrew provides the casks' CLIs (op, adb). Appended, so a stray Homebrew
    # copy of a tool can never shadow the Nix one.
    path+=(/opt/homebrew/bin)
    # OrbStack's own integration: docker, orb and friends on PATH.
    source ~/.orbstack/shell/init.zsh 2>/dev/null || :
  '';
  # ...and `ssh orb`.
  programs.ssh.includes = [ "~/.orbstack/ssh/config" ];
  programs.zsh.shellAliases = {
    rebuild = "sudo darwin-rebuild switch --flake ${config.skillIssue.repo}#mac";
    localip = "ipconfig getifaddr en0";
    cpwd = "pwd | pbcopy";
  };

  programs.zsh.initContent = lib.mkAfter ''
    [[ $TERM_PROGRAM == iTerm.app ]] && source ${itermIntegration}

    # Toolchains installed by their own vendor scripts, outside Nix.
    [ -f "$HOME/.starkli/env" ] && . "$HOME/.starkli/env"
    [ -f "$HOME/.vite-plus/env" ] && . "$HOME/.vite-plus/env"
    [ -f "$HOME/.safe-chain/scripts/init-posix.sh" ] && source "$HOME/.safe-chain/scripts/init-posix.sh"
    [ -d "$HOME/.opencode/bin" ] && path=("$HOME/.opencode/bin" $path)
  '';

  home.file = {
    # Emacs-style word movement in every Cocoa text field.
    "Library/KeyBindings/DefaultKeyBinding.dict".source = ../darwin/files/DefaultKeyBinding.dict;
    # A dynamic profile, so iTerm picks it up without its preferences being edited.
    "Library/Application Support/iTerm2/DynamicProfiles/Hotkey Window.json".source =
      ../darwin/files/iterm-hotkey-window.json;
  };

  # Both edit preference files the apps also write, so they merge rather than own.
  home.activation.editorDefaults = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${pkgs.python3}/bin/python3 ${../darwin/scripts/editor-defaults.py}
  '';
  home.activation.itermKeymap = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${pkgs.python3}/bin/python3 ${../darwin/scripts/iterm-keymap.py}
  '';
}
