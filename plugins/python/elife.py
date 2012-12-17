#!/usr/bin/env python2.6

import sys, codecs, cookielib, re
import urllib2

import metaheaders
from cultools import bail


def get_header(metaheaders, a, b):
	A = metaheaders.get_item(a)
	if A:
		return A
	B = metaheaders.get_item(b)
	if B:
		return B
	return None

url = sys.stdin.readline().strip()

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

f = opener.open(url)
page = f.read().strip()

#print page

metaheaders = metaheaders.MetaHeaders(page=page)


key_map = {
	"publisher" : "DC.Publisher",
	"abstract" : "description",
	"journal":  "citation_journal_title",
	"issue": "citation_issue",
	"title": "DC.Title",
	"volume": "citation_volume",
	"start_page": "citation_firstpage",
	"end_page": "citation_lastpage"
}

"""
   <meta content="2012-01-01" name="DC.Date"/>
        <meta content="eLife Sciences" name="citation_journal_title"/>
        <meta content="" name="citation_issn"/>
        <meta content="2050-084X" name="citation_issn"/>
        """

doi = metaheaders.get_item("DC.Identifier")

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

authors = metaheaders.get_multi_item("DC.Contributor")
if authors:
	for a in authors:
		print "author\t%s" % a

metaheaders.print_date("DC.Date")

# Hmmm. there are sometimes 2 issns, one empty
issn = metaheaders.get_multi_item("citation_issn")
if issn:
	for i in issn:
		if i != "":
			print "issn\t%s" % i
			break

root = metaheaders.root
abs = []
for p in root.cssselect("#abstract p"):
	abs.append(p.xpath("string()"))
if len(abs) > 0:
	abstract = ' '.join(abs)

	abstract = re.sub('\n+',' ',abstract)
	abstract = re.sub('\s+',' ',abstract)
	print "abstract\t%s" % abstract


print "end_tsv"
print "status\tok"


