import os
from pathlib import Path
import re
import tempfile
import unittest


class TestSetup(unittest.TestCase):
    """Test ./setup.py"""

    def test_distributions_package(self):
        """Make sure a distribution has all the needed package data"""
        package_root = Path(__file__).parent.parent.resolve()

        number_of_grammar_files = len(
            list(package_root.joinpath("optimade/grammar").rglob("*.lark"))
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            current_dir = Path(temp_dir)
            file_output = current_dir.joinpath("sdist.out")

            os.system(
                f"python {package_root.joinpath('setup.py')} sdist --dry-run > {file_output}"
            )

            with open(file_output, "r") as file_:
                # Removing new-line-chars via slice
                lines = [_[:-1] for _ in file_.readlines()]

            present = {
                r"\.lark": False,
                r"index_links\.json": False,
                r"cors_providers\.json": False,
                r"test_structures\.json": False,
                r"test_references\.json": False,
                r"test_links\.json": False,
                r"filters\.txt": False,
                r"optional_filters\.txt": False,
                r"landing_page\.html": False,
            }
            count = 0
            for line in lines:
                for requirement in present:
                    if re.findall(requirement, line):
                        if requirement == r"\.lark":
                            count += 1
                            if count == number_of_grammar_files:
                                present[requirement] = True
                            else:
                                present[requirement] = False
                        else:
                            present[requirement] = True

            for requirement, is_present in present.items():
                if requirement == r"\.lark":
                    msg = f"{requirement} files NOT found. Expected {number_of_grammar_files}, found instead {count}."
                else:
                    msg = f"{requirement} file NOT found."

                self.assertTrue(is_present, msg=msg)
