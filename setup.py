from pathlib import Path
import re
from setuptools import setup, find_packages

module_dir = Path(__file__).resolve().parent

with open(module_dir.joinpath("optimade/__init__.py")) as version_file:
    for line in version_file:
        match = re.match(r'__version__ = "(.*)"', line)
        if match is not None:
            VERSION = match.group(1)
            break
    else:
        raise RuntimeError(
            f"Could not determine package version from {version_file.name} !"
        )

# Dependencies
# Server minded
elastic_deps = ["elasticsearch-dsl~=6.4,<7.0"]
mongo_deps = ["pymongo~=3.11", "mongomock~=3.23"]
server_deps = [
    "uvicorn~=0.13.4",
    "Jinja2>=2.10,<4.0",
    "pyyaml~=5.1",  # Keep at pyyaml 5.1 for aiida-core support
] + mongo_deps

# Client minded
aiida_deps = ["aiida-core~=1.6"]
ase_deps = ["ase~=3.21"]
cif_deps = ["numpy~=1.20"]
pdb_deps = cif_deps
pymatgen_deps = ["pymatgen==2021.3.9"]
jarvis_deps = ["jarvis-tools==2021.5.28"]
client_deps = cif_deps

# General
docs_deps = [
    "mkdocs~=1.1",
    "mkdocs-awesome-pages-plugin~=2.5",
    "mkdocs-material~=7.1",
    "mkdocs-minify-plugin~=0.4.0",
    "mkdocstrings~=0.15.1",
]
testing_deps = [
    "pytest~=6.2",
    "pytest-cov~=2.12",
    "codecov~=2.1",
    "jsondiff~=1.3",
] + server_deps
dev_deps = (
    ["pylint~=2.8", "pre-commit~=2.13", "invoke~=1.5"]
    + docs_deps
    + testing_deps
    + client_deps
)
all_deps = dev_deps + elastic_deps + aiida_deps + ase_deps + pymatgen_deps + jarvis_deps

setup(
    name="optimade",
    version=VERSION,
    url="https://github.com/Materials-Consortia/optimade-python-tools",
    license="MIT",
    author="OPTIMADE Development Team",
    author_email="dev@optimade.org",
    description="Tools for implementing and consuming OPTIMADE APIs.",
    long_description=open(module_dir.joinpath("README.md")).read(),
    long_description_content_type="text/markdown",
    keywords="optimade jsonapi materials",
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
    ],
    python_requires=">=3.7",
    install_requires=[
        "lark-parser~=0.11.3",
        "fastapi~=0.65.2",
        "pydantic~=1.8,>=1.8.2",
        "email_validator~=1.1",
        "requests~=2.25",
    ],
    extras_require={
        "all": all_deps,
        "dev": dev_deps,
        "docs": docs_deps,
        "testing": testing_deps,
        "server": server_deps,
        "client": client_deps,
        "elastic": elastic_deps,
        "mongo": mongo_deps,
        "aiida": aiida_deps,
        "ase": ase_deps,
        "cif": cif_deps,
        "pdb": pdb_deps,
        "pymatgen": pymatgen_deps,
        "jarvis": jarvis_deps,
    },
    entry_points={
        "console_scripts": ["optimade-validator=optimade.validator:validate"]
    },
)
