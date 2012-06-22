#!/usr/bin/env perl

#
# Copyright (c) 2008 Robert Blake
# All rights reserved.
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
#        CiteULike <http://www.citeulike.org> and its
#        contributors.
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

use LWP::Simple;
use HTML::TreeBuilder;
use strict;

binmode STDOUT, ":utf8";

my $unclean_url = <>;

# Example URLs
# http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.19.4216
# http://citeseerx.ist.psu.edu.proxy2.library.uiuc.edu/viewdoc/summary?doi=10.1.1.19.4216

my $clean_url;
my $doi;
if ($unclean_url !~ m,^https?://citeseerx?.ist.psu.edu(\.[^/]+)?(?:/citeseerx)?/viewdoc/[^/]*?(?:\?doi=)?([0-9.]+),) {
	print "status\tnot_interested\n";
	exit;
} else {
	$doi = $2;
	$clean_url = "http://citeseer.ist.psu.edu/viewdoc/versions?doi=$doi";
}

my $data = "";
$data = get $clean_url;
if (not $data) {
	print "status\terr\tCouldn't connect to $clean_url\n";
	exit;
}

print "begin_tsv\n";
print "linkout\tCITESX\t\t$doi\t\t\n";

print "ignore\t$clean_url\n";


my $type="JOUR";

my $tree = HTML::TreeBuilder->new();
$tree->parse($data);
my $head = ($tree->look_down('_tag','head'))[0];
my @meta = $head->look_down('_tag','meta');


foreach my $m (@meta) {
	my $name = $m->attr("name");
	my $content = $m->attr("content");
	$content =~ s/\s+$//;
	$content =~ s/^\s+//;
	#print "$name = $content\n";
	$name =~ /description/i and do {
		$content =~ s/CiteSeerX - Document Details \([^\)]+\): //;
		print "abstract\t$content\n";
	};
	$name =~ /citation_title/i and do {
		print "title\t$content\n";
	};
	$name =~ /citation_year/i and do {
		print "year\t$content\n";
	};
	$name =~ /citation_conference/i and do {
		print "title_secondary\t$content\n";
		$type = "INCONF";
	};
	$name =~ /citation_authors/i and do {
		my @au = split /,\s+/, $content;
		foreach my $a (@au) {
			print "author\t$a\n";
		}
	};
	$name =~ /citation_issue/i and do {
		print "issue\t$content\n";
	};
	$name =~ /citation_volume/i and do {
		print "volume\t$content\n";
	};
	$name =~ /citation_x/i and do {
		print "\t$content\n";
	};
}

if ($data =~ m{<tr><td>PAGES</td>\s+<td>(.*)--(.*)</td>}) {
	print "start_page\t$1\n";
	print "end_page\t$2\n";
}



print "type\t$type\n";


#$tree->dump();
#print "$data\n";

print "end_tsv\n";
print "status\tok\n";
exit;

my $venue = "";
my $venue_type = "";
foreach my $line (split(/\n/, $data)) {
	#print "$line\n";
  if ($line !~ m,^\s*<tr><td>,) {
    next;
  }
  elsif($line =~ m,<tr><td>AUTHOR NAME</td><td>(.*)</td><td>,) {
    print "author\t$1\n"
  }
  elsif ($line =~ m,<tr><td>TITLE</td><td>(.*)</td><td>,) {
    print "title\t$1\n";
  }
  elsif ($line =~ m,<tr><td>ABSTRACT</td><td>(.*)</td><td>,) {
    print "abstract\t$1\n";
  }
  elsif ($line =~ m,<tr><td>YEAR</td><td>(.*)</td><td>,) {
    print "year\t$1\n";
  }
  elsif ($line =~ m,<tr><td>NUMBER</td><td>(.*)</td><td>,) {
    print "issue\t$1\n";
  }
  elsif ($line =~ m,<tr><td>PAGES</td><td>(.*)--(.*)</td><td>,) {
    print "start_page\t$1\n";
    print "end_page\t$2\n";
  }
  elsif ($line =~ m,<tr><td>VOLUME</td><td>(.*)</td><td>,) {
    print "volume\t$1\n";
  }
  elsif($line =~ m,<tr><td>VENUE TYPE</td><td>(.*)</td><td>,) {
    $venue_type = uc $1;
  }
  elsif($line =~ m,<tr><td>VENUE</td><td>(.*)</td><td>,) {
    $venue = $1;
  }
}

# Type is a required field, so we'll say ELEC if we don't know.
my $type = "ELEC";
my $journal = "";
my $title_secondary = "";

if ($venue and $venue_type) {
  if ($venue_type eq "CONFERENCE") {
    $title_secondary = $venue;
    $type = "INCONF";
  }
  elsif ($venue_type eq "JOURNAL") {
  	$journal = $venue;
  	$type = "JOUR";
  }
  elsif ($venue_type eq "TECHREPORT") {
  	$journal = $venue;
  	$type = "REP";
  }
}

print "title_secondary\t$title_secondary\n" if $title_secondary;
print "journal\t$journal\n" if $journal;
print "type\t$type\n";

print "end_tsv\n";
print "status\tok\n";
exit;
