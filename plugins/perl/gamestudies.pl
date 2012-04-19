#!/usr/bin/env perl

# parser for Game Studies
# <http://gamestudies.org/>
# no RIS/BibTeX supplied so we parse the meta headers
# Tristan Henderson <tnhh@tnhh.org>

use LWP::Simple;
use HTML::TreeBuilder;
use strict;
use warnings;

my $url = <>;
chomp $url;
$url =~ s|http://www.gamestudies.org|http://gamestudies.org|;

my ($ikey_1, $ckey_1) = $url=~m|gamestudies.org/(\d+)/articles/(\w+)|;

if (!defined $ikey_1 || !defined $ckey_1) {
    print "state\terr\tCouldn't find Game Studies article.\n";
    exit;
}

# all the bibliographic info
my $title;
my @authors;
my $journal = "Game Studies";
my $volume;
my $issue;
my $year;
my $month;
my $abstract;
my $issn;

my %months = (
	"january" => "1",
	"jan" => "1",
	"february" => "2",
	"feb" => "2",
	"march" => "3",
	"mar" => "3",
	"april" => "4",
	"apr" => "4",
	"may" => "5",
	"june" => "6",
	"jun" => "6",
	"july" => "7",
	"jul" => "7",
	"august" => "8",
	"aug" => "8",
	"september" => "9",
	"sep" => "9",
	"october" => "10",
	"oct" => "10",
	"november" => "11",
	"nov" => "11",
	"december" => "12",
	"dec" => "12",
);


my $page = get($url)  || (print "status\terr\tCouldn't fetch HTML\n" and exit);

my $tree = HTML::TreeBuilder->new();
$tree->parse($page);

$title = $tree->look_down('_tag','h2');

if ($title) {
	$title = $title->as_text;
} else {
	print "status\terr\tCouldn't find title in HTML\n";
	exit;
}

my $metainfo = $tree->look_down('id','metainfo');
if ($metainfo) {
	foreach my $author ($metainfo->look_down('_tag','h4')) {
	push(@authors, $author->as_text);
}
} else {
	print "status\terr\tCouldn't find authors in HTML\n";
	exit;
}

$volume = $tree->look_down('class', 'volume', '_tag', 'span');
if ($volume) {
	$volume = $volume->as_text;
	$volume =~ s/^volume //i;
} else {
	print "status\terr\tCouldn't find volume in HTML\n";
	exit;
}

$issue = $tree->look_down('class', 'issueno', '_tag', 'span');
if ($issue) {
	$issue = $issue->as_text;
	$issue =~ s/^issue //i;
} else {
	print "status\terr\tCouldn't find issue in HTML\n";
	exit;
}

my $date = $tree->look_down('class', 'date', '_tag', 'span');
if ($date) {
	$date = $date->as_text;
	if ($date =~ /(\w+) (\d{4})/) {
		$month = lc($1);
		$month = $months{$month};
		$year = $2;
	} else {
		print "status\terr\tCouldn't find date in HTML\n";
		exit;
	}
}

$issn = $tree->look_down('class', 'issn', '_tag', 'span');
if ($issn) {
	$issn = $issn->as_text;
	$issn =~ s/^issn://i;
}

# abstract is not present in all articles
my $abstract_header = $tree->look_down(
	'_tag', 'h3',
	sub {
		$_[0]->as_text =~ m{Abstract};
	}
);
if ($abstract_header) {
	$abstract = $tree->find('p');
	if ($abstract) {
		$abstract = $abstract->as_text;
		$abstract =~ s/^\s+//;
		$abstract =~ s/\s+$//;
	}
}

print "begin_tsv\n";
print "linkout\tGAMEST\t$ikey_1\t$ckey_1\t\t\n";
print "title\t$title\n";
foreach my $author (@authors) {
	print "author\t$author\n";
}
print "journal\t$journal\n";
print "volume\t$volume\n";
print "issue\t$issue\n";
print "year\t$year\n";
print "month\t$month\n";
print "issn\t$issn\n" if $issn;
print "abstract\t$abstract\n" if $abstract;
print "type\tJOUR\n";
print "url\t$url\n";
print "end_tsv\n";
print "status\tok\n";
