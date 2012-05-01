#!/bin/sh

cd `dirname $0`

./highwire-journallister.pl > out.txt



cat out.txt | cut -f 1 | sort -u > highwire-urls.txt
cat out.txt | cut -f 2 | sort -u > highwire-names.txt

# diff highwire-urls.txt highwire-journal-list.txt

