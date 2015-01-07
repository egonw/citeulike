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

import re, sys, urlparse, urllib2
from cultools import urlparams, bail
import socket
import metaheaders

socket.setdefaulttimeout(15)

#
# Read URL from stdin and check it's OK
#
url = sys.stdin.readline().strip()

match = re.search(r'^http://((www\.)?(biomedcentral|genomebiology|physmathcentral).com/[0-9A-Z.-]+/)|((www.actavetscand.com|www.aidsrestherapy.com|www.almob.org|alzres.com|www.ann-clinmicrob.com|www.annals-general-psychiatry.com|www.asir-journal.com|arthritis-research.com|www.apfmj.com|www.anzhealthpolicy.com|www.aejournal.net|www.behavioralandbrainfunctions.com|www.biodatamining.org|www.biology-direct.com|www.biomedical-engineering-online.com|www.bpsmedicine.com|www.biotechnologyforbiofuels.com|breast-cancer-research.com|www.cancerci.com|www.cbmjournal.com|www.cardiab.com|www.cardiovascularultrasound.com|www.biosignaling.com|www.celldiv.com|www.cerebrospinalfluidresearch.com|www.journal.chemistrycentral.com|www.capmh.com|www.cmjournal.org|www.chiroandosteo.com|www.clinicalmolecularallergy.com|www.comparative-hepatology.com|www.conflictandhealth.com|www.resource-allocation.com|www.coughjournal.com|ccforum.com|www.dmsjournal.com|www.diagnosticpathology.org|www.dynamic-med.com|www.ete-online.com|www.ehjournal.net|www.epi-perspectives.com|www.epigeneticsandchromatin.com|www.etsmjournal.com|www.fibrogenesis.com|www.frontiersinzoology.com|www.gvt-journal.com|www.gsejournal.org|genomebiology.com|genomemedicine.com|www.geochemicaltransactions.com|www.globalizationandhealth.com|www.gutpathogens.com|www.harmreductionjournal.com|www.head-face-med.com|www.headandneckoncology.org|www.hqlo.com|www.health-policy-systems.com|www.hccpjournal.com|www.human-resources-health.com|www.immunityageing.com|www.immunome-research.com|www.implementationscience.com|www.infectagentscancer.com|www.intarchmed.com|www.internationalbreastfeedingjournal.com|www.equityhealthj.com|www.ijbnpa.org|www.ij-healthgeographics.com|www.ijmhs.com|www.issoonline.com|www.ijponline.net|www.jangiogenesis.com|www.jbioleng.org|jbiol.com|www.jbiomedsci.com|www.jbiomedsem.com|www.jbppni.com|www.cardiothoracicsurgery.org|jcmr-online.com|www.jcheminf.com|www.jcircadianrhythms.com|www.ethnobiomed.com|www.jeccr.com|www.jfootankleres.com|www.jhoonline.org|www.jibtherapies.com|www.journal-inflammation.com|www.jmolecularsignaling.com|www.jnanobiotechnology.com|www.jnrbm.com|www.jneuroengrehab.com|www.jneuroinflammation.com|www.occup-med.com|www.josr-online.com|www.ovarianresearch.com|www.jsystchem.com|www.jiasociety.org|www.jissn.com|www.translational-medicine.com|www.traumamanagement.org|www.lipidworld.com|www.malariajournal.com|www.microbialcellfactories.com|www.mobilednajournal.com|www.molecularautism.com|www.molecularbrain.com|www.molecular-cancer.com|www.molecularcytogenetics.org|www.molecularneurodegeneration.com|www.molecularpain.com|www.neuraldevelopment.com|www.nonlinearbiomedphys.com|www.nutritionandmetabolism.com|www.nutritionj.com|www.ojrd.com|www.om-pc.com|www.parasitesandvectors.com|www.particleandfibretoxicology.com|www.pathogeneticsjournal.com|www.pssjournal.com|www.ped-rheum.com|www.peh-med.com|www.plantmethods.com|www.physmathcentral.com/pmcbiophys|www.pophealthmetrics.com|www.proteomesci.com|www.ro-journal.com|www.rbej.com|www.reproductive-health-journal.com|respiratory-research.com|www.retrovirology.com|www.salinesystems.org|www.sjtrem.com|www.scoliosisjournal.com|www.silencejournal.com|www.scfbm.org|www.smarttjournal.com|stemcellres.com|www.substanceabusepolicy.com|www.tbiomed.com|www.thrombosisjournal.com|www.thyroidresearchjournal.com|www.tobaccoinduceddiseases.com|www.trialsjournal.com|www.virologyj.com|www.wjes.org|www.wjso.com)/content)', url, re.IGNORECASE)
if not match:
	bail("Cannot parse this BioMed Central paper. Unrecognized URL: " + url + " - does the plugin need updating?")

#
# Fetch the page
#
try:
	page = urllib2.urlopen(url).read().strip()
except:
	bail("Couldn't fetch page (" + url + ")")

print "begin_tsv"

metaheaders = metaheaders.MetaHeaders(page=page)

pmid = metaheaders.get_item("citation_pmid");
if pmid:
	print "linkout\tPMID\t%s\t\t\t" % pmid

doi = metaheaders.get_item("citation_doi");
if doi:
	print "linkout\tDOI\t\t%s\t\t" % doi
	print "url\thttp://dx.doi.org/" + doi
	print "doi\t" + doi
else:
	bail("Couldn't find a DOI")

if not metaheaders.get_item("citation_title"):
	bail("Cannot find a title in that article")

title = metaheaders.get_item("citation_title")
if title:
	print "title\t%s" % title.encode('utf-8')

authors = metaheaders.get_multi_item("citation_author")
firstAuthorSurname = None
if authors:
	for a in authors:
		if not firstAuthorSurname:
			firstAuthorSurname = ""
			match = re.search(r'^([^\s|^,]+)', a.encode('utf-8'), re.IGNORECASE)
			if match:
				firstAuthorSurname = match.group(1)
		print "author\t%s" % a.encode('utf-8')

journal = metaheaders.get_item("citation_journal_title")
if journal:
	print "journal\t%s" % journal

docType = metaheaders.get_item("dc.type");
if docType == 'Research article' or journal:
	print "type\tJOUR"

# if docType != "text":
#	bail("Only supports journal papers ('text', 'JOUR') at this moment, but found " + docType)


issn = metaheaders.get_item("prism.issn")
if issn:
	match = re.search(r'urn:issn:(.+)', issn, re.IGNORECASE)
	if match:
		issn = match.group(1)
	print "issn\t%s" % issn

abstract = metaheaders.get_item("dc.description")
if abstract:
	print "abstract\t%s" % abstract.encode('utf-8')

volume = metaheaders.get_item("citation_volume")
if volume:
	print "volume\t%s" % volume

issue = metaheaders.get_item("citation_issue")
if issue:
	print "issue\t%s" % issue

start_page = metaheaders.get_item("citation_firstpage")
if start_page:
	print "start_page\t%s" % start_page

publisher = metaheaders.get_item("citation_publisher")
if publisher:
	print "publisher\t%s" % publisher

if metaheaders.get_item("citation_date"):
	metaheaders.print_date("citation_date")

print "end_tsv"
print "status\tok"
