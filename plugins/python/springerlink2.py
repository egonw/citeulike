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

page = unicode(urllib2.urlopen(url).read().strip(),"utf8")

root = lxml.html.document_fromstring(page)

m = re.search("/([^/]+)/(10\.\d\d\d\d/.*)", path)
if not m:
	bail("Unrecognised URL %s - cannot extract a DOI" % url)

(atype, doi) = (m.group(1), m.group(2))

print "begin_tsv"
print "linkout\tSLINK2\t\t%s\t\t%s" % (atype, doi)

for div in root.cssselect("div.abstract-content"):
	print "abstract\t%s" % div.xpath("string()").strip()

print "end_tsv"
print "begin_ris"

ris_url = "http://link.springer.com/export-citation%s.ris" % path
print unicode(urllib2.urlopen(ris_url).read().strip(),"utf8")

print "end_ris"
print "status\tok"

