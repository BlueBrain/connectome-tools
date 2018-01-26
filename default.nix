# Nix development environment
#
# source <bbp-nixpkgs>/sourcethis.sh
#
# nix-build
# nix-shell
#
with import <nixpkgs> {};
{
  connectome-tools = connectome-tools.overrideDerivation (oldAtr: rec {
    version = "DEV_ENV";
    src = ./.;
  });
}
