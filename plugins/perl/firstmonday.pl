#!/usr/bin/env perl

use LWP::Simple;
use HTML::TreeBuilder;
use strict;
use warnings;
use Encode;

binmode STDOUT, ":utf8";

my $url = <>;
chomp $url;
# remove (outdated) cgiwrapper from URL
$url =~ s|htbin/cgiwrap/bin/||;
# remove unneeded extra ID from URL
$url =~ s|article/view/(\d+)/(\d+)|article/view/$1|;

my ($fmkey) = $url=~m|/article/view/(\d+)|;

if (!defined $fmkey) {
    print "status\terr\tCouldn't find First Monday article.\n";
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

my $page = get($url)  || (print "status\terr\tCouldn't fetch HTML\n" and exit);

my $tree = HTML::TreeBuilder->new();
$tree->parse($page);

my $head = $tree->look_down('_tag','head');
my @meta = $head->look_down('_tag','meta');

foreach my $m (@meta) {
	my $name = $m->attr("name");
	my $content = $m->attr("content");
    #$content = decode("utf-8",$content);

	if ($name) {
		if ($name =~ /^citation_title$/) {
			$title = $content;
		} elsif ($name =~ /^citation_journal_title$/) {
			$journal = $content;
		} elsif ($name =~ /^citation_author$/) {
			foreach my $author (split /;/, $content) {
				$author =~ s/^\s+//;
				$author =~ s/\s+$//;
				push(@authors, $author);
			}
		} elsif ($name =~ /^citation_date$/) {
			my $date = $content;
			if ($content =~ /^(\d{4})\/(\d{2})\/(\d{2})$/) {
				$year = $1;
				$month = $2;
                if ($month) {
                    $month =~ s/^0//;
                }
				$day = $3;
                if ($day) {
                    $day =~ s/^0//;
                }
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
			$abstract = $content;
		} elsif ($name =~ /^citation_doi$/) {
            $doi = $content;
        }
	}
}

print "begin_tsv\n";
print "linkout\tFSTMON\t$fmkey\t\t\t\n";
print "linkout\tDOI\t\t$doi\t\t\n" if $doi;
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
print "type\tJOUR\n";
print "url\t$url\n";
print "abstract\t$abstract\n" if $abstract;
print "end_tsv\n";
print "status\tok\n";

