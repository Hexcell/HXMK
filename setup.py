from setuptools import setup, find_packages

setup(
	name = "HXMK",
	version = "0.0.1",
	url = "https://github.com/Hexcell/HXMK.git",
	author = "Hexcell",
	author_email = "fabian0010k@gmail.com",
	description = "A Python-based build system with a Makefile-like experience",
	packages = find_packages(),
	install_requires = ["lark-parser >= 0.6.6"]
)