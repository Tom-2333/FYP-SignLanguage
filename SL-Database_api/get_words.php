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

// Support both schema variants: categories.name_en (new) and categories.engname (legacy).
$categoryNameEnColumn = 'engname';
$nameEnCheck = $conn->query("SHOW COLUMNS FROM categories LIKE 'name_en'");
if ($nameEnCheck && $nameEnCheck->num_rows > 0) {
    $categoryNameEnColumn = 'name_en';
}

// Fetch categories and words
$sql = "SELECT c.key_name, c.name as category_name, c.$categoryNameEnColumn as category_name_en, w.id, w.word, w.engword 
        FROM categories c
        LEFT JOIN words w ON c.key_name = w.category_key
        ORDER BY c.id, w.id";
$result = $conn->query($sql);

if (!$result) {
    http_response_code(500);
    echo json_encode(["error" => "Query failed: " . $conn->error]);
    $conn->close();
    exit;
}

$data = ["All" => ["name" => "所有詞彙", "name_en" => "All Words", "words" => []]];
if ($result->num_rows > 0) {
    while ($row = $result->fetch_assoc()) {
        $cat_key = $row['key_name'];
        if (!isset($data[$cat_key])) {
            $data[$cat_key] = [
                "name" => $row['category_name'],
                "name_en" => $row['category_name_en'] ?: $row['category_name'],
                "words" => []
            ];
        }
        
        if ($row['id']) {
            $word_data = [
                "id" => $row['id'], 
                "word" => $row['word'],
                "engword" => $row['engword']
            ];
            $data[$cat_key]["words"][] = $word_data;
            $data["All"]["words"][] = $word_data;
        }
    }
}

echo json_encode($data);
$conn->close();
?>