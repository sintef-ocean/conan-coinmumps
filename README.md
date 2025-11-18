[![Linux GCC](https://github.com/sintef-ocean/conan-coinmumps/workflows/Linux%20GCC/badge.svg)](https://github.com/sintef-ocean/conan-coinmumps/actions?query=workflow%3A"Linux+GCC")

[Conan.io](https://conan.io) recipe for [coinmumps](http://mumps.enseeiht.fr).

This recipe is made with the help of `coin-or` builder repository [ThirdParty-Mumps](https://github.com/coin-or-tools/ThirdParty-Mumps).

## How to use this package

1. Add remote to conan's package [remotes](https://docs.conan.io/2/reference/commands/remote.html)

   ```bash
   $ conan remote add sintef https://package.smd.sintef.no
   ```

2. Using [*conanfile.txt*](https://docs.conan.io/2/reference/conanfile_txt.html) and *cmake* in your project.

   Add *conanfile.txt*:
   ```
   [requires]
   coinmumps/5.8.1@sintef/stable

   [tool_requires]
   cmake/[>=3.25.0]

   [options]

   [layout]
   cmake_layout

   [generators]
   CMakeDeps
   CMakeToolchain
   VirtualBuildEnv
   ```
   Insert into your *CMakeLists.txt* something like the following lines:
   ```cmake
   cmake_minimum_required(VERSION 3.15)
   project(TheProject CXX)

   find_package(coinmumps REQUIRED)

   add_executable(the_executor code.cpp)
   target_link_libraries(the_executor coinmumps::coinmumps)
   ```
   Install and build e.g. a Release configuration:
   ```bash
   $ conan install . -s build_type=Release -pr:b=default
   $ source build/Release/generators/conanbuild.sh
   $ cmake --preset conan-release
   $ cmake --build build/Release
   $ source build/Release/generators/deactivate_conanbuild.sh
   ```

## Package options

Option | Default | Domain
---|---|---
shared  | False | [True, False]
fPIC | True | [True, False]
precision | double | ["single, "double", "all"]
with_64bit_int | False | [True, False]
with_lapack | True | [True, False]
with_metis | True | [True, False]
with_openmp | False | [True, False]
with_openmpi | False | [True, False]
with_pthread | True [True, False]

## Known recipe issues

  - This recipe does not yet build mumps on Windows
  - There is an issue with static openmpi, so if compiling with `-o "*:shared=False`, add also `-o openmpi*:shared=True`.
  - `pkg-config` must be installed.
