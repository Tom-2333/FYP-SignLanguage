<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode(["success" => false, "error" => "Method not allowed"]);
    exit;
}

$user_id = isset($_GET['user_id']) ? intval($_GET['user_id']) : 0;
if ($user_id <= 0) {
    http_response_code(400);
    echo json_encode(["success" => false, "error" => "Missing or invalid user_id"]);
    exit;
}

$servername = "localhost";
$username = "root";
$password = "";
$dbname = "SL_db";

$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
    http_response_code(500);
    echo json_encode(["success" => false, "error" => "Connection failed: " . $conn->connect_error]);
    exit;
}

$stmt = $conn->prepare("SELECT word_id FROM user_progress WHERE user_id = ?");
$stmt->bind_param("i", $user_id);
$stmt->execute();
$result = $stmt->get_result();

$wordIds = [];
while ($row = $result->fetch_assoc()) {
    $wordIds[] = $row['word_id'];
}

echo json_encode(["success" => true, "word_ids" => $wordIds]);

$stmt->close();
$conn->close();
?>