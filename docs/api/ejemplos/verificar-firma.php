<?php
// Comprobar la firma de un aviso de WORLDIVES (PHP 7.4 o posterior).
//
//   $ok = worldives_verificar($secreto, $_SERVER['HTTP_X_WORLDIVES_SIGNATURE'] ?? '', file_get_contents('php://input'));

function worldives_verificar(string $secreto, string $cabecera, string $cuerpo, ?int $ahora = null): bool {
    $partes = [];
    foreach (explode(',', $cabecera) as $p) {
        $kv = explode('=', $p, 2);
        if (count($kv) === 2) { $partes[$kv[0]] = $kv[1]; }
    }
    if (!isset($partes['t'], $partes['v1']) || !ctype_digit($partes['t'])) { return false; }
    $t = (int) $partes['t'];
    if (abs(($ahora ?? time()) - $t) > 300) { return false; }
    $esperada = hash_hmac('sha256', $t . '.' . $cuerpo, $secreto);
    return hash_equals($esperada, $partes['v1']);
}

// En la página que recibe los avisos:
//
// $cuerpo = file_get_contents('php://input');
// if (!worldives_verificar(getenv('WORLDIVES_WEBHOOK_SECRET'), $_SERVER['HTTP_X_WORLDIVES_SIGNATURE'] ?? '', $cuerpo)) {
//     http_response_code(400); exit;
// }
// $aviso = json_decode($cuerpo, true);
// // ... guarda $aviso['id'] para no procesarlo dos veces
// http_response_code(204);
