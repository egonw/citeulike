#!/usr/bin/env tclsh

package require struct
package require http

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

proc driver_from_command_line {} {
	if {[info exists ::argv0] && [file tail $::argv0]=="driver.tcl"} {
		# We've been started up from the command line (by a plugin developer)
		# rather than from inside the application.
		return 1
	}
	return 0
}

if {[driver_from_command_line]} {
	set path [file dirname $::argv0]
	source [file join $path author.tcl]
	source [file join $path bibtex.tcl]
	source [file join $path ris.tcl]
	source [file join $path crossref.tcl]
	source [file join $path url.tcl]
}

# First thing to do is load the plugin description files and get some idea of what we're dealing with.
# They're all defined in a tcl-like syntax, so we need to define two trivial commands to parse them

# The base filenames of all the extensions we know about
namespace eval driver {

	variable PLUGINS

	proc plugin {raw_kvpairs} {
		variable PLUGIN
		variable DETAIL_${PLUGIN}

		# Bodge the contents of this string to remove
		# pseudo "comments".
		set kvpairs ""
		foreach line [split $raw_kvpairs "\n"] {
			if {![regexp {^\s*#} $line]} {
				append kvpairs "$line\n"
			}
		}

		array set DETAIL_${PLUGIN} $kvpairs


#		if {[info exists DETAIL_${PLUGIN}(regexp)] || [set DETAIL_${PLUGIN}(regexp)] ne ""} {
#			proc interested_in_${PLUGIN} {url} {
#				return [regexp $DETAIL_${PLUGIN}(regexp) $url]
#			}
#		}

		# Check for required fields
		foreach f {author email language regexp version} {
			if {![info exists DETAIL_${PLUGIN}($f)] || [set DETAIL_${PLUGIN}($f)]==""} {
				error "Plugin definition file for $PLUGIN does not define a value for: $f"
			}
		}
	}

	# This command is executed with the config file is sourced.

	proc format_linkout {type body} {
		# Slight Tcl tricker here. Define a procedure, but with
		# a slightly different signature to what might be obvious
		if {[string length $type] > 6} {
			error "format_linkout type can have a maximum of 6 chars (found '$type')"
		}
		proc format_linkout_${type} {type ikey_1 ckey_1 ikey_2 ckey_2} $body
	}


	proc test {url kvpairs} {
		variable PLUGIN
		variable TESTS_${PLUGIN}
		lappend TESTS_${PLUGIN} [list $url $kvpairs]
	}

	proc skiptest {url kvpairs} {
		#puts "Skipping tests for $url"
	}

#	proc interested {body} {
#		variable PLUGIN
#		proc interested_in_${PLUGIN} {url} {
#			return [eval {$body} $url]
#		}
#	}


	proc descr_dir {} {
	    if {![driver_from_command_line]} {
		return [file join $::env(PWD) descr]
	    } else {
		return [file join [file dirname $::argv0] descr]
	    }
	}

	proc read_descr {} {
		variable PLUGINS
		variable PLUGIN
		foreach file [glob -directory [descr_dir] "*.cul"] {
			set name [file rootname [file tail $file]]

			set PLUGIN $name

			# The description file is actually a valid TCL file, which we can source
			if {[source $file] eq "DISABLED"} {
				continue
			}

			lappend PLUGINS $name

			# Confirm it actually defined what it had to
			variable DETAIL_$PLUGIN
			if {![info exists DETAIL_${PLUGIN}]} {
				error "Plugin description file for $PLUGIN does not have a valid plugin directive"
			}

			set language [set DETAIL_${PLUGIN}(language)]

			variable TESTS_$PLUGIN
			if {$language!="none"} {
				if {![info exists TESTS_${PLUGIN}] || [llength [set TESTS_${PLUGIN}]]==0} {
					error "Plugin $PLUGIN does not define any tests"
				}
			}

			# And it had better actually have an executable
			set exe [executable_for_name $language $PLUGIN]
			if {![file exists $exe] && $language!="none"} {
				error "No executable exists for plugin ${PLUGIN}. I was expecting $exe"
			}
			if {![file executable $exe] && $language!="none"} {
				error "File should be executable: $exe"
			}
		}

		set PLUGINS [lsort $PLUGINS]
	}


	# The list of plugins which pass the initial
	# regexp test for the url
	proc interested_plugins {url} {
		variable PLUGINS

		set ret {}

		foreach p $PLUGINS {
			variable DETAIL_${p}
			if {[regexp [set DETAIL_${p}(regexp)] $url]} {
				lappend ret $p
			}
		}

		return $ret
	}

	# Some fields are special in that the support multiple
	# values. Linkouts and authors are two examples of this
	proc is_multiple_field {field} {
		if {[lsearch {author editor linkout formatted_url} $field]>-1} {
			return 1
		}
		return 0
	}


	proc set_doi_linkout_if_not_exist {r doi} {
		upvar $r ret
		set want_doi 1
		if {[info exists ret(linkout)]} {
			foreach lo $ret(linkout) {
				::struct::list assign [split $lo "\t"] type dummy dummy
				if {$type eq "DOI"} {
					set want_doi 0
				}
			}
		}
		if {$want_doi} {
			lappend ret(linkout) "DOI\t\t$doi\t\t"
		}
	}

	# Actually do the work. Given a URL, we'll actually
	# run the appropriate plugins and then we'll have a result.
	proc parse_url {in_url {rec_level 0} {candidate ""} {extra_linkouts {}}} {

		# strip off any google "utm_*" stuff
		# In many cases this will remove the qs completely
		set in_url [cul::url::cleanup_qs $in_url]

		# Plugins are permitted to "redirect" to other URLs
		# but we really don't want to end up in an infinite loop
		# with each iteration doing a DOS attack on our hosts.
		# Limit the recursion to much lower than the default tcl
		# recursion limit.
		if {$rec_level > 5} {
			error "Too much recursion. Last url was $in_url"
		}

		if {$candidate ne ""} {
			set candidates [list $candidate]
		} else {
			set candidates [interested_plugins $in_url]
		}

		foreach plugin $candidates {
			set url $in_url

			# For now, we'll just exec() a process. This is
			# not terribly efficient, and we ultimately want to
			# have the plugins run in a persistent executable which
			# we can talk to over a little socket server.
			#
			# It's fine for now though. One or two exec()s per post
			# isn't the limiting factor for performance at the moment.

			variable DETAIL_${plugin}
			set language [set DETAIL_${plugin}(language)]

			# Blocking IO. In production the server will abort the request
			# after a timeout and free the filedescriptor if it hangs.
			set exe [executable_for_name $language $plugin]
			set olddir [pwd]
			cd [file dirname $exe]
			if {1} {
				set result [exec ./[file tail $exe] << $url]
			} else {
				set fd [open "|./[file tail $exe]" "r+"]
				puts $fd $url
				flush $fd
				set result [read $fd]
				close $fd
			}

			cd $olddir

			set lines [split $result "\n"]

			# Tcl enforces the old unix convention that files end with a blank line
			set last_line [lindex $lines end]
			if {$last_line==""} {
				set lines [lrange $lines 0 end-1]
				set result [join $lines "\n"]
				set last_line [lindex $lines end]
			}

			# The last line of the file should contain some status information.
			if {![regexp {status\t([^\t]+)(\t(.*)+)?$} $last_line -> status extra]} {
				error "$plugin: Expected plugin to return status in last line. Got:\n---\n$result\n---"
			}

			if {$status!="ok" && $status!="err" && $status!="redirect" && $status!="not_interested"} {
				error "Invalid status code from plugin. Expected ok, err, or redirect. Got: $last_line"
			}

			set extra [string trim $extra]

			if {$status=="err"} {
				return [list status err msg [string trim $extra]]
			}

			# If this plugin is not interested, then we'll see if the next guy in the queue
			# can do any better
			if {$status=="not_interested"} {
				continue
			}


			# Otherwise we'll just have to sort out the data.
			set ret(status) $status

			set state ""
			set lineno 1
			foreach line [lrange $lines 0 end-1] {

				# Toy state machine to keep track of which block we should be parsing
				if {[regexp {^begin_(tsv|ris|bibtex|crossref)$} $line -> new_state]} {
					if {$state!=""} {
						error "$lineno: Nested begin blocks in output from $parser $url"
					}
					set state $new_state

					continue
				} elseif {[regexp {^end_(tsv|ris|bibtex|crossref)$} $line -> old_state]} {
					if {$state!=$old_state} {
						error "$lineno: Found end_$old_state block, but was in $state block"
					}

					# Flush the remaining buffer into the array
					if {$state=="tsv" && [info exists tsv_state]} {
						if {[is_multiple_field $tsv_state]} {
							lappend ret($tsv_state) $tsv_buffer
						} else {
							set ret($tsv_state) $tsv_buffer
						}
						set tsv_buffer ""
					}

					set state ""
					continue
				}

				if {$state=="tsv"} {
					if {[regexp {^([^\t]+)\t(.*)$} $line -> key value]} {
						if {[info exists tsv_state]} {
							if {[is_multiple_field $tsv_state]} {
								lappend ret($tsv_state) $tsv_buffer
							} else {
								set ret($tsv_state) $tsv_buffer
							}
						}
						set tsv_buffer $value
						set tsv_state $key
					} else {
						# It's a continuation of the previous key
						if {![info exists tsv_state]} {
							error "$lineno: Found data in output without knowing which key it belongs to: $line"
						}
						append tsv_buffer "\n$line"
					}
				} elseif {$state=="ris"} {
					lappend ris_lines $line
				} elseif {$state=="bibtex"} {
					if {![regexp "^%" $line]} {
						lappend bibtex_lines $line
					}
				} elseif {$state=="crossref"} {
					lappend crossref_lines $line
				}
			}
			if {$state!=""} {
				error "Saw begin $state block, but no end $state block"
			}


			# If another plugin can handle it, we'll do that
			# This is not caught earlier since a redirecting plugin
			# may nevertheless pass back linkouts
			if {$status=="redirect"} {
				if [info exists ret(linkout)] {
					set extra_linkouts [concat $extra_linkouts $ret(linkout)]
				}
				#puts "REDIRECT -> $extra :: $extra_linkouts"
				# puts [array get ret]
				incr rec_level
				return [parse_url [string trim $extra] $rec_level {} $extra_linkouts]
			}

			if {[info exists ret(linkout)] && $extra_linkouts ne ""} {
				set ret(linkout) [concat $extra_linkouts $ret(linkout)]
			}


			if {[info exists ris_lines]} {
				set ris [join $ris_lines "\n"]

				# Merge in. TSV data takes priority.
				foreach {k v} [parse_ris $ris] {
					if {![info exists ret($k)]} {
						set ret($k) $v
					}
					if {$k eq "doi"} {
						set_doi_linkout_if_not_exist ret $v
					}
				}
			}

			if {[info exists bibtex_lines]} {
				set bibtex [join $bibtex_lines "\n"]

				# Merge in. TSV data takes priority.
				foreach {k v} [parse_bibtex $bibtex] {
					if {![info exists ret($k)]} {
						set ret($k) $v
					}
					if {$k eq "doi" || $k eq "DOI"} {
						set_doi_linkout_if_not_exist ret $v
					}
				}
			}

			# puts "XXX: [array get ret]"

			# Shall we use extra crossref data?  Off by default
			# Either set globally in .cul file or in TSV, the latter taking
			# priority
			set use_crossref 0
			if {[info exists ret(use_crossref)]} {
				set use_crossref $ret(use_crossref)
			} else {
				catch {
					set use_crossref [set DETAIL_${plugin}(use_crossref)]
				}
			}

			if {[info exists crossref_lines]} {
				set crossref_xml [join $crossref_lines "\n"]

				# Merge in. TSV data takes priority.
				foreach {k v} [CROSSREF::parse_xml $crossref_xml] {
					if {![info exists ret($k)]} {
						if {$k eq "authors" || $k eq "editors"} {
							set au {}
							foreach a $v {
								lappend au [::author::parse_author $a]
							}
							set ret($k) $au
						} else {
							set ret($k) $v
						}
					}
				}
			} elseif {[info exists ret(linkout)] && $use_crossref} {
				# load crossref to augment above data
				foreach lo $ret(linkout) {
					::struct::list assign [split $lo "\t"] type dummy doi
					if {$type eq "DOI"} {
						set crossref_xml [CROSSREF::load $doi]
						if {$crossref_xml eq ""} {
							break
						}
						set crossref_data [CROSSREF::parse_xml $crossref_xml]


						foreach {k v} $crossref_data {
							if {$k eq "authors"} {
								# plugin returns "author" but xref -> "authors"
								set k "author"
							}
							if {$k eq "editors"} {
								# plugin returns "editor" but xref -> "editors"
								set k "editor"
							}
							if {![info exists ret($k)] || $ret($k) eq ""} {
								# puts "XREF::set $k -> $v"
								set ret($k) $v
							} else {
								# puts "XREF::noset $k -> $v"
							}

						}

						break
					}
				}

			}

			# Post-process what we've got from the plugin (TSV, which takes priority).
			if {[info exists ret(author)]} {
				catch {
					unset ret(authors)
				}
				foreach author $ret(author) {
					lappend ret(authors) [::author::parse_author $author]
				}
				unset ret(author)
			}

			if {[info exists ret(editor)]} {
				catch {
					unset ret(editors)
				}
				foreach editor $ret(editor) {
					lappend ret(editors) [::author::parse_author $editor]
				}
				unset ret(editor)
			}

			if {[info exists ret(linkout)]} {

				foreach lo $ret(linkout) {
					#
					# The elements in the linkout have types: str, int, str, int, str
					#
					set lst [split $lo "\t"]

					if {[llength $lst] != 5} {
						error "Linkout contains [llength $lst] element. Should be 5: $lst"
					}

					foreach {type ikey_1 ckey_1 ikey_2 ckey_2} [split $lo "\t"] { break }

					lappend ret(linkouts) [list $type $ikey_1 $ckey_1 $ikey_2 $ckey_2]
				}
				unset ret(linkout)
			}

			#
			# If it's an empty string, we may as well not have it
			#
			foreach {k v} [array get ret] {
				if {$v eq ""} {
					unset ret($k)
				}
			}

			# This is a particular BibTeX oddity
			if {[info exists ret(end_page)] && $ret(end_page)=="+"} {
				unset ret(end_page)
			}

			set ret(plugin) $plugin
			set ret(plugin_version) [set DETAIL_${plugin}(version)]


			# strip some funnies from start of abstract
			if {[info exists ret(abstract)]} {
				# 1. "Abstract: " - need to be careful since "Abstract" *might*
				# be a valid world, so check for colon.
				regsub -nocase {^\s*abstract\s*:\s*} $ret(abstract) {} ret(abstract)

				# 2. DOIs
				regsub -nocase {^\s*(doi:?\s*:\s*)?(10\.\d\d\d\d/[^\s]+(\s+|$))} $ret(abstract) {} ret(abstract)
				if {$ret(abstract) eq ""} {
					unset ret(abstract)
				}
			}


			# TODO - make sure the kv pairs takes priority over bibtex/ris
			# Return the first plugin which gets a result.

			return [array get ret]
		}

		return {}
	}

	proc executable_base_dir {} {
	    if {![driver_from_command_line]} {
		return "$::env(PWD)"
	    } else {
		return [file dirname $::argv0]
	    }
	}

	proc executable_for_name {language plugin} {

		switch -- [string tolower $language] {
			tcl {set ext "tcl"}
			perl {set ext "pl"}
			python {set ext "py"}
			ruby {set ext "rb"}
			none {set ext ""}
			default {error "Unsupported language: $language"}
		}

		# Check we're not going to be executing anything
		# surprising
		if {![regexp {[A-Za-z0-9_-]} $plugin]} {
			error "Illegal plugin name: $plugin"
		}
		return [file join [executable_base_dir] $language ${plugin}.${ext}]
	}


	proc test_error {level plugin url field error} {
		set field_part ""
		if {$field!=""} {
			set field_part "(Field = $field): "
		}
		puts stderr "$level: (Plugin = $plugin): (URL = $url): $field_part $error"
	}

	proc test_plugins {} {
		# Test 'em all.
		variable PLUGINS

		puts "Testing all plugins"
		puts ""
		puts "Please note that some tests may fail if you are running them from a"
		puts "machine which does not have access rights to the content, or if the"
		puts "scraper is written in an obscure language which you don't have installed"
		puts "on your machine."
		puts ""

		foreach p $PLUGINS {
			variable TESTS_$p
			if {[info exists TESTS_$p]} {
				test_plugin $p
			}
		}
	}

	proc is_integer {str} {
		# TCL does have a bit of a braindead implementation of "string is integer 09"
		return [regexp {^[0-9]+$} $str]
	}

	proc atoi {str} {
		if {[is_integer $str]} {
			return [scan $str "%d"]
		}
		error "Not an integer: $str"
	}

	proc test_plugin {plugin} {
		variable TESTS_${plugin}

		set count 1
		foreach test [set TESTS_$plugin] {
			set url [lindex $test 0]
			puts "Testing $plugin $count/[llength [set TESTS_$plugin]]"
			incr count

			set expected [lindex $test 1]

			set c [catch {
				set actual [parse_url $url]
			} msg]

			if {$c} {
				test_error Error $plugin $url "" "parse_url failed: $msg"
				continue
			}
			# set actual [parse_url $url]

			if {[llength $actual]==0} {
				test_error Error $plugin $url "" "Failed to parse $url"
				# No point checking anything else here
				continue
			}


			catch {unset x_expected}
			catch {unset x_actual}

			array set x_actual $actual

			# Can't do an array set as this contains multiple values
			foreach {k v} $expected {
				if {[is_multiple_field $k]} {
					lappend x_expected($k) $v
				} else {
					set x_expected($k) $v
				}
			}

			# The test case needs a bit of post-processing to put it into
			# canonical form
			if {[info exists x_expected(linkout)]} {
				set x_expected(linkouts) $x_expected(linkout)
				unset x_expected(linkout)
			}

			if {[info exists x_expected(author)]} {
				set x_expected(authors) $x_expected(author)
				unset x_expected(author)
			}

			if {[info exists x_expected(editor)]} {
				set x_expected(editors) $x_expected(editor)
				unset x_expected(editor)
			}


			# We'll also run the linkout formatter as we'll want to test that too.
			if {[info exists x_actual(linkouts)]} {
				foreach l $x_actual(linkouts) {
					foreach {type ikey_1 ckey_1 ikey_2 ckey_2} $l {}
					if {[info procs format_linkout_$type] ne ""} {
						foreach {descr link} [format_linkout_$type $type [string trim $ikey_1] [string trim $ckey_1] [string trim $ikey_2] [string trim $ckey_2]] {
							lappend x_actual(formatted_url) [list $descr $link]
						}
					}
				}
			}

			if {![info exists x_expected(status)]} {
				test_error Error $plugin $url status "Test case does not specify a value for the status field"
				continue
			}

			if {![info exists x_actual(status)]} {
				test_error Error $plugin $url status "Plugin did not return a value in the status field"
				continue
			}

			if {$x_actual(status) != $x_expected(status)} {
				if {[info exists x_actual(msg)]} {
					set msg " : $x_actual(msg)"
				} else {
					set msg ""
				}
				test_error Error $plugin $url status "Expected status $x_expected(status), but got $x_actual(status) $msg"
				continue
			}

			set expected [array get x_expected]
			set actual   [array get x_actual]


			# Check we get what we wanted
			foreach {k v} $expected {
				if {[info exists x_actual($k)]} {
					set actual_v $x_actual($k)
				} else {
					set actual_v ""
				}

				if {![string equal $actual_v $v]} {
					test_error Error $plugin $url $k "Expected:\n'$v'\nbut actually got:\n'$actual_v'\n\n\n"
				}
			}

			# And warn about any extra information
			foreach {k v} $actual {

				if {[lsearch {plugin plugin_version cite} $k]>-1} {
					# These aren't required to be in the test case
					continue
				}

				if {![info exists x_expected($k)]} {
					test_error Warning $plugin $url $k "Plugin returned data unexpected by test case: $v"
				}
			}
		}
	}



	if {[driver_from_command_line]} {
		# On startup from command line do stuff. Otherwise leave
		# the decision to the main application.
		read_descr

		set ok 0
		if {[llength $::argv]==2 && ([lindex $argv 0]=="test" || [lindex $argv 0]=="parse")} {
			set ok 1
		}

		if {!$ok} {
			puts {Usage:
  driver.tcl test all
  driver.tcl test -plugin-
  driver.tcl parse -url-

  test all: runs all tests. Note that some may fail
            unless you have access rights to everything
            the plugins require

  test -plugin-: will test just your plugin, where
                 the plugin is the base name of the .cul file

  parse -url-: will show the results of parsing an arbitrary url
			}
			exit
		}

		switch -- [lindex $::argv 0] {
			test {
				set plugin [lindex $::argv 1]
				if {$plugin=="all"} {
					test_plugins
				} else {
					test_plugin $plugin
				}
			}
			parse {
				set url [lindex $::argv 1]
				set parsed [parse_url $url]

				puts "parsing $url"
				puts ""
				if {[llength $parsed]==0} {
					puts "No plugin was interested in this url."
				} else {
					foreach {k v} $parsed {
						puts "$k -> $v"
					}
				}
			}

		}
	}
}
