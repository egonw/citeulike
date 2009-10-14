#!/usr/bin/env perl
use strict;
use LWP;
use HTTP::Request::Common;
use JSON;
use File::Spec;

my $old = $/;
undef $/;
# data on STDIN
my $DATA = <>;
$/=$old;

print $DATA;

my $DATA = from_json($DATA);

my $ua = LWP::UserAgent->new;

$ua->cookie_jar( {} );

my $base = $DATA->{baseurl} || "http://www.citeulike.org";
my $basepath = $DATA->{basepath} || ".";

my $post_username = $DATA->{post_username} || $DATA->{username};

my $res = $ua->request(POST $base."/login.json", [username => $DATA->{username}, password => $DATA->{password}]);
status($res);

my @files = @{$DATA->{files}};

foreach my $f (@files) {
	my $user = $f->{username} || $post_username;
	my $abs_path = File::Spec->rel2abs( $f->{path}, $basepath );

	print "Uploading: ".$abs_path." to ".$user."/".$f->{article_id}."\n";

	my $res = $ua->request(POST $base."/personal_pdf_upload_json",
		Content_Type => 'multipart/form-data',
		Content => [
				username => $user,
				article_id => $f->{article_id},
				file => [$abs_path],
				rightsholder => $f->{rightsholder}
		]);

	status($res);
}


sub status {
	my ($res) = @_;
	if ($res->is_success) {
		print ">>>>> ".$res->base."\n";
		print $res->content;
	}
	else {
		print ">>>>> ERROR: ".$res->base."\n";
		print $res->status_line, "\n";
		print $res->content;
	}
	print "---------------------------------------------------\n";
}

__END__


Run this as

$ perl pdf_upload.pl < myfile.json

"username"/"password" : your citeulike credentials
"basepath" [optional]: default location for PDFs
"post_username" [optional] : if you want to post everything to a group
	by default, set this to "group:nnnn"


"files":
	"article_id" : citeulike article_id (i.e., from URL)
	"path" : PDF file name.  "basepath" (above) gives default location
	"username" [optional]: overrides "username" or "post_username" (see above)
	"rightsholder" [needed for uploading to groups]: "true" - just a legal
		thing, same as on website.

Any other fields are ignored, so you can "annotate" the file with extra stuff, e.g.,
in the example below there's a title field to remind you which actual article it is.

Example.
========

{
	"username" : "johnsmith",
	"password" : "mypassword",
	"basepath" : "/home/johnsmith/pdfs/",
	"post_username" : "group:1234",
	"files" : [
		{
			"title" : "An article title",
			"article_id": "3787533",
			"path" : "file1.pdf"
		},
		{
			"username" : "group:3134",
			"article_id": "3753568",
			"path" : "/home/johnsmith/Desktop/file2.pdf",
			"rightsholder" : "true"
		}
	]
}
