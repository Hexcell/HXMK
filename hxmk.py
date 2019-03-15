@rule()
def everything(c):
	c << "pip install ."

@rule()
def upload(c) -> "build":
	c << "python -m twine upload dist/*"

@rule()
def build(c):
	c << "python setup.py sdist bdist_wheel"