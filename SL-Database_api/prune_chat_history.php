<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// prune_chat_history.php
// Usage (POST JSON): { "user_id": 1, "since": "2026-04-02 10:00:00", "confirm": true }
// Deletes chat_history rows for the given user_id with timestamp > since.

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);

if (!$data) {
    echo json_encode(['success' => false, 'error' => 'Invalid JSON']);
    exit;
}

$user_id = isset($data['user_id']) ? intval($data['user_id']) : 0;
$since = isset($data['since']) ? $data['since'] : '';
$confirm = isset($data['confirm']) ? boolval($data['confirm']) : false;

if (!$user_id || !$since) {
    echo json_encode(['success' => false, 'error' => 'Missing parameters (user_id and since required)']);
    exit;
}

if (!$confirm) {
    echo json_encode(['success' => false, 'error' => 'Operation not confirmed. Set confirm=true to proceed.']);
    exit;
}

$conn = new mysqli("localhost", "root", "", "SL_db");
if ($conn->connect_error) {
    echo json_encode(['success' => false, 'error' => 'DB connection failed']);
    exit;
}

// Validate timestamp format (basic)
if (!preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/', $since)) {
    echo json_encode(['success' => false, 'error' => 'Invalid timestamp format. Use YYYY-MM-DD HH:MM:SS']);
    exit;
}

$stmt = $conn->prepare("DELETE FROM chat_history WHERE user_id = ? AND timestamp > ?");
$stmt->bind_param('is', $user_id, $since);
if ($stmt->execute()) {
    $deleted = $stmt->affected_rows;
    echo json_encode(['success' => true, 'deleted' => $deleted]);
} else {
    echo json_encode(['success' => false, 'error' => 'Delete failed']);
}

$stmt->close();
$conn->close();

?>
