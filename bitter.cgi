#!/usr/bin/perl -w

# Ilan Goldman - z5050782
# Created :October 2015
# COMP2041/9041 assignment 2: http://cgi.cse.unsw.edu.au/~cs2041/assignments/bitter/

use CGI qw/:all/;
use List::Util 'first';
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use DateTime;
use Storable;

sub main() {
    # print start of HTML ASAP to assist debugging if there is an error in the script
    print page_header();
    
    # Now tell CGI::Carp to embed any warning in HTML
    warningsToBrowser(1);
    
    # define some global variables
    $debug = 1;
    $user_logged = "";
    $saved_flag = 0;
    $dataset_size = "medium"; 
    $users_dir = "dataset-$dataset_size/users";
    $bleats_dir = "dataset-$dataset_size/bleats";
   %users_info = ();
   %all_bleats = ();
    save_users_info();
   save_bleats_info();

    print navigation();
    print welcome_page();
    print page_trailer();
}

sub welcome_page() {
   return <<eof;
   <div class="menu">
   <div style="color:white;">
   <h1>Welcome to Bitter!</h1>
   <h2>The Place you want to be!</h2>
   <br> <h3>Please <a href="users.cgi?login=login" style="color:red;">login</a>.</h3>
   <h3> ------------ or --------------- </h3>
   <h3><a href="users.cgi?curr_user=all" class="btn btn-info btn-md"><span class="glyphicon glyphicon-search"></span> Search</a> for an user </h3>
   </div>
   </div>
eof
}

sub save_bleats_info {
   my @all_bleats = sort(glob("$bleats_dir/*"));
   foreach my $bleat_num (@all_bleats) {
      chomp $bleat_num;
      open(my $f, "$bleat_num") or die "can not open $bleat_num: $!";
      my @bleats_file = <$f>;
      close $f;
      foreach my $line (@bleats_file) {
         chomp $line;
         $line =~ m/(.*?):\s*(.*)/;
         $all_bleats{$bleat_num}{$1} = $2;
      }
   }
   store \%all_bleats, 'bleats_hash';
}

sub save_users_info {
   my @all_users = sort(glob("$users_dir/*"));
   foreach my $user (@all_users) {
      my $username = $user;
      my $details_filename = "$user/details.txt";
      open my $f, "$details_filename" or die "can not open $details_filename: $!";
      my @details = <$f>;
      close $f;
      foreach my $line (@details) {
         chomp $line;
         $line =~ m/(.*?):\s*(.*)/;
         $listens = $2;
         if ($1 =~ /listens/) {
            my @listening = split(' ',$listens);
            foreach my $other_user (@listening) {
               $users_info{$username}{"listens"}{$other_user} = 1;
            }
         } else {
            $users_info{$username}{$1} = $2;
         }
      }
      my $bleats_filename = "$user/bleats.txt";
      open my $f, "$bleats_filename" or die "can not open $bleats_filename: $!";
      my @bleats = <$f>;
      close $f;
      foreach my $line (@bleats) {
         chomp $line;
         $users_info{$username}{'bleats'}{$line} = 1;
      }
   }
   store \%users_info , 'users_hash'; 
}


sub navigation {
   my $login_bar =<<eof;
   <li><a href="signup.cgi"><span class="glyphicon glyphicon-user"></span> Sign Up</a></li>
   <li><a href="users.cgi?login=login"><span class="glyphicon glyphicon-log-in"></span> Login</a></li>
eof
   if ($user_logged ne "") {
      $login_bar = "<li><a href=\"users.cgi?logout=logout\"><span class=\"glyphicon glyphicon-log-out\"></span> Logout </a></li>";
   }
   
   return <<eof;
<nav class="navbar navbar-inverse">
  <div class="container-fluid">
    <div class="navbar-header">
      <a class="navbar-brand" href="bitter.cgi">Bitter</a>
    </div>
    <div>
      <ul class="nav navbar-nav"></ul>
      <ul class="nav navbar-nav navbar-right">
      $login_bar
      </ul>
    </div>
  </div>
</nav>
eof
}


#
# HTML placed at the top of every page
#
sub page_header {
    return <<eof
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
<head>
<title>Bitter</title>
  <link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
  <script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
  <link href="bitter.css" rel="stylesheet">
</head>
<body>
eof
}


#
# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable $debug is set
#
sub page_trailer {
    my $html = "";
    $html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
    $html .= end_html;
    return $html;
}

main();