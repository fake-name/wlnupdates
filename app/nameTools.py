

import re
import unicodedata

# --------------------------------------------------------------

# Asshole scanlators who don't put their name in "[]"
# Fuck you people. Seriously
shitScanlators = ["rhs", "rh", "mri", "rhn", "se", "rhfk", "mw-rhs"]

chapVolRe     = re.compile(r"(?:(?:ch?|v(?:ol(?:ume)?)?|(?:ep)|(?:stage)|(?:pa?r?t)|(?:chapter)|(?:story)|(?:extra)|(?:load)|(?:log)) ?\d+)", re.IGNORECASE)
trailingNumRe = re.compile(r"(\d+$)", re.IGNORECASE)


# In a lot of situations, we don't have a series name (particularly for IRC downloads, etc...)
# This function tries to clean up filenames enough that we can then match the filename into
# the name database.
# It's crude as hell, but short of a neural net or something, it's as good as it's gonna get
# for fuzzy matching strings into the database.
# Something like levenshtein string distance might be interesting, but I'd be too concerned
# about false-positive matches. Failing to no-match occationally is FAR preferable to
# failing to wrong-match, so we fail no-match.
def guessSeriesFromFilename(inStr):
	inStr = inStr.lower()
	inStr = removeBrackets(inStr)

	# if there is a "." in the last 6 chars, it's probably an extension. remove it.
	if "." in inStr[-6:]:
		inStr, dummy_ext = inStr.rsplit(".", 1)

	# Strip out scanlator name strings for scanlators who are assholes and don't bracket their group name.
	for shitScanlator in shitScanlators:
		if inStr.lower().endswith(shitScanlator.lower()):
			inStr = inStr[:len(shitScanlator)*-1]

	inStr = inStr.replace("+", " ")
	inStr = inStr.replace("_", " ")
	inStr = inStr.replace("the4koma", " ")
	inStr = inStr.replace("4koma", " ")

	inStr = stripChapVol(inStr)

	inStr = inStr.strip()
	inStr = stripTrailingNumbers(inStr)

	inStr = prepFilenameForMatching(inStr)
	return inStr

def stripChapVol(inStr):
	inStr = chapVolRe.sub(" ", inStr)
	return inStr

def stripTrailingNumbers(inStr):
	inStr = trailingNumRe.sub(" ", inStr)
	return inStr

# Execution time of ~ 0.000052889607680 second (52 microseconds)
def prepFilenameForMatching(inStr):
	# inStr = cleanUnicode(inStr)
	inStr = makeFilenameSafe(inStr)
	inStr = sanitizeString(inStr)
	return inStr.lower()

def makeFilenameSafe(inStr):

	# FUCK YOU SMART-QUOTES.
	inStr = inStr.replace("“",  " ") \
				 .replace("”",  " ")

	inStr = inStr.replace("%20", " ") \
				 .replace("<",  " ") \
				 .replace(">",  " ") \
				 .replace(":",  " ") \
				 .replace("\"", " ") \
				 .replace("/",  " ") \
				 .replace("\\", " ") \
				 .replace("|",  " ") \
				 .replace("?",  " ") \
				 .replace("*",  " ") \
				 .replace('"', " ")

	# zero-width space bullshit (goddammit unicode)
	inStr = inStr.replace("\u2009",  " ") \
				 .replace("\u200A",  " ") \
				 .replace("\u200B",  " ") \
				 .replace("\u200C",  " ") \
				 .replace("\u200D",  " ") \
				 .replace("\uFEFF",  " ")

	# Collapse all the repeated spaces down.
	while inStr.find("  ")+1:
		inStr = inStr.replace("  ", " ")


	# inStr = inStr.rstrip(".")  # Windows file names can't end in dot. For some reason.
	# Fukkit, disabling. Just run on linux.

	inStr = inStr.rstrip("! ")   # Clean up trailing exclamation points
	inStr = inStr.strip(" ")    # And can't have leading or trailing spaces

	return inStr


# I have a love-hate unicode relationship. I'd /like/ to normalize everything, but doing
# so breaks more then it fixes. Arrrrgh.
def cleanUnicode(inStr):
	return unicodedata.normalize("NFKD", inStr).encode("ascii", errors="replace").decode()


bracketStripRe = re.compile(r"(\[[\+\~\-\!\d\w &:]*\])")

def removeBrackets(inStr):
	inStr = bracketStripRe.sub(" ", inStr)
	while inStr.find("  ")+1:
		inStr = inStr.replace("  ", " ")
	return inStr

# Basically used for dir-path cleaning to prep for matching, and not much else
def sanitizeString(inStr, flatten=True):
	baseName = inStr
	if flatten:
		# Adding "-" processing.
		baseName = baseName.replace("-", " ")
		baseName = baseName.replace("!", " ")

		baseName = baseName.replace("~", "")		 # Spot fixes. We'll see if they break anything
		baseName = baseName.replace(".", "")
		baseName = baseName.replace(";", "")
		baseName = baseName.replace(":", "")
		baseName = baseName.replace("-", "")
		baseName = baseName.replace("?", "")
		baseName = baseName.replace('"', "")
		baseName = baseName.replace("'", "")

	# Bracket stripping has to be done /after/ special chars are cleaned,
	# otherwise, they can break the regex.
	baseName = removeBrackets(baseName)				#clean brackets

	# baseName = baseName.replace("'", "")
	while baseName.find("  ")+1:
		baseName = baseName.replace("  ", " ")

	# baseName = unicodedata.normalize('NFKD', baseName).encode("ascii", errors="ignore")  # This will probably break shit


	return baseName.lower().strip()





# ------------------------------------------------------
