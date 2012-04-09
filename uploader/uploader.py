#!/usr/bin/env python

import mechanize
import lxml.html
import re, urllib, csv, sys, time
from optparse import OptionParser

browser = mechanize.Browser()
browser.set_handle_robots(False)
browser.set_debug_http(False)

BASE="http://www.citeulike.org"

################################################################################
def check_header(page, name):
	root = lxml.html.document_fromstring(page)
	for m in root.cssselect("meta"):
		attr=m.attrib
		if attr.has_key("name") and attr["name"] == name:
			return attr["content"]

	return None

################################################################################
def login(username, password):
	browser.open(BASE+"/login?from=/profile/"+username)
	browser.select_form(name="frm")

	browser["username"] = username
	browser["password"] = password

	response = browser.submit()

	page =  response.read()

	logged_in = False

	#
	# Look for a magic meta header. Not yet implemented
	#
	h = check_header(page, "logged_in")

	if h and h == "yes":
		logged_in = True

	# Use a cruder check, whether the "[logout]" link exists
	if not logged_in:
		root = lxml.html.document_fromstring(page)
		for b in root.cssselect('#logout_button'):
			logged_in = True
			break

	assert logged_in, "Unable to log in"

################################################################################
def post(url, tags=None):

	print "Posting %s" % url

	browser.open(BASE+"/posturl?"+urllib.urlencode({"url": url}))

	here = browser.geturl()

	m = re.search(r'show_msg=already_posted', here)
	if m:
		print "ALREADY_POSTED:%s" % url
		return

	m = re.search(r'/post_unknown.adp', here)
	if m:
		print "UNKNOWN:%s" % url
		return

	m = re.search(r'/posturl2', here)
	if not m:
		print "ERROR:%s" % url
		return

	print "Preparing to post: %s" % url

	browser.select_form(name="frm")

	if tags:
		browser["tags"] = tags

	browser.submit()
	print "POSTED:%s" % url

################################################################################

if ( len(sys.argv) == 1 ):
	sys.argv.append("-h")

parser = OptionParser()

parser.add_option("-u", "--username",
		dest="username",
		help="citeulike username",
		metavar="U")

parser.add_option("-p", "--password",
		dest="password",
		help="citeulike username",
		metavar="P")

parser.add_option("-b", "--base",
		dest="base",
		help="base URL",
		metavar="B")

(options, args) = parser.parse_args()

if options.base:
	BASE=options.base

if not options.username or not options.password:
	print "Supply username/password"
	sys.exit()

# CiteUlike rejects the default user-agent
browser.addheaders = [('User-agent', 'citeulike uploader/username=%s' % options.username)]

login(options.username, options.password)

lines = csv.reader(sys.stdin)
for r in lines:
	(url, tags) = r
	post(url,tags)
	# Don't post too fast!
	time.sleep(5)
