#!/usr/bin/env python

# Copyright (c) 2014 Egon Willighagen <egonw@users.sf.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import re, sys, urlparse, urllib2
from cultools import urlparams, bail
import socket
import metaheaders

socket.setdefaulttimeout(15)

#
# Read URL from stdin and check it's OK
#
url = sys.stdin.readline().strip()

m = re.search(r'//figshare.com/articles/([^/]+)/(\d+)', url, re.IGNORECASE)
if not m:
	bail("Unrecognised site: " + url_host + " - does the plugin need updating")

fg_descr = m.group(1)
fg_id = m.group(2)

#
# Fetch the page
#
try:
	page = urllib2.urlopen(url).read().strip()
except:
	bail("Couldn't fetch page (" + url + ")")

#
# DOI is in the page
#
metaheaders = metaheaders.MetaHeaders(page=page)
doi_str = metaheaders.get_item("citation_doi")
doi_match = re.search(r'doi:(10\.[^/]+/[^\s]+)', doi_str,  re.IGNORECASE)

if doi_match:
	doi = doi_match.group(1)
else:
	bail("Couldn't find an DOI")

root = metaheaders.root

abstractDiv = root.xpath("//div[@id='article_desc']/div/p/text()")

if abstractDiv:
	abstract = abstractDiv[0]
else:
	abstract = None

if not metaheaders.get_item("citation_title"):
	bail("Cannot find a title in that article")

print "begin_tsv"
print "publisher\tfigshare"
print "type\tGEN"

if metaheaders.get_item("citation_title"):
	metaheaders.print_item("title","citation_title")
	authors = metaheaders.get_multi_item("citation_author")
	if authors:
		for a in authors:
			print "author\t%s" % a
	metaheaders.print_date("citation_publication_date")

print "linkout\tDOI\t\t%s\t\t" % doi
print "linkout\tFIGSHR\t%s\t%s\t\t" % (fg_id, fg_descr)

if abstract:
	print "abstract\t%s" % abstract

print "end_tsv"
print "status\tok"
