<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

$conn = new mysqli("localhost", "root", "", "SL_db");
if ($conn->connect_error) die(json_encode(["error" => "DB connection failed"]));

$data = json_decode(file_get_contents('php://input'), true);
$user_id = isset($data['user_id']) ? intval($data['user_id']) : 0;
$session_id = isset($data['session_id']) ? $data['session_id'] : '';
$message = isset($data['message']) ? $data['message'] : '';
$role = isset($data['role']) ? $data['role'] : 'user';

if (!$user_id || $message === '' || $session_id === '') {
    echo json_encode(["error" => "Missing parameters"]);
    exit;
}

$stmt = $conn->prepare("INSERT INTO chat_history (user_id, session_id, message, role) VALUES (?, ?, ?, ?)");
$stmt->bind_param("isss", $user_id, $session_id, $message, $role);
if ($stmt->execute()) {
    echo json_encode(["success" => true, "chat_id" => $stmt->insert_id]);
} else {
    echo json_encode(["error" => "Insert failed"]);
}

$stmt->close();
$conn->close();
?>
