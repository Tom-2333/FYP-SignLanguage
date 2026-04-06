<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');

$conn = new mysqli("localhost", "root", "", "SL_db");
if ($conn->connect_error) die(json_encode(["error" => "DB connection failed"]));

$user_id = isset($_GET['user_id']) ? intval($_GET['user_id']) : 0;
$session_id = isset($_GET['session_id']) ? $_GET['session_id'] : '';
$limit = isset($_GET['limit']) ? intval($_GET['limit']) : 50;

if (!$user_id) {
    echo json_encode(["error" => "Missing user_id"]);
    exit;
}

$sql = "SELECT id, session_id, message, role, timestamp FROM chat_history WHERE user_id = ?";
if ($session_id) {
    $sql .= " AND session_id = ?";
}
$sql .= " ORDER BY timestamp DESC LIMIT ?";

if ($session_id) {
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("isi", $user_id, $session_id, $limit);
} else {
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("ii", $user_id, $limit);
}

if (!$stmt->execute()) {
    echo json_encode(["error" => "Query failed"]);
    exit;
}

$res = $stmt->get_result();
$rows = [];
while ($r = $res->fetch_assoc()) {
    $rows[] = $r;
}

echo json_encode(["success" => true, "messages" => $rows]);

$stmt->close();
$conn->close();
?>
