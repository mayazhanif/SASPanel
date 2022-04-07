<?php


#$sso_server = "http://chat.local:8080/api/clients/validateDb";
$sso_server = "http://185.162.10.153/phpmyadmin/testjson.php";

/* Need to have cookie visible from parent directory */
session_set_cookie_params(0, '/', '', true, true);
/* Create signon session */
$session_name = 'SignonSession';
session_name($session_name);
// Uncomment and change the following line to match your $cfg['SessionSavePath']
// session_save_path('');
@session_start();

/* Was data posted? */
if (isset($_GET['remote_token']) || isset($_COOKIE['remote_token'])) { 

    $token = ( isset($_GET['remote_token']) ? $_GET['remote_token'] : $_COOKIE['remote_token']);

    // Request credentials from remote server
    #$response = file_get_contents($sso_server . "/?token=" . $token);
    #$response = file_get_contents($sso_server . "/?token=" . $token);
	#echo $response;
	$response = '{"user":"root","pass":"Master@786"}';
    $response = json_decode($response);

    /* Store there credentials */
	echo $response->{'user'};
	#exit();
    $_SESSION['PMA_single_signon_user'] = $response->{'user'};
    $_SESSION['PMA_single_signon_password'] = $response->{'pass'};
    /* Update another field of server configuration */
    $_SESSION['PMA_single_signon_cfgupdate'] = array('verbose' => 'Signon test');
    $id = session_id();
    /* Close that session */
    @session_write_close();

    setcookie($session_name, $id , 0, "/");

    /* Redirect to phpMyAdmin (should use absolute URL here!) */
    header('Location: ../phpmyadmin/index.php');

     // echo 'DONE';
} else {
    /* Show simple form */
    header('Content-Type: text/html; charset=utf-8');
    echo '<?xml version="1.0" encoding="utf-8"?>' , "\n";
    ?>
    <!DOCTYPE HTML>
    <html lang="en" dir="ltr">
    <head>
    <link rel="icon" href="../favicon.ico" type="image/x-icon" />
    <link rel="shortcut icon" href="../favicon.ico" type="image/x-icon" />
    <meta charset="utf-8" />
    <title>phpMyAdmin single signon</title>
    </head>
    <body>
    <?php
    if (isset($_SESSION['PMA_single_signon_error_message'])) {
        echo '<p class="error">';
        echo $_SESSION['PMA_single_signon_error_message'];
        echo '</p>';
    }
    ?>
    <h1>Autenticação deve ser realizada pelo portal do Edu3</h1> 
    Token: <?php echo $_GET['remote_token'] ?> 
    </body>
    </html>
    <?php
}
?>