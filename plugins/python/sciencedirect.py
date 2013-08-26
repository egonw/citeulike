#!/usr/bin/env python2.7
# NOTE THIS NEEDS 2.6 as parser breaks with 2.5 :-)
import warnings
warnings.simplefilter("ignore",DeprecationWarning)

import os, sys, re, urllib2, string, socket
import htmlentitydefs
import mechanize
import html5lib
from html5lib import treebuilders
import lxml.html, lxml.etree
from lxml.cssselect import CSSSelector

socket.setdefaulttimeout(15)

class ParseException(Exception):
	pass


##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text).encode('utf-8')



#
# Strip off any institutional proxies we find
#
def canon_url(url):
#	print "xxxxx url = %s" % url
	m = re.match(r'http://[^/]*sciencedirect.com[^/]*/(science(\?_ob|/article).*$)', url)
	if not m:
		raise ParseException, "bad source url"
	return "http://www.sciencedirect.com/" + m.group(1)

#
# Make up crossref metadata URL (just need the DOI)
#
def crossref_xml_url(doi):
	url = "http://www.crossref.org/openurl/?id=doi:" + doi
	url += "&noredirect=true"
	# see http://www.crossref.org/help/Content/05_Interfacing_with_the_CrossRef_system/Using_the_Open_URL_Resolver.htm
	# key is either "username:password" or "<email>"
	key_file = os.environ.get("HOME") + "/.crossref-key"
	if os.path.exists(key_file):
		f = open(key_file)
		key = f.read().strip()
		f.close()
		url += "&pid=" + key

	url += "&format=unixref"

	return url


#
# Try, by foul trickery, to get an abstract
# We're looking for HTML like this:
#   <div class="articleText" style="display: inline;">
#       <h3 class="h3">Abstract</h3>
#       <p>An instrumented indentation technique...
#

def scrape_abstract(page):

	root = lxml.html.fromstring(page)

	#root = lxml.html.fromstring(html_data)
	#links_lxml_res = root.cssselect("a.detailsViewLink")
	#links_lxml = [link.get("href") for link in links_lxml_res]
	#links_lxml = list(set(links_lxml))

	abs = []
	for div in root.cssselect("div.articleText"):
		for h3 in div.cssselect("h3.h3"):
			if h3.text and string.lower(h3.text) in ('abstract','summary'):
				for p in div.cssselect("p"):
					abs.append(p.xpath("string()"))

	if len(abs) == 0:
		for div in root.cssselect('div.svAbstract'):
			for p in div.cssselect("p"):
				abs.append(p.xpath("string()"))

	if len(abs) == 0:
		for div in root.cssselect('#articleContent'):
			for p in div.cssselect("div.articleText_indent"):
				abs.append(p.xpath("string()"))

	abstract = ' '.join(abs)

	abstract = re.sub('\n+',' ',abstract)
	abstract = re.sub('\s+',' ',abstract)
#	print "1================================================================="
#	print abstract
#	print "2================================================================="
	return unescape(abstract)

#
# Just try to fetch the metadata from crossref
#
def handle(url):

	cUrl = canon_url(url)
	#print "%s => %s" % (url, cUrl)

	cookies = mechanize.CookieJar()

	browser = mechanize.Browser()
	browser.addheaders = [("User-Agent", "Mozilla/5.0 (compatible; citeulike/1.0)"),
			     ("From", "plugins@citeulike.org")]
	#browser.add_handler(PrettifyHandler())
	browser.set_handle_robots(False)
	browser.set_debug_http(False)
	browser.set_debug_redirects(False)
	browser.open(cUrl)

	response = browser.response()
	page = response.get_data()
	# print page

	#
	# Elsevier insist on user selecting a "preferred source" when the article is
	# available.  This is normally stored in a cookie.
	# If we get directed to the Elsevier "linking hub", find the 1st SD link on the
	# and follow that.
	# Yeah, I know - rubbish.
	#

	huburl = browser.geturl()

	doi = None

	m = re.search(r'linkinghub.elsevier.com/', huburl)
	if m:
		root = lxml.html.fromstring(page)
		inputs = root.cssselect("input")
		hrefs = [link.get("value") for link in inputs]
		for href in hrefs:
			n = re.search('sciencedirect.com',href)
			if n:
				browser.open(href)
				response = browser.response()
				page = response.get_data()
				break

	m = re.search(r'<a(?: id="[^"]+")? href="http://dx.doi.org/([^"]+)"', page)

	# this page might requires a login.  Luckily there seems to be a
	# link "View Abstract" which can take us to a page we can read
	if not m and not doi:

		root = lxml.html.fromstring(page)
		links = root.cssselect("a")
		for href in [e.get("href") for e in links]:
			if href:
				m = re.search(r'http://dx.doi.org/([^"]+)', href)
				if m:
					break

		if False:
			parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("beautifulsoup"))
			# print page
			soup = parser.parse(page)

			link = soup.find(text=re.compile(r"view abstract", re.I))
			if link:
				href = link.parent['href']
				browser.open(href)
				response = browser.response()
				page = response.get_data()

			m = re.search(r'<a(?: id="[^"]+")?  href="http://dx.doi.org/([^"]+)"', page)

	if m:
		doi = m.group(1)
	else:
		root = lxml.html.fromstring(page)
		doi_nodes = root.cssselect("#doi")
		for n in [e.text for e in doi_nodes]:
			doi = re.sub(r'doi:','',n)
			break

	if not doi:
		m = re.search(r'/doi/(10\.\d\d\d\d)_([^/]+)/', page) 
		if m:
			doi = "%s/%s" % (m.group(1), m.group(2))

	if not doi:
		raise ParseException, "Cannot find DOI in page"


	# if not re.search(r'^10[.](1016|1006|1053)/',doi):
	#	raise ParseException, "Cannot find an Elsevier DOI (10.1006, 10.1016, 10.1053) DOI"

	xml_url  = crossref_xml_url(doi)

	browser.open(xml_url)
	response = browser.response()
	xml_page = response.get_data()
	xml_page = xml_page.decode('utf-8')

	# Get rid of extraneous "stars" \u2606.   Sometimes at end of title (hopefully
	# they're never meant to be "real" elsewhere...)
	xml_page = xml_page.replace(u'\u2606',' ')

	m = re.search("not found in CrossRef", xml_page)
	if m:
		raise ParseException, "Unable to locate that DOI (%s) in crossref" % doi

	yield "begin_tsv"
	yield "use_crossref\t1"
	yield "linkout\tDOI\t\t%s\t\t" % doi

	abstract = scrape_abstract(page)
#	try:
#		abstract = scrape_abstract(page)
#	except:
#		abstract = ''

	if abstract:
		print "abstract\t%s" % (abstract)

	yield "end_tsv"

	yield "status\tok"

if __name__ == "__main__":

	url = sys.stdin.readline().strip()

	for line in handle(url):
		print line.encode("utf-8")
	sys.exit(0)

	try:
		for line in handle(url):
			print line.encode("utf-8")
	except Exception, e:
		import traceback
		line = traceback.tb_lineno(sys.exc_info()[2])
		print "\t".join(["status", "error", "There was an internal error processing this request. Please report this to bugs@citeulike.org quoting error code %d." % line])
		raise
