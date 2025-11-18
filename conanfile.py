import os
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.files import (
    get, copy, rename, rmdir, rm,
    apply_conandata_patches, export_conandata_patches
    )
from conan.tools.gnu import (
    Autotools, AutotoolsDeps, AutotoolsToolchain,
    PkgConfig, PkgConfigDeps
    )
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path
from conan.tools.system.package_manager import Apt


class CoinMumpsConan(ConanFile):
    name = "coinmumps"
    license = ("CeCILL-C",)
    author = "SINTEF Ocean"
    url = "https://github.com/sintef-ocean/conan-coinmumps"
    homepage = "https://github.com/coin-or-tools/ThirdParty-Mumps"
    description =\
        "MUltifrontal Massively Parallel sparse direct Solver"
    topics = ("solver", "sparse", "direct", "parallel", "linear-algebra")
    settings = "os", "compiler", "build_type", "arch"
    package_type = "library"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "precision": ["single", "double", "all"],
        "with_64bit_int": [True, False],
        "with_lapack": [True, False],
        "with_metis": [True, False],
        "with_openmp": [True, False],
        "with_openmpi": [True, False],
        "with_pthread": [True, False],

    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "precision": "double",
        "with_64bit_int": False,
        "with_lapack": True,
        "with_metis": True,
        "with_openmp": False,
        "with_openmpi": False,
        "with_pthread": True,
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

        self.options["metis"].with_64bit_types = self.options.with_64bit_int
        if self.settings.os == "Windows":
            self.options["msys2"].additional_packages = "mingw-w64-ucrt-x86_64-gcc-fortran"

    def requirements(self):
        if self.options.with_openmpi:
            self.requires("openmpi/4.1.6")
        if self.options.with_lapack:
            self.requires("openblas/0.3.30")
        if self.options.with_metis:
            self.requires("metis/5.2.1")
        if self.options.with_openmp and not self.settings.os == "Windows":
            if not self.settings.compiler == "gcc":
                self.requires("llvm-openmp/20.1.6")
        if self.options.with_pthread:
            self.requires("pthreads4w/3.0.0")

    def validate(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration("This recipe is not tested with MSVC")

        if self.options.with_lapack and not self.dependencies["openblas"].options.build_lapack:
            raise ConanInvalidConfiguration("MUMPS requires openblas with build_lapack=True")

    def build_requirements(self):
        self.tool_requires("gnu-config/cci.20210814")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if self._settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")
        if is_msvc(self):
            self.tool_requires("automake/1.16.5")

    def layout(self):
        basic_layout(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["build_scripts"], strip_root=True)
        get(self, **self.conan_data["sources"][self.version]["source"], destination="MUMPS", strip_root=True)

    def generate(self):
        at = AutotoolsDeps(self)
        at.generate()

        deps = PkgConfigDeps(self)
        deps.generate()
        yes_no = lambda v: "yes" if v else "no"
        bit_32_64 = lambda with64: "64" if with64 else "32"

        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            f"--enable-shared={yes_no(self.options.shared)}",
            f"--enable-static={yes_no(not self.options.shared)}",
            f"--enable-pthread-mumps={yes_no(self.options.with_pthread)}",
            f"--enable-openmp={yes_no(self.options.with_openmp)}",
            f"--with-lapack={yes_no(self.options.with_lapack)}",
            f"--with-metis={yes_no(self.options.with_metis)}",
            f"--with-precision={self.options.precision}",
            f"--with-intsize={bit_32_64(self.options.with_64bit_int)}",
        ])
        gen_dir = os.path.join(self.build_folder, "conan")
        if self.options.with_lapack:
            dep_info = self.dependencies["openblas"].cpp_info.aggregated_components()
            lib_flags = " ".join([f"-l{lib}" for lib in dep_info.libs + dep_info.system_libs])
            tc.configure_args.append(f"--with-lapack-lflags=-L{dep_info.libdir} {lib_flags}")
        if self.options.with_metis:
            metis = PkgConfig(self, "metis", pkg_config_path=gen_dir)
            tc.configure_args.extend([
                "--with-metis-cflags=" + " ".join(["-I" + " -I".join(metis.includedirs),
                                                   "-D" + " -D".join(metis.defines)]),
                "--with-metis-lflags=" + " ".join(["-L" + " -L".join(metis.libdirs),
                                                   "-l" + " -l".join(metis.libs)]),
            ])

        env = tc.environment()

        if is_msvc(self):
            compile_wrapper = unix_path(self, self.conf.get("user.automake:compile-wrapper", check_type=str))
            ar_wrapper = unix_path(self, self.conf.get("user.automake:lib-wrapper", check_type=str))
            env.define("CC", f"{compile_wrapper} cl -nologo")
            env.define("CXX", f"{compile_wrapper} cl -nologo")
            env.define("LD", f"{compile_wrapper} link -nologo")
            env.define("AR", f"{ar_wrapper} lib")
            env.define("NM", "dumpbin -symbols")
            env.define("OBJDUMP", ":")
            env.define("RANLIB", ":")
            env.define("STRIP", ":")

        tc.generate(env)

    def _patch_sources(self):
        # https://github.com/coin-or-tools/ThirdParty-Mumps/blob/releases/3.0.11/get.Mumps#L62-L67
        apply_conandata_patches(self)
        rename(self,
               os.path.join(self.source_folder, "MUMPS", "libseq", "mpi.h"),
               os.path.join(self.source_folder, "MUMPS", "libseq", "mumps_mpi.h"))

    def build(self):
        self._patch_sources()
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.install()

        lic_dest = os.path.join(self.package_folder, "licenses")
        copy(self, "LICENSE", os.path.join(self.source_folder, "MUMPS"), lic_dest)
        rename(self, os.path.join(lic_dest, "LICENSE"), os.path.join(lic_dest, "LICENSE-Mumps"))
        copy(self, "LICENSE", os.path.join(self.source_folder), lic_dest)
        rename(self, os.path.join(lic_dest, "LICENSE"), os.path.join(lic_dest, "LICENSE-ThirdParty-Mumps"))

        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "coinmumps")
        self.cpp_info.libs = ["coinmumps"]
        self.cpp_info.includedirs.append(os.path.join("include", "coin-or"))
        self.cpp_info.includedirs.append(os.path.join("include", "coin-or", "mumps"))
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m"])
            # Assumes gfortran
            self.cpp_info.system_libs.extend(["gfortran", "quadmath"])

            if self.options.with_pthread:
                self.cpp_info.system_libs.extend(["pthread"])
        if self.settings.os == "Windows" and self.options.with_pthread:
            self.cpp_info.requires.append("pthreads4w:pthreads4w")

        if self.options.with_openmpi:
            self.cpp_info.requires.append("openmpi::ompi-c")
        if self.options.with_lapack:
            self.cpp_info.requires.append("openblas::openblas")
        if self.options.with_metis:
            self.cpp_info.requires.append("metis::metis")
        if self.options.with_openmp:
            if self.settings.compiler == "gcc":
                self.cpp_info.system_libs.extend(["gomp"])
            elif not self.settings.os == "Windows":
                self.cpp_info.requires.append("llvm-openmp::llvm-openmp")

    def system_requirements(self):
        Apt(self).install(["dos2unix"])
        if self.settings.compiler == "gcc":
            # Depends on gcc version..
            Apt(self).install(["libgfortran5", "libquadmath0"])
            if self.options.with_openmp:
                # May change..
                Apt(self).install(["libgomp1"])
