# macOS client laptops: system settings and GUI apps. The user's shell and CLI
# tools come from nix/home (common.nix + darwin.nix).
{ pkgs, ... }:
let
  user = "msaug";
in
{
  system.stateVersion = 6;
  system.primaryUser = user;
  users.users.${user}.home = "/Users/${user}";

  # Determinate Nix manages the Nix installation and daemon itself.
  nix.enable = false;

  # Touch ID for sudo. `reattach` makes it work inside herdr and tmux panes too,
  # whose server runs outside the login session.
  security.pam.services.sudo_local = {
    touchIdAuth = true;
    reattach = true;
  };

  # --- Apps -------------------------------------------------------------------
  # Homebrew itself. A Mac that already has Homebrew needs `autoMigrate = true`
  # for its first switch only.
  nix-homebrew = {
    enable = true;
    inherit user;
  };
  homebrew = {
    enable = true;
    # "check" refuses to switch while something installed is not declared here,
    # so nothing is ever removed silently. Declare it or uninstall it by hand.
    onActivation.cleanup = "check";
    taps = [ "penso/tap" ];
    casks = [
      # Daily tools
      "1password"
      "1password-cli"
      "bitwarden"
      "cursor"
      "visual-studio-code"
      "iterm2"
      "orbstack" # free for personal use; commercial use needs a paid license
      "raycast"
      "tailscale-app"
      "penso/tap/herdr-gpui"
      "android-platform-tools"
      "localsend"

      # Communication and notes
      "slack"
      "telegram" # native macOS client; "telegram-desktop" is the Qt build
      "discord"
      "notion"
      "obsidian"

      # Design, media, AI
      "figma"
      "spotify"
      "chatgpt"
      "aside"
      "monologue"
      "typeless"
      "tldraw" # tldraw offline

      # Other
      "ledger-wallet"
      "windscribe"
      "hiddenbar" # hide menu-bar icons around the notch
      "font-meslo-lg-nerd-font" # installs as "MesloLGS NF"
    ];
    masApps = {
      Amphetamine = 937984704;
      WhatsApp = 310633997;
    };
    # Manual installs: Grok Bot, Scrawl and Canon Utilities have no cask; the
    # darktable cask is disabled (fails Gatekeeper); Blender is pinned at 4.x
    # by hand, while the cask is 5.x.
  };

  # --- System defaults ----------------------------------------------------------
  # Most take effect at the next login.
  system.defaults = {
    NSGlobalDomain = {
      # Content moves with the scroll wheel, not with the fingers. It is one
      # global setting, so an external mouse inverts with it.
      "com.apple.swipescrolldirection" = false;
      AppleWindowTabbingMode = "always";
    };
    # Tighter menu bar spacing so icons stop sliding behind the notch. Apple's own
    # icons only honour these under com.apple.controlcenter.
    CustomUserPreferences."com.apple.controlcenter" = {
      NSStatusItemSpacing = 6;
      NSStatusItem2ExtensionMinPadding = 6;
    };
  };

  # Release Cmd+Space from Spotlight so Raycast can take it. Edited key by key:
  # writing the AppleSymbolicHotKeys dict through `defaults` would replace every
  # other symbolic hotkey with it. Raycast's own hotkey stays a manual setting.
  system.activationScripts.postActivation.text = ''
    sudo -u ${user} ${pkgs.bash}/bin/bash ${./scripts/spotlight-hotkey.sh}
  '';
}
