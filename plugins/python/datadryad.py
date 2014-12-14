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

import re, sys, urlparse, urllib2, codecs
from cultools import urlparams, bail
import socket
import metaheaders

socket.setdefaulttimeout(15)
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

#
# Read URL from stdin and check it's OK
#
url = sys.stdin.readline().strip()

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
dois = metaheaders.get_multi_item("DC.identifier")
doi = None
if dois:
	for doi_str in dois:
		doi_match = re.search(r'doi:(10\.[^/]+/[^\s]+)', doi_str,  re.IGNORECASE)
		if doi_match:
			doi = doi_match.group(1)
if not doi:
	bail("Couldn't find a DOI")

if not metaheaders.get_item("DC.title"):
	bail("Unable to find the article title")

print "begin_tsv"
print "publisher\tDryad Digital Repository"
print "type\tGEN"

metaheaders.print_item("title","DC.title")
authors = metaheaders.get_multi_item("DC.creator")
if authors:
	for a in authors:
		print "author\t%s" % a
metaheaders.print_date("DCTERMS.issued")

abstract = metaheaders.get_item("DC.description");
if abstract:
	print "abstract\t%s" % abstract

print "linkout\tDRYAD\t\t%s\t\t" % (doi)
print "linkout\tDOI\t\t%s\t\t" % (doi)

print "end_tsv"
print "status\tok"

