#!/usr/bin/env python2.6

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

matched = None
doi = None
match = re.search(r'scripts.iucr.org/cgi-bin/paper\?([0-9a-zA-Z]+)', url, re.IGNORECASE)
if match:
	matched = True
	doi = "10.1107/" + match.group(1)
	key = match.group(1)
match = re.search(r'dx.doi.org/10.1107/([0-9a-zA-Z]+)', url, re.IGNORECASE)
if match:
	matched = True
	doi = "10.1107/" + match.group(1)
	key = match.group(1)
match = re.search(r'journals.iucr.org/j/issues/(.+)', url, re.IGNORECASE)
if match:
	matched = True

if not matched:
	bail("Cannot parse IUCR journal. Unrecognized URL: " + url + " - does the plugin need updating?")

#
# Fetch the page
#
try:
	page = urllib2.urlopen(url).read().strip()
except:
	bail("Couldn't fetch page (" + url + ")")

print "begin_tsv"

metaheaders = metaheaders.MetaHeaders(page=page)
if not doi:
	doiMatch = metaheaders.get_item("citation_doi");
	match = re.search(r'10.1107/([0-9a-zA-Z]+)', doiMatch, re.IGNORECASE)
	if match:
		doi = "10.1107/" + match.group(1)
		key = match.group(1)

if doi:
	print "linkout\tIUCR\t\t%s\t\t" % key
	print "linkout\tDOI\t\t%s\t\t" % doi
	print "url\thttp://dx.doi.org/" + doi
	print "doi\t" + doi
else:
	bail("Couldn't find a DOI")

if not metaheaders.get_item("DC.title"):
	bail("Cannot find a title in that article")

title = metaheaders.get_item("DC.title")
if title:
	print "title\t%s" % title.encode('utf-8')

authors = metaheaders.get_multi_item("DC.creator")
firstAuthorSurname = None
if authors:
	for a in authors:
		if not firstAuthorSurname:
			firstAuthorSurname = ""
			match = re.search(r'^([^\s|^,]+)', a.encode('utf-8'), re.IGNORECASE)
			if match:
				firstAuthorSurname = match.group(1)
		print "author\t%s" % a.encode('utf-8')

shortCode = None
if metaheaders.get_item("DC.link"):
	link = metaheaders.get_item("DC.link")
	match = re.search(r'^http://scripts.iucr.org/cgi-bin/paper\?(.+)', link, re.IGNORECASE)
	if match:
		shortCode = match.group(1)

if firstAuthorSurname:
	if shortCode:
		print "cite\t" + firstAuthorSurname + ":" + shortCode

journal = metaheaders.get_item("prism.publicationName")
if journal:
	print "journal\t%s" % journal

docType = metaheaders.get_item("DC.type");
if docType == 'text' or journal:
	print "type\tJOUR"

# if docType != "text":
#	bail("Only supports journal papers ('text', 'JOUR') at this moment, but found " + docType)


issn = metaheaders.get_item("prism.issn")
if issn:
	match = re.search(r'urn:issn:(.+)', issn, re.IGNORECASE)
	if match:
		issn = match.group(1)
	print "issn\t%s" % issn

abstract = metaheaders.get_item("DC.description")
if abstract:
	print "abstract\t%s" % abstract.encode('utf-8')

volume = metaheaders.get_item("prism.volume")
if volume:
	print "volume\t%s" % volume

issue = metaheaders.get_item("prism.number")
if issue:
	print "issue\t%s" % issue

start_page = metaheaders.get_item("prism.startingPage")
if start_page:
	print "start_page\t%s" % start_page

end_page = metaheaders.get_item("prism.endingPage")
if end_page:
	print "end_page\t%s" % end_page

publisher = metaheaders.get_item("DC.publisher")
if publisher:
	print "publisher\t%s" % publisher

if metaheaders.get_item("citation_date"):
	metaheaders.print_date("citation_date")
else:
	metaheaders.print_date("prism.coverDate")

print "end_tsv"
print "status\tok"
