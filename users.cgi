#!/usr/bin/perl -w

# Ilan Goldman - z5050782
# Created :October 2015
# COMP2041/9041 assignment 2: http://cgi.cse.unsw.edu.au/~cs2041/assignments/bitter/

use CGI qw/:all/;
use CGI::Cookie;
use List::Util 'first';
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use DateTime;
use Digest::MD5 qw(md5_hex);
use Storable;
$CGI::POST_MAX = 1024 * 5000;

sub main() {
   # define some global variables
   $debug = 1;
   $dataset_size = "medium"; 
   $users_dir = "dataset-$dataset_size/users";
   $bleats_dir = "dataset-$dataset_size/bleats";
   $curr_user = param('curr_user') || "";
   $not_found_flag = 0;
   $user_logged = "";
   $username = "";
   
   @cookies = cookie();
   check_login();
   
   %users_info = %{retrieve('users_hash')};
   %all_bleats = %{retrieve('bleats_hash')};

   if (defined(param('login'))) {
      $login = login();
   } elsif (defined(param('logout'))) {
      $logout = logout();
   }
   
   # need this cookie, so it can send the second one
   $null_cookie = cookie(-name=>'null',-value=>"0",-expires=>'+1h');
   
    # print start of HTML ASAP to assist debugging if there is an error in the script
    print header(-cookie=>[$null_cookie, $login_cookie]);
    print page_header();
    #@keys = keys %bleats_info;
   #print "<< @keys<br><br><br>";
   
    # Now tell CGI::Carp to embed any warning in HTML
    warningsToBrowser(1);
    
    #my $delete = ;
   
   if (defined(param('login'))) {
      # print the login page
      print login_navigation();
      print $login;
   } elsif (defined(param('logout'))) {
      # print the logout page
      print login_navigation();
      print $logout;
   } elsif (defined param('bleat')) {
      # print the logged user page when they bleat
      # or when they reply a bleat
      add_bleat();
      print navigation();
      print user_page();
      print input_new_bleats() if ($curr_user eq $user_logged);
      print bleats();
   } elsif (defined param('reply')) {
      # print the reply bleat page
      print navigation();
      print user_page();
      print reply_bleat();
      print input_reply();
   } elsif (defined param('delete')) {
      # print the delete bleat page
      print navigation();
      print user_page();
      print bleat_to_be_deleted();
   } elsif (defined param('edit_profile') or defined param('save_profile') or 
             defined param('remove_img')) {
      # print the edit_profile page
      # when saving the profile the user remain in the  edit page
      print navigation();
      print save_profile() unless (defined param('edit_profile'));
      print edit_profile();
   } elsif (defined param('search_bleat') or defined param('bleat_search') or
            defined param('prev_search') or defined param('next_search')) {
      print navigation();
      print search_bleats();
      print bleats_found() unless (defined param('search_bleat'));
   } elsif (defined param('in_reply_to')) {
      print navigation();
      print see_responses();
   } else {
      print navigation();
      
      if (defined param("search_user")) {
            print search_user();
      } elsif ($curr_user eq $user_logged) {
         # print all the bleats in the logged user main page
         # have to search every bleat
         print delete_bleat() if (defined param('yes_delete_bleat'));
         print user_page();
         print input_new_bleats();
         print bleats();
         
      } elsif (defined param('search_bleat')) {
         # have to search every bleat
         print search_bleats();
         
      } else {
         # if it the curr user is not the user logged
         # don't have to search every bleat
         
         if (defined param('listen')) {
            start_listen();
         } elsif (defined param('unlisten')) {
            unlisten();
         }
      
         if ($curr_user eq "all") {
            get_all_users();  
         } else {
            $not_found_flag = 1;
         }

         # decide if it is in a search or is just the user page
         if ($curr_user eq "all") {
            print all_users();   
         } elsif ($curr_user ne "") {
            add_bleat() if (defined param('send_reply'));
            
            print user_page();
            print curr_user_bleats();
         } else {
            print page_not_found();
         }
      }
   }
    print variables();
    print page_trailer();
}

##### all users ####################
sub get_all_users {
   @users = sort(glob("$users_dir/*"));
}

sub all_users() {
   my @all_users = ();
   my $num_of_users = 0;
   
   my $users_to_display = param('users_to_display') || 10;
   if (defined param('next_users')) {
      $users_to_display += 10;
   } elsif (defined param('prev_users')) {
      $users_to_display -= 10;
   }
   
   get_all_users();
   my $total_num_users = @users;
   foreach my $user (@users) {
      $num_of_users++;
      next if ($num_of_users <= $users_to_display-10);
      last if ($num_of_users > $users_to_display);
      my $check_user = $user;
      $user =~ s/$users_dir\///i;
      $all_users[$#all_users+1] = <<eof;
         <div class="container"><pre><li style="list-style-type:none;"><h4><a href="users.cgi?curr_user=$user">\t\@$user: $users_info{$check_user}{'full_name'} </a></h4></li></pre></div>
eof
   }
   
   # pagination
    my $page_num = $users_to_display/10;
    my $page = "<center><label>Page $page_num</label></center>";
   my $prev_users = "";
   my $next_users = "";
   $prev_users = "<input type=\"submit\" name=\"prev_users\" value=\"Previous 10 users\" class=\"btn btn-primary btn-md\" style=\"float:left;\">" if ($users_to_display-10 > 0);
   $next_users = "<input type=\"submit\" name=\"next_users\" value=\"Next 10 users\" class=\"btn btn-primary btn-md\" style=\"float:right;\">" if ($users_to_display < $total_num_users);
   
   my $html = join " ", @all_users;
   my $end_html="<form method=\"POST\" action=\"\">$page $prev_users $next_users <input type=\"hidden\" name=\"curr_user\" value=\"$curr_user\"><input type=\"hidden\" name=\"users_to_display\" value=\"$users_to_display\"></form><br></div>";
   
   return $html.$end_html;
}


##### search users ################

sub search_user {
   my $search_user = param('search_user');
   $search_user =~ s/[<>\"\']*//gi;
   my $print_user = "";
   
   my $users_to_display = param('users_to_display') || 10;
   if (defined param('next_users')) {
      $users_to_display += 10;
   } elsif (defined param('prev_users')) {
      $users_to_display -= 10;
   }
   
   get_all_users();
   my $total_num_users = 0;
   if ($search_user =~ /^\@/) {
      $search_user =~ s/@//g;
      foreach my $user (@users) {
         my $check_user = $user;
         $user =~ s/$users_dir\///;
         #print "$user -- $search_user";
         
         if ($user =~ /$search_user/i) {
            $total_num_users++;
            next if ($total_num_users <= $users_to_display-10);
            last if ($total_num_users > $users_to_display);
            $print_user .= "<div class=\"container\"><pre><li style=\"list-style-type:none;\"><h4><a href=\"users.cgi?curr_user=$user\">\t\@$user: $users_info{$check_user}{'full_name'} </a></h4></li></pre></div>";
         }
      }
   } else {
      foreach my $user (@users) {
         my $check_user = $user;
         $user =~ s/$users_dir\///;
         if ($users_info{$check_user}{'full_name'} =~ /$search_user/i) {
            $total_num_users++;
            next if ($total_num_users <= $users_to_display-10);
            last if ($total_num_users > $users_to_display);
            $print_user .= "<div class=\"container\"><pre><li style=\"list-style-type:none;\"><h4><a href=\"users.cgi?curr_user=$user\">\t\@$user: $users_info{$check_user}{'full_name'} </a></h4></li></pre></div>";
         }
      }
   }
   
   # pagination
    my $page_num = $users_to_display/10;
    my $page = "<center><label>Page $page_num</label></center>";
   my $prev_users = "";
   my $next_users = "";
   $prev_users = "<input type=\"submit\" name=\"prev_users\" value=\"Previous 10 users\" class=\"btn btn-primary btn-md\" style=\"float:left;\">" if ($users_to_display-10 > 0);
   $next_users = "<input type=\"submit\" name=\"next_users\" value=\"Next 10 users\" class=\"btn btn-primary btn-md\" style=\"float:right;\">" if ($users_to_display < $total_num_users);
   
   my $end_html="<form method=\"POST\" action=\"\">$page $prev_users $next_users <input type=\"hidden\" name=\"curr_user\" value=\"$curr_user\"><input type=\"hidden\" name=\"users_to_display\" value=\"$users_to_display\"><input type=\"hidden\" name=\"search_user\" value=\"$search_user\"></form><br>";
   
   return (($total_num_users > 10) ? $print_user.$end_html:$print_user);
}


##### users display ###############
sub page_not_found {
   return <<eof;
   <div class="page_not_found">
      <h1> Page not found. </h1>
      <h3> Please try again </h3>
   </div>
eof
}

sub user_page {
   my $user_image = "$users_dir/$curr_user/profile.jpg";
    $user_image = "default_profile.jpg" unless -e $user_image;
    
   my $user = "$users_dir/$curr_user";
   my $suburb = "";
   if (defined $users_info{$user}{"home_suburb"}) {
      $suburb = "<br>Suburb: ".$users_info{$user}{"home_suburb"};
   } 
   
   my $text = "";
   if (defined $users_info{$user}{"text"}) {
      $text = "<br>About me: ".$users_info{$user}{"text"};
   }
   
   my @users_listens = ();
   my $personal_info = "";
   my $edit_button = "";
   my @users_listening = keys %{$users_info{"$users_dir/$user_logged"}{"listens"}};
   my $listening_status = "";
   if ($curr_user ne $user_logged) {
      $users_listens[$#users_listens+1] = "<br>Listens to <br>";
      foreach my $listening_user (keys %{$users_info{$user}{"listens"}}) {
         $users_listens[$#users_listens+1] = <<eof;
            <a href="users.cgi?curr_user=$listening_user"> \@$listening_user </a>
eof
      }
      @users_listens = join "\n", @users_listens;
      if ($user_logged ne "") {
         if (match_regexp($curr_user,\@users_listening)) {
            $listening_status =<<eof;
            <form method="POST" action=""><center><input type="submit" name="unlisten" value="Unlisten" class="btn btn-danger btn-lg">
            </center><input type="hidden" name="curr_user" value="$curr_user"></form>
eof
         } else {
            $listening_status =<<eof;
            <form method="POST" action=""><center><input type="submit" name="listen" value="Listen" class="btn btn-success btn-lg">
            </center><input type="hidden" name="curr_user" value="$curr_user"></form>
eof
         }
      }
   } else {
      $edit_button =<<eof;
      <form method="POST" action="">
      <center><input type="submit" name="edit_profile" value="Edit personal information" class="btn btn-warning btn-md"></center></form>
eof
      $personal_info = "Email: $users_info{\"$users_dir/$user_logged\"}{'email'}";  
   }
      
    return <<eof;
<div class="user_details">
<img class="user_image" src="$user_image" alt="user_img"> $listening_status $edit_button
<h5>Name: $users_info{$user}{"full_name"}<br>
\@$users_info{$user}{"username"}
$suburb 
$personal_info
$text
@users_listens</h5>
</div>
eof
}

##### edit profile ##################

sub edit_profile {
   my $user = "$users_dir/$user_logged";
   my $user_image = "$users_dir/$user_logged/profile.jpg";
    $user_image = "default_profile.jpg" unless -e $user_image;
    
   my $information_to_edit =<<eof;
   <form method="POST" action="" class="form-horizontal" enctype="multipart/form-data">
   <div class="container">
   <div class="jumbotron">
   <h2><b> Edit your personal information: </b></h2>
   <div class="form-group">
      <h4><label class="control-label col-sm-2">Image: </label></h4>
      <div class="col-md-3"><img class="user_image" src="$user_image" alt="user_img"><br>
      <h5><input type="file" name="profile_img" accept="image/*"></h5>
      <h5><input type="submit" name="remove_img" class="btn btn-default btn-sm" value="Remove image"></div></h5>
    </div>
   <div class="form-group">
      <h4><label class="control-label col-sm-2">Username: </label>
      <div class="col-md-3"><p class="form-control-static"> \@$users_info{$user}{"username"}</p></div></h4>
    </div>
   <div class="form-group">
      <h4><label class="control-label col-sm-2">Name: </label>
      <div class="col-md-3"><input type="textfield" name="full_name" class="form-control" placeholder="$users_info{$user}{"full_name"}"></div></h4>
    </div>
    <div class="form-group">
      <h4><label class="control-label col-sm-2">Email: </label>
      <div class="col-sm-3"><input type="textfield" name="email" class="form-control" placeholder="$users_info{$user}{"email"}"></div></h4>
    </div>
    <div class="form-group">
      <h4><label class="control-label col-sm-2">Suburb: </label>
      <div class="col-sm-3"><input type="textfield" name="suburb" class="form-control" placeholder="$users_info{$user}{"home_suburb"}"></div></h4>
    </div>
    <div class="form-group">
      <h4><label class="control-label col-sm-2">About me: </label>
      <div class="col-sm-3"><textarea rows="4" cols="45" name="profile_text" maxlength="150" placeholder="$users_info{$user}{"text"}"></textarea></div></h4>
    </div>
    <div class="form-group">
      <h4><label class="control-label col-sm-2">Password: </label>
      <div class="col-sm-3"><input type="submit" name="change_pwd" class="btn btn-default btn md" value="Change Password"></div></h4>
    </div>
    <div class="form-group">
      <div class="col-sm-offset-2 col-sm-10"><input type="submit" name="save_profile" value="Save" class="btn btn-default"></div>
    </div>
    </div>
    </div>
   </form>
eof
   
   return $information_to_edit;
}

sub save_profile {
   my $user = "$users_dir/$user_logged";
   

   my $img = param('profile_img') || "";
   my $new_image = upload("profile_img"); 
   # sanatised the image name
   my $safe_characters = "a-zA-Z0-9_.-";
   $img =~ s/[^$safe_characters]//g;
   my $extension = $img;
   #print ">>$extension<<";
   $extension = s/(.*)\.(.*?)$/$2/; 
   #print ">>$extension--$1<<";
   if ($img ne "") {
      open(my $fh, ">$user/profile.jpg") or die "can not open $user/profile.jpg: $!";
      binmode $fh;
      local $/;
      my $content = <$img>;
      print $fh $content;
      close $fh;
   }
   
   if (defined param('remove_img')) {
      my $img_filename = "$user/profile.jpg";
      unlink $img_filename or warn "can not delete $img_filename: $!";
   }
   
   my $name = param('full_name') || $users_info{$user}{"full_name"};
   my $email = param('email') || $users_info{$user}{"email"};
   my $suburb = param('suburb') ||$users_info{$user}{"home_suburb"};
   my $text = param('profile_text') || $users_info{$user}{"text"};
   my $user_filename = "$users_dir/$user_logged/details.txt";
   open(my $fh, '<', $user_filename) or die "can not open $user_filename: $!";
   @user_details = <$fh>;
   close $fh;
   open($fh, '>', $user_filename) or die "can not open $user_filename: $!";
   foreach my $line (@user_details) {
      chomp $line;
      next if ($line =~ /^full_name/ or $line =~ /^email/ or $line =~ /^suburb/ or $line =~ /^text/);
      print $fh "$line\n";
   }
   print $fh "full_name: $name\n";
   print $fh "email: $email\n";
   print $fh "home_suburb: $suburb\n";
   print $fh "text: $text\n";
   close $fh;
   
   # update the users_hash
   save_users_info();
   return <<eof;
   <div class="container"><div class="alert alert-success"><h4>Your profile was updated successfully!</h4></div></div>
eof
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
         $hash = $1;
         $information = $2;
         if ($hash =~ /listens/) {
            my @listening = split(' ',$information);
            foreach my $other_user (@listening) {
               $users_info{$username}{"listens"}{$other_user} = 1;
            }
         } else {
            $users_info{$username}{$hash} = $information;
         }
      }
      my $bleats_filename = "$user/bleats.txt";
      open $f, "$bleats_filename" or die "can not open $bleats_filename: $!";
      my @bleats = <$f>;
      close $f;
      foreach my $line (@bleats) {
         chomp $line;
         $users_info{$username}{'bleats'}{$line} = 1;
      }
   }
   store \%users_info , 'users_hash'; 
}


##### listen and unlisten ###########
# changes the details.txt file to add the user you want to listen
sub start_listen {
   my $logged = "$users_dir/$user_logged";
   $users_info{$logged}{'listens'}{$curr_user} = 1;
   store \%users_info , 'users_hash';
   
   my $logged_filename = "$logged/details.txt";
   open(my $fh, '<', $logged_filename) or die "can not open $logged_filename: $!";
   my @details = <$fh>;
   close $fh;

   open($fh, '>', $logged_filename) or die "can not open $logged_filename: $!";
   foreach my $line (@details) {
      chomp $line;
      $line = "$line $curr_user" if ($line =~ /listens: /);
      print $fh "$line\n";
   }
   close $fh;
}

# changes the details.txt file to remove the user you want to stop listening
sub unlisten {
   my $logged = "$users_dir/$user_logged";
   delete $users_info{$logged}{'listens'}{$curr_user};
   store \%users_info , 'users_hash';
   
   my $logged_filename = "$logged/details.txt";
   open(my $fh, '<', $logged_filename) or die "can not open $logged_filename: $!";
   my @details = <$fh>;
   close $fh;

   open($fh, '>', $logged_filename) or die "can not open $logged_filename: $!";
   foreach my $line (@details) {
      chomp $line;
      if ($line =~ /listens: /) {
         $line =~ s/listens: //i;
         my @users = split / /, $line;
         foreach my $current (@users) {
            next if ($current =~ "$curr_user");
            $listening_users[$#listening_users+1] = $current;
         }
         @listening_users = join " ", @listening_users;
         print $fh "listens: @listening_users\n";
      } else {
         print $fh "$line\n";
      }
   }
   close $fh;
}

####### bleats display #############
# adds the html for the capacity of "bleating"
sub input_new_bleats {
   return <<eof;
   <div class="bleats">
   <form method="POST" action="">
      <textarea rows="4" cols="45" name="new_bleat" id="new_bleat" maxlength="142" placeholder="What's up?" onkeyup="countChar(this)"></textarea>
      <br>
      <input type="submit" name="bleat" id="bleat" value="Bleat" class="btn btn-info btn-lg" style="float:right;">
      <div id="bleat_feedback" style="font-size:1.5em;float:right;"></div>
      <input type="hidden" name="curr_user" value="$curr_user">
   </form>
   </div>
eof
}

# saves the bleat number in the logged user bleats.txt using the
# number stored in last_bleat.txt
# saves the bleat information in a file with the bleat number
sub add_bleat {
   open F, "<last_bleat.txt" or die "can not open last_bleat.txt: $!";
   $last_bleat = <F>;
   close F;
   chomp $last_bleat;
   $last_bleat += 1;
   open F, ">last_bleat.txt" or die "can not open last_bleat.txt: $!";
   print F "$last_bleat\n";
   close F;
   my $user_bleats = "$users_dir/$user_logged/bleats.txt";
   open(my $fh, '>>', $user_bleats) or die "can not open $user_bleats: $!";
   print $fh "$last_bleat\n";
   close $fh;
   my $new_bleat_text = param('new_bleat');
   my $time = time();
   my $reply_to = param('bleat_number') if (defined param('send_reply'));
   $reply_to =~ s/[^0-9]//g if (defined param('send_reply'));
   my $new_bleat = "$bleats_dir/$last_bleat";

   open F, ">$new_bleat" or die "can not open $new_bleat: $!";
   print F "bleat: $new_bleat_text\n";
   print F "time: $time\n";
   print F "username: $user_logged\n";
   print F "in_reply_to: $reply_to\n" if (defined param('send_reply'));
   close F;
   
   # update bleats_hash
   save_bleats_info();
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

sub search_bleats {
   my $search_param = param('search_param') || "";
   $search_param =~ s/[^a-z0-9\_\-\ \#\$\&]//gi;
   return <<eof;
   <div class="container"><div class="jumbotron">
   <form method="POST" action="">
      <h4><label>Type in search parameter: </label></h4>
      <input type="textfield" name="search_param" value="$search_param" class="form-control">
      <input type="submit" name="bleat_search" value="Search for bleats" class="btn btn-default btn-md">
   </form>
   </div></div>
eof
}

# returns a list of all the bleats it found after the search param are added
sub bleats_found {
   my $search_param = param('search_param');
   $search_param =~ s/[^a-z0-9\_\-\ \#\$\&]//gi;   
   
   my $total_num_bleats = 0;
   my %bleat_detail = ();
   
   foreach my $bleat_num (keys %all_bleats) {
      if ($all_bleats{$bleat_num}{"bleat"} =~ /$search_param/i) {
         $total_num_bleats++;
         my $time = $all_bleats{$bleat_num}{"time"};
         my $num = $bleat_num;
         $num =~ s/$bleats_dir\///;
         $bleat_detail{$time}{'bleat_num'} = $num;
         foreach my $info (keys %{$all_bleats{$bleat_num}}) {
            next if $info eq "time";
            $bleat_detail{$time}{$info} = $all_bleats{$bleat_num}{$info};
         }
      }
   }
   
   my @formated_bleats = ();
    my $bleats_to_display = param('bleats_to_display') || 10;
   if (defined param('next_search')) {
      $bleats_to_display += 10;
   } elsif (defined param('prev_search')) {
      $bleats_to_display -= 10;
   }
   my $num_of_bleats = 0;
    foreach my $time (reverse sort {$a <=> $b} keys %bleat_detail) {
      $num_of_bleats++;
      next if ($num_of_bleats <= $bleats_to_display-10);
      last if ($num_of_bleats > $bleats_to_display);
      my $delete = "";
      my $reply = "";
      if ($user_logged eq $curr_user and $bleat_detail{$time}{"username"} eq $user_logged) {
         $delete = "<input type=\"submit\" name=\"delete\" value=\"Delete\" class=\"btn btn-danger btn-sm\" style=\"float:right;\">";
      } elsif ($user_logged ne "") {
         $reply = "<input type=\"submit\" name=\"reply\" value=\"Reply\" class=\"btn btn-default btn-sm\" style=\"float:right;\">";
         $in_reply_to = "<input type=\"submit\" name=\"in_reply_to\" value=\"See replies\" class=\"btn btn-default btn-sm\" style=\"float:right;\">" if ($bleat_detail{$time}{"in_reply_to"} ne "");
      }
      my $dt = DateTime->from_epoch(epoch => $time);
      my $day = $dt->day;
      my $month = $dt->month;
      my $year = $dt->year;
      my $hour = $dt->hour;
      my $min = $dt->minute;
      $formated_bleats[$#formated_bleats+1] = <<eof;
      <form method="POST" action=""> $delete $reply $in_reply_to
      <span style="font-style: italic;font-weight:bold;text-decoration:underline;"><a href="users.cgi?curr_user=$bleat_detail{$time}{"username"}">\@$bleat_detail{$time}{"username"}</a> - $day/$month/$year</span> 
      <br>\t$bleat_detail{$time}{"bleat"} <input type="hidden" name="curr_user" value="$curr_user"><input type="hidden" name="bleat_number" value="$bleat_detail{$time}{'bleat_num'}"><input type="hidden" name="reply_user" value="$bleat_detail{$time}{"username"}"></form> <hr style="border-color:black"> 
eof
    }
    
    my $page_num = $bleats_to_display/10;
    my $page = "<center><label>Page $page_num</label></center>";
   my $prev_bleats = "";
   my $next_bleats = "";
   
   $prev_bleats = "<input type=\"submit\" name=\"prev_search\" value=\"Previous 10 bleats\" class=\"btn btn-primary btn-md\" style=\"float:left;\">" if ($bleats_to_display-10 > 0);
   $next_bleats = "<input type=\"submit\" name=\"next_search\" value=\"Next 10 bleats\" class=\"btn btn-primary btn-md\" style=\"float:right;\">" if ($bleats_to_display < $total_num_bleats);
   
   my $start_html= "<div class=\"container\"><div class=\"jumbotron\"";
   my $return_hmtl = join "<br>", @formated_bleats;
   my $end_html="<form method=\"POST\" action=\"\">$page $prev_bleats $next_bleats <input type=\"hidden\" name=\"curr_user\" value=\"$curr_user\"><input type=\"hidden\" name=\"bleats_to_display\" value=\"$bleats_to_display\"><input type=\"hidden\" name=\"search_param\" value=\"$search_param\"></form><br></div></div>";
   
   return $start_html.$return_hmtl.$end_html;
}

# the bleats in the logged_user page
sub bleats {
   my $total_num_bleats = 0;
   my %bleat_detail = ();
   
   my $user = "$users_dir/$curr_user";
   my @see_users = keys %{$users_info{$user}{'listens'}};
   push @see_users, $user_logged;
   
   foreach my $bleat_num (keys %all_bleats) {
      my $username = $all_bleats{$bleat_num}{"username"};
      my $bleat = $all_bleats{$bleat_num}{"bleat"};
      if (match_regexp($username,\@see_users) or $bleat =~ /\@$user_logged/) {
         $total_num_bleats++;
         my $time = $all_bleats{$bleat_num}{"time"};
         my $num = $bleat_num;
         $num =~ s/$bleats_dir\///;
         $bleat_detail{$time}{'bleat_num'} = $num;
         foreach my $info (keys %{$all_bleats{$bleat_num}}) {
            next if $info eq "time";
            $bleat_detail{$time}{$info} = $all_bleats{$bleat_num}{$info};
         }  
      }
   }
  
    my @formated_bleats = ();
    my $bleats_to_display = param('bleats_to_display') || 10;
   if (defined param('next_bleats')) {
      $bleats_to_display += 10;
   } elsif (defined param('prev_bleats')) {
      $bleats_to_display -= 10;
   }
   my $num_of_bleats = 0;
    foreach my $time (reverse sort {$a <=> $b} keys %bleat_detail) {
      $num_of_bleats++;
      next if ($num_of_bleats <= $bleats_to_display-10);
      last if ($num_of_bleats > $bleats_to_display);
      my $delete = "";
      my $reply = "";
      my $in_reply_to = "";
      if ($user_logged eq $curr_user and $bleat_detail{$time}{"username"} eq $user_logged) {
         $delete = "<input type=\"submit\" name=\"delete\" value=\"Delete\" class=\"btn btn-danger btn-sm\" style=\"float:right;\">";
         $in_reply_to = "<input type=\"submit\" name=\"in_reply_to\" value=\"See replies\" class=\"btn btn-default btn-sm\" style=\"float:right;\">" if (defined $bleat_detail{$time}{"in_reply_to"});
      } elsif ($user_logged ne "") {
         $reply = "<input type=\"submit\" name=\"reply\" value=\"Reply\" class=\"btn btn-default btn-sm\" style=\"float:right;\">";
         $in_reply_to = "<input type=\"submit\" name=\"in_reply_to\" value=\"See replies\" class=\"btn btn-default btn-sm\" style=\"float:right;\">" if (defined $bleat_detail{$time}{"in_reply_to"});
      }
      
      my $dt = DateTime->from_epoch(epoch => $time);
      my $day = $dt->day;
      my $month = $dt->month;
      my $year = $dt->year;
      my $hour = $dt->hour;
      my $min = $dt->minute;
      $formated_bleats[$#formated_bleats+1] = <<eof;
      <form method="POST" action=""> $delete $reply $in_reply_to
      <span style="font-style: italic;font-weight:bold;text-decoration:underline;"><a href="users.cgi?curr_user=$bleat_detail{$time}{"username"}">\@$bleat_detail{$time}{"username"}</a> - $day/$month/$year</span> 
      <br>\t$bleat_detail{$time}{"bleat"} <input type="hidden" name="curr_user" value="$curr_user"><input type="hidden" name="bleat_number" value="$bleat_detail{$time}{'bleat_num'}"><input type="hidden" name="reply_user" value="$bleat_detail{$time}{"username"}"></form> <hr style="border-color:black"> 
eof
    }
    my $page_num = $bleats_to_display/10;
    my $page = "<center><label>Page $page_num</label></center>";
   my $prev_bleats = "";
   my $next_bleats = "";
   $prev_bleats = "<input type=\"submit\" name=\"prev_bleats\" value=\"Previous 10 bleats\" class=\"btn btn-primary btn-md\" style=\"float:left;\">" if ($bleats_to_display-10 > 0);
   $next_bleats = "<input type=\"submit\" name=\"next_bleats\" value=\"Next 10 bleats\" class=\"btn btn-primary btn-md\" style=\"float:right;\">" if ($bleats_to_display < $total_num_bleats);
   
   my $start_html= "<div class=\"bleats\">";
   my $return_hmtl = join "<br>", @formated_bleats;
   my $end_html="<form method=\"POST\" action=\"\">$page $prev_bleats $next_bleats <input type=\"hidden\" name=\"curr_user\" value=\"$curr_user\"><input type=\"hidden\" name=\"bleats_to_display\" value=\"$bleats_to_display\"></form><br></div>";
   
   return $start_html.$return_hmtl.$end_html;
}

# display only the bleats form the curr_user
# doesn't have to access every bleat
sub curr_user_bleats {
   my $user_bleats = "$users_dir/$curr_user/bleats.txt";
    open my $f, "$user_bleats" or die "can not open $user_bleats: $!";
    my @bleats = <$f>;
    close $f;
    
    my %bleat_detail = ();
    my $total_num_bleats = @bleats;
    foreach my $bleat (@bleats) {
      chomp $bleat;
      my $bleats_filename = "$bleats_dir/$bleat";
      open(my $f, "$bleats_filename") or die "can not open $bleats_filename: $!";
      my @bleats_file = <$f>;
      close $f;
      my $time = first {/^time/} @bleats_file;
      next if $time eq "";
      chomp $time;
      $time =~ s/time:\s*(.*)/$1/i;
      $bleat_detail{$time}{'bleat_num'} = $bleat;
      foreach my $line (@bleats_file) {
         chomp $line;
         next if ($line =~ /^time:/);
         $line =~ m/(.*?):\s*(.*)/;
         $bleat_detail{$time}{$1} = $2;
      }
    }
    my @formated_bleats = ();
    my $bleats_to_display = param('bleats_to_display') || 10;
   if (defined param('next_bleats')) {
      $bleats_to_display += 10;
   } elsif (defined param('prev_bleats')) {
      $bleats_to_display -= 10;
   }
   my $num_of_bleats = 0;
    foreach my $time (reverse sort {$a <=> $b} keys %bleat_detail) {
      $num_of_bleats++;
      next if ($num_of_bleats <= $bleats_to_display-10);
      last if ($num_of_bleats > $bleats_to_display);
      my $reply = "";
      my $in_reply_to = "";
      if ($user_logged ne "") {
         $reply = "<input type=\"submit\" name=\"reply\" value=\"Reply\" class=\"btn btn-default btn-sm\" style=\"float:right;\">";
         $in_reply_to = "<input type=\"submit\" name=\"in_reply_to\" value=\"See replies\" class=\"btn btn-default btn-sm\" style=\"float:right;\">" if ($bleat_detail{$time}{"in_reply_to"} ne "");
      }
      my $dt = DateTime->from_epoch(epoch => $time);
      my $day = $dt->day;
      my $month = $dt->month;
      my $year = $dt->year;
      my $hour = $dt->hour;
      my $min = $dt->minute;
      $formated_bleats[$#formated_bleats+1] = <<eof;
      <form method="POST" action=""> $reply $in_reply_to 
      <span style="font-style: italic;font-weight:bold;text-decoration:underline;"><a href="users.cgi?curr_user=$bleat_detail{$time}{"username"}">\@$bleat_detail{$time}{"username"}</a> - $day/$month/$year</span> 
      <br>\t$bleat_detail{$time}{"bleat"} <input type="hidden" name="curr_user" value="$curr_user"><input type="hidden" name="bleat_number" value="$bleat_detail{$time}{'bleat_num'}"><input type="hidden" name="reply_user" value="$bleat_detail{$time}{"username"}"></form> <hr style="border-color:black"> 
eof
    }
    my $page_num = $bleats_to_display/10;
    my $page = "<center><label>Page $page_num</label></center>";
   my $prev_bleats = "";
   my $next_bleats = "";
   $prev_bleats = "<input type=\"submit\" name=\"prev_bleats\" value=\"Previous 10 bleats\" class=\"btn btn-primary btn-md\" style=\"float:left;\">" if ($bleats_to_display-10 > 0);
   $next_bleats = "<input type=\"submit\" name=\"next_bleats\" value=\"Next 10 bleats\" class=\"btn btn-primary btn-md\" style=\"float:right;\">" if ($bleats_to_display < $total_num_bleats);

   my $start_html= "<div class=\"bleats\">";
   my $return_hmtl = join "<br>", @formated_bleats;
   my $end_html="<form method=\"POST\" action=\"\">$page $prev_bleats $next_bleats <input type=\"hidden\" name=\"curr_user\" value=\"$curr_user\"><input type=\"hidden\" name=\"bleats_to_display\" value=\"$bleats_to_display\"></form><br></div>";

   return $start_html.$return_hmtl.$end_html;
}

##### delete bleat ###############

# deletes the bleat from the users reference and
# the actual file of the bleat
sub delete_bleat {
    my $bleat = param('bleat_number');
    chomp $bleat;
   my $user_bleats = "$users_dir/$user_logged/bleats.txt";
   open(my $fh, '<', $user_bleats) or die "can not open $user_bleats: $!";
   my @user_bleats = <$fh>;
   close $fh;
   open($fh, '>', $user_bleats) or die "can not open $user_bleats: $!";
   foreach my $line (@user_bleats) {
      chomp $line;
      next if ($line =~ /^$bleat/);
      print $fh "$line\n";
   }
   close $fh;
   
   my $bleat_filename = "$bleats_dir/$bleat";
   unlink $bleat_filename or warn "can not delete $bleat_filename: $!";
   
   #update hash
   delete $all_bleats{$bleat_filename};
   store \%all_bleats, 'bleats_hash';
   save_bleats_info();

   
   return <<eof;
   <div class="container"><div class="alert alert-success"><h4>The bleat was deleted successfully!</h4></div></div>
eof
}

sub bleat_to_be_deleted {
   my %delete_bleat = ();
    my $bleat = param('bleat_number');
    chomp $bleat;
   my $bleat_filename = "$bleats_dir/$bleat";
   open(my $f, "$bleat_filename") or die "can not open $bleat_filename: $!";
   my @bleat_file = <$f>;
   close $f;
   foreach my $line (@bleat_file) {
      chomp $line;
      $line =~ m/(.*?):\s*(.*)/;
      $delete_bleat{$1} = $2;
   }
   my $dt = DateTime->from_epoch(epoch => $delete_bleat{'time'});
   my $day = $dt->day;
   my $month = $dt->month;
   my $year = $dt->year;
   my $hour = $dt->hour;
   my $min = $dt->minute;
   my $formated_bleat = <<eof;
   <br>
   <span style="font-style: italic;font-weight:bold;text-decoration:underline;"><a href="users.cgi?curr_user=$delete_bleat{"username"}">\@$delete_bleat{"username"}</a> - $day/$month/$year</span> 
   <br>\t$delete_bleat{"bleat"}
   <form method="POST" action="" class="form-inline">
   <hr style="border-color:black"><br><label>Are you sure you want to delete this bleat: </label>    <input type="submit" class="btn btn-default btn-md" name="yes_delete_bleat" value="Yes">    <input type="submit" class="btn btn-default btn-md" name="no_delete_bleat" value="No">
   <input type="hidden" name="curr_user" value="$curr_user"><input type="hidden" name="bleat_number" value="$bleat"></form>
eof

   my $start_html= "<div class=\"bleats\">";
   my $end_html="<br></div>";
   
   return $start_html.$formated_bleat.$end_html;
}

##### reply bleat ###############

# prints all the replies given to that bleat and
# all the bleats that  this bleat responded to
sub see_responses {
   my $bleat_num = param('bleat_number');
   $bleat_num =~ s/[^0-9]//g;
   $bleat_num = "$bleats_dir/$bleat_num";
   
   my $in_reply_to = $all_bleats{$bleat_num}{"in_reply_to"};
   
   my $total_num_bleats = 0;
   my %bleat_detail = ();
   
   while ($bleat_num ne "$bleats_dir/") {
      my $time = $all_bleats{$bleat_num}{"time"};
      my $num = $bleat_num;
      $num =~ s/$bleats_dir//;
      $bleat_detail{$time}{'bleat_num'} = $num;
      foreach my $info (keys %{$all_bleats{$bleat_num}}) {
         next if $info eq "time";
         $bleat_detail{$time}{$info} = $all_bleats{$bleat_num}{$info};
      }
      $total_num_bleats++;
      $bleat_num = "$bleats_dir/$in_reply_to";
      $in_reply_to = $all_bleats{$bleat_num}{"in_reply_to"};
   }
   
   my @formated_bleats = ();
    my $bleats_to_display = param('bleats_to_display') || 10;
   if (defined param('next_search')) {
      $bleats_to_display += 10;
   } elsif (defined param('prev_search')) {
      $bleats_to_display -= 10;
   }
   my $num_of_bleats = 0;
    foreach my $time (sort {$a <=> $b} keys %bleat_detail) {
      $num_of_bleats++;
      next if ($num_of_bleats <= $bleats_to_display-10);
      last if ($num_of_bleats > $bleats_to_display);
      my $delete = "";
      my $reply = "";
      if ($user_logged eq $curr_user and $bleat_detail{$time}{"username"} eq $user_logged) {
         $delete = "<input type=\"submit\" name=\"delete\" value=\"Delete\" class=\"btn btn-danger btn-sm\" style=\"float:right;\">";
      } elsif ($user_logged ne "") {
         $reply = "<input type=\"submit\" name=\"reply\" value=\"Reply\" class=\"btn btn-default btn-sm\" style=\"float:right;\">"
      }
      my $dt = DateTime->from_epoch(epoch => $time);
      my $day = $dt->day;
      my $month = $dt->month;
      my $year = $dt->year;
      my $hour = $dt->hour;
      my $min = $dt->minute;
      $formated_bleats[$#formated_bleats+1] = <<eof;
      <form method="POST" action=""> $delete $reply
      <span style="font-style: italic;font-weight:bold;text-decoration:underline;"><a href="users.cgi?curr_user=$bleat_detail{$time}{"username"}">\@$bleat_detail{$time}{"username"}</a> - $day/$month/$year</span> 
      <br>\t$bleat_detail{$time}{"bleat"} <input type="hidden" name="curr_user" value="$curr_user"><input type="hidden" name="bleat_number" value="$bleat_detail{$time}{'bleat_num'}"><input type="hidden" name="reply_user" value="$bleat_detail{$time}{"username"}"></form> <hr style="border-color:black"> 
eof
    }
    
    my $page_num = $bleats_to_display/10;
    my $page = "<center><label>Page $page_num</label></center>";
   my $prev_bleats = "";
   my $next_bleats = "";
   
   $prev_bleats = "<input type=\"submit\" name=\"prev_search\" value=\"Previous 10 bleats\" class=\"btn btn-primary btn-md\" style=\"float:left;\">" if ($bleats_to_display-10 > 0);
   $next_bleats = "<input type=\"submit\" name=\"next_search\" value=\"Next 10 bleats\" class=\"btn btn-primary btn-md\" style=\"float:right;\">" if ($bleats_to_display < $total_num_bleats);
   
   my $start_html= "<div class=\"container\"><div class=\"jumbotron\"";
   my $return_hmtl = join "<br>", @formated_bleats;
   my $pagination = "<form method=\"POST\" action=\"\">$page $prev_bleats $next_bleats <input type=\"hidden\" name=\"curr_user\" value=\"$curr_user\"><input type=\"hidden\" name=\"bleats_to_display\" value=\"$bleats_to_display\"></form><br>";
   
   my $end_html= (($total_num_bleats > 10) ? "$pagination":"");
   $end_html .= "</div></div>";

   return $start_html.$return_hmtl.$end_html;
}

# prints the bleat you are replying to
sub reply_bleat {
   my %reply_bleat = ();
    my $bleat = param('bleat_number');
    chomp $bleat;
   my $bleat_filename = "$bleats_dir/$bleat";
   open(my $f, "$bleat_filename") or die "can not open $bleat_filename: $!";
   my @bleat_file = <$f>;
   close $f;
   foreach my $line (@bleat_file) {
      chomp $line;
      $line =~ m/(.*?):\s*(.*)/;
      $reply_bleat{$1} = $2;
   }
   my $dt = DateTime->from_epoch(epoch => $reply_bleat{'time'});
   my $day = $dt->day;
   my $month = $dt->month;
   my $year = $dt->year;
   my $hour = $dt->hour;
   my $min = $dt->minute;
   my $formated_bleat = <<eof;
   <form method="POST" action="">
   <span style="font-style: italic;font-weight:bold;text-decoration:underline;"><a href="users.cgi?curr_user=$reply_bleat{"username"}">\@$reply_bleat{"username"}</a> - $day/$month/$year</span> 
   <br>\t$reply_bleat{"bleat"} <input type="hidden" name="curr_user" value="$curr_user"></form>
eof

   my $start_html= "<div class=\"bleats\">";
   my $end_html="<br></div>";
   
   return $start_html.$formated_bleat.$end_html;
}

# prints a place for the user to type in their response
sub input_reply {
   my $reply_user = param('reply_user');
   my $bleat = param('bleat_number');
   return <<eof;
   <div class="bleats">
   <form method="POST" action="">
      <textarea rows="4" cols="45" name="new_bleat" id="new_bleat" maxlength="142" onkeyup="countChar(this)"> \@$reply_user </textarea>
      <br>
      <input type="submit" name="send_reply" value="Reply" class="btn btn-info btn-lg" style="float:right;">
      <div id="bleat_feedback" style="font-size:1.5em;float:right;"></div>
      <input type="hidden" name="curr_user" value="$curr_user">
      <input type="hidden" name="bleat_number" value="$bleat">
   </form>
   </div>
eof
}

##### login and logout ##############
sub check_login {
   my $login_code = "";
   foreach my $c (@cookies) {
      next unless ($c eq "login_info");
      ($login_code,$username) = split("<->",cookie($c));
   }
   $username =~ s/\W//g;
   $login_code =~ s/\W//g;
   #print ">$login_code--$username<<br>";
   open F, "<password_codes.txt";
   my @all_logged_users = <F>;
   close F;
   foreach my $logged_user (@all_logged_users) {
      #print ">>$logged_user<br>";
      chomp $logged_user;
      my ($correct_code,$correct_user) = split("<->",$logged_user);
      #print "<$correct_code--$correct_user><br>";
      if ($correct_code eq $login_code and $correct_user eq $username) {
         $user_logged = $username;
         last;
      }
   }
}

sub login_navigation {
   my $sign_up = "";
   my $login_bar = "";
   
   if (not defined param('login_status')) {
      $sign_up = "<li><a href=\"signup.cgi\"><span class=\"glyphicon glyphicon-user\"></span> Sign Up</a></li>";
   }
   
   if (defined param('logout')) {
      $login_bar = "<li><a href=\"users.cgi?login=login\"><span class=\"glyphicon glyphicon-log-in\"></span> Login </a></li>";
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
        $sign_up
        $login_bar
      </ul>
    </div>
  </div>
</nav>
   <form method="POST" action="">
      <input type="hidden" name="login" value="Login">
      <input type="hidden" name="logout" value="Logout">
   </form>
eof
}

sub login {
   $username = param('username') || '';
   my $password = param('password') || '';
   $username =~ s/[>\s\"]+//g;
   $password =~ s/[>\s\"]+//g;
   
   my $login_return = "<div class=\"container\"><div class=\"jumbotron\">\n";
   my $wrong_message = "<h4><span style=\"color:red;\"> Unknown username or password! Please type again!</span></h4>\n";
   my $username_pass_input = <<eof;
   <form method="POST" action="" class="form-horizontal">
   <div class="form-group">
      <h4><label class="control-label col-sm-2">Username: </label>
      <div class="col-md-3"><input type="textfield" name="username" class="form-control" placeholder=""></div></h4>
    </div>
    <div class="form-group">
      <h4><label class="control-label col-sm-2">Password: </label>
      <div class="col-sm-3"><input type="password" name="password" class="form-control" placeholder=""></div></h4>
    </div>
    <div class="form-group">
      <div class="col-sm-offset-2 col-sm-10"><input type="submit" name="login" value="Submit" class="btn btn-default"></div>
      <input type="hidden" name="login_status" value="not_done">
    </div>
   </form>
eof
   
   if (!defined param('username')) {
      $login_return .= $username_pass_input;
   } elsif ($username && $password) {
      $path = "$users_dir/$username/details.txt";
      if (!open F, $path) {
         $login_return .= $wrong_message.$username_pass_input;
      } else {
         my @users_details = <F>;
         close F;
         foreach my $line (@users_details) {
            if ($line =~ /password/) {
               $correct_pwd = $line;
               $correct_pwd =~ s/password:\s*//i;
            }
         }
         chomp $correct_pwd;
         if ($password eq $correct_pwd) {
            $login_return .= "<h3 style=\"color:black\"> \@$username authenticated.<br><a href=\"users.cgi?curr_user=$username\">Go to the user page</a></h3>";
            $login_code = md5_hex(rand);
            open F ,">>password_codes.txt";
            print F "$login_code<->$username\n";
            close F;
            $login_cookie = cookie(-name=>'login_info',-value=>"$login_code<->$username",-expires=>'+1d');
            
         } else {
            $login_return .= $wrong_message.$username_pass_input;
         }
      }
   } elsif (!$username and !$password) {
      $login_return .= $wrong_message.$username_pass_input;;
   } elsif (!$username or !$password) {
      $login_return .= $wrong_message.$username_pass_input;
   } else {
      $login_return .= $username_pass_input;
   }
   $login_return .= "\n</div></div>\n";
   return $login_return;
}

sub logout {
   open F ,"<password_codes.txt" or die;
   @all_logged_users = <F>;
   close F;
   open F, ">password_codes.txt" or die;
   foreach my $logged_user (@all_logged_users) {
      chomp $logged_user;
      next if ($logged_user =~ /<->$user_logged\s*$/);
      print F "$logged_user\n";
   }
   close F;
   return <<eof;
   <div class="container"><div class="jumbotron">
   <h3><b> \@$user_logged successfully logged out.</b></h3>
   <h4><a href="bitter.cgi">Go to the main menu.</a></h4>
   </div></div>
eof
}


##### navigation bar ###############
# added with bootstrap the initial bar on the website
# include login or logout appropriately - depending if there is an user logged in it
# adds the name of the current user and the name of the logged user with a link to go
# back to the logged users main page
sub navigation {
   my $login = "";
   my $print_login = "";
   my $log = "";
   my $add_user = "";
   
   # add the login or logout button to the navbar
   if ($user_logged eq "") {
      $login = "users.cgi?login=login";
      $print_login = "  Login";
      $log = "in";
      $add_user =<<eof;
         <li><a href="signup.cgi"><span class="glyphicon glyphicon-user"></span> Sign Up</a></li>
eof
   } else {
      $login = "users.cgi?logout=logout";
      $print_login = "  Logout";
      $log = "out";
      $add_user =<<eof;
         <li><a href="users.cgi?curr_user=$user_logged"> \@$user_logged</a></li> 
eof
   }
   
   # add link to come back to main page
   my $bitter = "bitter.cgi";
   $bitter = "users.cgi?curr_user=$user_logged" if ($user_logged ne "");
   
   my $listen = "";
   if ($user_logged ne "") {
      $listen =<<eof;
         <li class="dropdown"><a class="dropdown-toggle" data-toggle="dropdown" href="#"> Listening <span class="caret"></span></a>
         <ul class="dropdown-menu">
eof
      my $user = "$users_dir/$user_logged";
      foreach my $listen_user (keys %{$users_info{$user}{'listens'}}) {
         $listen .= "<li><a href=\"users.cgi?curr_user=$listen_user\">\@$listen_user</a></li>";
      }
      $listen .= "</ul></li>";
   }
   

   return <<eof;
<nav class="navbar navbar-inverse">
  <div class="container-fluid">
    <div class="navbar-header">
      <a class="navbar-brand" href="$bitter">Bitter</a>
    </div>
    <div>
      <ul class="nav navbar-nav">
        $listen
        <li><a href="users.cgi?curr_user=all">All users</a></li>
        <li><a href="users.cgi?search_bleat=search"><span class="glyphicon glyphicon-search"></span> Search for bleats</a></li>
        <li>
        <form method="POST" action="" class="form-inline">
         <input type="textfield" name="search_user" class="form-control" placeholder="\@username or full name">
         <input type="submit" name="search" value="Search" class="btn btn-info btn-md">
      </form>
      </li>
      </ul>
      <ul class="nav navbar-nav navbar-right">
        $add_user
        <li><a href="$login"><span class="glyphicon glyphicon-log-$log"></span>$print_login</a></li>
      </ul>
    </div>
  </div>
</nav>
eof
}


# add hidden variables that inform the state of the program
sub variables {
   return <<eof;
<form method="POST" action="">
   <input type="hidden" name="curr_user" value="$curr_user">
   <input type="hidden" name="login" value= "">
   <input type="hidden" name="logout" value= "">
</form>
eof
}


#
# HTML placed at the top of every page
#
sub page_header {
   my $new_bleat_header = "";
   
   if ($user_logged eq $curr_user or defined param('reply')) {
      $new_bleat_header = <<xxJSxx;
   <script>
      \$(document).ready(function() {
         var text_max = 142;
         \$('#bleat_feedback').html(text_max+'\t');
         \$('#new_bleat').keyup(function() {
            var text_length = \$('#new_bleat').val().length;
            var text_remaining = text_max - text_length;
            \$('#bleat_feedback').html(text_remaining+'\t');
         });   
      });
   </script>
xxJSxx
   
   }
    return <<eof;
<!DOCTYPE html>
<html lang="en">
<head>
<title>Bitter</title>
  <link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
  <script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
  <link href="users.css" rel="stylesheet">
  <script src="http://code.jquery.com/jquery-1.5.js"></script>
  $new_bleat_header
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

sub match_regexp {
   my $word = $_[0];
   my @regexp_list = @{$_[1]};
   foreach my $regexp (@regexp_list) {
      # print "$word -- $regexp<br>\n";
      if ($word =~ /^$regexp/) {
         # print "<br>yes!!<br>";
         return $regexp;
      }
   }
   return 0;
}

main();