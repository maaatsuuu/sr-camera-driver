from glob import glob
from os.path import join

from setuptools import find_packages
from setuptools import setup


package_name = "bringup"


setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (join("share", package_name, "config", "elp"), glob("config/elp/*.yaml")),
        (join("share", package_name, "config", "routecam"), glob("config/routecam/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="matsudri",
    maintainer_email="matudariku@gmail.com",
    description="Camera bringup launch and configuration files.",
    license="TODO: License declaration",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [],
    },
)
