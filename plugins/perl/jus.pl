#!/usr/bin/env perl

# parser for Journal of Usability Studies <http://www.upassoc.org/upa_publications/jus/>
# no RIS/BibTeX supplied so we parse the HTML
# hopefully things won't change too much!
# Tristan Henderson <tnhh@tnhh.org>

use LWP::Simple;
use HTML::TreeBuilder;
use strict;
use warnings;

my $url = <>;
chomp $url;
$url =~ s|http://www.upassoc.org|http://upassoc.org|;

my ($ckey_1, $ckey_2) = $url=~m|/jus/(\d+\w+)/(\w+).html|;

if (!defined $ckey_1 || !defined $ckey_2) {
    print "state\terr\tCouldn't find JUS article.\n";
    exit;
}

# all the bibliographic info
my $title;
my @authors;
my $journal;
my $volume;
my $issue;
my $month;
my $year;
my $start_page;
my $end_page;

# months are sometimes long, sometimes short...
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

my $page = get($url)  or (print "status\terr\tCouldn't fetch HTML\n" and exit);

my $tree = HTML::TreeBuilder->new();
$tree->parse($page);

$title = $tree->look_down('_tag','h1');

if ($title) {
	$title = $title->as_text;
} else {
	print "status\terr\tCouldn't find title in HTML\n";
	exit;
}

# authors are in the first "normal" <p>
my $author_str = $tree->look_down(
    'class', 'normal',
    '_tag', 'p');

# other info is denoted by pointer including journal title
my $info = $tree->look_down(
	'class', 'normal',
	'_tag', 'p',
	sub {
		$_[0]->as_text =~ m{Journal of Usability Studies}
	}
);

# parse the authors
if ($author_str) {
	$author_str = $author_str->as_text;
	# author can be listed as "Alice, Bob and Charlie" or "Alice, Bob, and Charlie"
	$author_str =~ s/,/and/g;
	$author_str =~ s/and and/and/g;
	@authors = split (/and/, $author_str);
} else {
	print "status\terr\tCouldn't parse authors\n";
	exit;
}


if ($info) {
	$info = $info->as_text;
	if ($info =~ /(Journal of Usability Studies), Volume (\d+)\s?, Issue (\d+)\s?, (\w+) (\d{4})\s?, pp. (\d+)\s?-\s?(\d+)/) {
		$journal = $1;
		$volume = $2;
		$issue = $3;
		$month = lc($4);
		$month = $months{$month};
		$year = $5;
		$start_page = $6;
		$end_page = $7;
	} else {
		print "status\terr\tCouldn't parse bibliographic info in HTML\n";
		exit;
	}
}

print "begin_tsv\n";
print "linkout\tJUS\t\t$ckey_1\t\t$ckey_2\n";
print "title\t$title\n";
foreach my $author (@authors) {
	print "author\t$author\n";
}
print "journal\t$journal\n";
print "volume\t$volume\n";
print "issue\t$issue\n";
print "year\t$year\n";
print "month\t$month\n";
print "start_page\t$start_page\n";
print "end_page\t$end_page\n";
print "type\tJOUR\n";
print "url\t$url\n";
print "end_tsv\n";
print "status\tok\n";
