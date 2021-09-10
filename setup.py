from setuptools import setup

VERSION = "0.0.1"
DESCRIPTION = "Stac Labs python utilities"

setup(
    name="stac-utils-python",
    version=VERSION,
    author="Micheál Keane",
    author_email="micheal@staclabs.io",
    description=DESCRIPTION,
    packages=["stac_utils"],
    install_requires=[],
    keywords=["python", "stac labs"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
)
