<?php

// $url1=$_SERVER['REQUEST_URI'];
// header("Refresh: 10; URL=$url1");

// hosting parametrs
$servername = "localhost";
$username = "root";
$password = "";    
$dbname = "id21804168_iotsystem";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

$sql = "SELECT temperature FROM sensor_data ORDER BY timestamp DESC LIMIT 12;";
$result = $conn->query($sql);

$temperatures = []; // Initialize an empty array to store the temperatures

if ($result->num_rows > 0) {
    // Fetch all temperature values
    while($row = $result->fetch_assoc()) {
        $temperatures[] = intval($row['temperature']);
    }
    // Send the temperatures back as a JSON-encoded array
    echo json_encode($temperatures);
} else {
    // Send back an empty array if no data was found
    echo json_encode($temperatures);
}

$conn->close();
?>