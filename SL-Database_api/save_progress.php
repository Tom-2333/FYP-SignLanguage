<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(["success" => false, "error" => "Method not allowed"]);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
if (!$input) {
    http_response_code(400);
    echo json_encode(["success" => false, "error" => "Invalid JSON payload"]);
    exit;
}

$user_id = isset($input['user_id']) ? intval($input['user_id']) : 0;
$word_id = isset($input['word_id']) ? trim($input['word_id']) : '';
$confidence = isset($input['confidence']) ? intval($input['confidence']) : 0;

if ($user_id <= 0 || $word_id === '') {
    http_response_code(400);
    echo json_encode(["success" => false, "error" => "Missing or invalid user_id/word_id"]);
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

// Check if progress exists for this user/word
$checkStmt = $conn->prepare("SELECT id FROM user_progress WHERE user_id = ? AND word_id = ? LIMIT 1");
$checkStmt->bind_param("is", $user_id, $word_id);
$checkStmt->execute();
$checkStmt->store_result();

if ($checkStmt->num_rows > 0) {
    $checkStmt->free_result();
    $checkStmt->close();

    $updateStmt = $conn->prepare("UPDATE user_progress SET confidence = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND word_id = ?");
    $updateStmt->bind_param("iis", $confidence, $user_id, $word_id);
    if ($updateStmt->execute()) {
        echo json_encode(["success" => true, "action" => "updated"]);
    } else {
        http_response_code(500);
        echo json_encode(["success" => false, "error" => "Update failed: " . $conn->error]);
    }
    $updateStmt->close();
} else {
    $checkStmt->close();
    $insertStmt = $conn->prepare("INSERT INTO user_progress (user_id, word_id, confidence) VALUES (?, ?, ?)");
    $insertStmt->bind_param("isi", $user_id, $word_id, $confidence);
    if ($insertStmt->execute()) {
        echo json_encode(["success" => true, "action" => "inserted"]);
    } else {
        http_response_code(500);
        echo json_encode(["success" => false, "error" => "Insert failed: " . $conn->error]);
    }
    $insertStmt->close();
}

$conn->close();
?>