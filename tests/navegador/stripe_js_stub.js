/* Solo para las pruebas en el navegador: un sustituto de Stripe.js (https://js.stripe.com/v3/), que no se puede abrir
 * sin internet. Imita lo que la reserva usa de él: Stripe(clave, {stripeAccount}).initEmbeddedCheckout(...) y
 * mount(...). Enseña un formulario marcado «simulado» con los botones de Apple Pay y de pagar con tarjeta. Al pulsar,
 * la prueba marca la sesión como pagada en el simulador de Stripe (tests/stripe_mock.py) y llama a onComplete, como
 * hace Stripe cuando el pago termina. Nunca se sirve desde el servidor de WORLDIVES. */
(function () {
  'use strict';
  window.__stripeStub = { calls: [], clicked: null, secret: null, account: null, complete: null };
  window.Stripe = function (key, opts) {
    window.__stripeStub.calls.push({ key: key, account: opts && opts.stripeAccount, locale: opts && opts.locale });
    window.__stripeStub.account = opts && opts.stripeAccount;
    return {
      initEmbeddedCheckout: function (o) {
        return Promise.resolve(o.fetchClientSecret ? o.fetchClientSecret() : o.clientSecret).then(function (secret) {
          window.__stripeStub.secret = secret;
          window.__stripeStub.complete = function () { if (o.onComplete) o.onComplete(); };
          var el = null;
          return {
            mount: function (sel) {
              el = typeof sel === 'string' ? document.querySelector(sel) : sel;
              el.innerHTML = '<div data-stripe-stub style="border:1px solid #d6dde0;border-radius:12px;padding:14px;font:14px system-ui;display:grid;gap:10px;background:#fff">' +
                '<small style="color:#a05f0a;font-weight:700">Formulario de pago de Stripe · simulado en las pruebas</small>' +
                '<button type="button" data-stub-wallet style="background:#000;color:#fff;border:0;border-radius:8px;padding:12px;font-weight:700"> Pay</button>' +
                '<div style="text-align:center;color:#6b7c85;font-size:12px">o paga con tarjeta</div>' +
                '<input data-stub-card placeholder="1234 1234 1234 1234" style="padding:10px;border:1px solid #c3ced3;border-radius:8px;font-size:16px">' +
                '<div style="display:flex;gap:8px"><input data-stub-exp placeholder="MM / AA" style="flex:1;padding:10px;border:1px solid #c3ced3;border-radius:8px;font-size:16px"><input data-stub-cvc placeholder="CVC" style="flex:1;padding:10px;border:1px solid #c3ced3;border-radius:8px;font-size:16px"></div>' +
                '<input data-stub-name placeholder="Nombre en la tarjeta" style="padding:10px;border:1px solid #c3ced3;border-radius:8px;font-size:16px">' +
                '<button type="button" data-stub-pay style="background:#0570de;color:#fff;border:0;border-radius:8px;padding:12px;font-weight:700">Pagar</button></div>';
              el.querySelector('[data-stub-wallet]').addEventListener('click', function () { window.__stripeStub.clicked = 'wallet'; });
              el.querySelector('[data-stub-pay]').addEventListener('click', function () { window.__stripeStub.clicked = 'card'; });
            },
            destroy: function () { if (el) el.innerHTML = ''; }
          };
        });
      }
    };
  };
})();
