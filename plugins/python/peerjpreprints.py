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

match = re.search(r'//peerj.com/preprints/(\w+)', url, re.IGNORECASE)
if not match:
	bail("Cannot parse PeerJ PrePrintsl. Unrecognized URL: " + url + " - does the plugin need updating?")

artId = match.group(1)
doi = "10.7717/peerj.preprints." + artId

#
# Fetch the page
#
try:
	page = urllib2.urlopen(url).read().strip()
except:
	bail("Couldn't fetch page (" + url + ")")

print "begin_tsv"
print "publisher\tPeerJ Inc."

#
# DOI is in the page
#
metapropsheaders = metaheaders.MetaHeaders(name="property", page=page)
metaheaders = metaheaders.MetaHeaders(page=page)
doi = metaheaders.get_item("citation_doi")
if doi:
	print "linkout\tDOI\t\t%s\t\t" % doi
	print "linkout\tPEERJP\t\t%s\t\t" % artId
else:
	bail("Couldn't find an DOI")

docType = metapropsheaders.get_item("og:type");
if not docType:
	bail("Cannot determine the publication type")

if docType != "article":
	bail("Only supports journal papers ('article', 'JOUR') at this moment, but found " + docType)

if not metaheaders.get_item("citation_title"):
	bail("Cannot find a title in that article")

print "type\tREP"

metaheaders.print_item("title","citation_title")
authors = metaheaders.get_multi_item("citation_author")
if authors:
	for a in authors:
		print "author\t%s" % a

journal = metaheaders.get_item("citation_technical_report_institution")
if journal:
	print "journal\t%s" % journal

issn = metaheaders.get_item("citation_issn")
if issn:
	print "issn\t%s" % issn

abstract = metaheaders.get_item("description")
if abstract:
	print "abstract\t%s" % abstract

start_page = metaheaders.get_item("citation_firstpage")
if start_page:
	print "start_page\t%s" % start_page

metaheaders.print_date("citation_date")

print "end_tsv"
print "status\tok"
