# Package an upstream's prebuilt release binary instead of building it locally.
# Used where nixpkgs lacks a tool, or where its macOS build is often not cached.
{
  stdenvNoCC,
  fetchurl,
  unzip,
}:
{
  pname,
  version,
  # Executable name inside the archive, also the name installed in bin/.
  bin ? pname,
  # Nix system -> fetchurl arguments ({ url; hash; }).
  sources,
  meta ? { },
}:
let
  system = stdenvNoCC.hostPlatform.system;
in
stdenvNoCC.mkDerivation {
  inherit pname version;
  src = fetchurl (sources.${system} or (throw "${pname}: no release binary for ${system}"));
  nativeBuildInputs = [ unzip ];
  # Archives differ: some wrap the binary in a directory, some do not.
  sourceRoot = ".";
  # No strip, no patchelf: deno- and pkg-compiled binaries keep their payload
  # after the executable image, which both corrupt. The loader they expect is
  # there on macOS and Ubuntu.
  dontStrip = true;
  dontPatchELF = true;
  installPhase = ''
    runHook preInstall
    install -Dm755 "$(find . -type f -name ${bin} -print -quit)" $out/bin/${bin}
    runHook postInstall
  '';
  meta = meta // {
    mainProgram = bin;
    platforms = builtins.attrNames sources;
  };
}
