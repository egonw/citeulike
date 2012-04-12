IMPORTANT:

This is experimental software.  Use at your own risk.

(To be honest, the chance of catastophic destruction of your data is close
to zero.)

============================================================================
What this does.
============================================================================





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

b) Attach any notes, files and CiTO. (CiTO support isn't perfect yet.)

c) Upload your metadata. Mostly this won't do very much but anything your
untrusted copy has that's not present in the trusted one will be uploaded. 
A common example is abstracts which we can't get from crossref but which you
may have added by other means.

d) it should spit out a JSON list of files that can't be posted (Mostly
likely if there's no postable URL in the source article.)

e) If a trusted article already exists, the script will augment the
untrusted data (notes, files, metadata).
