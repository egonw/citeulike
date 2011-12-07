#!/usr/bin/env python2.6

#
# Copyright (c) 2008 Richard Cameron
# All rights reserved.
#

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#        This product includes software developed by
#		 CiteULike <http://www.citeulike.org> and its
#		 contributors.
# 4. Neither the name of CiteULike nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CITEULIKE.ORG AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import urllib, re, sys, codecs
import socket, subprocess
from metaheaders import MetaHeaders

socket.setdefaulttimeout(15)
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

def url_to_id(url, page):


	# first try meta headers
	metaheaders = MetaHeaders(page=page,name='scheme')

	jstoreId = metaheaders.get_item("jstore-stable")
	doi = metaheaders.get_item("doi")

	if doi and jstoreId:
		print "doi=%s, id=%s" % (doi,jstoreId)
		return (jstoreId, doi)

	# If there's a doi=DOI in the URL then we'll have that
	m = re.search(r'doi=(10.\d\d\d\d/(\d+))', url)
	if m:
		return (int(m.group(2)),m.group(1))
	m = re.search(r'doi=(10.\d\d\d\d/.+)', url)
	if m:
		return (None,m.group(1))

	# If it's the old style SICI then, annoyingly, we'll need to fetch it
	if 'sici=' in url:
		m = re.search(r'<a id="info" href="/stable/(\d+)">Article Information</a>', page)
		if m:
			return (int(m.group(1)), None)
		else:
			return (None, None)

	# Otherwise assume anything which looks like /123123/ is an ID
	#m = re.search(r'https?://.*?jstor.+?/(\d{4,})(/|$|\?|#)', url)
	m = re.search(r'/(10.\d\d\d\d/(\d+))', url)
	if m:
		return (m.group(1), m.group(1))

	# sometimes there's a general DOI, no jstore ID
	m = re.search(r'/(10.\d\d\d\d/.+)', url)
	if m:
		return (None, m.group(1))


	# plain old jstore ID, at least 4 digits
	m = re.search(r'/(\d{4,})', url)
	if m:
		return (int(m.group(1)), None)

	return (None,None)

def grab_bibtex(id, doi):
	url = "http://www.jstor.org/action/downloadCitation?format=bibtex&include=abs"

	if not doi:
		doi = '10.2307/%s' % id

	params = {
		'noDoi' : 'yesDoi',
		'doi' : doi,
		'suffix' : id,
		'downloadFileName' : id }

	page = get_url("%s?%s" %  (url, urllib.urlencode(params)))

	# Remove the random junk found in the record
	m = re.search(r'@comment{{NUMBER OF CITATIONS : 1}}(.*)@comment{{ These records have been provided', page, re.M|re.DOTALL)
	if m:
		page = m.group(1)

	# This bit is fun. Book reviews come through as [untitled]. Piece things back together for them
	if "title = {Review: [untitled]}," in page and "reviewedwork_1 = {" in page:
		work_title = re.search(r'reviewedwork_1 = {(.+?)},', page).group(1)
		page = page.replace('{Review: [untitled]}', "{Review: [%s]}" % work_title)

	# pages have leading "pp. "
	page = page.replace("{pp. ","{")

	return page

def parse_citation(s):
	re.compile(r'<li class="sourceInfo">\s+<cite>(.*?)</cite>, Vol. ([^,]+)')

# JSTOR barfs at normal python urllib, so spawn lynx, which seem to work
def get_url(url):
	#return subprocess.Popen(["lynx", "-source", "-read_timeout", "10", url],stdout=subprocess.PIPE).stdout.read()
	page = subprocess.Popen(["lynx", "-source", url],stdout=subprocess.PIPE).stdout.read()
	page = page.decode("utf-8")
	return page


def main(id, doi, page):

	print "begin_tsv"
	if id:
		print "\t".join([ "linkout", "JSTR2", "%s"%id, "", "", ""])
	# Sometimes other prefixes
	if doi:
		print "\t".join([ "linkout", "DOI", "", doi, "", ""])



	meta = MetaHeaders(page=page)
	title = meta.get_item("dc.Title")

	if doi:
		abstract = meta.get_item("dc.Description")
		if abstract:
			print "abstract\t%s" % re.sub("^ABSTRACT.\s*", "", abstract)
		meta.print_item("publisher","dc.Publisher")
		print "use_crossref\t1"
		print "end_tsv"
	elif id:
		print "end_tsv"
		print "begin_bibtex"
		print grab_bibtex(id, doi)
		print "end_bibtex"
	elif title:
		# look for meta headers
		meta = MetaHeaders(page=page)
		meta.print_item("title","dc.Title")
		abstract = meta.get_item("dc.Description")
		if abstract:
			print "abstract\t%s" % re.sub("^ABSTRACT.\s*", "", abstract)
		meta.print_item("publisher","dc.Publisher")
		# <meta name="dc.Date" scheme="WTN8601" content="Nov 17, 2011" />
		meta.print_date("dc.Date");

		authors = meta.get_multi_item("dc.Creator")
		if authors:
			for au in authors:
				print "author\t%s" % au
		article_type = meta.get_item("dc.Type")
		if article_type:
			if article_type == "book-review":
				print "type\tBOOK"
			else:
				print "type\tJOUR"
		else:
			print "type\tJOUR"

		print "end_tsv"


	print "status\tok"

if __name__=="__main__":
	import sys
	url = sys.stdin.readline().strip()

	page = get_url(url)

	(jstor_id, doi) = url_to_id(url, page)

	main(jstor_id, doi, page)
