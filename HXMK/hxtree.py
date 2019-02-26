import re, glob, os

class Patterns:
	def __init__(self, t):
		self.src = Pattern(t.children[0])
		self.dest = Pattern(t.children[1])
		assert self.src.is_compatible(self.dest)

	def evaluate(self):
		return self.dest.dest_get_data(self.src.src_get_data())

	def __repr__(self):
		return repr(self.src) + " -> " + repr(self.dest)


class star:
	pass

def get_regex(parts):
	r = r"^"
	for p in parts:
		if type(p) is str:
			if p in ["/", "\\"]:
				r += p
			else:
				r += ".{" + str(len(p)) + r"}"
		elif p is star:
			r += r"(.+)"
		else: raise ValueError
	r += r"$"
	return re.compile(r)

class Pattern:
	def __init__(self, t):
		tp = []
		for p in t.children:
			if hasattr(p, "children"):
				for pp in p.children:
					if pp.type == "STRING":
						tp.append(pp.value)
					elif pp.type == "STAR":
						tp.append(star)
					else: raise ValueError
			elif hasattr(p, "value"):
				if p.type == "STRING":
					tp.append(p.value)
				elif p.type == "STAR":
					tp.append(star)
				else: raise ValueError
			else: raise ValueError
		
		if type(tp[0]) is str:
			tp[0] = tp[0].lstrip()

		if type(tp[-1]) is str:
			tp[-1] = tp[-1].rstrip()

		self.parts = tp
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
			if type(part) is str:
				s += part
			elif part is star:
				s += groups[i]
				i += 1
			else: raise ValueError
		return s

	def count_stars(self):
		s = 0
		for part in self.parts:
			if part is star:
				s += 1
		return s

	def is_compatible(self, other):
		return self.count_stars() == other.count_stars()

	def __str__(self):
		s = ""
		for p in self.parts:
			if type(p) is str:
				s += p
			elif p is star:
				s += "*"
			else: raise ValueError
		return s

	def __repr__(self):
		return str(self)