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

my $json = JSON->new;

$json = $json->relaxed(1);

my $DATA = $json->decode($DATA);

my $ua = LWP::UserAgent->new;

$ua->cookie_jar( {} );

my $base = $DATA->{baseurl} || "http://www.citeulike.org";
my $basepath = $DATA->{basepath} || ".";

my $post_username = $DATA->{post_username} || $DATA->{username};

my $res = $ua->request(POST $base."/login.json", [
	username => $DATA->{username},
	password => $DATA->{password}
]);

status($res);

my @files = @{$DATA->{files}};

foreach my $f (@files) {
	my $user = $f->{username} || $post_username;
	my $abs_path = File::Spec->rel2abs( $f->{path}, $basepath );

	print "Uploading: ".$abs_path." to ".$user."/".$f->{article_id}."\n";

	my $res = $ua->request(POST $base."/personal_pdf_upload.json",
		Content_Type => 'multipart/form-data',
		Content => [
				username => $user,
				article_id => $f->{article_id},
				file => [$abs_path],
				rightsholder => $f->{rightsholder} || $DATA->{rightsholder},
				md5 => $f->{md5}
		]
	);

	status($res);
}


sub status {
	my ($res) = @_;
	if ($res->is_success) {
		print ">>>>> ".$res->base."\n";
		print $res->content;
	} else {
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
"rightsholder" [needed for uploading to groups]: "true" - just a legal
		thing, same as on website.

"files":
	"article_id" : citeulike article_id (i.e., from URL)
	"path" : PDF file name.  "basepath" (above) gives default location
	"username" [optional]: overrides "username" or "post_username" (see above)
	"rightsholder": see above - set per file.
	"md5" : hex md5 (lowercase) of PDF.   If there's an existing remote PDF
		with same checksum, get status=not_changed

Any other fields are ignored, so you can "annotate" the file with extra stuff, e.g.,
in the example below there's a title field to remind you which actual article it is.

Example.
========

The format is JSON (http://json.org/).  The options are set to "relaxed" to
be less strict so extra commas allowed, and "#" comments

Simple example:

{
	"username" : "johnsmith",
	"password" : "mypassword",
	"files" : [
		{
			"article_id": "54321",
			"path" : "/home/johnsmith/Desktop/file1.pdf"
		},
		{
			"article_id": "54322",
			"path" : "/home/johnsmith/Desktop/file2.pdf"
		},
		{
			"article_id": "54323",
			"path" : "/home/johnsmith/Desktop/file3.pdf"
		}
	]
}

More complicated:

{
	"username" : "johnsmith",
	"password" : "mypassword",
	"basepath" : "/home/johnsmith/pdfs/",
	"post_username" : "group:1234",
	"rightsholder" : "true",
	"files" : [
		{
			"title" : "An article title",
			"article_id": "54321",
			"path" : "file1.pdf"
		},
		{
			# Interesting article
			"username" : "johnsmith", # need to "reset" because
			                          # post_username is set to a group
			"article_id": "987654321",
			"path" : "file2.pdf",
			"md5":"0351b9502c906ec9383368f07c45c4fc"
		},
		{
			# this is a comment
			"username" : "group:12345", # a different group
			"article_id": "12345",
			"path" : "/home/johnsmith/Desktop/file3.pdf"
		}
	]
}
