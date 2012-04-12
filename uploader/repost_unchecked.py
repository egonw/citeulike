#!/usr/bin/env python

import re, urllib, sys, time, urlparse, os, errno, os.path, socket, codecs, json

import mechanize
import lxml.html

from datetime import datetime
from optparse import OptionParser
from lxml import etree
from subprocess import Popen, PIPE, STDOUT
from OrderedSet import OrderedSet
import ClientForm

socket.setdefaulttimeout(15)


"""
Usage:
	./repost_unchecked.py -u USERNAME -p PASSWORD -f file.json
"""

#
# Mechanize (which uses BeautifulSoup, I think) doesn't like our HTML, so we
# need the nuclear options of cleaning it up with "tidy" (BeautifulTree and
# lxml both fail - we need to look at our XHTML!)
#
class PrettifyHandler(mechanize.BaseHandler):
	def http_response(self, request, response):
		if not hasattr(response, "seek"):
			response = mechanize.response_seek_wrapper(response)
		if response.info().dict.has_key('content-type') and ('html' in response.info().dict['content-type']):

			p = Popen(["/usr/bin/tidy", "-q", "-i"], stdout=PIPE, stdin=PIPE, stderr=PIPE)

			html = p.communicate(input=response.get_data())[0]
			#print html

			#p = Popen(["/usr/bin/tidy", "-q", "-i"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
			#p.stdin.write(response.get_data())
			#p.stdin.flush()
			#p.stdin.close()
			#html = p.stdout.read()
			#p.stdout.close()
			response.set_data(html)

			#html = etree.HTML(response.get_data())
			#response.set_data(etree.tostring(html))
		return response


################################################################################
#
# Look for a <meta name="NAME" content="CONTENT"> header from HTML and return
# CONTENT
#
def check_header(root, name):
	for m in root.cssselect("meta"):
		attr=m.attrib
		if attr.has_key("name") and attr["name"] == name:
			return attr["content"]

	return None

################################################################################
#
# Login to CiteULike using the normal form
#
def login(username, password):
	browser.open(BASE+"/login?from=/profile/"+username)
	browser.select_form(name="frm")

	browser["username"] = username
	browser["password"] = password

	response = browser.submit()

	page =  response.read()
	root = lxml.html.document_fromstring(page)

	logged_in = False

	#
	# Look for a magic meta header. Not yet implemented
	#
	h = check_header(root, "logged_in")

	if h and h == "yes":
		logged_in = True

	# Use a cruder check, whether the "[logout]" link exists
	if not logged_in:
		for b in root.cssselect('#logout_button'):
			logged_in = True
			break

	assert logged_in, "Unable to log in"

################################################################################
#
#
#
def get_linkouts(article):
	linkouts = OrderedSet([])

	# 1st try DOI, followed by PUBMED, since these are stable
	if article.has_key("doi"):
		linkouts.add("http://dx.doi.org/%s" % article["doi"])

	# Look for a DOI added as a URL
	if article.has_key("linkouts"):
		for linkout in article["linkouts"]:
			if linkout["type"] == "URL":
				# look for an explicit CrossRef link
				m = re.search(r'dx.doi.org/(.*)', linkout["url"])
				if m:
					linkouts.add(linkout["url"])
					continue

				parsed_url = urlparse.urlparse(linkout["url"])

				# Look for anything DOI-like.
				# DOI spec very loose and pretty much any char allowed
				# in the 2nd part.   In practice, / is rare!


				m = re.search(r'(10\.\d\d\d\d/[^/]+)', parsed_url.path)
				if m:
					linkouts.add("http://dx.doi.org/%s" % m.group(1))
					continue

				qs = urlparse.parse_qs(parsed_url.query)
				done = False
				for k in qs:
					for v in qs[k]:
						m = re.search(r'(10\.\d\d\d\d/[^/]+)', v)
						if m:
							linkouts.add("http://dx.doi.org/%s" % m.group(1))
							done = True
							break
					if done:
						break

	# Look for PubMed.
	if article.has_key("linkouts"):
		for linkout in article["linkouts"]:
			if linkout["type"] == "URL" and re.search("http://view.ncbi.nlm.nih.gov/pubmed/", linkout["url"]):
				linkouts.add(linkout["url"])

	# OK, let's try anything, but exclude any linkout that seems to be a PDF
	if article.has_key("linkouts"):
		for linkout in article["linkouts"]:
			u = linkout["url"]
			m = re.search(r'\.pdf', u, re.I);
			if not m:
				linkouts.add(u)

	print [l for l in linkouts]

	return linkouts


################################################################################
#
#
#
def pre_post(url):
	get(BASE+"/posturl?"+urllib.urlencode({"url": url}))

	here = browser.geturl()

	print "Got", here

	#
	# If the article is already in the library, sync up the metadata.
	# TODO: make this an option
	#
	# There's a problem here when we deal with groups - there's no way to post
	# directly to a group, the "already_posted" comes back when the article is
	# in the user's own library.
	#
	# The later workaround/hack is to detect whether the to_group checkbox
	# exists on the 2nd stage posting page.
	#
	m = re.search(r'article/(\d+)\?show_msg=already_posted', here)
	if m:
		print "ALREADY_POSTED:%s" % here
		dest_article = get_dest_article(here)
		if dest_article == None:
			return None

		sync_articles(article, dest_article)
		return "EXISTS"

	m = re.search(r'/post_unknown.adp', here)
	if m:
		print "ERROR:UNKNOWN:%s" % url
		return "UNKNOWN_URL"

	m = re.search(r'/post_error.adp', here)
	if m:
		print "ERROR:UNKNOWN:driver unable to post: %s" % url
		return "DRIVER_ERROR"

	# Make sure we're at the actual posting page
	m = re.search(r'/posturl2', here)
	if not m:
		print "ERROR:%s" % url
		return None

	return "NEW"

################################################################################
#
#
#
def init_group_copy(src_article_id):
	print "DEBUG:init_group_copy:"
	browser.open(BASE+"/copy?article_id=%s&src_username=group:%s" % (src_article_id, options.group))

################################################################################
#
#
#
def dump_form():
	for n in [c for c in browser.controls]:
		print ">>>> ",n


################################################################################
#
# Post an individual article
#
def post(article):

	# This in now filtered out in the calling func. so should never fire.
	if article["is_unchecked"]!="Y":
		print "Skipping checked article"
		return 2

	src_article_id = article["article_id"]

	linkouts = get_linkouts(article)

	if len(linkouts) == 0:
		print "ERROR:could not find a linkout"
		return -1

	url = None
	for linkout in linkouts:
		print "Trying Linkout:", linkout

		ret = pre_post(linkout)
		if ret == None:
			pass
		elif ret == "EXISTS":
			if not options.group:
				return 1
			# posting redirects to the user's own library copy
			# if it exists.  In that case we need to simulate a "[copy]"
			# from the user's library.
			# SMELL: this will probably copy across stuff from the user's
			# library we don't want in the group library.
			init_group_copy(src_article_id)
			url = linkout
			break
		elif ret == "UNKNOWN_URL":
			pass
		elif ret == "DRIVER_ERROR":
			pass
		elif ret == "NEW":
			url = linkout
			break
		else:
			raise

	if url == None:
		return -1

	print "Preparing to post: %s" % url

	browser.select_form(name="frm")

	if article.has_key("tags"):
		tags = " ".join(article["tags"])
	else:
		tags = "";

	tags = "%s %s" % (tags, COPY_TAG)

	browser["tags"] = tags

	# citation keys are a triplet - 3rd item is the user supplied one
	user_citation_key = article["citation_keys"][2]
	if user_citation_key:
		browser["bibtex_import_cite"] = user_citation_key

	print "Posting %s (tags:%s; key:%s)" % (url, tags, user_citation_key)

	# make sure no libraries are selected
	# Mechinize barfs if the form elements don't exist, which is the case
	# when the article already exists in the user/group library. So catch that.
	try:
		browser["to_group"] = []
	except:
		pass
	try:
		browser["to_own_library"] = []
	except:
		pass

	if options.group:
		print "posting to group", options.group
		try:
			browser["to_group"] = [options.group]
		except ClientForm.ItemNotFoundError:
			print "NOTICE: group checkbox unavailable - the article must already exist in that group"
			dest_article = get_dest_article(BASE+"/group/"+options.group+"/article/"+src_article_id)
			sync_articles(article, dest_article)
			return 1
	else:
		print "posting to own library"
		browser["to_own_library"] = ["y"]

	# Add the 1st note - we'll sync multiple notes later.
	if article.has_key("notes") and len(article["notes"]) > 0:
		note = article["notes"][0]
		print "Note:\n%s" % note
		browser["note"] = note["text"]
		if note["private"]:
			browser["private_note"] = ["y"]

	if article["privacy"]=="private":
		browser["is_private"] = "Y"

	# make sure we don't go to journal page
	# this might not exist if we're copying, which is the case when
	# posting to a group (since we've gone via the "copy" page)
	try:
		browser["to_orig"] = []
	except:
		pass

	# reading priority
	browser["to_read"] = [article["priority"]]

	do_submit()

	new_url = browser.geturl()

	m = re.search(r'/article/(\d+)', new_url)
	if not m:
		print "ERROR: unexpected page %s" % new_url
		return -1

	dest_article_id = m.group(1)

	# should never happen as it should have been trapped earlier.
	if not options.group and dest_article_id == src_article_id:
		print "ERROR: src and dest articles the same"
		return -1

	print "POSTED:%s as %s" % (url, new_url)

	#
	# OK sync up metadata and attachments
	#
	dest_article = get_dest_article(new_url)
	if dest_article == None:
		return -1

	sync_articles(article, dest_article)

	#
	# TODO: add a tag to src article to show that it's been reposted.
	# I guess the duplicates page does this for the time being.
	#

	return 1


################################################################################
#
#
#
def select_form_by_id(id):
	browser.select_form(predicate=lambda f: 'id' in f.attrs and f.attrs['id'] == id)

################################################################################
#
#
#
def get_dest_article(new_url):
	m = re.search(r'(http://[^/]+)(/.+)', new_url)
	if not m:
		print "ERROR: cannot parse %s" % new_url
		return None

	json_url = "%s/json%s" % (m.group(1), m.group(2))
	print "Downloading json from %s" % json_url

	resp = get(json_url)

	dest_article = json.loads(resp)[0]
	return dest_article


################################################################################
#
#
#
def sync_articles(src_article, dest_article):
	# print article, dest_article
	if options.copy_attachments:
		sync_userfiles(src_article, dest_article)
	sync_notes(src_article, dest_article)
	sync_metadata(src_article, dest_article)
	sync_cito(src_article, dest_article)

################################################################################
#
#
#
def get_library_path():
	if options.group:
		return "/group/%s" % options.group
	else:
		return "/user/%s" % options.username

################################################################################
#
#
#
def sync_cito(src_article, dest_article):
	if src_article.has_key("cito"):
		print "Syncing CiTO"
	else:
		print "No CiTO"
		return

	this_article_id = dest_article["article_id"]

	for c in src_article["cito"]:
		browser.open(BASE+"/add_cito.json.do?",
			"this_article_id=%s&that_article_id=%s&cito_code=%s&from=%s" %
			(this_article_id,c["article_id"],c["relation"],get_library_path()))
		browser.response().get_data()


################################################################################
#
#
#
def sync_metadata(src_article, dest_article):
	browser.open("%s/edit_article_details?user_article_id=%s" % (BASE,dest_article["user_article_id"]))
	browser.select_form(predicate=lambda f: 'id' in f.attrs and f.attrs['id'] == 'article')

	form_name_map = {
		"title": "title",
		"journal": "journal",
		"issn": "issn",
		"volume": "volume",
		"issue": "issue",
		"chapter": "chapter",
		"edition": "edition",
		"start_page": "start_page",
		"end_page": "end_page",
		"date_other": "date_other",
		"isbn": "isbn",
		"title_secondary": "booktitle",
		"how_published": "how_published",
		"institution": "institution",
		"organization": "organization",
		"publisher": "publisher",
		"address": "address",
		"location": "location",
		"school": "school",
		"title_series": "series",
		"abstract": "abstract"
	}


	# TODO.  Need an option to export RAW records, especially for
	# "//" fields and (possibly) authors.

	fields = browser.controls
	#fields = [f for f in fields if f.name == "abstract" ]

	for n in [c for c in fields]:
		cname = n.name

		if cname and form_name_map.has_key(cname) and form_name_map[cname] and src_article.has_key(form_name_map[cname]):
			v = src_article[form_name_map[cname]]
			v = v.encode("utf-8","ignore")
			browser[cname] = v

	#do_submit()
	#return

	if src_article.has_key("published"):
		published = src_article["published"]
		if len(published) > 0:
			browser["year"]  = published[0]
		if len(published) > 1:
			browser["month"]  = [str(int(published[1]))]
		if len(published) > 2:
			browser["day"]  = published[2]

	if src_article.has_key("authors"):
		browser["authors"] = "\n".join([a.encode("utf-8","ignore") for a in src_article["authors"]])

	if src_article.has_key("editors"):
		browser["editors"] = "\n".join([a.encode("utf-8","ignore") for a in src_article["editors"]])

	do_submit()

################################################################################
#
# Had some problems with requests hanging so wrote this to ensure that
# data was read properly.  Not sure this helps, but no harm...
#
def do_submit():
	browser.submit()
	browser.response().get_data()


################################################################################
#
# see comments on do_sumit to see why this func exists.
#
def get(url):
	browser.open(url)
	return browser.response().get_data()

################################################################################
#
#
#
def sync_notes(src_article, dest_article):
	if not src_article.has_key("notes"):
		print "No notes to sync"
		return

	print "Syncing notes"

	src_notes = src_article["notes"]

	if dest_article.has_key("notes"):
		dest_notes = dest_article["notes"]
	else:
		dest_notes = []

	wanted = []

	for s in src_notes:
		matched = False
		for d in dest_notes:
			if s["text"] == d["text"]:
				matched = True
		if not matched:
			wanted.append(s)

	browser.open(dest_article["href"])
	for n in wanted:
		print "Syncing note: ", n["text"]

		# print browser.response().get_data()
		select_form_by_id("addnote_frm")
		browser["text"] = n["text"]
		if n["private"]:
			browser["private_note"] = ["y"]
		# returns us to article page, so OK in loop
		do_submit()

################################################################################
#
#
#
def sync_userfiles(src_article, dest_article):
	if not src_article.has_key("userfiles"):
		print "No attachments to sync"
		return

	print "Syncing attachments"

	src_userfiles = src_article["userfiles"]

	if dest_article.has_key("userfiles"):
		dest_userfiles = dest_article["userfiles"]
	else:
		dest_userfiles = []

	wanted = []

	dest_userfiles_hash = {}
	for f in dest_userfiles:
		dest_userfiles_hash[f["sha1"]] = f

	for f in src_userfiles:
		if not dest_userfiles_hash.has_key(f["sha1"]):
			print "To sync:",f["name"]
			wanted.append(f)
		else:
			print "Skipping:",f["name"],"(already exists)"


	browser.open(dest_article["href"])
	for f in wanted:
		print "Syncing: ", f["path"]
		s = FILE_CACHE_DIR+"/"+f["sha1"]
		if os.path.isfile(s):
			print "Already in cache ",s
		else:
			print "Downloading ",s
			browser.retrieve(BASE+f["path"],s)

		browser.select_form(name="fileupload_frm")
		browser.add_file(open(s), 'application/octet-stream', f["name"])
		browser["keep_name"] = ["yes"]
		do_submit()


################################################################################
#
# Unthrottled, this proc can be very server unfriendly, so add a "smart" pause.
# between posts.  There are still quite a lot of requests in each post, though.
#
def pause():
	pause = options.pause
	if not pause and status == 2:
		pause = False
	if pause:
		if len(articles) <= 3:
			pass
		elif len(articles) <= 10:
			time.sleep(1)
			pass
		else:
			time.sleep(5)
			pass

#<MAIN>#########################################################################

if ( len(sys.argv) == 1 ):
	sys.argv.append("-h")

parser = OptionParser()

parser.add_option("-u", "--username",
		dest="username",
		help="citeulike username")

parser.add_option("-p", "--password",
		dest="password",
		help="citeulike password")

parser.add_option("-g", "--group",
		dest="group",
		help="citeulike group")


parser.add_option("-b", "--base",
		dest="baseurl",
		default="http://www.citeulike.org",
		help="Base URL (default http://www.citeulike.org/)")

parser.add_option("--no-copy-attachments",
		action="store_false",
		dest="copy_attachments",
		default=True,
		help="Copy attachments")

parser.add_option("-C", "--cache-dir",
		dest="cachedir",
		default="/tmp/mycache",
		help="Copy attachments")

parser.add_option("-f", "--file",
		dest="srcfile",
		help="Source JSON file")

parser.add_option("--no-pause",
		dest="pause",
		action="store_false",
		default=True,
		help="Don't pause between posts.  Please don't use this or you might get blocked.")

(options, args) = parser.parse_args()

if not options.username or not options.password:
	print "Supply username/password"
	sys.exit()

if not options.srcfile:
	print "Supply source JSON file"
	sys.exit()

BASE=options.baseurl

FILE_CACHE_DIR=options.cachedir
try:
	os.makedirs(FILE_CACHE_DIR)
except OSError, e:
	if e.errno != errno.EEXIST:
		raise

browser = mechanize.Browser()
browser.add_handler(PrettifyHandler())
browser.set_handle_robots(False)
browser.set_debug_http(False)
# CiteUlike rejects the default user-agent
browser.addheaders = [('User-agent', 'citeulike uploader/username=%s' % options.username)]

#
# This tag is added to all created article, mainly so they can be easily deleted in
# case of SNAFU
#
COPY_TAG="*repost-%s" % datetime.now().strftime("%Y%m%d-%H%M%S")

login(options.username, options.password)

articles = json.load(open(options.srcfile))
print "Got %s articles (total)" % len(articles)

# filter out checked articles
articles = [a for a in articles if a["is_unchecked"] == "Y"]
print "Got %s articles (unchecked)" % len(articles)

# This stores articles that couldn't be posted.  It's dumped to STDOUT at the end
failed = []

count = 0
for article in articles:
	count = count + 1
	print "========================================================================="
	print "%s: Posting: %s" % (count, article["title"])
	status = post(article)
	if status < 0:
		failed.append(article)

	# A few article is fine, otherwise don't post too fast!
	pause()

if len(failed) > 0:
	print "========================================================================"
	print "Failed to post:"
	print json.dumps(failed,indent=4)
