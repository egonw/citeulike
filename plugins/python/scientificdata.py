#!/usr/bin/env python2.7

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

match = re.search(r'//www.nature.com/articles/sdata(\d+)', url, re.IGNORECASE)
if not match:
	bail("Cannot parse Scientific Data paper. Unrecognized URL: " + url + " - does the plugin need updating?")

artId = match.group(1)

#
# Fetch the page
#
try:
	page = urllib2.urlopen(url).read().strip()
except:
	bail("Couldn't fetch page (" + url + ")")

print "begin_tsv"
print "publisher\tNature Publishing Group"

#
# DOI is in the page
#
metaheaders = metaheaders.MetaHeaders(page=page)
doi_str = metaheaders.get_item("citation_doi")
doi_match = re.search(r'doi:(10\.[^/]+/[^\s]+)', doi_str,  re.IGNORECASE)

doi = None
if doi_match:
	doi = doi_match.group(1)
else:
	bail("Couldn't find an DOI")

if doi:
	print "linkout\tDOI\t\t%s\t\t" % doi
else:
	bail("Couldn't find an DOI")

print "linkout\tSCIDAT\t\t%s\t\t" % artId

root = metaheaders.root

abstractDiv = root.xpath("//div[@id='abstract-section']/p/text()")

if abstractDiv:
	abstract = abstractDiv[0]
else:
	abstract = None

if not metaheaders.get_item("citation_title"):
	bail("Cannot find a title in that article")

print "type\tJOUR"

metaheaders.print_item("title","citation_title")
authors = metaheaders.get_multi_item("citation_author")
if authors:
	for a in authors:
		print "author\t%s" % a.encode("utf-8")

journal = metaheaders.get_item("citation_journal_title")
if journal:
	print "journal\t%s" % journal

issn = metaheaders.get_item("citation_issn")
if issn:
	print "issn\t%s" % issn

volume = metaheaders.get_item("citation_volume")
if volume:
	print "volume\t%s" % volume

start_page = metaheaders.get_item("citation_firstpage")
if start_page:
	print "start_page\t%s" % start_page

metaheaders.print_date("citation_publication_date")

if abstract:
	print "abstract\t%s" % abstract.encode("utf-8")

print "end_tsv"
print "status\tok"
