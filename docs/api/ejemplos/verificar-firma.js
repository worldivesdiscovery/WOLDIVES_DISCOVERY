// Comprobar la firma de un aviso de WORLDIVES (Node.js 18 o posterior, sin librerías).
//
//   const ok = verificar(secreto, req.headers['x-worldives-signature'], cuerpoEnBruto);
'use strict';
const crypto = require('crypto');
const TOLERANCIA = 300; // segundos

function verificar(secreto, cabecera, cuerpo, ahora = Math.floor(Date.now() / 1000)) {
  const partes = Object.fromEntries(String(cabecera || '').split(',').map((p) => {
    const i = p.indexOf('='); return [p.slice(0, i), p.slice(i + 1)];
  }));
  const t = Number(partes.t), firma = partes.v1 || '';
  if (!Number.isInteger(t) || !firma || Math.abs(ahora - t) > TOLERANCIA) return false;
  const esperada = crypto.createHmac('sha256', secreto).update(`${t}.`).update(cuerpo).digest('hex');
  return firma.length === esperada.length && crypto.timingSafeEqual(Buffer.from(esperada), Buffer.from(firma));
}

module.exports = { verificar };

// Con Express (el cuerpo en bruto, no express.json()):
//
// app.post('/worldives/avisos', express.raw({ type: 'application/json' }), (req, res) => {
//   if (!verificar(process.env.WORLDIVES_WEBHOOK_SECRET, req.get('X-WORLDIVES-Signature'), req.body)) return res.sendStatus(400);
//   const aviso = JSON.parse(req.body);
//   // ... guarda aviso.id para no procesarlo dos veces
//   res.sendStatus(204);
// });
