#!/usr/bin/env python

import sys,re, json, urllib, os
from urlparse import urlparse, urljoin
import mechanize
import lxml.html
from subprocess import Popen, PIPE, STDOUT
import logging

#
# Mechanize (which uses BeautifulSoup, I think) doesn't like our HTML, so we
# need the nuclear options of cleaning it up with "tidy" (BeautifulTree and
# lxml both fail - we need to look at our XHTML!)
#
class PrettifyHandler(mechanize.BaseHandler):

	def __init__(self, tidybin=None):
		if tidybin==None:
			tidybin="/usr/bin/tidy"

		self.tidybin=tidybin

	def http_response(self, request, response):
		if not hasattr(response, "seek"):
			response = mechanize.response_seek_wrapper(response)
		if response.info().dict.has_key('content-type') and ('html' in response.info().dict['content-type']):

			p = Popen([self.tidybin, "-q", "-i"], stdout=PIPE, stdin=PIPE, stderr=PIPE)

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


class CULBrowser:

	def __init__(self, username=None, password=None, baseurl="http://www.citeulike.org", appname="browser", tidybin=None, group_id=None):
		self.username = username
		self.password = password
		self.baseurl = baseurl
		self.group_id = group_id
		self.logger = logging.getLogger(str(self.__class__))


		self.browser = mechanize.Browser()
		self.browser.add_handler(PrettifyHandler(tidybin=tidybin))
		self.browser.set_handle_robots(False)
		self.browser.set_debug_http(False)
		# CiteUlike rejects the default user-agent
		self.browser.addheaders = [('User-agent', 'citeulike %s/username=%s' % (appname, self.username)), ("Connection", "close")]

		if username:
			self.login()

	################################################################################
	#
	# Utility to debug forms
	#
	def dump_form(self):
		for n in [c for c in self.browser.controls]:
			print ">>>> ",n
	################################################################################
	#
	#
	#
	def get_library_path(self):
		if self.group_id:
			return "/group/%s" % (self.group_id,)
		else:
			return "/user/%s" % (self.username,)

	################################################################################
	#
	# Normally can only select by name (though I think this is fixed in newer
	# versions of mechanize).  Luckily, there's a backdoor.
	#
	def select_form_by_id(self, id):
		self.browser.select_form(predicate=lambda f: 'id' in f.attrs and f.attrs['id'] == id)

	################################################################################
	#
	# Had some problems with requests hanging so wrote this to ensure that
	# data was read properly.  Not sure this helps, but no harm...
	#
	def do_submit(self):
		self.logger.debug("SUBMIT:from=%s; to=%s" % (self.browser.geturl(), self.browser.form.action))
		self.browser.submit()
		return self.browser.response().get_data()


	################################################################################
	#
	# see comments on do_sumit to see why this func exists.
	#
	def GET(self, url):
		url = urljoin(self.baseurl,url)
		self.logger.debug("GET:%s" % url)
		self.browser.open(url)
		return self.browser.response().get_data()

	def POST(self, url, params):
		url = urljoin(self.baseurl,url)
		self.logger.debug("POST:%s <= %s" % (url, params))
		self.browser.open(url, params)
		return self.browser.response().get_data()

	def get_root(self):
		page = self.browser.response().get_data()
		return lxml.html.document_fromstring(page)



	########################################################################
	#
	#  Download src -> local file dest.
	#  Optionally create path,
	#
	def download(self, src, dest, createPath=False, cache=False):
		if os.path.isfile(dest):
			self.logger.info("Already in cache "+dest)
			return

		self.logger.info("Downloading "+dest)

		(path, fname) = os.path.split(dest)
		if createPath and not os.path.exists(path):
			try:
				os.makedirs(path)
			except OSError, e:
				if e.errno != errno.EEXIST:
					raise
		if not os.path.exists(path):
			raise RuntimeError("Path %s does not exist")

		self.browser.retrieve(urljoin(self.baseurl,src),dest)

	################################################################################
	#
	# Login to CiteULike using the normal form
	#
	def login(self):
		# "from" here is a "cheap" URL (The default listing page is slow
		# and expensive)
		url = "/login?from=/profile/%s/export" % self.username
		self.logger.info("login:%s (to %s)" % (self.username, url))
		self.GET(url)
		self.browser.select_form(name="frm")

		self.browser["username"] = self.username
		self.browser["password"] = self.password

		page = self.do_submit()

		root = lxml.html.document_fromstring(page)

		logged_in = False

		# <link rel="stylesheet" type="text/css" media="all" href="/static/css/gold.fab0fdb5c5051bf6823a82ca531823ce.css" />
		#print self.check_header(root, "stylesheet", tag="link", attr="rel", content="href", returnall=True )

		#
		# Look for a magic meta header. Not yet implemented
		#
		h = self.check_header(root, "logged_in")
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
	# Look for a <meta name="NAME" content="CONTENT"> header from HTML and return
	# CONTENT.
	# Overrides to look for any similar tag <TAG ATTR="NAME" CONTENT="xxxxxx" >
	#
	def check_header(self, root, name, tag="meta", attr="name", content="content", returnall=False):
		# default is meta[name="<NAME>"]

		# Return all matching
		if returnall:
			ret = []
			for m in root.cssselect('%s[%s="%s"]' % (tag, attr, name)):
				ret.append(m.attrib[content])
			return ret

		# return just first
		for m in root.cssselect('%s[%s="%s"]' % (tag, attr, name)):
			return m.attrib[content]

		return None

	################################################################################
	#
	#
	#
	def get_article(self, url=None, article_id=None, raw=False, format="json"):
		if article_id:
			url = self.get_library_path()+"/article/"+article_id

		json_url = "/json%s" % (url,)
		if raw:
			json_url = json_url+"?raw=1"

		self.logger.debug("Downloading json from %s" % json_url)

		resp = self.GET(json_url)

		return json.loads(resp)[0]

	################################################################################
	#
	# The browser's current location.  By default it returns just the /path component.
	#
	def geturl(self):
		return self.browser.geturl()

	################################################################################
	#
	#  Add a set of tags (space delimited) to the given article
	#
	def add_tags(self, article_id, tags):
		# We need a context so /do_list_tag can infer user or group
		context="%s/article/%s" % (self.get_library_path(), article_id)

		qs=urllib.urlencode([
			("action","Add"),
			("tags", tags),
			("from",context),
			("article_id",article_id)
			])

		self.logger.info("Adding tags %s to %s" % (tags, article_id))
		self.POST("/do_list_tag", qs);

	################################################################################
	#
	# Load an article's page (to load the form)
	#
	def loadArticlePage(self, article):
		self.GET(article["href"])

if __name__ == '__main__':
	"""
		Simple test.  run with USERNAME PASSWORD on the command line
	"""
	(un,pw) = sys.argv[1:]
	br = CULBrowser(un,pw)
	br.login()




