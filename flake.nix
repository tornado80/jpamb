{
  description = "JPAMB: Java Program Analysis Micro Benchmarks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/23.05";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = {
    self,
    nixpkgs,
    flake-utils,
    ...
  } @ inputs:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {inherit system;};
    in {
      devShells = {
        default = pkgs.mkShell {
          name = "jpamb";
          packages = with pkgs; [
            jdt-language-server
            jdk
            maven
            (python3.withPackages (p: with p; []))
          ];
        };
      };
    });
}
