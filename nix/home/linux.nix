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
