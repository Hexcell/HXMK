import sys, os, importlib.util, json, glob, shutil

try:
	from . import coloring, pattern_parser
except Exception:
	import coloring, pattern_parser

class Commander:
	def __init__(self, env):
		self.env = env

	def __lshift__(self, other):
		if not type(other) is str:
			print(coloring.not_a_command % repr(other))
			exit(1)

		print(coloring.info_command % other)
		code = os.system(other)
		if code != 0:
			print(coloring.error_command % ("Exited with code " + str(code)))
			exit(1)
		
		return self

class Environment:
	def __init__(self, path, args=sys.argv[1:], mlocals={}, root=True, project_root=None, name=""):
		self.args = {}
		self.rules = {}
		self.cache = {}
		self.module = None
		self.mask = None
		self.locals = mlocals
		self.root = root
		self.project_root = project_root
		self.name = name

		self.parse_args(args)
		self.execute_in(path, mlocals)

# UTILS
	def default(self, arg, val):
		"""
		Try to optain "arg" from the CLI args,
		if it's not available, return "val"
		"""
		if not arg in self.args:
			return val
		return self.args[arg]

	def as_args(self, l, *, prefix="", suffix=""):
		assert type(l) in [list, tuple, dict]


		if type(l) in [list, tuple]:
			x = "\"" + ("\" \"".join([(prefix + x.replace("\"", "\\\"") + suffix ) for x in l if x.strip() != ""])) + "\""
			return x if x.strip("\"") else ""
		
		if type(l) is dict:
			if prefix or suffix: raise ValueError
			x = "\"" + ("\" \"".join([(x.replace("\"", "\\\"") + "=" + l[x].replace("\"", "\\\"")) for x in l])) + "\""
			return x if x.strip("\"") else ""

	def make(self, path, args=[], isolate=False):
		if not os.path.isdir(path):
			print(coloring.dir_not_found % path)
			exit(1)

		oldpath = os.getcwd()
		newpath = os.path.abspath(path)
		name = newpath.replace(oldpath, "").strip("/")
		if not isolate:
			self.update_locals()
		l = self.locals if not isolate else {}

		print(coloring.dir_entering % path)
		Environment(path, args=args, mlocals=l, root=False, project_root=self.project_root, name=name)
		print(coloring.dir_exiting % path)

		os.chdir(oldpath)

	def is_root(self):
		return self.root

	def mkdir(self, *path):
		for p in path:
			np = p.replace('\\\\', '/') if os.name == 'posix' else p.replace('/', '\\\\')
			os.system(f"mkdir {'-p' if os.name == 'posix' else ''} {np}")

# DECORATORS
	# TODO: consider syntax in IDEA.md
	def rule(self, *, always=None, dependencies=None, not_found=None, changed=None):
		"""
		A decorator that takes care of rules.
		"""

		# parameter checking
		if always and (dependencies or not_found or changed):
			print(coloring.always_overrides)
			exit(1)
		
		# set always to True by default
		if not always and not (dependencies or not_found or changed):
			always = True

		# TODO: more parameter checking

		def rule_decorator(func):
			rule_name = (self.name + "/" if self.name else "", func.__name__)

			# the wrapper that executes our function
			def wrapper(c, rebuild=False):
				deps_did_something = False
	
				# execute dependencies
				if "return" in func.__annotations__:
					r = func.__annotations__["return"]
					if type(r) is str: r = [r]

					deps_did_something = self.execute_batch(r)

				# execute self
				did_something = False
				if self.check_triggers(deps_did_something, always, dependencies, not_found, changed):
					print(coloring.executing_rule % rule_name)
					func(c)
					did_something = True
				
				# check if expectation was met
				v = not_found
				if v:
					if type(v) is str: v = [v]
					for p in v:
						if not os.path.exists(p):
							print(coloring.expectation_not_met % p)

				# up to date message
				if not did_something:
					print(coloring.up_to_date % rule_name)

				# return
				if always:
					return False
				return did_something

			return wrapper

		return rule_decorator

	def pattern(self, pttrn):
		"""
		A decorator that takes care of pattern rules.
		"""

		pttrn_tree = pattern_parser.parse(pttrn)
		def pattern_decorator(func):
			rule_name = (self.name + "/" if self.name else "", func.__name__)
			
			# the wrapper that executes our function
			def wrapper(c, rebuild=False):
				did_something = False
				deps_did_something = False

				# execute dependencies
				if "return" in func.__annotations__:
					r = func.__annotations__["return"]
					if type(r) is str: r = [r]

					if self.execute_batch(r):
						deps_did_something = True
				
				# execute self
				ff = pttrn_tree.evaluate()
				for files in ff:
					if not self.files_up_to_date(files[0], files[1]) or rebuild or deps_did_something:
						print(coloring.executing_rule % rule_name)
						func(c, files[0], files[1])
						self.files_update_cache(files[0], files[1])
						did_something = True

				# check if expectation was met
				for files in ff:
					if not os.path.exists(files[1]):
						print(coloring.expectation_not_met % files[1])

				# up to date message
				if not did_something:
					print(coloring.up_to_date % rule_name)

				# return
				return did_something

			return wrapper

		return pattern_decorator

# INTERNAL UTILS
	def check_triggers(self, deps_did_something, always, dependencies, not_found, changed):
		if always:												return True
		if dependencies	and deps_did_something:					return True
		if not_found	and not self.exists_str_list(not_found):return True
		if changed		and self.files_changed(changed):		return True
		return False

	def check_triggers_(self, trigger, deps_did_something, path, dest):
		for t in trigger:
			if t == "always":
				return True
			elif t == "dependencies":
				if deps_did_something: return True
			elif t == "not_found":
				if not self.exists_str_list(dest): return True
			elif t == "changed":
				if self.files_changed(path): return True
			
			return False

	def update_locals(self):
		for attr in [x for x in dir(self.module) if x not in self.mask + ["__builtins__"]]:
			if not attr in self.rules:
				self.locals[attr] = getattr(self.module, attr)

	def exists_str_list(self, v):
		if not type(v) in [str, list, tuple]:
			print(coloring.invalid_decorator_params % (str(v), "path"))
			exit(1)

		x = v
		if type(x) is str:
			x = [x]
		for p in x:
			if not os.path.exists(p): return False
		return True

	def execute_batch(self, batch):
		did_something = False
		for rule in batch:
			if rule in self.rules:
				r = self.rules[rule](Commander(self))
				if r: did_something = True
			else:
				print(coloring.rule_not_found % rule)
				exit(1)
		return did_something
		

	def files_up_to_date(self, src_, dest_):
		src = src_
		dest = dest_
		if type(src) is str: src = [src]
		if type(dest) is str: dest = [dest]

		ds = "".join(dest)

		for d in dest:
			if not os.path.isfile(d):
				return False # output file doesn't exist, build it

		for s in src:
			if not s+"->"+ds in self.cache:
				return False # file hasn't been cached, and thus built yet, build it

			# get the last modification time
			mtime = str(os.stat(s).st_mtime)
			# the files have been modified, build it
			if self.cache[s+"->"+ds] != mtime:
				return False

		return True

	def files_update_cache(self, src_, dest_):
		src = src_
		dest = dest_
		if type(src) is str: src = [src]
		if type(dest) is str: dest = [dest]

		ds = "".join(dest)

		for s in src:
			mtime = str(os.stat(s).st_mtime)
			self.cache[s+"->"+ds] = mtime

	def files_changed(self, tsrc):
		src = tsrc
		if type(src) is str: src = [src]

		for file in src:
			if not os.path.exists(file):
				print(coloring.cache_file_missing % file)
				exit(1)

			# file hasn't been cached
			if not file in self.cache:
				self.cache[file] = str(os.stat(file).st_mtime)
				return True

			# get the last modification time
			mtime = str(os.stat(file).st_mtime)
			# the file has been modified
			if self.cache[file] != mtime:
				self.cache[file] = mtime
				return True
		
		return False

	def parse_args(self, args):
		"""
		Parse arguments and flags and store them.
		"""
		argdict = {}
		flaglist = []

		for arg in args:
			if "=" in arg:
				a = arg.split("=", 1)
				argdict[a[0]] = a[1]
			else:
				flaglist.append(arg)

		self.flags = flaglist
		self.args = argdict

	def clean(self):
		if not os.path.isfile(".clean"):
			print(coloring.clean_not_found)
			exit(1)

		print(coloring.cleaning)

		files, folders = (0, 0)
		cleanfile = open(".clean", "r").readlines()
		for line in cleanfile:
			for file in glob.iglob(line.strip(), recursive=True):
				if os.path.exists(file):
					print(coloring.deleting % file)
					if os.path.isfile(file):
						os.remove(file)
						files += 1
					elif os.path.isdir(file):
						shutil.rmtree(file)
						folders += 1
		if os.path.isfile(".hxmkcache"):
			print(coloring.deleting % ".hxmkcache")
			files += 1
			os.remove(".hxmkcache")

		print(coloring.cleaning_done % (files, folders))

	def execute_in(self, path, mlocals):
		"""
		Execute in a specific directory
		"""
		# cd to the directory
		os.chdir(path)

		# set project_root
		if self.root:
			self.project_root = os.getcwd()

		# check if a cachefile exists and load it
		cachefile = os.path.join(os.getcwd(), ".hxmkcache")
		if os.path.isfile(cachefile):
			self.cache = json.load(open(cachefile, "r"))

		# check if a hxmk.py file exists
		file = os.path.join(os.getcwd(), "hxmk.py")
		if not os.path.isfile(file):
			print(coloring.invalid_directory % os.getcwd())
			exit(1)
		
		# load the module
		spec = importlib.util.spec_from_file_location("module.name", file)
		module = importlib.util.module_from_spec(spec)
		self.module = module

		# set data
		module.rule = self.rule
		module.pattern = self.pattern
		module.default = self.default
		module.glob = glob.glob
		module.as_args = self.as_args
		module.make = self.make
		module.is_root = self.is_root
		module.mkdir = self.mkdir
		for l in mlocals:
			setattr(module, l, mlocals[l])
		module.root = self.project_root

		# get its attributes
		attrs = dir(module)
		self.mask = attrs

		# execute the module
		spec.loader.exec_module(module)

		# get the newly defined attributes
		new_attrs = [x for x in dir(module) if x not in attrs + ["__builtins__"]]

		# sort out all attributes
		for a in new_attrs:
			attr = getattr(module, a)
			# if it's callable, it's a rule
			# TODO: find a better solution, this is error prone
			if callable(attr):
				self.rules[a] = attr

		ex = False
		# resolve and execute builtin flags
		for flag in self.flags:
			if flag == "clean":
				ex = True
				self.flags.remove(flag)
				self.clean()

		# execute the rules
		for flag in self.flags:
			if flag in self.rules:
				ex = True
				self.rules[flag](Commander(self))
			else:
				print(coloring.rule_not_found % flag)
				exit()

		# execute "everything" if no rule was executed
		if not ex and "everything" in self.rules:
			self.rules["everything"](Commander(self))

		# write the cache
		json.dump(self.cache, open(cachefile, "w"))

def main():
	Environment(os.getcwd())

if __name__ == "__main__":
	# this is useful for debugging
	Environment(input("> "))
