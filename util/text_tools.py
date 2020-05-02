
import urllib.parse
import re
import ftfy


WHITESPACE_CHARS = [
		'\t', '\n', '\x0b', '\x0c', '\r', '\x1c', '\x1d', '\x1e', '\x1f', ' ',
		'\x85', '\xa0', '\u1680', '\u2000', '\u2001', '\u2002', '\u2003',
		'\u2004', '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200a',
		'\u2028', '\u2029', '\u202f', '\u205f', '\u3000'
	]

def fixSmartQuotes(text):
	if isinstance(text, list):
		text = [fixSmartQuotes(tmp) for tmp in text]
		return text
	text = text.replace(r"\'", "'")
	text = text.replace(r'\"', '"')
	text = text.replace(r"’", "'")
	text = text.replace(r"‘", "'")
	text = text.replace(r"“", '"')
	text = text.replace(r"”", '"')
	return text

def fixCase(inText):
	if isinstance(inText, list):
		inText = [fixCase(tmp) for tmp in inText]
		return inText
	caps  = sum(1 for c in inText if c.isupper())
	lower = sum(1 for c in inText if c.islower())
	if (lower == 0) or (caps == 0) or (caps / lower) > 2.5:
		inText = inText.title()
	return inText


def fixUnicodeSpaces(val):
	for badchar in WHITESPACE_CHARS:
		val = val.replace(badchar, " ")
	while "  " in val:
		val = val.replace("  ", " ")
	return val.strip()

def fix_string(val, recase=True):
	if isinstance(val, list):
		val = [fixCase(tmp) for tmp in val]
		return val

	if not val:
		return val

	if isinstance(val, str):
		val = fixUnicodeSpaces(val)
		val = fixSmartQuotes(val)
		if recase:
			val = fixCase(val)
		val = ftfy.fix_text(val)
		val = fixUnicodeSpaces(val)

	return val

def fix_dict(inRelease, recase=True):
	for key in inRelease.keys():
		if isinstance(inRelease[key], str):
			inRelease[key] = fix_string(inRelease[key], recase)

	# Managed to derp this somehow.
	if 'tl_type' in inRelease:
		inRelease["tl_type"] = inRelease["tl_type"].lower()

	return inRelease

is_rrl_chap_re = re.compile(r'^https?://(?:www\.)?royalroadl?\.com/fiction/\d+/[a-z0-9\-]+/chapter/(\d+)/[a-z0-9\-]+$', flags=re.IGNORECASE)

def check_fix_rrl(url):

	is_chp = is_rrl_chap_re.search(url)
	if is_chp:
		url = "https://www.royalroad.com/fiction/chapter/{}".format(is_chp.group(1))

	return url


def clean_fix_url(url):
	nl = urllib.parse.urlparse(url).netloc

	if nl.endswith("royalroad.com") or nl.endswith("royalroadl.com"):
		url = check_fix_rrl(url)

	return url

