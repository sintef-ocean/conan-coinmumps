[![GCC Conan](https://github.com/sintef-ocean/conan-coinmumps/workflows/GCC%20Conan/badge.svg)](https://github.com/sintef-ocean/conan-coinmumps/actions?query=workflow%3A"GCC+Conan")
[![Clang Conan](https://github.com/sintef-ocean/conan-coinmumps/workflows/Clang%20Conan/badge.svg)](https://github.com/sintef-ocean/conan-coinmumps/actions?query=workflow%3A"Clang+Conan")
[![MSVC Conan](https://github.com/sintef-ocean/conan-coinmumps/workflows/MSVC%20Conan/badge.svg)](https://github.com/sintef-ocean/conan-coinmumps/actions?query=workflow%3A"MSVC+Conan")
[![Download](https://api.bintray.com/packages/sintef-ocean/conan/coinmumps%3Asintef/images/download.svg)](https://bintray.com/sintef-ocean/conan/coinmumps%3Asintef/_latestVersion)


[Conan.io](https://conan.io) recipe for [coinmumps](http://mumps.enseeiht.fr).

This recipe is made with the help of `coin-or` builder repository [ThirdParty-Mumps](https://github.com/coin-or-tools/ThirdParty-Mumps).
The recipe generates library packages, which can be found at [Bintray](https://bintray.com/sintef-ocean/conan/coinmumps%3Asintef).
The package is usually consumed using the `conan install` command or a *conanfile.txt*.

## How to use this package

1. Add remote to conan's package [remotes](https://docs.conan.io/en/latest/reference/commands/misc/remote.html?highlight=remotes):

   ```bash
   $ conan remote add sintef https://api.bintray.com/conan/sintef-ocean/conan
   ```

2. Using *conanfile.txt* in your project with *cmake*

   Add a [*conanfile.txt*](http://docs.conan.io/en/latest/reference/conanfile_txt.html) to your project. This file describes dependencies and your configuration of choice, e.g.:

   ```
   [requires]
   coinmumps/[>=4.10.0]@sintef/stable

   [options]
   coinmumps:shared=True

   [imports]
   licenses, * -> ./licenses @ folder=True

   [generators]
   cmake_paths
   cmake_find_package
   ```

   Insert into your *CMakeLists.txt* something like the following lines:
   ```cmake
   cmake_minimum_required(VERSION 3.13)
   project(TheProject CXX)

   include(${CMAKE_BINARY_DIR}/conan_paths.cmake)
   find_package(coinmumps MODULE REQUIRED)

   add_executable(the_executor code.cpp)
   target_link_libraries(the_executor coinmumps::coinmumps)
   ```
   Then, do
   ```bash
   $ mkdir build && cd build
   $ conan install .. -s build_type=<build_type>
   ```
   where `<build_type>` is e.g. `Debug` or `Release`.
   You can now continue with the usual dance with cmake commands for configuration and compilation. For details on how to use conan, please consult [Conan.io docs](http://docs.conan.io/en/latest/)

## Package options

Option | Default | Domain
---|---|---
shared  | True | [True, False]
fPIC | True | [True, False]

## Known recipe issues

  - This recipe does not yet build mumps on Windows
