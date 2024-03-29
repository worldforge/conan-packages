import os

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.files import get, replace_in_file, copy, rmdir
from conan.tools.gnu import AutotoolsToolchain, AutotoolsDeps, Autotools
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc


class ReadLineConan(ConanFile):
    version = "8.1.2"
    user = "worldforge"
    name = "readline"
    description = "A set of functions for use by applications that allow users to edit command lines as they are typed in"
    topics = ("cli", "terminal", "command")
    license = "GPL-3.0-only"
    homepage = "https://tiswww.case.edu/php/chet/readline/rltop.html"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_library": ["termcap", "curses"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_library": "termcap",
    }

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_library == "termcap":
            self.requires("termcap/1.3.1")
        elif self.options.with_library == "curses":
            self.requires("ncurses/6.2")

    def configure(self):
        if is_msvc(self):
            # Just skip on win32
            return

        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        get(self, **self.conan_data["sources"][self.version], destination=self.folders.source_folder, strip_root=True)

    def generate(self):
        if is_msvc(self):
            # Just skip on win32
            return
        tc = AutotoolsToolchain(self)
        tc.configure_args.append("--with-curses={}".format("yes" if self.options.with_library == "curses" else "no"))
        if self.options.shared:
            tc.configure_args.extend(["--enable-shared", "--disable-static"])
        else:
            tc.configure_args.extend(["--enable-static", "--disable-shared"])
        if cross_building(self, self.settings):
            tc.configure_args.append("bash_cv_wcwidth_broken=yes")

        tc.generate()

        deps = AutotoolsDeps(self)
        deps.generate()

    def _patch_sources(self):
        replace_in_file(self, os.path.join(self.folders.source_folder, "shlib", "Makefile.in"),
                        "-o $@ $(SHARED_OBJ) $(SHLIB_LIBS)",
                        "-o $@ $(SHARED_OBJ) $(SHLIB_LIBS) -ltermcap")
        replace_in_file(self, os.path.join(self.folders.source_folder, "Makefile.in"), "@TERMCAP_LIB@", "-ltermcap")

    def build(self):
        if is_msvc(self):
            # Just skip on win32
            return
        self._patch_sources()
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        if is_msvc(self):
            # Just skip on win32
            return
        copy(self, pattern="COPYING", dst="licenses", src=self.folders.source_folder)
        autotools = Autotools(self)
        autotools.install()

        rmdir(self, os.path.join(self.folders.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.folders.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["history", "readline"]
