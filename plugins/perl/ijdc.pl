#!/usr/bin/env perl

# Parser for the International Journal of Digital Curation
# <http://ijdc.net/>
# No RIS/BibTeX supplied so we parse the meta headers
# Would be good to have a generic OJS parser but not sure how that
# would fit in to the CUL plugin model
# Tristan Henderson <tnhh@tnhh.org>

use LWP::Simple;
use HTML::TreeBuilder;
use strict;
use warnings;
use Encode;

binmode STDOUT, ":utf8";

my $url = <>;
chomp $url;
# remove optional "www" from URL
$url =~ s|http://www.ijdc.net|http://ijdc.net|;

my ($ckey_1, $ikey_1) = $url=~m|index.php/(\w+)/article/view/(\d+)|;

if (!defined $ikey_1 || !defined $ckey_1) {
    print "state\terr\tCouldn't find IJDC article.\n";
    exit;
}

# all the bibliographic info
my $title;
my @authors;
my $journal;
my $volume;
my $issue;
my $year;
my $month;
my $day;
my $issn;
my $abstract;
my $doi;
my $start_page;
my $end_page;

my $page = get($url)  || (print "status\terr\tCouldn't fetch HTML\n" and exit);

my $tree = HTML::TreeBuilder->new();
$tree->parse($page);

my $head = $tree->look_down('_tag','head');
my @meta = $head->look_down('_tag','meta');

foreach my $m (@meta) {
	my $name = $m->attr("name");
	my $content = $m->attr("content");
	$content = decode("utf-8",$content);

	if ($name) {
		if ($name =~ /^description$/) {
			$title = sanitise($content);
		} elsif ($name =~ /^citation_journal_title$/) {
			$journal = $content;
		} elsif ($name =~ /^citation_authors$/) {
			foreach my $author (split /;/, $content) {
				$author =~ s/^\s+//;
				$author =~ s/\s+$//;
				push(@authors, $author);
			}
		} elsif ($name =~ /^citation_date$/) {
			my $date = $content;
			if ($content =~ /^(\d{2})\/(\d{2})\/(\d{4})$/) {
				$day = $1;
				$month = $2;
				$year = $3;
			} elsif ($content =~ /^(\d{4})$/) {
				$year = $1;
			}
		} elsif ($name =~ /^citation_volume$/) {
			$volume = $content;
		} elsif ($name =~ /^citation_issue$/) {
			$issue = $content;
		} elsif ($name =~ /^citation_issn$/) {
			$issn = $content;
		} elsif ($name =~ /^DC.Description$/) {
			$abstract = sanitise($content);
		} elsif ($name =~ /^citation_doi$/) {
            $doi = $content;
		} elsif ($name =~ /^citation_firstpage$/) {
            if ($content =~ /^(\d+)-(\d+)$/) {
                $start_page = $1;
                $end_page = $2;
            }
        }
	}
}

print "begin_tsv\n";
print "linkout\tIJDC\t$ikey_1\t$ckey_1\t\t\n";
print "title\t$title\n";
foreach my $author (@authors) {
	print "author\t$author\n";
}
print "journal\t$journal\n";
print "volume\t$volume\n" if $volume;
print "issue\t$issue\n" if $issue;
print "year\t$year\n" if $year;
print "month\t$month\n" if $month;
print "day\t$day\n" if $day;
print "issn\t$issn\n" if $issn;
print "doi\t$doi\n" if $doi;
print "start_page\t$start_page\n" if $start_page;
print "end_page\t$end_page\n" if $end_page;
print "type\tJOUR\n";
print "url\t$url\n";
print "abstract\t$abstract\n" if $abstract;
print "end_tsv\n";
print "status\tok\n";

# get rid of those annoying smart quotation marks and more
sub sanitise {
	my ($text) = @_;

	$text =~ s/(\x{2018}|\x{2019})/'/g;
	$text =~ s/(\x{201C}|\x{201D})/"/g;
	$text =~ s/\x{2014}/--/g;
	$text =~ s/^\s+//;
	$text =~ s/\s+$//;
	$text =~ s/\s\s+/ /g;
	return $text;
}
