<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');

$conn = new mysqli("localhost", "root", "", "SL_db");
if ($conn->connect_error) die(json_encode(["error" => "DB connection failed"]));

$user_id = isset($_GET['user_id']) ? intval($_GET['user_id']) : 0;
$limit = isset($_GET['limit']) ? intval($_GET['limit']) : 50;

if (!$user_id) {
    echo json_encode(["error" => "Missing user_id"]);
    exit;
}

// For each session_id, get first message + last message and timestamp and count
$sql = "SELECT session_id, COUNT(*) as message_count, MAX(timestamp) as last_ts,
              SUBSTRING_INDEX(GROUP_CONCAT(message ORDER BY timestamp DESC SEPARATOR '||'), '||', 1) as last_message,
              SUBSTRING_INDEX(GROUP_CONCAT(message ORDER BY timestamp ASC SEPARATOR '||'), '||', 1) as first_message
        FROM chat_history
        WHERE user_id = ?
        GROUP BY session_id
        ORDER BY last_ts DESC
        LIMIT ?";

$stmt = $conn->prepare($sql);
$stmt->bind_param("ii", $user_id, $limit);
if (!$stmt->execute()) {
    echo json_encode(["error" => "Query failed"]);
    exit;
}

$res = $stmt->get_result();
$rows = [];
while ($r = $res->fetch_assoc()) {
    $rows[] = [
        'session_id' => $r['session_id'],
        'message_count' => intval($r['message_count']),
        'last_message' => $r['last_message'],
        'first_message' => $r['first_message'],
        'last_timestamp' => $r['last_ts']
    ];
}

echo json_encode(["success" => true, "sessions" => $rows]);

$stmt->close();
$conn->close();
?>
