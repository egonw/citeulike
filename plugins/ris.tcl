#
# Copyright (c) 2005 Richard Cameron, CiteULike.org
# All rights reserved.
#
# This code is derived from software contributed to CiteULike.org
# by
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#        This product includes software developed by
#		 CiteULike <http://www.citeulike.org> and its
#		 contributors.
# 4. Neither the name of CiteULike nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CITEULIKE.ORG AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# Responsible for parsing RIS information returned by the scraper
# part of the plugins

# This code is a disgrace, but it seems to work on most of the
# broken implementations of RIS which are enountered in the wild.


proc map_ris_type {type} {

	# We use STD, but "officially" it's STAND
	if {$type eq {STAND}} {
		return {STD}
	}

	# These are the types we know about
	set known_types [regexp -all -inline {[A-Z]{3,}} {
		BOOK  - Whole book
		CHAP  - Book chapter
		GEN   - Generic
		CONF  - Conference proceeding
		INPR  - In Press
		JOUR  - Journal
		PAMP  - Pamphlet
		RPRT  - Report
		STD - Standard
		THES  - Thesis/Dissertation
		UNPB  - Unpublished work
		DATA  - Data file
		ELEC  - Web Page
	}]

	if {[lsearch -exact $known_types $type] != -1} {
		return $type
	}

	return {GEN}

	# TODO, provide a better mapping, e.g., ebook->book
	set all_types {
		ABST  - Abstract
		ADVS  - Audiovisual material
		AGGR  - Aggregated Database
		ANCIENT - Ancient Text
		ART   - Art Work
		BILL  - Bill
		BLOG  - Blog
		CASE  - Case
		CHART - Chart
		CLSWK - Classical Work
		COMP  - Computer program
		CONF  - Conference proceeding
		CPAPER - Conference paper
		CTLG  - Catalog
		DATA  - Data file
		DBASE - Online Database
		DICT  - Dictionary
		EBOOK - Electronic Book
		ECHAP - Electronic Book Section
		EDBOOK - Edited Book
		EJOUR - Electronic Article
		ELEC  - Web Page
		ENCYC - Encyclopedia
		EQUA  - Equation
		FIGURE - Figure
		GOVDOC - Government Document
		GRANT - Grant
		HEAR  - Hearing
		ICOMM - Internet Communication
		INPR  - In Press
		JFULL - Journal (full)
		JOUR  - Journal
		LEGAL - Legal Rule or Regulation
		MANSCPT - Manuscript
		MAP   - Map
		MGZN  - Magazine article
		MPCT  - Motion picture
		MULTI - Online Multimedia
		MUSIC - Music score
		NEWS  - Newspaper
		PAMP  - Pamphlet
		PAT   - Patent
		PCOMM - Personal communication
		RPRT  - Report
		SER   - Serial publication
		SLIDE - Slide
		SOUND - Sound recording
		STAND - Standard
		STAT  - Statute
		THES  - Thesis/Dissertation
		UNPB  - Unpublished work
		VIDEO - Video recording
	}
}



proc parse_ris {rec} {
	set last_tag ""
	set seen_abstracts [list]

	foreach l [split $rec "\n"] {

		set l [string map [list "\n" "" "\r" ""] $l]

		# We never have any use for blank lines
		if {[regexp {^ *$} $l]} {
			continue
		}

		# This is the gospel spec for a field header
		set ok [regexp {^([A-Z][A-Z0-9])  - (.*)$} $l match k v]

		# special case for "DOI" which is not part of the spec, but, ho, hum
		if {!$ok && [regexp {^(DOI)  - (.*)$} $l match k v]} {
			set ok 1
		}

		# Sometimes there are some borderline legal implementations
		# where empty fields are defined.
		if {!$ok && [regexp {^([A-Z][A-Z0-9])  -$} $l match k]} {
			set v ""
			set ok 1
		}


		# Maybe it's a line continuation
		# Technically should have some leading space, but this
		# doesn't always seem to happen, especially from one leading
		# publisher.
		if {!$ok && $last_tag!=""} {
			set k $last_tag
			set v $l
			set ok 1
		}


		if {$ok} {
			set v [string trim $v]
			set last_tag $k
			switch -regexp -- $k {

				{ER} {}
				{TY} {
					if {$v=="CHAP" || $v=="CHAPTER"} {
						set ret(type) INCOL
					} elseif {$v=="RPRT"} {
						set ret(type) REP
					} elseif {$v=="ABST"} {
						set ret(type) JOUR
					} else {
						set ret(type) [map_ris_type $v]
						#set ret(type) $v
					}
				}

				{ID} {
					set ret(id) $v
				}

				{(T1|TI|CT)} {
					if {![info exists ret(title)]} {
						set ret(title) "$v "
					} else {
						set t [string trim $v]
						if {($t ne "") && ([string first $t $ret(title)] < 0)} {
							append ret(title) "$v "
						}
					}
				}
				{BT} {
					if {$ret(type) == "UNPB" || $ret(type) == "BOOK"} {
						append ret(title) "$v "
					} else {
						set ret(title_secondary) $v
					}
				}

				{T2} {
					set ret(title_secondary) $v
				}

				{T3} {
					set ret(title_series) $v
				}


				{A1|AU} {
					# a few dud cases we've seen
					if {[regexp {^\s*[,\.]*\s*$} $v]} {
						continue
					}
					lappend ret(authors) $v
				}

				{A[2-9]|ED} {
					# a few dud cases we've seen
					if {[regexp {^\s*[,\.]*\s*$} $v]} {
						continue
					}
					lappend ret(editors) $v
				}

				{Y1|PY|Y2} {
					# We need to priortize Y1 > PY > Y2 so
					# store each and process later
					set date($k) $v
				}

				{N1|AB|N2} {
					# skip a leading DOI
					regsub {^\s*10\.\d\d\d\d/[^\s]+} $v {} v

					# Some sites (e.g. informahealthcare) put the abstract in multiple
					# fields.  Let's try and deal with that.
					if {$v eq "" || [lsearch $seen_abstracts $v] != -1} {
						# nothing
					} else {
						append ret(abstract) "$v "
						lappend seen_abstracts $v
					}
				}


				{JF|JO|JA} {
					if {$ret(type) eq "CHAP" || $ret(type) eq "CHAPTER" || $ret(type) eq "INCOL"} {
						set ret(title_secondary) "$v "
					} else {
						set ret(journal) $v
					}
				}
				{J1} {
					set ret(journal_user_abbrev_1) $v
				}
				{J2} {
					set ret(journal_user_abbrev_2) $v
				}

				{VL} {
					set ret(volume) $v
				}

				{IS} {
					set ret(issue) $v
				}

				{SP} {
					# sometimes have SP-EP (esp. SpringerLink)
					if {[regexp {(\d+)-(\d+)} $v -> sp ep]} {
						set ret(start_page) $sp
						set ret(end_page) $ep
					} else {
						set ret(start_page) $v
					}
				}

				{EP} {
					set ret(end_page) $v
				}

				{CP|CY} {
					set ret(city) $v
				}

				{PB} {
					set ret(publisher) $v
				}

				{SN} {
					set ret(serial) $v
				}

				{AD} {
					set ret(address) $v
				}

				{DOI|DO} {
					set ret(doi) $v
				}

				{UR} {
					set ret(url) $v
					if {[regexp {^http://dx.doi.org/(.*)$} $v -> ret(doi)]} {
						set ret(doi) [::cul::url::decode $ret(doi)]
					}
				}

				{L2} {
					set ret(fulltext_url) $v
				}

				{L1} {
					set ret(pdf_url) $v
				}

			}
		}
	}

	# We want priority of Y1 > PY > Y2
	foreach d {Y1 PY Y2} {
		if {[info exists date($d)]} {
			set thedate $date($d)
			break
		}
	}


	if {[info exists thedate]} {
		# Metapress bug has "yyyy-mm-dd/"
		set spl [split $thedate "/-"]
		if {[llength $spl]>0} {
			foreach {year month day other} $spl {}
			if {$year!="" && [string is integer $year]} {
				set ret(year) [format %04d $year]
			} else {
				set ret(year) ""
			}
			if {$month!="" && [scan $month %d month]} {
				set ret(month) $month
			} else {
				set ret(month) ""
			}

			if {$day!="" && [scan $day %d day]} {
				set ret(day) $day
			} else {
				set ret(day) ""
			}
			set ret(date_other) $other
		}
		# Some highwire has "September 2004", grab any year for now
		if {[info exists ret(year)] && $ret(year) eq ""} {
			regexp {(\d\d\d\d)} $thedate -> ret(year)
		}
	}


	if {[info exists ret(abstract)]} {
		set ret(abstract) [string trim $ret(abstract)]
	}

	if {[info exists ret(title)]} {
		set ret(title) [string trim $ret(title)]
	}

	#
	# RefMan Spec not good here.  Current version has T2=Full Journal Name, J2= Abbr.
	#
	# [prev had extra cond.: && $ret(journal) eq $ret(title_secondary)]
	if {[info exists ret(journal)] && [info exists ret(title_secondary)] } {
		unset ret(title_secondary)
	}

	if {[info exists ret(authors)]} {
		set authors {}
		foreach author $ret(authors) {
			lappend authors [::author::parse_author $author]
		}
		set ret(authors) $authors
	}

	if {[info exists ret(editors)]} {
		set editors {}
		foreach editor $ret(editors) {
			lappend editors [::author::parse_author $editor]
		}
		set ret(editors) $editors
	}


	return [array get ret]
}
