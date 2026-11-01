# Overlay: packages nixpkgs lacks, and release binaries used in place of slow
# local builds. To update one: change `version`, then each hash
# (`nix store prefetch-file <url>` prints it).
final: _:
let
  releaseBinary = final.callPackage ./release-binary.nix { };
in
{
  # nixpkgs builds atuin from source, and its macOS build is often not cached.
  atuin =
    let
      version = "18.24.4";
      url =
        triple: "https://github.com/atuinsh/atuin/releases/download/v${version}/atuin-${triple}.tar.gz";
    in
    releaseBinary {
      pname = "atuin";
      inherit version;
      sources = {
        aarch64-darwin = {
          url = url "aarch64-apple-darwin";
          hash = "sha256:edd06294377599bf4d85ca3337abc802256a991262260bdd980d1b649583553d";
        };
        x86_64-linux = {
          url = url "x86_64-unknown-linux-gnu";
          hash = "sha256:d5ed5958ef04a4c20cb876feaa7fbad965f6ccd7b997e7ed54e862adec9ce0fc";
        };
        aarch64-linux = {
          url = url "aarch64-unknown-linux-gnu";
          hash = "sha256:5216c5fc98d46c0f99106699f88f122e4a5332e8151f481fdaac408329e3d0c6";
        };
      };
      meta.description = "Shell history in a searchable database, optionally synced";
    };

  # Not in nixpkgs.
  linear-cli =
    let
      version = "3.1.0";
      url =
        triple:
        "https://github.com/schpet/linear-cli/releases/download/v${version}/linear-${triple}.tar.xz";
    in
    releaseBinary {
      pname = "linear-cli";
      inherit version;
      bin = "linear";
      sources = {
        aarch64-darwin = {
          url = url "aarch64-apple-darwin";
          hash = "sha256:bba81cf3ce19f3486f1ada52cf9841a8d749fca716338ea684e6b3b08a706954";
        };
        x86_64-linux = {
          url = url "x86_64-unknown-linux-gnu";
          hash = "sha256:bf7712097ce6a01e8a379de8357eca66d5748050201d336ba787b6ad3687f3e7";
        };
        aarch64-linux = {
          url = url "aarch64-unknown-linux-gnu";
          hash = "sha256:4b0b15b69464e8b6a665290d702817654be2124cf1d58fad7d7ed5754f9431d7";
        };
      };
      meta.description = "Linear from the command line";
    };

  # nixpkgs builds it from source with Node and webpack; not cached on macOS.
  bitwarden-cli =
    let
      version = "2026.10.1";
      url =
        platform:
        "https://github.com/bitwarden/clients/releases/download/cli-v${version}/bw-${platform}-${version}.zip";
    in
    releaseBinary {
      pname = "bitwarden-cli";
      inherit version;
      bin = "bw";
      sources = {
        aarch64-darwin = {
          url = url "macos-arm64";
          hash = "sha256:4e595f9da80ef8b30abca808d0c78a1560d9589466d1bccd2b3e70f321fb12bf";
        };
        x86_64-linux = {
          url = url "linux";
          hash = "sha256:eb09c3715291c21cf744819b873a255c1247b1b8b45bae138621a644ec7ad8f5";
        };
        aarch64-linux = {
          url = url "linux-arm64";
          hash = "sha256:79ecb3293fb259660961c949d3e32fdab8682b2bcff0f6764ce38a411ca1ac5d";
        };
      };
      meta.description = "Bitwarden password manager CLI";
    };
}
