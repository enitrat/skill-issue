{
  description = "Machine setup: macOS client laptops and Linux dev boxes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nix-darwin = {
      url = "github:nix-darwin/nix-darwin/master";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    nix-homebrew.url = "github:zhaofengli/nix-homebrew";
    nix-index-database = {
      url = "github:nix-community/nix-index-database";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      nixpkgs,
      nix-darwin,
      home-manager,
      nix-homebrew,
      nix-index-database,
      ...
    }:
    let
      overlay = import ./nix/pkgs;

      # Unfree packages allowed by name, on both kinds of machine.
      allowUnfreePredicate = pkg: builtins.elem (nixpkgs.lib.getName pkg) [ "claude-code" ];

      # Everything both kinds of machine get. Platform files add only what differs.
      sharedHome = [
        ./nix/home/common.nix
        nix-index-database.homeModules.default
      ];

      linuxHome =
        system:
        home-manager.lib.homeManagerConfiguration {
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ overlay ];
            config = { inherit allowUnfreePredicate; };
          };
          modules = sharedHome ++ [ ./nix/home/linux.nix ];
        };
    in
    {
      # macOS client: `sudo darwin-rebuild switch --flake .#mac`, or the `rebuild` alias.
      darwinConfigurations.mac = nix-darwin.lib.darwinSystem {
        modules = [
          {
            nixpkgs.hostPlatform = "aarch64-darwin";
            nixpkgs.overlays = [ overlay ];
            nixpkgs.config = { inherit allowUnfreePredicate; };
          }
          ./nix/darwin
          nix-homebrew.darwinModules.nix-homebrew
          home-manager.darwinModules.home-manager
          {
            home-manager.useGlobalPkgs = true;
            home-manager.useUserPackages = true;
            # Files that already exist on the first switch are moved aside, not overwritten.
            home-manager.backupFileExtension = "pre-nix";
            home-manager.users.msaug.imports = sharedHome ++ [ ./nix/home/darwin.nix ];
          }
        ];
      };

      # Linux dev boxes (Boat sandboxes run as `user`): bootstrap/linux.sh, then
      # the `rebuild` alias for later changes.
      homeConfigurations = {
        "user@x86_64-linux" = linuxHome "x86_64-linux";
        "user@aarch64-linux" = linuxHome "aarch64-linux";
      };

      # The home-manager CLI at the version flake.lock pins, for the first switch.
      packages = nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" ] (system: {
        home-manager = home-manager.packages.${system}.default;
      });

      # This repo's own checks (`prek run --all-files`), entered by direnv.
      devShells = nixpkgs.lib.genAttrs [ "aarch64-darwin" "x86_64-linux" "aarch64-linux" ] (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShellNoCC {
            packages = with pkgs; [
              shellcheck
              nixfmt
            ];
          };
        }
      );
    };
}
