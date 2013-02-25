================================================================================
IMPORTANT CAVEATS
================================================================================

This is experimental software.  Use at your own risk.

(To be honest, the chance of catastophic destruction of your data is close
to zero.)

This script does not use any official API, instead it uses a Python module called
"mechanize" which emulates a browsers action - it effectively mimics exactly the
same sequence of actions you would do yourself.  As such it is somewhat sensitive to
certain changes in the HTML (in particular form parameters).

As we expect this script to be useful for occasional use by relatively few users,
we will not necessarily be keeping it up-to-date unless errors are reported by users.
Please report any problems as soon as possible - we might be able to fix things
very quickly.

Similarly, if you have successfully used this in the past, don't assume it will still
work this time.  Approach will caution and only upload a few articles in the
first instance, until you're confident nothing has broken.

============================================================================
What is this for?
============================================================================

CiteULike categorizes articles as "trusted/checked" and "untrusted/unchecked"
depending on how they got into the system.  For more details see:

http://wiki.citeulike.org/index.php/Importing_and_Exporting#Importing_vs._Posting

For most users it is preferable to have as many articles as possible "trusted".
This tool attempts to re-post as many articles as possible using the official
mechanism, so adding a trusted copy.

============================================================================
Usage
============================================================================

1) get a JSON (/json) file of some view.  Add "?raw=1" to the end to get any
"//" overrides.

e.g.,

	/json/user/ME?raw=1

Do this in your browser while logged in and save the result (Ctrl-S, say) so
you'll retain see any private data (private tags, notes or attachments).

The script will ignore any checked files.

In the first instance I would suggest just a single article, until you're
sure this does what you want

	/json/user/ME/article/nnnnn?raw=1

2) run

	$ ./repost_unchecked.py -u USERNAME -p PASSWORD -f file.json


Run without option for more options, or look at the source code. "file.json"
is the file you saved at step (1).

You will need "tidy" installed as /usr/bin/tidy.  (Edit the script if it's
somewhere else.)

It should

a) post each article as trusted. It can only do this if there's a URL in the
source article we can process.  A DOI is ideal.  It also adds an unique tag
to each batch of uploads so you can delete any mistakes quite easily.

b) Attach any notes, files and CiTO (support isn't perfect yet) and tags.  Privacy
flags should be maintained (the only exception at the moment is for self-published
attachments)

c) Upload your metadata. Mostly this won't do very much but anything your
untrusted copy has that's not present in the trusted one will be uploaded.
A common example is abstracts which we can't get from crossref but which you
may have added by other means.

d) it should spit out a JSON list of files that can't be posted (Mostly
likely if there's no postable URL in the source article.)

e) If a trusted article already exists, the script will augment the
untrusted data (notes, files, metadata, tags, CiTO).

================================================================================
Notes
================================================================================

1) This does not convert articles from untrusted to trusted.  Instead you will get
an additional copy.

2) You should be able to see both the untrusted and trusted copies on the Duplicates
page.

3) When articles are posted, the new (trusted) copy has a private tag
*repost-<date> and the untrusted copy has *repost-<date>-unchecked.

4) If you don't like the new articles, simply delete all the articles with the
*repost-<date> tag.

5) If you're happy with the conversion, delete all those with *repost-<date>-unchecked.

================================================================================
CiTO
================================================================================

CitO tags are copied to the new articles and you will have CiTO links between both the
new and old articles and the article at the other end of the CiTO link.

However, if both the original articles are untrusted, there will be no link bewteen
the two new trusted articles

Before:

A
|
B

After

A A'
|X
B B'

THIS NEXT MIGHT WORK.  IT NEEDS MORE TESTING.

To rebuild the CiTO link, repeat the whole process from scratch (download the JSON
and re-run the script).

