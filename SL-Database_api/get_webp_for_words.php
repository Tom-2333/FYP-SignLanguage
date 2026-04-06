<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!$data || !isset($data['words']) || !is_array($data['words'])) {
    echo json_encode(['success' => false, 'error' => 'Invalid request, expected JSON {"words": ["..."]}']);
    exit;
}

$words = $data['words'];
$conn = new mysqli("localhost", "root", "", "SL_db");
if ($conn->connect_error) {
    echo json_encode(['success' => false, 'error' => 'DB connection failed']);
    exit;
}

$mapping = [];
$stmt = $conn->prepare('SELECT id, word, engword FROM words WHERE word = ? OR engword = ? LIMIT 1');
foreach ($words as $w) {
    $w_trim = trim($w);
    $stmt->bind_param('ss', $w_trim, $w_trim);
    $stmt->execute();
    $res = $stmt->get_result();
    if ($row = $res->fetch_assoc()) {
        $id = intval($row['id']);
        $filename = sprintf('%08d.webp', $id);
        $url = sprintf('http://localhost/FYP-SignLanguage-poe_conn/FYP-SignLanguage-poe_conn/SL-Database_api/video-webp/%s', $filename);
        $mapping[$w_trim] = $url;
    } else {
        // no mapping found
        $mapping[$w_trim] = null;
    }
}

$stmt->close();
$conn->close();

echo json_encode(['success' => true, 'mapping' => $mapping]);

?>
