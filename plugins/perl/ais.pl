#!/usr/bin/env perl

# parser for the Association for Information Systems Electronic Library
# <http://aisel.aisnet.org/journals/>
# no RIS/BibTeX supplied so we parse the meta headers
# this might be reusable for other "bepress" journals
# Tristan Henderson <tnhh@tnhh.org>

use LWP::Simple;
use HTML::TreeBuilder;
use strict;
use warnings;

binmode STDOUT, ":utf8";

my $url = <>;
chomp $url;

my ($ckey_1, $ikey_1, $ikey_2, $ckey_2) = $url=~m|aisnet.org/(\w+)/vol(\d+)/iss(\d+)/(\d+)/|;

if (!defined $ikey_1 || !defined $ikey_2 || !defined $ckey_1) {
	print "state\terr\tCouldn't find AIS article.\n";
	exit;
}

# all the bibliographic info
my $title;
my @authors;
my $journal;
my $volume;
my $issue;
my $year;
#my $start_page;
my $issn;
my $abstract;

my $page = get($url)  || (print "status\terr\tCouldn't fetch HTML\n" and exit);

my $tree = HTML::TreeBuilder->new();
$tree->parse($page);

my $head = $tree->look_down('_tag','head');
my @meta = $head->look_down('_tag','meta');

foreach my $m (@meta) {
	my $name = $m->attr("name");
	my $content = $m->attr("content");

	if ($name) {
		if ($name =~ /^bepress_citation_journal_title$/) {
			$journal = $content;
			# not sure why they call this firstpage - it's the article number
			#        } elsif ($name =~ /^bepress_citation_firstpage$/) {
			#            $start_page = $content;
		} elsif ($name =~ /^bepress_citation_author$/) {
			my $author = $content;
			if ($author =~ /(.*), (.*)/) {
				$author = "$2 $1";
			}
			push(@authors, $author);
		} elsif ($name =~ /^bepress_citation_title$/) {
			$title = cleanup($content);
		} elsif ($name =~ /^bepress_citation_date$/) {
			$year = $content;
		} elsif ($name =~ /^bepress_citation_volume$/) {
			$volume = $content;
		} elsif ($name =~ /^bepress_citation_issue$/) {
			$issue = $content;
		} elsif ($name =~ /^bepress_citation_issn$/) {
			$issn = $content;
		} elsif ($name =~ /^description$/) {
			$abstract = cleanup($content);
			# $abstract =~ s/[^[:ascii:]]+//g; # get rid of non-ASCII
		}
	}
}

print "begin_tsv\n";
print "linkout\tAIS\t$ikey_1\t$ckey_1\t$ikey_2\t$ckey_2\n";
print "title\t$title\n";
foreach my $author (@authors) {
	print "author\t$author\n";
}
print "journal\t$journal\n";
print "volume\t$volume\n";
print "issue\t$issue\n";
print "year\t$year\n";
#print "start_page\t$start_page\n";
print "issn\t$issn\n";
print "type\tJOUR\n";
print "url\t$url\n";
print "abstract\t$abstract\n";
print "end_tsv\n";
print "status\tok\n";


sub cleanup {
	my ($text) = @_;
	$text =~ tr/\x{2018}\x{2019}\x{201C}\x{201D}/''""/;
	$text =~ s/^\s+//;
	$text =~ s/\s+$//;
	$text =~ s/\s\s+/ /g;

	return $text;
}
