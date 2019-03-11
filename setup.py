from setuptools import setup, find_packages

with open("README.md", "r") as f:
	long_description = f.read()

setup(
	name				= "HXMK",
	version				= "0.0.5",
	url					= "https://github.com/Hexcell/HXMK.git",
	author 				= "Hexcell",
	author_email		= "fabian0010k@gmail.com",
	description			= "A Python-based build system with a Makefile-like experience",
	long_description	= long_description,
	long_description_content_type = "text/markdown",
	packages			= find_packages(),
	install_requires	= ["lark-parser >= 0.6.6"],

	entry_points = {
		"console_scripts": [
			"hxmk = HXMK.environment:main"
		]
	},
	
	classifiers = [
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent"
	]
)