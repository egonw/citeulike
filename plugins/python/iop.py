#!/usr/bin/env python

#
# Copyright (c) 2005 Kristinn B. Gylfason <citeulike@askur.org>
# All rights reserved.
#
# This code is derived from software contributed to CiteULike.org
# by
#    Diwaker Gupta
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
#

import re
import sys
import urllib2

BIBTEX_SERVER_ROOT = 'http://www.iop.org/EJ/sview/'
BIBTEX_SERVER_POST_STR = 'submit=1&format=bibtex'

# general regexp for document object identifier (DOI) screen scraping
DOI_REGEXP = r"""doi:\s*	# strip whitespace at begining
		(10\.\S*?)/	# valid DOI prefixes start with '10.'
		(.*?)		# DOI suffixes can be anything
		\s*<"""		# terminate at next tag open (strip witesp.)
DOI_REGEXP_FLAGS = re.IGNORECASE | re.VERBOSE

# regexp for grabing keys for the linkout formater from the bibtex url field
LINKOUT_REGEXP = r"""url\s*=\s*{\s*http://stacks.iop.org/	# base url
		(\d*-\d*)/	# journal key
		(\d*)/		# volume key
		(\w*)		# page key
		\s*}"""		# terminate at closing brace(strip witesp.)
LINKOUT_REGEXP_FLAGS = re.IGNORECASE | re.VERBOSE

# regexp for screen scraping keywords
KEYWORD_REGEXP = r"""<I>Keywords:</I>\s*
		(.*?)
		\s*</SPAN>"""	# terminate at closing brace(strip witesp.)
KEYWORD_REGEXP_FLAGS = re.DOTALL | re.VERBOSE

# error messages
ERR_STR_PREFIX = 'status\terr\t'
ERR_STR_FETCH = 'Unable to fetch the page: '
ERR_STR_TRY_AGAIN = 'The server may be down.  Please try later.'
ERR_STR_NO_DOI = 'No document object identifier found on the page: '
ERR_STR_NO_BIBTEX = 'No BibTeX entry found for the DOI: '
ERR_STR_NO_URL = 'No URL found in the BibTeX entry for the DOI: '
ERR_STR_REPORT = 'Please report the error to plugins@citeulike.org.'

# read url from std input
url = sys.stdin.readline()
# get rid of the newline at the end
url = url.strip()

# fetch the page the user is viewing and exit gracefully in case of trouble
try:
	f = urllib2.urlopen(url)
except:
	print ERR_STR_PREFIX + ERR_STR_FETCH + url + '.  ' + ERR_STR_TRY_AGAIN
	sys.exit(1)

content = f.read()

# screen scrape the DOI from the page and exit gracefully if not found
doi_match  = re.search(DOI_REGEXP, content, DOI_REGEXP_FLAGS)
if not doi_match:
	print ERR_STR_PREFIX + ERR_STR_NO_DOI + url + '.  ' + ERR_STR_REPORT
	sys.exit(1)

doi_prefix = doi_match.group(1)
doi_suffix = doi_match.group(2)
doi = doi_prefix + '/' + doi_suffix

# screen scrape keywords displayed on the page (if any)
keyword_match  = re.search(KEYWORD_REGEXP, content, KEYWORD_REGEXP_FLAGS)
if keyword_match:
	keywords = keyword_match.group(1)
	# strip newlines
	keywords = ' '.join(keywords.splitlines())
	# strip HTML tags 
	# (http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/275370)
	from sgmllib import SGMLParser
	class XMLJustText (SGMLParser):
		just_text = ''
		def handle_data (self,data):
			self.just_text = self.just_text + ' ' + data

	parser = XMLJustText()
	parser.feed(keywords)
	keywords = parser.just_text.replace(',',';').strip()

# fetch the BibTeX entry for the DOI and exit gracefully in case of trouble
req = urllib2.Request(BIBTEX_SERVER_ROOT + doi_suffix)
req.add_data(BIBTEX_SERVER_POST_STR)
try:
	f = urllib2.urlopen(req)
except:
	print ERR_STR_PREFIX + ERR_STR_NO_BIBTEX + doi + '.  ' + ERR_STR_REPORT
	sys.exit(1)

bibtex_entry = f.read()
# get rid of the extra newline at the end
bibtex_entry = bibtex_entry.strip()
#print bibtex_entry

# grab the keys for the linkout formater from the BibTeX url field
linkout_match  = re.search(LINKOUT_REGEXP, bibtex_entry, LINKOUT_REGEXP_FLAGS)
if not linkout_match:
	print ERR_STR_PREFIX + ERR_STR_NO_URL + doi + '.  ' + ERR_STR_REPORT
	sys.exit(1)

linkout_journal = linkout_match.group(1)
linkout_volume = linkout_match.group(2)
linkout_page = linkout_match.group(3)

# print the results
print "begin_tsv"
print "linkout\tIOP\t%s\t%s\t\t%s" % \
	(linkout_volume, linkout_journal, linkout_page)
print "linkout\tDOI\t\t%s\t\t" % (doi)
print "type\tJOUR"
print "doi\t" + doi
if keyword_match: print "keywords\t" + keywords
print "end_tsv"
print "begin_bibtex"
print bibtex_entry
print "end_bibtex"
print "status\tok"
