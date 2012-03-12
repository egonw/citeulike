#!/usr/bin/env perl

use LWP::UserAgent;
use strict;

my $ua = LWP::UserAgent->new;
$ua->agent('CiteULike');

my $url = <>;
chomp $url;
my ($conf_key1, $conf_key2, $aaai_key) = $url=~m|/index.php/(.*)/(.*)/paper/view/(\d+)|;
my $ris_url = $url;
$ris_url =~ s|paper/view|rt/captureCite|;
$ris_url =~ s|$aaai_key.*|$aaai_key/0/RefManCitationPlugin|;

if (!defined $aaai_key) {
    print "status\terr\tCouldn't find AAAI article.\n";
    exit;
}

my $res = $ua->get( $ris_url ) || (print "status\terr\tCouldn't fetch the RIS\n" and exit);
my $ris = $res->content;

print "begin_tsv\n";
print "linkout\tAAAI\t$conf_key1\t$aaai_key\t$conf_key2\t\n";
# Assume everything is a conference, since the parser only seems to work for conferences
print "type\tINCONF\n";
foreach my $line (split(/\n/,$ris)) {
    if ($line =~ /^JF  - (.*); (.*)/) {
        # The RIS JF entry contains breadcrumbs
        print "booktitle\t$2\n";
        print "journal\t\n";
    } elsif ($line =~ /^UR  - (.*)/) {
        # URL depends on the address used in request
        my $url = $1;
        $url =~ s|http://aaai.org|http://www.aaai.org|;
        print "url\t$url\n";
    }
}
print "end_tsv\n";

print "begin_ris\n";
print "$ris\n";
print "end_ris\n";

print "status\tok\n";
