#!/usr/bin/env python

import re, urllib, sys, time, urlparse, os, errno, os.path, socket, codecs, json

from datetime import datetime
from optparse import OptionParser
from OrderedSet import OrderedSet
import ClientForm
from culutils import CULBrowser
import logging

FMT="%(levelname)-8s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FMT)

socket.setdefaulttimeout(25)


"""
Usage:
	./repost_unchecked.py -u USERNAME -p PASSWORD -f file.json
"""


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

	logging.info("Linkouts: " + str([l for l in linkouts]) )

	return linkouts


################################################################################
#
#
#
def pre_post(url):
	CUL.GET("/posturl?"+urllib.urlencode({"url": url}))

	here = CUL.geturl()

	logging.debug( "Got " + here)

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
		logging.info( "ALREADY_POSTED:(in user lib):%s" % here)
		if CUL.group_id != None:
			here = "/group/%s/article/%s" % (CUL.group_id, m.group(1))
			logging.info("Looking for group article %s" % here)
			try:
				dest_article = CUL.get_article(article_id=m.group(1))
				pass
			except:
				logging.info( "Cannot find existing group article. Will copy")
				CUL.GET("/copy?article_id=%s" % (m.group(1),))
				return "GROUP_COPY"
		else:
			logging.info("Looking for user article %s" % here)
			dest_article = CUL.get_article(url="/user/%s/article/%s" % (options.username, m.group(1)))
			if dest_article == None:
				logging.error("Not found (should never happen)")
				return None

		logging.info("Found existing article, syncing")
		sync_articles(article, dest_article)
		return "EXISTS"

	m = re.search(r'/post_unknown.adp', here)
	if m:
		logging.error("ERROR:UNKNOWN:%s" % url)
		return "UNKNOWN_URL"

	m = re.search(r'/post_error.adp', here)
	if m:
		logging.error( "ERROR:UNKNOWN:driver unable to post: %s" % url)
		return "DRIVER_ERROR"

	# Make sure we're at the actual posting page
	m = re.search(r'/posturl2', here)
	if not m:
		logging.error( "ERROR:got %s while posting %s" % (here, url))
		return None

	return "NEW"


################################################################################
#
# returns the value of the first matching <input name="NAME" value="VALUE">
#
def get_input_value(name, root=None):
	if not root:
		root = CUL.get_root()
	for m in root.cssselect('input[name="%s"]' % name):
		return m.attrib["value"]
	return None


################################################################################
#
# Post an individual article
#
def post(article):

	# This in now filtered out in the calling func. so should never fire.
	if article["is_unchecked"]!="Y":
		logging.info("Skipping checked article")
		return 2

	src_article_id = article["article_id"]

	linkouts = get_linkouts(article)

	if len(linkouts) == 0:
		logging.error("could not find a linkout")
		return -1

	url = None
	for linkout in linkouts:
		logging.info("Trying Linkout:"+linkout)

		ret = pre_post(linkout)
		if ret == None:
			pass
		elif ret == "EXISTS":
			return 1
		elif ret == "GROUP_COPY":
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
			raise RuntimeError("Unexpected return code %s" % ret)

	if url == None:
		return -1

	logging.info("Preparing to post: %s from %s" % (url,CUL.geturl()))

	CUL.browser.select_form(name="frm")

	if article.has_key("tags"):
		tags = " ".join(article["tags"])
	else:
		tags = "";

	tags = "%s %s" % (tags, COPY_TAG)

	CUL.browser["tags"] = tags

	# citation keys are a triplet - 3rd item is the user supplied one
	user_citation_key = article["citation_keys"][2]
	if user_citation_key:
		CUL.browser["bibtex_import_cite"] = user_citation_key

	logging.info("Posting %s (tags:%s; key:%s)" % (url, tags, user_citation_key))

	# make sure no libraries are selected
	# Mechinize barfs if the form elements don't exist, which is the case
	# when the article already exists in the user/group library. So catch that.
	try:
		CUL.browser["to_group"] = []
	except:
		pass
	try:
		CUL.browser["to_own_library"] = []
	except:
		pass

	if CUL.group_id:
		logging.info("Posting to group"+CUL.group_id)
		try:
			CUL.browser["to_group"] = [CUL.group_id]
		except ClientForm.ItemNotFoundError:
			logging.info("group checkbox unavailable - the article must already exist in that group")
			dest_article_id = get_input_value("article_id")
			dest_article = CUL.get_article(article_id=dest_article_id)
			sync_articles(article, dest_article)
			return 1
	else:
		logging.info("Posting to own library")
		CUL.browser["to_own_library"] = ["y"]

	# Add the 1st note - we'll sync multiple notes later.
	if article.has_key("notes") and len(article["notes"]) > 0:
		note = article["notes"][0]
		logging.debug("Note:\n%s" % note)
		CUL.browser["note"] = note["text"]
		if note["private"]:
			CUL.browser["private_note"] = ["y"]

	if article["privacy"]=="private":
		CUL.browser["is_private"] = "Y"

	# make sure we don't go to journal page
	# this might not exist if we're copying, which is the case when
	# posting to a group (since we've gone via the "copy" page)
	try:
		CUL.browser["to_orig"] = []
	except:
		pass

	# reading priority
	CUL.browser["to_read"] = [article["priority"]]

	CUL.do_submit()

	new_url = CUL.geturl()

	m = re.search(r'/article/(\d+)', new_url)
	if not m:
		logging.error("unexpected page %s" % new_url)
		return -1

	dest_article_id = m.group(1)

	# should never happen as it should have been trapped earlier.
	#if not CUL.group_id and dest_article_id == src_article_id:
	if dest_article_id == src_article_id:
		logging.error("src and dest articles the same")
		return -1

	logging.info( "POSTED:%s as %s" % (url, new_url))

	#
	# OK sync up metadata and attachments
	#
	dest_article = CUL.get_article(url=new_url)
	if dest_article == None:
		return -1

	# We don't need the extra sync-tags since we're copying all in the first
	# place.
	sync_articles(article, dest_article, sync_all_tags=False)

	#
	# TODO: add a tag to src article to show that it's been reposted.
	# I guess the duplicates page does this for the time being.
	#

	return 1



################################################################################
#
#
#
def sync_articles(src_article, dest_article, sync_all_tags=True):
	logging.info("Syncing from %s to %s" % (src_article["article_id"], dest_article["article_id"]))
	if src_article["article_id"] == dest_article["article_id"]:
		logging.error("Source and destination articles the same")
		raise RuntimeError("Source and destination articles the same")
	if options.copy_attachments:
		sync_userfiles(src_article, dest_article)
	sync_notes(src_article, dest_article)
	sync_metadata(src_article, dest_article)
	sync_cito(src_article, dest_article)
	if sync_all_tags:
		sync_tags(src_article, dest_article)
	add_tags(src_article, SRC_TAG)

################################################################################
#
#
#
def sync_tags(src_article, dest_article):
	if src_article.has_key("tags"):
		logging.info( "Syncing tags")
	else:
		logging.info( "No tags")
		return

	dest_tags = []
	for t in src_article["tags"]:
		# Don't copy some tags
		if re.search(r'^(no-tag|\*repost-)', t):
			continue
		dest_tags.append(t)
	add_tags(dest_article, " ".join(dest_tags))


################################################################################
#
#
#
def sync_cito(src_article, dest_article):
	if src_article.has_key("cito"):
		logging.info("Syncing CiTO")
	else:
		logging.info("No CiTO")
		return

	this_article_id = dest_article["article_id"]

	for c in src_article["cito"]:
		qs=urllib.urlencode([
				("this_article_id", this_article_id),
				("that_article_id", c["article_id"]),
				("from",            CUL.get_library_path()),
				("cito_code",       c["relation"])
		])
		CUL.POST("/add_cito.json.do?", qs)
#			"this_article_id=%s&that_article_id=%s&cito_code=%s&from=%s" %
#			(this_article_id,c["article_id"],c["relation"],CUL.get_library_path()))


################################################################################
#
#
#
def sync_metadata(src_article, dest_article):
	logging.info("Syncing metadata")
	CUL.GET("/edit_article_details?user_article_id=%s" % (dest_article["user_article_id"]))
	CUL.browser.select_form(predicate=lambda f: 'id' in f.attrs and f.attrs['id'] == 'article')

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

	fields = CUL.browser.controls
	#fields = [f for f in fields if f.name == "abstract" ]

	for n in [c for c in fields]:
		cname = n.name

		if cname and form_name_map.has_key(cname) and form_name_map[cname] and src_article.has_key(form_name_map[cname]):
			v = src_article[form_name_map[cname]]
			v = v.encode("utf-8","ignore")
			CUL.browser[cname] = v

	#CUL.do_submit()
	#return

	if src_article.has_key("published"):
		published = src_article["published"]
		if len(published) > 0:
			CUL.browser["year"]  = published[0]
		if len(published) > 1:
			CUL.browser["month"]  = [str(int(published[1]))]
		if len(published) > 2:
			CUL.browser["day"]  = published[2]

	if src_article.has_key("authors"):
		CUL.browser["authors"] = "\n".join([a.encode("utf-8","ignore") for a in src_article["authors"]])

	if src_article.has_key("editors"):
		CUL.browser["editors"] = "\n".join([a.encode("utf-8","ignore") for a in src_article["editors"]])

	CUL.do_submit()


################################################################################
#
#
#
def add_tags(article, tags):
	CUL.add_tags(article["article_id"],tags)

################################################################################
#
#
#
def sync_notes(src_article, dest_article):
	if not src_article.has_key("notes"):
		logging.info("No notes to sync")
		return

	logging.info("Syncing notes")

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

	CUL.loadArticlePage(dest_article)
	for n in wanted:
		logging.info("Syncing note: "+n["text"])

		CUL.select_form_by_id("addnote_frm")
		CUL.browser["text"] = n["text"]
		if n["private"]:
			CUL.browser["private_note"] = ["y"]
		# returns us to article page, so OK in loop
		CUL.do_submit()

################################################################################
#
#
#
def sync_userfiles(src_article, dest_article):
	if not src_article.has_key("userfiles"):
		logging.info("No attachments to sync")
		return

	logging.info("Syncing attachments")

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
			logging.info( "To sync: "+f["name"])
			wanted.append(f)
		else:
			logging.info( "Skipping: "+f["name"]+" (already exists in destination)")

	CUL.loadArticlePage(dest_article)
	for f in wanted:
		s = options.cachedir+"/"+f["sha1"]
		logging.info("Syncing: "+f["path"])
		CUL.download(f["path"],s, cache=True)

		CUL.browser.select_form(name="fileupload_frm")
		CUL.browser.add_file(open(s), 'application/octet-stream', f["name"])
		try:
			CUL.browser["rightsholder"] = ["true"]
		except:
			pass
		CUL.browser["keep_name"] = ["yes"]
		CUL.do_submit()


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
		help="Don't copy attachments")

parser.add_option("-f", "--file",
		dest="srcfile",
		help="Source JSON file")

parser.add_option("--no-pause",
		dest="pause",
		action="store_false",
		default=True,
		help="Don't pause between posts.  Please don't use this or you might get blocked.")

parser.add_option("--tidy",
		dest="tidybin",
		default="/usr/bin/tidy",
		help="Location of the tidy binary (default /usr/bin/tidy)")

(options, args) = parser.parse_args()

if not options.username or not options.password:
	print "Supply username/password"
	sys.exit()

if not options.srcfile:
	print "Supply source JSON file"
	sys.exit()

FILE_CACHE_DIR=options.cachedir
try:
	os.makedirs(FILE_CACHE_DIR)
except OSError, e:
	if e.errno != errno.EEXIST:
		raise

#
# This tag is added to all created article, mainly so they can be easily deleted in
# case of SNAFU
#
COPY_TAG="*repost-%s" % datetime.now().strftime("%Y%m%d-%H%M%S")
SRC_TAG=COPY_TAG+"-unchecked"

articles = json.load(open(options.srcfile))

#
# Check the articles are all in the same library.  Infer the group_id.
#
group_id = None
found_userlib = False
for article in articles:
	href= article["href"]
	m = re.search(r'/user/([^/]+)', href)
	if m:
		if options.username != m.group(1):
			print "ERROR: Articles must be from the your library.  Found %s, expected /user/%s" % (href, options.username)
			sys.exit(0)
		if group_id:
			print "ERROR: All articles must be from the same library.  Found %s, expected /group/%s" % (href, group_id)
			sys.exit(0)
		found_userlib = True
	m = re.search(r'/group/(\d+)', href)
	if m:
		if found_userlib:
			print "ERROR: All articles must be from the same library.  Found %s, expected /user/%s" % (href, options.username)
			sys.exit(0)
		if group_id and group_id != m.group(1):
			print "ERROR: All articles must be from the same library.  Found %s, expected /group/%s" % (href, group_id)
			sys.exit(0)
		group_id = m.group(1)

if group_id:
	print "Syncing to group library:", group_id
else:
	print "Syncing to user library:", options.username


# filter out checked articles
print "Got %s articles (total)" % len(articles)
articles = [a for a in articles if a["is_unchecked"] == "Y"]
print "Got %s articles (unchecked)" % len(articles)

#
# If user adds "skip":"Y" to a JSON article, it will be ignored.  Poss
# useful if there's a tricky article that bombs out in an otherwise postable
# list.
#
pre_skip = len(articles)
articles = [a for a in articles if not a.has_key("skip") or a["skip"] not in ["Y","y"]]
post_skip = len(articles)
if pre_skip != post_skip:
	print "Skipped %s articles" % (pre_skip-post_skip,)

CUL = CULBrowser(username=options.username, password=options.password,
	group_id=group_id, baseurl=options.baseurl)

# This stores articles that couldn't be posted.  It's dumped to STDOUT at the end
failed = []

count = 0
for article in articles:
	count = count + 1
	print "========================================================================="
	print "%s: Posting: %s (%s)" % (count, article["title"], article["article_id"])
	status = post(article)
	print "status:",status
	if status < 0:
		failed.append(article)

	# A few article is fine, otherwise don't post too fast!
	pause()

if len(failed) > 0:
	print "========================================================================"
	print "Failed to post:"
	print json.dumps(failed,indent=4)
