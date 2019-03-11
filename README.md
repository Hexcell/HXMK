# HXMK (Hexcell Make)
HXMK is a python-based build system for the Hexcell Projects. It brings a Makefile like experience to a familiar and simple environment.

Best of all: it has nice colors

![colors2](https://raw.githubusercontent.com/Hexcell/HXMK/master/screenshots/colors2.png)
![colors](https://raw.githubusercontent.com/Hexcell/HXMK/master/screenshots/colors.png)

### Installation
```shell
pip install HXMK
```

##### Manual (latest version)
```shell
$ git clone https://github.com/Hexcell/HXMK.git
$ cd HXMK

$ pip install .
```

### Usage
If the project directory contains a `hxmk.py` file, you can do
```shell
hxmk [args|rules]
```
Arguments are specified like `name=value` and rules like `name`.
```shell
hxmk abc=123 somerule
```

In case no rule was given, HXMK will look for the rule `@everything` and execute it (if it exists).
No arguments or rules have to be specified be default.
```shell
hxmk # <- this is completely valid
```

HXMK can also be used to clean directories.
```shell
hxmk clean [args|rules]
```
This will look for a `.clean` file that contains a [glob](https://docs.python.org/3/library/glob.html#glob.glob) pattern on each line.

Example of a `.clean` file:
```shell
bin
obj
*.o
__pycache__
```

`clean` counts as a rule (although it's not an actual rule), so the rule `@everything` will not be run if not explicitly stated like this:
```shell
hxmk clean everything # will clean and THEN run @everything
```

### `hxmk.py`
##### Rules
The simplest rule would look something like this:
```py
@rule()
def everything(c):
    pass
```
`c` is an instance of the class `Commander`, it is used to execute commands. To do so, it overloads the lshift operator.
```py
@rule()
def everything(c):
    c << "echo Commands are executed like this."
```
Rules can have dependencies. They are given through the return annotation. A rules dependencies are executed before it.
```py
@rule()
def everything(c) -> "other":
    c << "echo What a lovely day it is today."

def other(c):
    c << "echo @everything depends on me so I go first!"
```
Multiple dependencies are given in a list or tuple, whichever you prefer.
```py
@rule()
def everything(c) -> ("other", "something")
```

Rules have triggers, which are state if and when a rule shall be executed. If no trigger is specified, the trigger `always` will be set to `True`.

For example, to execute a rule whenever at least one of the folders `bin` and `obj` are missing, you could do the following:
```py
@rule(not_found=["bin", "obj"])
def dirs(c):
    c << "mkdir -p bin"
    c << "mkdir -p obj"
```
The following triggers are implemented so far:
 - `always`, always execute the rule. It is a bool.
 - `dependencies`, execute it if one or more dependencies were executed. It is a bool.
 - `not_found`, execute when a specified path is not found (file or folder). It can be a `str`, `list` or a `tuple`.
 - `changed`, cache a file or list of files. Execute when any of the specified files are not found in the cache or have been changed. It can be a `str`, `list`, or a `tuple`.

If `not_found` is given, the rule will assume that you are going to create the specified path. If that path is not found after the rule was executed, a warning will be shown.

An example of a caching rule:
```py
@rule(changed=["a.cpp", "b.cpp"], not_found="program")
```

This above rule will be executed if `a.cpp` or `b.cpp` have been changed, or when `program` was not found.
Though for this particular case, pattern rules would be recommended.

##### Pattern Rules
Pattern Rules are rules that are executed multiple times for multiple files.
They look like this:
```py
@pattern("src/*.c -> obj/*.o")
def somerule(c, src, dest):
    pass
```
(The syntax for the patterns is `src -> dest`.)
This basically means, every `.c` file in `src` will be turned into an `.o` file in `obj`.
The Pattern Rule will be executed for every `.c` file.
This could be used to compile every `.c` file in a directory.#
```py
@pattern("src/*.c -> obj/*.o")
def somerule(c, src, dest):
    c << "gcc -c %s -o %s" % (src, dest)
```
Pattern rules are cached.
Before executing, the Pattern Rule checks whether the source files have been modified since the last build and if the destination file exists already. If the destination file does not exist, the rule will be executed, else it will only be executed if the source file was modified or not found in the cache.

#### Builtins
All builtins are immediately available without having to import anything.

##### make
```py
make(self, path, args=[], isolate=False)
```
`make` will start HXMK in a different folder. Optionally args (in the sense of CLI args) can be passed in to `args`.

By default all variables from the root module are readable in every module called by `make`. This behavior can be stopped by setting `isolate` to `True`.

```py
# hxmk.py
somevar = "hello"
@rule()
def everything(c):
    make("other")
```
```py
# other/hxmk.py
@rule()
def everything(c):
    print(somevar)
```
```shell
>>> @all
>>> Entering other
>>> other/@all
>>> "hello"
```

##### default
```py
default(arg, val)
```
`default` is used to optain a value from the CLI or default to another value in case it's not found. The first argument is the name and the second one is the default value.
An example would be:
```shell
$ hxmk config=debug
```
```py
config = default("config", "release")
assert config in ["debug", "release"]

# ...now config can be used
```

##### as_args
```py
as_args(l, prefix="", suffix="")
```
`as_args` is used to use a list as CLI arguments. The first argument is a list, tuple or dict, the keyword arguments are `prefix` and `suffix`.

An example use case would be this:
```py
...
    c << "ld ... %s" % as_args(["a.o", "b.o", "c.o"])

>>> ld ... "a.o" "b.o" "c.o"
```
Passing in a dict would return `"key=value"` for each item.
```py
...
    c << "ld ... %s" % as_args({"a": "b", "c": "d"})

>>> ld ... "a=b" "c=d"
```
When passing in a dict, the prefix and suffix parameters can not be used.

##### glob
```
glob(pathname, *, recursive=False)
```
`glob` is just the glob function from pythons standard library. For more information, look at [Pythons documentation on it](https://docs.python.org/3/library/glob.html#glob.glob).

It could be used in combination with `as_args` to link all object files.
```py
...
    c << "ld ... %s" % as_args(glob("obj/*.o"))

>>> ld ... "main.o" "utils.o"
```

### Goals
The main goal is to create a simple build too with the same functionality as make (+ more) while maintaining readability and sanity.

Currently, HXMK runs just fine, but there have been and will most likely be many API changes. Bugs are to be expected, if you find one, do not hesitate to create an issue.

#### TODO
 - [x] rules
 - [x] pattern eules
 - [x] argument parsing
 - [x] build subdirectories
 - [x] cleaning
 - [ ] add docstrings and comments for every function
 - [ ] full api documentation
 - [ ] better cross-platform support / more builtins (mkdir, ...)

### Contributing
Any form of contribution is welcome ^^
