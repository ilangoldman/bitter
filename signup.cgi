#!/usr/bin/perl -w

# Ilan Goldman - z5050782
# Created :October 2015
# COMP2041/9041 assignment 2: http://cgi.cse.unsw.edu.au/~cs2041/assignments/bitter/

use CGI qw/:all/;
use List::Util 'first';
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use DateTime;
use Storable;
use File::Copy;

sub main() {
    # print start of HTML ASAP to assist debugging if there is an error in the script
    print page_header();
    
    # Now tell CGI::Carp to embed any warning in HTML
    warningsToBrowser(1);
    
    # define some global variables
    $debug = 1;
    $user_logged = "";
    $dataset_size = "medium"; 
    $users_dir = "dataset-$dataset_size/users";
    $bleats_dir = "dataset-$dataset_size/bleats";
    $curr_user = param('curr_user') || "";
   %users_info = ();
   
   print navigation();
   
   if (defined param('verified')) {
      print verified_page();
   } elsif (defined param('sign_up')) {
      $status = store_user();
      if ($status ne "") {
         print $status;
      } else {
         print sign_up();
      }
   } else {
      print sign_up();
   }
   
    print page_trailer();
}

# let's the user input their information
# if there is a compulsory field missing
# doesn't proceed
sub sign_up {
   my $username_error = "";
   my $email_error = "";
   my $password_error = "Minimum of 5 characters";
   my $form_name = "";
   my $form_username = "";
   my $form_email = "";
   my $form_pwd = "";
   
   my $full_name = param('full_name') || "";
   my $username = param('username') || "";
   my $email = param('email') || "";
   my $suburb = param('suburb') || "";
   my $text = param('profile_text') || "";
   
   if (defined param('sign_up')) {
      $username_error = check_username();
      $form_username = "has-error" if ($username_error ne "");
      $email_error = check_email();
      $form_email = "has-error" if ($email_error ne "");
      $form_name = "has-error" if (param('full_name') eq "");
      $password_error = check_pwd();
      $form_pwd = "has-error" if ($password_error ne "");
   }  
   
   return <<eof;
   <div class="container">
   <div class="jumbotron">
   <form method="POST" action="" class="form-horizontal">
   <h2><b> User Information: </b></h2><br>
      <div class="form-group $form_name">
         <label class="control-label">Name</label>
         <input type="textfield" class="form-control" name="full_name" placeholder="Enter your full name" value="$full_name" required>
      </div>
      <div class="form-group $form_username">
         <label class="control-label">Username</label>
         <div class="input-group">
            <span class="input-group-addon">@</span>
            <input type="textfield" maxlength="15" name="username" class="form-control" value="$username" required>
         </div>
         <span class="help-block">$username_error</span>
      </div>
      <div class="form-group $form_email">
         <label class="control-label">Email</label>
         <input type="textfield" class="form-control" name="email" value="$email" required>
         <span class="help-block">$email_error</span>
      </div>
      <div class="form-group $form_pwd">
         <div class="form-group col-sm-6">
            <label class="control-label">Password</label>
            <input type="password" data-minlength="5" class="form-control" name="password" placeholder="Password" required>
            <span class="help-block">$password_error</span>
            <input type="password" class="form-control" name="pwd_confirm" placeholder="Confirm" required>
         </div>
      </div>
      <div class="form-group">
         <label class="control-label">Suburb</label>
         <input type="textfield" class="form-control" name="suburb" placeholder="Enter your home suburb" value="$suburb">
      </div>
      <div class="form-group">
         <label class="control-label">About me</label><br>
         <textarea rows="4" cols="45" name="profile_text" maxlength="150" placeholder="Give some details about yourself...">$text</textarea>
      </div>
      <input type="submit" name="sign_up" class="btn btn-default btn md" value="Sign Up">
   </form>
   </div>
    </div>
eof
}

# checks that the username is not already taken
sub check_username {
   my $username = param('username') || "";
   my @all_users = sort(glob("$users_dir/*"));
   my $error = "";
   $error = "Not allowed characters on the username" if ($username =~ /[^_0-9A-Za-z.-]/g);
   foreach my $user (@all_users) {
      chomp $user;
      $user =~ s/$users_dir\///i;
      #print ">>$user--$username<<<br>";
      $error = "Username has already been taken" if ($user eq $username);
   }
   return $error;
}

#checks that the two password fiels mathch
sub check_pwd {
   my $pwd = param('password') || "";
   my $pwd_confirm = param('pwd_confirm') || "";
   my $error = "";
   $pwd =~ s/<.*>?//g;
   $pwd =~ s/[\"\']//g;
   $pwd_confirm =~ s/<.*>?//g;
   $pwd_confirm =~ s/[\"\']//g;
   if ($pwd eq "" or $pwd ne $pwd_confirm) {
      $error = "Password and Confirm field don't match";
   }
   return $error;
}

# checks that it is an actual email
sub check_email {
   my $email = param('email') || "";
   my $error = "";
   $email =~ s/<.*>?//g;
   $email =~ s/[\"\']//g;
   #print "|$email|<br>";
   if ($email !~ /^.*?@.*?\..*$/) {
      $error = "This is not an email";
   }
   return $error;
}

# saves the users information in a temporary file
# in the verified directory and sends an email
# when confirming the email, this file is moved to
# the users directory
sub store_user {
   my $full_name = param('full_name') || "";
   my $username = param('username') || "";
   my $email = param('email') || "";
   my $suburb = param('suburb') || "";
   my $password = param('password') || "";
   my $text = param('profile_text') || "";
   
   return "" if (check_email() ne "" or check_pwd() ne "" or check_username() ne "");
   
   $username =~ s/[^_0-9A-Za-z.-]//g;
   $suburb =~ s/<.*>?//g;
   $suburb =~ s/<.*>?//g;
   $text =~ s/<.*>?//g;
   $text =~ s/[\"\']//g;
   $email =~ s/<.*>?//g;
   $email =~ s/[\"\']//g;
   $password =~ s/<.*>?//g;
   $password =~ s/[\"\']//g;
   
   my $verification_dir = "verify";
   mkdir $verification_dir,0755 unless -d $verification_dir;
   open(my $fh, ">$verification_dir/$username") or die "can not open $verification_dir/$username: $!";
   print $fh "username: $username\n";
   print $fh "password: $password\n";
   print $fh "full_name: $full_name\n";
   print $fh "email: $email\n";
   print $fh "listens: \n";
   print $fh "home_suburb: $suburb\n" if ($suburb ne "");
   print $fh "text: $text\n" if ($text ne "");
   close $fh;
   
   #http://cgi.cse.unsw.edu.au/~z5050782/15s2-comp2041-cgi/ass2/signup.cgi
   
   my $verify_url = "$ENV{'SCRIPT_URI'}"."?verified=yes&curr_user=$username"; 
   
   # sends email for verification to the user
   my $from ='z5050782@zmail.unsw.edu.au';
   my $subject = 'Bitter: Verify Account';
   my $message =<<eof;
   <h2>Thank you $full_name for signing up on Bitter.</h2><br>
   <h3>This is a confirmation email, please click <a href="$verify_url">here</a> to complete the verification process.</h3>
   <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><hr>
   This is an automatic email, please do not reply.
eof
   
   sendmail($email,$from,$subject,$message);
   
   my $page =<<eof;
   <div class="container">
   <div class="jumbotron">
   <h2>Thank you for signing up on Bitter.</h2>
   <h2>A verification email has just been sent you.</h2>
   <h2>Please verify to continue with your login.</h2>
   </div>
   </div>
eof

   return $page;
}

# sends an email to the user
sub sendmail {
   my ($to, $from, $subject, $message) = @_;
   open(M,"|/usr/sbin/sendmail -t") or die "problem sending email: $!";

   print M "To: $to\n";
   print M "From: $from\n";
   print M "Subject: $subject\n";
   print M "Content-type: text/html\n\n";
   print M $message;

   close M;
}

# prints depending if the user have already did the sign_up
sub verified_page() {
   my $status_ok = <<eof;
   <div class="container">
   <div class="jumbotron">
   <h2> Thank you for signing up on Bitter </h2>
   <h3> Your account has been verified </h3>
   </div>
   </div>
eof
   
   my $status_error =<<eof;
   <div class="container">
   <div class="jumbotron">
   <h2> Couldn't find your information </h2>
   <h2> Please <a href="signup.cgi" style="color:red;">sign up</a> again. </h2>
   </div>
   </div>
eof

   return ((verified() ne "") ? $status_ok:$status_error);
}

# checks if the user have done the sign up process
# then it moves the file to the users directory
sub verified {
   my @verify_users = sort(glob("verify/*"));
   my $username = "";
   my $pwd = "";
   my $email = "";
   
   foreach my $user (@verify_users) {
      chomp $user;
      $user =~ s/verify\///gi;
      if ($curr_user eq $user) {
         $username = $user;
         last;
      }
   }
   
   return "" if $username eq "";
   chomp $username;
   
   my $user_dir = "$users_dir/$username";
   mkdir $user_dir,0755 unless -d $user_dir;
   move("verify/$username","$user_dir/details.txt");
   #print ">>$username-->$user_dir/details.txt<<";
   
   # create file for bleats
   open(my $fh, ">$user_dir/bleats.txt") or die "can not open $user_dir/bleats.txt: $!";
   close $fh;
   
   # update users hash
   save_users_info();
   
   open($fh, "<$user_dir/details.txt") or die "can not open $user_dir/details.txt: $!";
   foreach my $line (<$fh>) {
      $pwd = $1 if ($line =~ /^password:\s*(.*)/i);
      $email = $1 if ($line =~ /^email:\s*(.*)/i);
      $full_name = $1 if ($line =~ /^full_name:\s*(.*)/i);
   }
   close $fh;
   chomp $pwd;
   
   #sends email to user with his username and password
   my $from ='z5050782@zmail.unsw.edu.au';
   my $subject = 'Bitter: Thank you for joining us';
   my $message =<<eof;
   Dear $full_name,<br>
      Thank you for joining us on Bitter.<br>
      We will make certain that you will have the best experience with us.<br>
      <br>
      This are your login details. Please keep them safe.<br>
      Login: $username<br>
      Password: $pwd<br>
   <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><hr>
   This is an automatic email, please do not reply.
eof
   
   sendmail($email,$from,$subject,$message);
   
   return "ok";
}

# save all the user in a hash
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
   return <<eof;
<nav class="navbar navbar-inverse">
  <div class="container-fluid">
    <div class="navbar-header">
      <a class="navbar-brand" href="bitter.cgi">Bitter</a>
    </div>
    <div>
      <ul class="nav navbar-nav"></ul>
      <ul class="nav navbar-nav navbar-right">
        <li><a href="users.cgi?login=login"><span class="glyphicon glyphicon-log-in"></span> Login</a></li>
      </ul>
    </div>
  </div>
</nav>
<form method="POST" action=""><input type="hidden" name="curr_user" value="$curr_user"></form>
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