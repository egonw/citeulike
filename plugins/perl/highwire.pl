#!/usr/bin/env perl

use warnings;
use LWP::Simple;
use LWP::UserAgent;

#
# Copyright (c) 2005 Richard Cameron, CiteULike.org
# All rights reserved.
#
# This code is derived from software contributed to CiteULike.org
# by
#	 Stevan Springer <stevan.springer@gmail.com>
#	 (Derived from original code by Will Wade and Richard Cameron)
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

my $ua = LWP::UserAgent->new;

$url = <>;

#Examples of compatible url formats:
#$url = "http://www.genetics.org/cgi/content/abstract/171/1/35";
#$url = "http://www.ajhp.org/cgi/content/full/62/3/239";					    #no doi
#$url = "http://gr.oxfordjournals.org/cgi/reprint/52/2/205";
#$url = "http://sth.sagepub.com/cgi/content/refs/28/1/5";
#$url = "http://bmj.bmjjournals.com/cgi/content/extract/331/7521/863";		    #extract page, abstract link seems to work
#$url = "http://jhered.oxfordjournals.org/cgi/content/extract/95/5/II";		    #extract with roman numerals
#$url = "http://glycob.oxfordjournals.org/cgi/content/abstract/cwj046v1";       #advance pub
#$url = "http://www.genesdev.org/cgi/reprint/gad.1352905v1";				    #advance pub
#$url = "http://www.genesdev.org/cgi/content/full/gad.1352905/DC1";             #advance pub-no link to citation mgr
#$url = "http://bioinformatics.oxfordjournals.org/cgi/screenpdf/18/4/529";      #frames page
#$url = "http://bmj.bmjjournals.com/cgi/content/abstract/330/7506/1457?ehom";   #weird stuff at end, seems ok
#$url = "http://bmj.bmjjournals.com/cgi/content/abstract/bmj.38498.669595.8Fv1"; #works
#$url = "http://bmj.bmjjournals.com/cgi/content/full/330/7506/0-g?ehom";			 #works
#$url = "http://bmj.bmjjournals.com/cgi/content/full/329/7475/1188-c/DC1?maxtoshow=&HITS=10&hits=10&RESULTFORMAT=1&author1=cameron&andorexacttitle=and&andorexacttitleabs=and&andorexactfulltext=and&searchid=1120043717953_4754&stored_search=&FIRSTINDEX=0&sortspec=relevance&resourcetype=1,2,3,4";
#$url = "http://bmj.bmjjournals.com/cgi/content/full/309/6970/1686?maxtoshow=&HITS=10&hits=10&RESULTFORMAT=1&andorexacttitle=and&andorexacttitleabs=and&andorexactfulltext=and&searchid=1120044557327_5038&stored_search=&FIRSTINDEX=0&sortspec=relevance&resourcetype=1,2,3,4";

# Parser for Highwire Web Addresses:
#  Published articles, determine journal,volume,number and page details. 
#  Create URL that links to abstract.

if ($url =~ m{http://(.*)/cgi(/|/content/)(abstract|short|extract|full|refs|reprint|screenpdf|summary)/(?:[a-zA-Z]+;)?([0-9]+)/([0-9]+)/((?:pe)?[0-9]+|[i|v|x|l|c|d|m]+|[I|V|X|L|C|D|M]+)})
	{
	($journal_site,$volume,$number,$page) = ($1,$4,$5,$6);
	$url_abstract = "http://$journal_site/cgi/content/abstract/$volume/$number/$page";
#	print "Details:\t$journal_site\t$volume\t$number\t$page\n";
#	print "URL:\t$url\n";	
#	print "Abstract:\t$url_abstract\n";
	} 
#  Unpublished articles, determine journal and AOP id number.
#  Create URL that links to abstract (some AOP links need minor modification)
elsif ($url =~ m{http://(.*)/cgi(/|/content/)(abstract|extract|full|refs|reprint|screenpdf|summary)/(.*)})
	{
	($journal_site,$volume,$number,$page) = ($1,$4,"","");
	if ($volume =~ m{(.*)/(.*)})
		{
		$volume = $1;
		}
	$url_abstract = "http://$journal_site/cgi/content/abstract/$volume";
#	print "Details:\t$journal_site\t$volume\t$number\t$page\n";
#	print "URL:\t$url\n";
#	print "Abstract:\t$url_abstract\n";
	}
else 
	{
	print "status\terr\t (1) This does not appear to be a Highwire Press article. Try posting the article from the abstract page.\n" and exit;
	}
	


# Get the link to the citebuilder url and formulate a link to the reference manager RIS file
$source_abstract = get("$url_abstract") || (print "status\terr\t (2) Could not retrieve information from the specified page. Try posting the article from the abstract page.\n" and exit);

if ($source_abstract =~ m{"([^"]+)">\s*(([D|d]ownload to [C|c]itation [M|m]anager)|(Download Citation))}) {
	$link_citmgr = $1;
	$link_citmgr = "http://"."$journal_site"."$link_citmgr" unless ($link_citmgr =~ m!^http://!);

	$source_citmgr = get("$link_citmgr") || (print "status\terr\t (2.5) Could not retrieve information from the citation manager page.\n" and exit);
	if ($source_citmgr =~ m{"(.*)">\s*<STRONG>Reference<BR><NOBR>Manager}) {
		$link_refman = "http://"."$journal_site"."$1";
	} else {
		print "status\terr\t (3) Could not find the citation details on this page. Try posting the article from the abstract page.\n" and exit;
	}
    } else {
	print "status\terr\t (4) Could not find the citation details on this page. Try posting the article from the abstract page.\n" and exit;
    }

#Get the reference manager RIS file and check retrieved file
$refman = $ua->get("$link_refman") || (print "status\terr\t (4)Could not retrieve the citation for this article, Try posting the article from the abstract page.\n" and exit);
$ris = $refman->content;

unless ($ris =~ m{ER\s+-})
	{
	print "status\terr\tCouldn't extract the details from HighWire's 'export citation'\n" and exit;
	}

#Generate linkouts and print output:
#HighWire linkout
print "begin_tsv\n";
print "linkout\tHWIRE\t$volume\t$journal_site\t$number\t$page\n";

#DOI linkout
if ($source_abstract =~ m{[DOI|doi|Doi]\s*:\s*([0-9]+.[0-9]+/([A-Za-z0-9.-/]+))})
	{
	$doi = $1;
	print "linkout\tDOI\t\t$doi\t\t\n";
	}

#PubMed/HubMed linkout
if ($source_abstract =~ m{access_num=([0-9]+)&link_type=PUBMED})
	{
	print "linkout\tPMID\t$1\t\t\t\n";
	}

print "end_tsv\n";
print "begin_ris\n";
print $ris;
print "end_ris\n";
print "status\tok\n";

