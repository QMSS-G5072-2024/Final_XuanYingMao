# read version from installed package
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("xuan_ying_final")
except PackageNotFoundError:
    # Package is not installed; set a default version or read from a file
    __version__ = "0.1.1"
