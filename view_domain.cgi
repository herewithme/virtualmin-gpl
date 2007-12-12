#!/usr/local/bin/perl
# Show the details of one domain

require './virtual-server-lib.pl';
use POSIX;
&ReadParse();
$d = &get_domain($in{'dom'});
$d || &error($text{'edit_egone'});
&can_edit_domain($d) || &error($text{'edit_ecannot'});
if ($d->{'parent'}) {
	$parentdom = &get_domain($d->{'parent'});
	}
if ($d->{'alias'}) {
	$aliasdom = &get_domain($d->{'alias'});
	}
if ($d->{'subdom'}) {
	$subdom = &get_domain($d->{'subdom'});
	}
$tmpl = &get_template($d->{'template'});

&ui_print_header(&domain_in($d), $aliasdom ?  $text{'view_title3'} :
                                 $subdom ?    $text{'view_title4'} :
                                 $parentdom ? $text{'view_title2'} :
                                              $text{'view_title'}, "");

@tds = ( "width=30%" );
print &ui_hidden_table_start($text{'edit_header'}, "width=100%", 4,
			     "basic", 1);

# Domain name (with link), user and group
if ($d->{'web'}) {
	print &ui_table_row($text{'edit_domain'},
			"<tt><a href=http://$d->{'dom'}/>$d->{'dom'}</a></tt>",
			undef, \@tds);
	}
else {
	print &ui_table_row($text{'edit_domain'},
			    "<tt>$d->{'dom'}</tt>", undef, \@tds);
	}
print &ui_table_row($text{'edit_user'}, "<tt>$d->{'user'}</tt>",
		    undef, \@tds);
print &ui_table_row($text{'edit_group'},
		    $d->{'unix'} && $d->{'group'} ? "<tt>$d->{'group'}</tt>"
						  : $text{'edit_nogroup'},
		    undef, \@tds);

# Databases
@dbs = &domain_databases($d);
@mysqldbs = grep { $_->{'type'} eq "mysql" } @dbs;
@postgresdbs = grep { $_->{'type'} eq "postgres" } @dbs;
print &ui_table_row($text{'edit_dbs'},
	    @dbs ? scalar(@dbs)
		 : $text{'edit_nodbs'}, undef, \@tds);

# Creator
print &ui_table_row($text{'edit_created'},
	$d->{'creator'} ? &text('edit_createdby', &make_date($d->{'created'}),
						  $d->{'creator'})
			: &make_date($d->{'created'}),
	undef, \@tds);

# Template
print &ui_table_row($text{'edit_tmpl'}, $tmpl->{'name'}, undef, \@tds);

# Reseller
if ($virtualmin_pro) {
	print &ui_table_row($text{'edit_reseller'},
			    $d->{'reseller'} ? "<tt>$d->{'reseller'}</tt>"
					     : $text{'edit_noreseller'},
			    undef, \@tds);
	}

# IP-related options
if (!$aliasdom) {
	if ($d->{'reseller'}) {
		$resel = &get_reseller($d->{'reseller'});
		if ($resel) {
			$reselip = $resel->{'acl'}->{'defip'};
			}
		}
	print &ui_table_row($text{'edit_ip'},
		  "<tt>$d->{'ip'}</tt> ".
		  ($d->{'virt'} ? $text{'edit_private'} :
		   $d->{'ip'} eq $reselip ? &text('edit_rshared',
						  "<tt>$resel->{'name'}</tt>") :
					    $text{'edit_shared'}), 3, \@tds);
	}

# Home directory
if (!$aliasdom && $d->{'dir'}) {
	print &ui_table_row($text{'edit_home'}, "<tt>$d->{'home'}</tt>",
			    3, \@tds);
	}

# Description
print &ui_table_row($text{'edit_owner'}, $d->{'owner'}, 3, \@tds);

# Show forwarding / proxy destination
if ($d->{'proxy_pass_mode'} && $d->{'proxy_pass'} && $d->{'web'}) {
	print &ui_table_row($text{'edit_proxy'.$d->{'proxy_pass_mode'}},
		$d->{'proxy_pass'}, 3, \@tds);
	}

if ($aliasdom) {
	# Alias destination
	print &ui_table_row($text{'edit_aliasto'},
	   "<a href='view_domain.cgi?dom=$d->{'alias'}'>$aliasdom->{'dom'}</a>",
	   3, \@tds);
	}
elsif (!$parentdom) {
	# Contact email address
	print &ui_table_row($text{'edit_email'}, $d->{'emailto'}, 3, \@tds);
	}
else {
	# Show link to parent domain
	print &ui_table_row($text{'edit_parent'},
	    "<a href='view_domain.cgi?dom=$d->{'parent'}'>$parentdom->{'dom'}</a>",
	    3, \@tds);
	}

# Show any alias domains
@aliasdoms = &get_domain_by("alias", $d->{'id'});
if (@aliasdoms) {
	print &ui_table_row($text{'edit_aliasdoms'},
		&domains_list_links(\@aliasdoms, "alias", $d->{'dom'}),
		3, \@tds);
	}

# Show any sub-servers
@subdoms = &get_domain_by("parent", $d->{'id'}, "alias", undef);
if (@subdoms) {
	print &ui_table_row($text{'edit_subdoms'},
		&domains_list_links(\@subdoms, "parent", $d->{'dom'}),
		3, \@tds);
	}

print &ui_hidden_table_end("basic");

if (!$parentdom) {
	# Start of collapsible section for limits
	print &ui_hidden_table_start($text{'edit_limitsect'}, "width=100%", 2,
				     "limits", 0);
	}

# Show user and group quotas
if (&has_home_quotas() && !$parentdom) {
	print &ui_table_row($text{'edit_quota'},
	    $d->{'quota'} ? &quota_show($d->{'quota'}, "home")
			  : $text{'form_unlimit'}, 3, \@tds);

	print &ui_table_row($text{'edit_uquota'},
	    $d->{'uquota'} ? &quota_show($d->{'uquota'}, "home")
			   : $text{'form_unlimit'}, 3, \@tds);
	}

# Show disk usage
if (&has_home_quotas() && !$parentdom && $d->{'unix'}) {
	&show_domain_quota_usage($d);
	}

# Show bandwidth limit and usage
if ($config{'bw_active'} && !$parentdom) {
	print &ui_table_row($text{'edit_bw'},
	    $d->{'bw_limit'} ?
		&text('edit_bwpast_'.$config{'bw_past'},
		      &nice_size($d->{'bw_limit'}), $config{'bw_period'})." ".
		($config{'bw_disable'} &&
		 !$d->{'bw_no_disable'} ? $text{'edit_bwdis'} : "") :
		$text{'edit_bwnone'}, 3, \@tds);

	&show_domain_bw_usage($d);
	}

if (!$parentdom) {
	print &ui_hidden_table_end("limits");
	}

# Show active features
if ($d->{'disabled'}) {
	print "<font color=#ff0000>".
	      $text{'edit_disabled_'.$d->{'disabled_reason'}}." ".
	      $text{'edit_disabled'}."\n".
	      ($d->{'disabled_why'} ?
	        "<br>".&text('edit_disabled_why', $d->{'disabled_why'}) :
	       "").
	      "</font>";
	}
else {
	print &ui_hidden_table_start($text{'edit_featuresect'}, "width=100%", 2,
				     "feature", 0);
	@grid = ( );
	$i = 0;
	foreach $f (@features, @feature_plugins) {
		if ($d->{$f}) {
			local $txt = $text{'feature_'.$f};
			push(@grid, $txt);
			}
		}
	$featmsg .= &ui_grid_table(\@grid, 2, [ "width=30%", "width=70%" ],
				   undef, "width=100%");
	print &ui_table_row(undef, $featmsg);
	print &ui_hidden_table_end("feature");
	}

# Show actions for this domain, unless the theme vetos it (cause they are on
# the left menu)
if ($current_theme ne "virtual-server-theme" &&
    !$main::basic_virtualmin_domain) {
	&show_domain_buttons($d);
	}

# Make sure the left menu is showing this domain
if (defined(&theme_select_domain)) {
	&theme_select_domain($d);
	}

&ui_print_footer("", $text{'index_return'});

