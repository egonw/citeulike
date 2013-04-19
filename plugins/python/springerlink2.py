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

import socket, codecs, sys, re
from urlparse import urlparse
import urllib2, lxml.html

from cultools import bail

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
socket.setdefaulttimeout(15)

# Read URL from stdin
url = sys.stdin.readline().strip()
path = urllib2.unquote(urlparse(url).path)

# strip off proxies:
m = re.match(r'http://(?:.*?)(?:(?:rd|link).springer.com)[^/]*/(.*)$', url)
if m:
	url = "http://link.springer.com/" + m.group(1)
m = re.match(r'http://(?:.*?)(?:springerlink.com)[^/]*/(.*)$', url)
if m:
	url = "http://www.springerlink.com/" + m.group(1)

handler=urllib2.HTTPHandler(debuglevel=0)
opener = urllib2.build_opener(handler)
urllib2.install_opener(opener)
location = urllib2.urlopen(url)

# we may have followed redirects, esp. from springerlink.com
path = urlparse(location.geturl()).path

page = unicode(location.read().strip(),"utf8")

root = lxml.html.document_fromstring(page)

m = re.search("/([^/]+)/(10\.\d\d\d\d)(?:/|%2f)(.*)", path, re.I)
if not m:
	bail("Unrecognised URL %s - cannot extract a DOI" % url)

(atype, doi_pref,doi_suff) = (m.group(1), m.group(2), m.group(3))
doi = "%s/%s" % (doi_pref,doi_suff)

print "begin_tsv"
print "linkout\tSLINK2\t\t%s\t\t%s" % (atype, doi)
print "linkout\tDOI\t\t%s\t\t" % doi

for div in root.cssselect("div.abstract-content"):
	print "abstract\t%s" % div.xpath("string()").strip()
	# Sometimes have abstracts in different languages, e.g.,
	# http://link.springer.com/article/10.1007%2Fbf01975011
	# Let's assume the 1st one is English.
	break

print "end_tsv"
print "begin_ris"

ris_url = "http://link.springer.com/export-citation/%s/%s.ris" % (atype,doi)
print unicode(urllib2.urlopen(ris_url).read().strip(),"utf8")

print "end_ris"
print "status\tok"
