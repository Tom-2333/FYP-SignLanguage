<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

$conn = new mysqli("localhost", "root", "", "SL_db");
if ($conn->connect_error) die(json_encode(["error" => "DB connection failed"]));

$data = json_decode(file_get_contents("php://input"), true);
$action = $data['action'] ?? '';

if ($action === 'register') {
    $email = $data['email'];
    $username = $data['username'];
    $password = password_hash($data['password'], PASSWORD_DEFAULT);
    $stmt = $conn->prepare("INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)");
    $stmt->bind_param("sss", $email, $username, $password);
    if ($stmt->execute()) echo json_encode(["success" => true]);
    else echo json_encode(["error" => "Registration failed"]);
} elseif ($action === 'login') {
    $email = $data['email'];
    $password = $data['password'];
    $stmt = $conn->prepare("SELECT id, username, password_hash FROM users WHERE email = ?");
    $stmt->bind_param("s", $email);
    $stmt->execute();
    $result = $stmt->get_result();
    if ($row = $result->fetch_assoc()) {
        if (password_verify($password, $row['password_hash'])) {
            echo json_encode(["success" => true, "user_id" => $row['id'], "username" => $row['username']]);
        } else echo json_encode(["error" => "Invalid password"]);
    } else echo json_encode(["error" => "User not found"]);
}
$conn->close();
?>