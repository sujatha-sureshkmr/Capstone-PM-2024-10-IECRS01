<?php
$script_output = shell_exec('ls /Users/sujathasureshkumar/Documents/GitHub/sujatha-sureshkmr.github.io/jms');
?>

<!DOCTYPE html>
<html>
<head>
    <title>Shell Script Output</title>
</head>
<body>
    <h1>Shell Script Output:</h1>
    <pre><?php echo $script_output; ?></pre>
</body>
</html>