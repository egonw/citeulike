#!/usr/bin/env python2.7

import sys, codecs, cookielib, re
import urllib2

import metaheaders
from cultools import bail


url = sys.stdin.readline().strip()

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

f = opener.open(url)
page = f.read().strip()

#print page

metaheaders = metaheaders.MetaHeaders(page=page)


key_map = {
	"journal":  "citation_journal_title",
	"issue": "citation_issue",
	"title": "citation_title",
	"volume": "citation_volume",
	"start_page": "citation_firstpage",
	"end_page": "citation_lastpage",
	"abstract": "citation_abstract"
}

doi = metaheaders.get_item("citation_doi")

if not doi:
	bail('Unable to find a DOI')
	sys.exit(0)

print "begin_tsv"
print "linkout\tDOI\t\t%s\t\t" % (doi)
print "type\tJOUR"
print "doi\t" + doi
for f in key_map.keys():
	k = key_map[f]
	v = metaheaders.get_item(k)
	if not v:
		continue
	v = v.strip()
	print "%s\t%s"  % (f,v)

authors = metaheaders.get_multi_item("citation_author")
if authors:
	for a in authors:
		print "author\t%s" % a

metaheaders.print_date("citation_publication_date")

# Hmmm. there are sometimes 2 issns, one empty
issn = metaheaders.get_multi_item("citation_issn")
if issn:
	for i in issn:
		if i != "":
			print "issn\t%s" % i
			break

print "end_tsv"
print "status\tok"
