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
	"journal":  "citation_journal_title",
	"issue": "citation_issue",
	"title": "citation_title",
	"volume": "citation_volume",
	"start_page": "citation_firstpage",
	"end_page": "citation_lastpage"
}

"""
	<meta name="citation_journal_title" content="Mathematics of Computation">
	<meta name="citation_journal_abbrev" content="Math. Comp.">
	<meta name="citation_issn" content="0025-5718">
	<meta name="citation_issn" content="1088-6842">
	<meta name="citation_author" content="LeVeque, Randall J.">
	<meta name="citation_author" content="Oliger, Joseph">
	<meta name="citation_title" content="Numerical methods based on additive splittings for hyperbolic partial differential equations">
	<meta name="citation_online_date" content="">
	<meta name="citation_publication_date" content="1983">
	<meta name="citation_volume" content="40">
	<meta name="citation_issue" content="162">
	<meta name="citation_firstpage" content="469">
	<meta name="citation_lastpage" content="497">
	<meta name="citation_doi" content="10.1090/S0025-5718-1983-0689466-8">
	<meta name="citation_abstract_html_url" content="http://www.ams.org/mcom/1983-40-162/S0025-5718-1983-0689466-8/">
"""

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

root = metaheaders.root
abs = []
for p in root.cssselect("#Abstract"):
	par = p.getparent()
	abs.append(par.xpath("string()"))
	
if len(abs) > 0:
	abstract = ' '.join(abs)

	abstract = re.sub('^\s*Abstract:\s*','',abstract)
	abstract = re.sub('\n+',' ',abstract)
	abstract = re.sub('\s+',' ',abstract)
	abstract = re.sub('^\s+','',abstract)
	abstract = re.sub('\s+$','',abstract)
	print "abstract\t%s" % abstract


print "end_tsv"
print "status\tok"
