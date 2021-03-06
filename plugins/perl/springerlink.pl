#!/usr/bin/env perl

use warnings;
#use LWP::Simple;
use LWP 5.64;
use File::Temp qw/tempfile/;
use WWW::Mechanize;
use Encode;

# print "status\terr\t (0) Springerlink is blocked at the moment. Please again try later.\n" and exit;

#
# Copyright (c) 2005 Richard Cameron, CiteULike.org
# All rights reserved.
#
# 05/oct/2006 Marcus Granado <mrc.gran(@)gmail.com>
#   - added support for cookies,required by new springerlink.com portal
#
# This code is derived from software contributed to CiteULike.org
# by
#	 Stevan Springer <stevan.springer@gmail.com>
#
# with modifications by
# 	Fergus Gallagher <fergus.gallagher@citeulike.org>
#
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

binmode STDOUT, ":utf8";


$url = <>;
chomp($url);


# Is this a "book section"?  If so we need to get user to click the "View Article" link
#
# Hmm.  This isn't always the case...
# e.g., http://www.springerlink.com/content/u7h51v562279gj07#section=692524&page=1&locus=5
# is a valid article.
#if ($url =~ /#section=/) {
	#print "status\terr\tWe cannot work out which chapter/section you want.  Please go back and select the 'View Details' button, and try that. \n";
	#exit;
#}



# Parser for Springerlink Web Addresses:
# ADD a parser to link from other forms of the article to the abstract later.

# lets remove any initial 'www.' : springerlink.com doesn't like it

$url =~ s/(beta|www)\.//;

# Remove any instance of metapress in the URL
$url =~ s/springerlink\.metapress\.com/springerlink.com/;

# Remove any trailing proxy stuff on the end
$url =~ s!springerlink\.com[^/]+/!springerlink.com/!;

# extract the UID from the end of the line.
$url =~ m{/content/([^/?]+)};

my $slink = $1 || "";


# If we have a UID from the source URL, then we can jump direct to the RIS
if (!$slink) {
	print "status\terr\t (3) Could not find a link to the citation details on this page. Try posting the article from the abstract page\n" and exit;
}

my $link = "http://www.springerlink.com/content/$slink/";
my $link_ris = "${link}export-citation/";

my $mech = WWW::Mechanize->new( autocheck => 1 );
$mech->quiet(1);
$mech->agent_alias( 'Windows IE 6' );

# Seems needed to get this page for the RIS link to work
$mech->get( $link);

$mech->get( $link_ris );

my $form = $mech->form_name("aspnetForm");

my @inputs = $form->inputs;

my $sep;

$sep = '$';

eval {
	# not always present
        no warnings 'all';
		$mech->field("ctl00${sep}ContentPrimary${sep}ctl00${sep}ctl00${sep}Export" , "AbstractRadioButton");

        $mech->field("ctl00${sep}ContentPrimary${sep}ctl00${sep}ctl00${sep}Format" , "RisRadioButton");
};

# There are "name" with "$" and "id" with "_".
$sep = '$';
my $res = $mech->select("ctl00${sep}ContentPrimary${sep}ctl00${sep}ctl00${sep}CitationManagerDropDownList" , "ReferenceManager");
if (!$res) {
	$mech->get( $link );
	# Books - can't get citation so get from crossref.  Need DOI first.
	# hacky... look for <dd>10.xxxxxx</dd>
	# TODO - crossref.tcl can't parse crossref books yet....
	my $c = $mech->content();
	if ($c =~ /<dd>(10\.\d\d\d\d\/[^<]+)<\/dd>/) {
		# fake a RIS - all we need is the DOI bit
		$ris= "UR  - http://dx.doi.org/".$1;
	} elsif ($c =~ /<span class="value">(10\.\d\d\d\d\/[^<]+)<\/span>/) {
		# fake a RIS - all we need is the DOI bit
		$ris= "UR  - http://dx.doi.org/".$1;
	} else {
		$ris = "";
	}
} else {
	#foreach (@inputs) {
		#print "$_\n";
		#print $_->name . " => " . $_->value."\n";
	#}
	#$mech->add_header( "Accept-Charset" => 'utf-8' );

	my $response = $mech->click("ctl00${sep}ContentPrimary${sep}ctl00${sep}ctl00${sep}ExportCitationButton");

	#
	# This seems very fragile - $ris is already UTF8 bytes.
	# There are no encoding headers in the response (always) but I think
	# browsers should default to UTF-8, whereas mechanize seems to assume something
	# like Latin-1
	#
	#$ris = $response->decoded_content({default_charset => "UTF-8"});
	$ris = $response->content();
	$ris = decode("utf8", $ris);

	# strip UTF BOM
	$ris =~ s/^\xEF\xBB\xBF//;
	# Hmmm - above doesn't work so use hammer
	$ris =~ s/^[^A-Z]+//;

	$ris =~ s/\r//g;

	unless ($ris =~ m{ER\s+-}) {
		print "status\terr\tCouldn't extract the details from SpringerLink's 'export citation'\n" and exit;
	}

}


#Generate linkouts and print RIS:
print "begin_tsv\n";

# Springer seem to use DOIs exclusively
#DOI linkout
#if ($ris =~ m{doi:([0-9a-zA-Z_/.:-]*)}) {
#if ($ris =~ m{doi:(\S*)}) {

my $have_linkouts = 0;
if ($ris =~ m{UR  - http://dx.doi.org/([0-9a-zA-Z_/.:-]+/[0-9a-zA-Z_/.:-]+)}) {
	$doi = $1;
	chomp $doi;
	print "linkout\tDOI\t\t$doi\t\t\n";
	$have_linkouts = 1;
}
if ($ris =~ m{UR  - http://www.springerlink.com/content/([^/\r\n]+)}) {
	$slink = $1;
	chomp $slink;
	print "linkout\tSLINK\t\t$slink\t\t\n";
	$have_linkouts = 1;
} elsif ($slink) {
	chomp $slink;
	print "linkout\tSLINK\t\t$slink\t\t\n";
	$have_linkouts = 1;
}

if (!$have_linkouts) {
	print "status\terr\tThis document does not have a DOI or a Springer ID, so cannot make a permanent link to it.\n" and exit;
}

print "end_tsv\n";
print "begin_ris\n";
print "$ris\n";
print "end_ris\n";
print "status\tok\n";
