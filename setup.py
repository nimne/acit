from setuptools import setup, find_packages
from os import path

# The text of the README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    README = f.read()

# This call to setup() does all the work
setup(
    name="acit",
    version="0.0.1",
    description="Automated cell identification and tracking",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/nimne/acit",
    author="Nick Negretti",
    author_email="nick.negretti@gmail.com",
    license="Apache License, Version 2.0",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
    include_package_data=True,
)
