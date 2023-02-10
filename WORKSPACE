workspace(name = "uber_poet")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "rules_python",
    sha256 = "36362b4d54fcb17342f9071e4c38d63ce83e2e57d7d5599ebdde4670b9760664",
    strip_prefix = "rules_python-0.18.0",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.18.0/rules_python-0.18.0.tar.gz",
)

load("@rules_python//python:repositories.bzl", "py_repositories")

py_repositories()

load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "pip_deps",
    requirements_lock = "@uber_poet//:requirements.txt",
)

load("@pip_deps//:requirements.bzl", "install_deps")

install_deps()