<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');  // Allow CORS for React app

$servername = "localhost";
$username = "root";
$password = "";
$dbname = "SL_db";

$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
    die(json_encode(["error" => "Connection failed: " . $conn->connect_error]));
}

// Fetch categories and words
$sql = "SELECT c.key_name, c.name, GROUP_CONCAT(CONCAT(w.id, ':', w.word) SEPARATOR '|') AS words
        FROM categories c
        LEFT JOIN words w ON c.key_name = w.category_key
        GROUP BY c.key_name";
$result = $conn->query($sql);

$data = ["All" => ["name" => "所有詞彙", "words" => []]];
if ($result->num_rows > 0) {
    while ($row = $result->fetch_assoc()) {
        $words = [];
        if ($row['words']) {
            foreach (explode('|', $row['words']) as $wordStr) {
                list($id, $word) = explode(':', $wordStr);
                $words[] = ["id" => $id, "word" => $word];
                $data["All"]["words"][] = ["id" => $id, "word" => $word];  // Add to 'All'
            }
        }
        $data[$row['key_name']] = ["name" => $row['name'], "words" => $words];
    }
}

echo json_encode($data);
$conn->close();
?>