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
puts "linkout\tJCI\t#{id}\t\t\t"
puts "linkout\tDOI\t\t#{doi}\t\t"
puts "end_tsv"
puts "status\tok"
