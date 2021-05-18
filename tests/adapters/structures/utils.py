from pathlib import Path
import re


def get_min_ver(dependency: str) -> str:
    """Retrieve version of `dependency` from setup.py, raise if not found."""
    setup_py = Path(__file__).parent.joinpath("../../../setup.py")
    with open(setup_py, "r") as setup_file:
        for line in setup_file.readlines():
            min_ver = re.findall(fr'"{dependency}((=|!|<|>|~)=|>|<)(.+)"', line)
            if min_ver:
                return min_ver[0][2].split(";")[0]
        else:
            raise RuntimeError(f"Cannot find {dependency} dependency in setup.py")
