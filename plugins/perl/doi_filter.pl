#!/usr/bin/env perl

use LWP 5.64;
use strict;
use warnings;

my $url = <>;
chomp($url);

# Only the first 2 fields "OK <URL>" are actually used, the others
# just for debugging

#
# These next bits should be needed as already done in
# the pre-filter go_posturl_doi_rewrite (post.tcl).
# However, still useful for command line testing
#
$url =~ s/^\s+//;
$url =~ s/\s+$//;
if (! $url =~ m{^(http://dx\.(doi|plos)\.org/|doi:|10\.|http://feedproxy\.google\.com)}i ) {
	print "OK\t$url\tNOT_CHANGED\tNO_MATCH\tEOL1\n";
	exit 0;
}

if ($url =~ m{^doi:\s*(.*)}i) {
	$url = "http://dx.doi.org/$1";
}
elsif ($url =~ m{^(10\..*)}) {
	$url = "http://dx.doi.org/$1";
}

my $browser = LWP::UserAgent->new;
$browser->cookie_jar({}); # just in case someone needs it

# some sites give a HTTP 400 to unknown headers
my @ns_headers = (
   'User-Agent' => 'Mozilla/5.0 (compatible; citeulike/1.0)',
   'From' => 'plugins@citeulike.org',
   'Accept' => 'image/gif, image/x-xbitmap, image/jpeg,
        image/pjpeg, image/png, */*',
   'Accept-Charset' => 'iso-8859-1,*,utf-8',
   'Accept-Language' => 'en-US',
  );


# Hmm, this doesn't seem to work as expected, e.g.,
# http://dx.doi.org/10.1234/xay (just a "random" url) hangs "forever"
# (I wonder if 10.1234 is a spam trap? - Most other dud url redirect to
# a sensible page, albeit with the same URL)
$browser->timeout(20); # secs
$browser->max_redirect(10); # secs


#
# CrossRef Multiple Resolvers: add magic flag to force redirection to primary.
#
my $url2 = $url;
#
# NOT TESTED PROPERLY YET - left here as "stub"
#
#if ($url =~ m{^dx.doi.org}) {
#	$url2 = $url."?locatt=mode:legacy";
#}

# HEAD not always supported :-(
my $resp = $browser->get("$url2", @ns_headers) or do {
	print "OK\t$url\tNOT_CHANGED\tERROR\tEOL2\n";
	exit 0;
};

# As mentioned above, most dud DOIs give a error page (200 OK)
# but, luckily for us, with the same URL. So a dud URL will appear
# here with uri=url, even though the line says "CHANGED".
# No worries, though potential problem if doi.org changes things
# e.g., might get a redirect to completely wrong page.
#
my $code = $resp->code;
if ($code == 200 ) {
	# this gives us back the last hop "request", i.e., the
	# URL of the last redirect
	my $req = $resp->request();
	my $uri = $req->uri;

	print "OK\t$uri\tCHANGED\t$url\tEOL3\n";
	exit 0;
}

print "OK\t$url\tNOT_CHANGED\tCODE=$code\tEOL4\n";
