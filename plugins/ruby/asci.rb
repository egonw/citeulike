#!/usr/bin/env ruby
require 'open-uri'

url = gets.strip
bibtex = open(url + '/cite/bibtex').read

id = url.split('/').last
doi = %r(doi\s*=\s*\{(10\.[^\/]+\/.+?)\}).match(bibtex)[1]

puts "begin_bibtex"
puts bibtex
puts "end_bibtex"
puts "begin_tsv"
puts "linkout\tJCI\t#{id}"
puts "linkout\tDOI\t#{doi}"
puts "end_tsv"
puts "status\tok"
