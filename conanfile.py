from conans import AutoToolsBuildEnvironment, ConanFile, tools
from conans.tools import PkgConfig
from conans.errors import ConanInvalidConfiguration
from os import path, unlink


class CoinMumpsConan(ConanFile):
    name = "coinmumps"
    version = "4.10.0"
    license = ("CeCILL-C",)
    author = "SINTEF Ocean"
    url = "https://github.com/sintef-ocean/conan-coinmumps"
    homepage = "http://mumps.enseeiht.fr"
    description =\
        "MUltifrontal Massively Parallel sparse direct Solver"
    topics = ("Sparse direct solver")
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": True, "fPIC": True}
    generators = "pkg_config"
    requires = (
        "openblas/[>=0.3.12]",
        "coinmetis/4.0.3@sintef/stable")

    _coin_helper = "ThirdParty-Mumps"
    _coin_helper_branch = "stable/2.0"
    _autotools = None

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools

        with tools.environment_append({"PKG_CONFIG_PATH": self.build_folder}):
            self._autotools = AutoToolsBuildEnvironment(self)  # win_bash=True

            pkg_openblas = PkgConfig("openblas")
            pkg_coinmetis = PkgConfig("coinmetis")
            auto_args = []
            auto_args.append(
                "--with-lapack={}".format(" ".join(pkg_openblas.libs)))
            auto_args.append(
                "--with-metis-lflags={}".format(" ".join(pkg_coinmetis.libs)))
            auto_args.append(
                "--with-metis-cflags={}".format(" ".join(pkg_coinmetis.cflags)))

            # Not relevant until mumps 5
            # self.output.warn("setting --with-intsize=64")
            # auto_args.append("--with-intsize=64")


            self._autotools.configure(args=auto_args)
            return self._autotools

    def configure(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration(
                "This recipe is does not support Visual Studio")

        self.options["openblas"].shared = self.options.shared
        self.options["openblas"].build_lapack = True
        # self.options["openblas"].use_thread = True
        # self.options["openblas"].dynamic_arch = True

        if self.settings.compiler == "gcc" and \
           int(self.settings.compiler.get_safe("version")) >= 10:
            self.output.warn(
                "If you are using gfortran >= 10; set environment FC=gfortran")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):

        _git = tools.Git()
        _git.clone("https://github.com/coin-or-tools/{}.git"
                   .format(self._coin_helper),
                   branch=self._coin_helper_branch,
                   shallow=True)

        self.run("./get.Mumps")

    def build(self):
        autotools = self._configure_autotools()
        autotools.make()

    def package(self):
        autotools = self._configure_autotools()
        autotools.install()

        tools.rmdir(path.join(self.package_folder, "lib", "pkgconfig"))
        unlink(path.join(self.package_folder, "lib", "libcoinmumps.la"))
        self.copy("LICENCE", src="MUMPS", dst="licenses")

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "MUMPS"
        self.cpp_info.libs = ["coinmumps"]
        self.cpp_info.includedirs = [path.join("include", "coin-or", "mumps")]

    def system_requirements(self):

        installer = tools.SystemPackageTool()
        debian_based = (tools.os_info.linux_distro == "ubuntu" or
                        tools.os_info.linux_distro == "debian")

        if tools.os_info.is_linux and debian_based:
            installer.install("dos2unix")
