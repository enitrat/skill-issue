# Linux dev boxes: Boat sandboxes and other throwaway Ubuntu VMs, used as `user`.
{
  config,
  lib,
  pkgs,
  ...
}:
{
  home.username = "user";
  home.homeDirectory = "/home/user";
  skillIssue.repo = "/home/user/skill-issue";

  # Not NixOS: sets XDG_DATA_DIRS and friends so the distro and Nix coexist.
  targets.genericLinux = {
    enable = true;
    # Headless boxes: the GPU shim alone is over 1 GB of mesa.
    gpu.enable = false;
  };
  # Every locale is 222 MB that each Boat start downloads again; these two are used.
  i18n.glibcLocales = pkgs.glibcLocales.override {
    allLocales = false;
    locales = [
      "en_US.UTF-8/UTF-8"
      "C.UTF-8/UTF-8"
    ];
  };

  # Boat restores /home/user through a FUSE layer that it swaps for the local disk once
  # the download ends. A socket made before the swap stops answering, so herdr's live
  # in /tmp, which Boat never restores. herdr creates the directory.
  home.sessionVariables.HERDR_SOCKET_PATH = "/tmp/herdr-user/herdr.sock";

  # Playwright's default, ~/.cache/ms-playwright, is not kept in a Boat snapshot, so a
  # box would download its browsers again.
  home.sessionVariables.PLAYWRIGHT_BROWSERS_PATH = "$HOME/.local/share/ms-playwright";

  # Standalone home-manager manages its own CLI.
  programs.home-manager.enable = true;

  programs.zsh.shellAliases = {
    localip = "hostname -I | awk '{print $1}'";
    # Apply this repo's config. nh cannot guess the output name: it would look
    # for user@<hostname>, and outputs are named by architecture instead.
    rebuild = "nh home switch ${config.skillIssue.repo} -c user@${pkgs.stdenv.hostPlatform.system}";
  };

  # In .zshenv, so non-interactive `ssh box cmd` gets it too, not only herdr panes.
  programs.zsh.envExtra = builtins.readFile ./zsh/boat-env.zsh;

  # Runs before every integration, which is the point: see the file.
  programs.zsh.initContent = lib.mkBefore (builtins.readFile ./zsh/ephemeral-host.zsh);
}
