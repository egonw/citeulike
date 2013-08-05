#!/usr/bin/env python2.6
# Copyright (c) 2011 Fergus Gallagher <fergus@citeulike.org>
# All rights reserved.
#
# This code is derived from software contributed to CiteULike.org
# by
#    Fergus Gallagher
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

import socket, codecs, sys, cookielib, urllib2
from urlparse import urlparse, parse_qs
from cultools import urlparams, bail

import metaheaders

socket.setdefaulttimeout(15)
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

# Read URL from stdin
url = sys.stdin.readline().strip()

u = urlparse(url)

# urlparse('http://www.cwi.nl:80/%7Eguido/Python.html')
# ParseResult(scheme='http', netloc='www.cwi.nl:80', path='/%7Eguido/Python.html',  params='', query='', fragment='')
q = parse_qs(u.query)
if (q.has_key("articleid")):
	article_id = q["articleid"][0]
else:
	bail("Could not determine the articleId")
	
# http://proceedings.spiedigitallibrary.org/downloadCitation.aspx?format=ris&articleid=763979
ris_file_url = "http://%s/downloadCitation.aspx?format=ris&articleid=%s" % (u.netloc, article_id)
cookie_jar = cookielib.CookieJar()
handlers = []
handlers.append( urllib2.HTTPHandler(debuglevel=0) )
handlers.append( urllib2.HTTPCookieProcessor(cookie_jar) )


opener=urllib2.build_opener(*handlers)
opener.addheaders = [("User-Agent", "CiteULike/1.0 +http://www.citeulike.org/")]
urllib2.install_opener(opener)

try:
	ris_file = urllib2.urlopen(ris_file_url).read()
except:
	bail("Could not fetch RIS file (" + ris_file_url + ")")

metaheaders = metaheaders.MetaHeaders(url)

print "begin_tsv"

if metaheaders.get_item("citation_conference") or metaheaders.get_item("citation_conference_title"):
	print "type\tINCONF"
else:
	print "type\tJOUR"

doi = metaheaders.get_item("citation_doi")
if doi:
	doi = doi.replace("doi:","")
	print "doi\t%s" % doi
	print "linkout\tDOI\t\t%s\t\t" % (doi)
else:
	bail("Couldn't find an DOI")
print "end_tsv"
print "begin_ris"
print "%s" % (ris_file)
print "end_ris"
print "status\tok"
