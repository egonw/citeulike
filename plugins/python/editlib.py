#!/usr/bin/env python

# Copyright (c) 2006, all rights reserved.
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
#                CiteULike <http://www.citeulike.org> and its
#                contributors.
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
from urllib import urlopen
import socket

socket.setdefaulttimeout(15)


# error messages
ERR_STR_NOID = "No ID found in this URL: "
ERR_STR_FETCH = 'Unable to fetch the bibliographic data: '
ERR_STR_TRY_AGAIN = 'The server may be down.  Please try later.'

DEFAULT_TYPE = "GEN"
TYPE_LOOKUP = {
	'book': "BOOK",
	'inbook': "CHAP",
	'proceedings': "CONF",
	'misc': "GEN",
	'incollection': "INCOL",
	'inproceedings': "INCONF",
	'unpublished': "INPR",
	'article': "JOUR",
	'manual': "MANUAL",
	'mastersthesis': "MTHES",
	'booklet': "PAMP",
	'techreport': "REP",
	'phdthesis': "THES",
	'unpublished': "UNPB",
}

# read url from standard input
url = sys.stdin.readline()
# strip newline at the end
url = url.strip()

paper_id_match = re.search("^http://(?:www\.)?editlib\.org/(?:p/|.*paper_id=)(?P<paper_id>\d+)", url)
if not paper_id_match:
    print 'status\terr\t' + ERR_STR_FETCH + url + '.'
    sys.exit(0)
paper_id = int(paper_id_match.groupdict()['paper_id'])

biburl = "http://editlib.org/p/%d/export/bibtex/" % paper_id

# fetch the bib file
try:
    f = urlopen(biburl)
except:
    print 'status\terr\t' + ERR_STR_FETCH + url + '.  ' + ERR_STR_TRY_AGAIN
    sys.exit(0)

bib = f.read()

# check if we got BibTeX or a HTML page redirecting to the pdf file (some
# papers have pdf only)
if bib.find('author') == -1 or bib.find('title') == -1 or bib.find('year') == -1:
    print 'status\tnot_interested'
    print biburl, bib
    sys.exit(0)

# strip newlines at the end
bib = bib.strip()
bib = re.sub(r'^[@]', '', bib)


citation_type = DEFAULT_TYPE
for bib_type, cite_type in TYPE_LOOKUP.items():
    if re.search(r"\s*@%s\s*\{" % bib_type, bib):
        citation_type = cite_type
        break

#sys.stderr.write("\n\n\nTYPE: %s\n" % citation_type)
#sys.stderr.write("\nBIB: %s\n\n\n" % bib)

# print the results
print 'begin_tsv'
print "linkout\tEdIT\t%s\t\t\t" % paper_id
print 'type\t%s' % citation_type
print 'end_tsv'
print 'begin_bibtex'
print bib
print 'end_bibtex'
print 'status\tok'

