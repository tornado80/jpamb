{
  description = "JPAMB: Java Program Analysis Micro Benchmarks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/23.05";
    flake-utils.url = "github:numtide/flake-utils";
    jvm2json.url = "github:kalhauge/jvm2json";
  };
  outputs = {
    self,
    nixpkgs,
    flake-utils,
    jvm2json,
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
            jvm2json.packages.${system}.default
            (python3.withPackages (p: with p; [click pandas]))
          ];
        };
      };
    });
}
