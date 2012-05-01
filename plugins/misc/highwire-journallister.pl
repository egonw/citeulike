#!/usr/bin/env perl

use warnings;
use LWP::Simple;
#use LWP::UserAgent;
use List::MoreUtils qw/ uniq /;

use HTML::TreeBuilder;

binmode STDOUT, ":utf8";

#my $ua = LWP::UserAgent->new;

$url = "http://highwire.stanford.edu/lists/allsites.dtl";
$source = get("$url") || (print "status\terr\t (1) Could not retrieve information from the journal page\n" and exit);

# print "$source" and exit;

my $tree = HTML::TreeBuilder->new();
$tree->parse($source);

my @links = $tree->look_down('_tag','a');
my @hrefs = ();
my @names = ();

foreach my $link (@links) {
	my $href = $link->attr("href");
	next if (!$href || $href !~ m{http://} || $href =~ m/(highwire|library).stanford.edu/g | $href =~ m/google/g);
	my $name  = $link->as_text;
	push @names, "{$name} {$href}";
	$href =~ s{http://}{};
	$href =~ s{^www\.}{};
	$href =~ s{\.}{\\.}g;
	#print "$href\t$name\n";
	push @hrefs, $href;
}

@hrefs = uniq @hrefs;
open(my $fh, ">", "../descr/highwire.re") or die "cannot open > highwire.re: $!";
my $body = join("|",@hrefs);
print $fh "http://(www\\.)?(intl-)?($body)/\n";

open(my $fh2, ">", "highwire.names") or die "cannot open > highwire.names: $!";
binmode $fh2, ":utf8";
print $fh2 "[list ".join(" ",@names)."]\n";

exit;

while ($source =~ m/http:\/\/([\w.-]+)/g) {
	$match = $1;
	unless ($match =~ m/(highwire|library).stanford.edu/g | $match =~ m/google/g) { # | $match =~ m/sagepub/g | $match =~ m/oxfordjournals/g)
		print "$match\n";
	}
}






