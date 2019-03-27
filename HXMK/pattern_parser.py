import glob, re, os

class InvalidPatternError(Exception):
	pass

def get_regex(parts):
	r = r"^"
	for p in parts:
		if p == "*":
			r += r"(.+)"
		elif type(p) is str:
			if p in ["/", "\\"]:
				r += p
			else:
				r += ".{" + str(len(p)) + r"}"
		else: raise ValueError
	r += r"$"
	return re.compile(r)

class Pattern:
	def __init__(self, parts):
		self.parts = parts
		self.regex = get_regex(self.parts)

	def src_get_data(self):
		files = glob.glob(str(self), recursive=True)

		filelist = []
		for file in files:
			rr = self.regex.match(file)
			if not rr: raise ValueError
			filelist.append({"source": file, "groups": rr.groups()})
		return filelist

	def dest_get_data(self, filelist):
		result = []
		for file in filelist:
			result.append((file["source"], self.dest_insert(file["groups"])))
		return result

	def dest_insert(self, groups):
		s = ""
		i = 0
		for part in self.parts:
			if part == "*":
				s += groups[i]
				i += 1
			elif type(part) is str:
				s += part
			else: raise ValueError
		return s

	def count_stars(self):
		s = 0
		for part in self.parts:
			if part == "*":
				s += 1
		return s

	def is_compatible(self, other):
		return self.count_stars() == other.count_stars()

	def __str__(self):
		return "".join(self.parts)

	def __repr__(self):
		return str(self)

class PatternCollection:
	def __init__(self, parts):
		self.src = []
		self.dest = []

		if len(parts) > 2: raise InvalidPatternError

		for p in parts[0]:
			self.src.append(Pattern(p))

		for p in parts[1]:
			self.dest.append(Pattern(p))

	def evaluate(self):
		# the first source given is the most significant
		sources = self.src[0].src_get_data()

		r = []
		for s in sources:	# s = [{main.c}, {test.c}]

			# collect sources
			ss = [s["source"]]
			for f in self.src[1:]:	# f = [{*.h}...]
				name = f.dest_insert(s["groups"])
				if os.path.exists(name):
					ss.append(name)

			# collect destinations
			dd=[]
			for f in self.dest:
				dd.append(f.dest_insert(s["groups"]))

			if len(ss) == 1: ss = ss[0]
			if len(dd) == 1: dd = dd[0]

			r.append((ss, dd))

		return r

	def __repr__(self):
		return repr(self.src) + " -> " + repr(self.dest)

def get_parts(p):
	r = []
	t = ""
	i = 0
	while i < len(p):
		if p[i] == "*" and (i > 0 and p[i-1] != "\\" and p[i-2] != "\\"):
			if t: r.append(t)
			t = ""
			r.append("*")
		else: t += p[i]
		i += 1

	if t: r.append(t)

	return r

def parse(p):
	"""
	parse a pattern
	a -> b
	"""
	at = 0
	parts = [[], []]

	tmp = ""
	i = 0
	while i < len(p):
		if p[i] == " " and (i > 0 and p[i-1] != "\\" and p[i-2] != "\\"):
			if tmp: parts[at].append(get_parts(tmp))
			tmp = ""
		elif p[i:i+2] == "->":
			if tmp: parts[at].append(get_parts(tmp))
			tmp = ""
			at += 1
			i += 1
			if at > 1: raise InvalidPatternError
		else:
			tmp += p[i]
		i += 1
	
	if tmp: parts[at].append(get_parts(tmp))

	return PatternCollection(parts)

if __name__ == "__main__":
	c = parse("src/*.c include/*.h -> obj/*.o")
	print(c)
	print(c.evaluate())