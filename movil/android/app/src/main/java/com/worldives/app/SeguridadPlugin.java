package com.worldives.app;

import android.app.Activity;
import android.app.KeyguardManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.os.Build;
import android.os.SystemClock;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyPermanentlyInvalidatedException;
import android.security.keystore.KeyProperties;
import android.security.keystore.UserNotAuthenticatedException;
import android.util.Base64;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.WebStorage;
import androidx.annotation.NonNull;
import androidx.biometric.BiometricManager;
import androidx.biometric.BiometricPrompt;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.FragmentActivity;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.util.List;
import java.util.Map;
import javax.crypto.AEADBadTagException;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;
import org.json.JSONObject;

/**
 * v50.55 · Encargo 2 (seguridad de la app WORLDIVES PRO), lado del móvil.
 *
 * <ul>
 *   <li>The refresh token of this device is kept encrypted with a key of the Android Keystore that only works for 30
 *   seconds after the person unlocks with the fingerprint (or face, if the phone counts it as strong) or the phone's
 *   own code (BiometricPrompt). The fingerprint never leaves the phone: the app only gets «yes» or «no».</li>
 *   <li>Without any screen lock on the phone, a 6-digit PIN of the app protects it instead (PBKDF2, then wrapped again
 *   with a Keystore key, so the file cannot be attacked on another computer).</li>
 *   <li>Divers may switch the lock off: then the token is only wrapped with a Keystore key.</li>
 *   <li>5 failed attempts delete the token, the keys and everything the app keeps (WebView storage and cookies).</li>
 *   <li>The offline data (boat lists, today's bookings, QR codes) are encrypted here, with a Keystore key that never
 *   leaves it; the web reads and writes them only while the app is unlocked (also over plain http in Pruebas, where
 *   the browser has no WebCrypto).</li>
 *   <li>The access session (15 minutes) is renewed here, with the token in memory, against the app's own server:
 *   the token never goes to the web page.</li>
 *   <li>The panel is hidden in the recent apps screen.</li>
 * </ul>
 */
@CapacitorPlugin(name = "Seguridad")
public class SeguridadPlugin extends Plugin {

    private static final String PREFS = "worldives_seguridad";
    private static final String PREFS_DATOS = "worldives_datos";        // the offline data, each value encrypted
    private static final String ALIAS_DATOS = "wd_datos";               // their key: never leaves the Keystore
    private static final String ALIAS_BLOQUEO = "wd_sesion_bloqueo";   // needs the fingerprint or the phone's code
    private static final String ALIAS_DISPOSITIVO = "wd_dispositivo";   // never leaves the Keystore, no unlock needed
    private static final int VALIDEZ_SEGUNDOS = 30;
    private static final int MAX_FALLOS = 5;
    private static final int PIN_ITERACIONES = 120000;
    private static final String MODO_SISTEMA = "sistema", MODO_PIN = "pin", MODO_LIBRE = "libre";

    private String token;            // the refresh token, only in memory and only while unlocked
    private long pausaEn = 0;        // elapsedRealtime of the last pause
    private boolean ocultarRecientes = false;

    private SharedPreferences prefs() {
        return getContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private SharedPreferences datos() {
        return getContext().getSharedPreferences(PREFS_DATOS, Context.MODE_PRIVATE);
    }

    // ------------------------------------------------------------------ keys
    private KeyStore keystore() throws Exception {
        KeyStore ks = KeyStore.getInstance("AndroidKeyStore");
        ks.load(null);
        return ks;
    }

    private SecretKey clave(String alias, boolean conBloqueo) throws Exception {
        KeyStore ks = keystore();
        if (ks.containsAlias(alias)) return (SecretKey) ks.getKey(alias, null);
        KeyGenParameterSpec.Builder b = new KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256);
        if (conBloqueo) {
            b.setUserAuthenticationRequired(true);
            if (Build.VERSION.SDK_INT >= 30) {
                b.setUserAuthenticationParameters(VALIDEZ_SEGUNDOS, KeyProperties.AUTH_BIOMETRIC_STRONG | KeyProperties.AUTH_DEVICE_CREDENTIAL);
            } else {
                b.setUserAuthenticationValidityDurationSeconds(VALIDEZ_SEGUNDOS);
            }
        }
        KeyGenerator g = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        g.init(b.build());
        return g.generateKey();
    }

    private static byte[] cifrar(SecretKey k, byte[] datos) throws Exception {
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.ENCRYPT_MODE, k);
        byte[] iv = c.getIV(), ct = c.doFinal(datos);
        return ByteBuffer.allocate(1 + iv.length + ct.length).put((byte) iv.length).put(iv).put(ct).array();
    }

    private static byte[] descifrar(SecretKey k, byte[] blob) throws Exception {
        int n = blob[0];
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.DECRYPT_MODE, k, new GCMParameterSpec(128, blob, 1, n));
        return c.doFinal(blob, 1 + n, blob.length - 1 - n);
    }

    private static byte[] cifrarCon(byte[] clave, byte[] datos) throws Exception {
        byte[] iv = new byte[12];
        new SecureRandom().nextBytes(iv);
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(clave, "AES"), new GCMParameterSpec(128, iv));
        byte[] ct = c.doFinal(datos);
        return ByteBuffer.allocate(1 + iv.length + ct.length).put((byte) iv.length).put(iv).put(ct).array();
    }

    private static byte[] descifrarCon(byte[] clave, byte[] blob) throws Exception {
        int n = blob[0];
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.DECRYPT_MODE, new SecretKeySpec(clave, "AES"), new GCMParameterSpec(128, blob, 1, n));
        return c.doFinal(blob, 1 + n, blob.length - 1 - n);
    }

    private static byte[] derivarPin(String pin, byte[] sal) throws Exception {
        SecretKeyFactory f = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        return f.generateSecret(new PBEKeySpec(pin.toCharArray(), sal, PIN_ITERACIONES, 256)).getEncoded();
    }

    private static String b64(byte[] b) { return Base64.encodeToString(b, Base64.NO_WRAP); }
    private static byte[] deB64(String s) { return Base64.decode(s, Base64.NO_WRAP); }

    private boolean telefonoSeguro() {
        KeyguardManager km = (KeyguardManager) getContext().getSystemService(Context.KEYGUARD_SERVICE);
        return km != null && km.isDeviceSecure();
    }

    private int autenticadores() {
        // BIOMETRIC_STRONG | DEVICE_CREDENTIAL is not supported before Android 11 (androidx.biometric).
        return Build.VERSION.SDK_INT >= 30
                ? BiometricManager.Authenticators.BIOMETRIC_STRONG | BiometricManager.Authenticators.DEVICE_CREDENTIAL
                : BiometricManager.Authenticators.BIOMETRIC_WEAK | BiometricManager.Authenticators.DEVICE_CREDENTIAL;
    }

    private String claveInstalacion() {
        String k = prefs().getString("instalacion", null);
        if (k == null) {
            byte[] r = new byte[24];
            new SecureRandom().nextBytes(r);
            k = Base64.encodeToString(r, Base64.NO_WRAP | Base64.URL_SAFE | Base64.NO_PADDING);
            prefs().edit().putString("instalacion", k).apply();
        }
        return k;
    }

    // ------------------------------------------------------------------ state
    @PluginMethod
    public void estado(PluginCall call) {
        SharedPreferences p = prefs();
        JSObject r = new JSObject();
        r.put("modo", p.getString("modo", null));
        r.put("token", p.contains("token"));
        r.put("desbloqueado", token != null);
        r.put("fallos", p.getInt("fallos", 0));
        r.put("maxFallos", MAX_FALLOS);
        r.put("seguro", telefonoSeguro());
        int bio = BiometricManager.from(getContext()).canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG);
        r.put("huella", bio == BiometricManager.BIOMETRIC_SUCCESS);
        r.put("dispositivo", p.getLong("dispositivo", 0));
        call.resolve(r);
    }

    /** What the app says about itself when it signs in (nothing secret). */
    @PluginMethod
    public void instalacion(PluginCall call) {
        JSObject r = new JSObject();
        r.put("device_key", claveInstalacion());
        r.put("platform", "android");
        r.put("model", Build.MANUFACTURER + " " + Build.MODEL);
        r.put("os", Build.VERSION.RELEASE);
        String v = "";
        try {
            PackageInfo pi = getContext().getPackageManager().getPackageInfo(getContext().getPackageName(), 0);
            v = pi.versionName;
        } catch (Exception ignored) { }
        r.put("app_version", v);
        call.resolve(r);
    }

    // ------------------------------------------------------------------ saving the token after signing in
    /** {token, dispositivo, modo: sistema|pin|libre, pin (modo pin), titulo}. */
    @PluginMethod
    public void activar(PluginCall call) {
        String t = call.getString("token", "");
        String modo = call.getString("modo", MODO_SISTEMA);
        long dispositivo = numero(call, "dispositivo");
        if (t == null || t.length() < 20) { call.reject("Falta el token"); return; }
        try {
            if (MODO_LIBRE.equals(modo)) {
                guardar(MODO_LIBRE, cifrar(clave(ALIAS_DISPOSITIVO, false), t.getBytes(StandardCharsets.UTF_8)), dispositivo, null);
                token = t;
                call.resolve(ok());
            } else if (MODO_PIN.equals(modo)) {
                String pin = call.getString("pin", "");
                if (pin == null || !pin.matches("\\d{6}")) { call.reject("El PIN tiene 6 números"); return; }
                byte[] sal = new byte[16];
                new SecureRandom().nextBytes(sal);
                byte[] interior = cifrarCon(derivarPin(pin, sal), t.getBytes(StandardCharsets.UTF_8));
                guardar(MODO_PIN, cifrar(clave(ALIAS_DISPOSITIVO, false), interior), dispositivo, sal);
                token = t;
                call.resolve(ok());
            } else {
                if (!telefonoSeguro()) { call.reject("sin_bloqueo"); return; }
                pedir(call, call.getString("titulo", "Protege WORLDIVES"), call.getString("subtitulo", ""), () -> {
                    try {
                        guardar(MODO_SISTEMA, cifrar(clave(ALIAS_BLOQUEO, true), t.getBytes(StandardCharsets.UTF_8)), dispositivo, null);
                        token = t;
                        call.resolve(ok());
                    } catch (Exception e) {
                        call.reject("No se ha podido guardar: " + e.getClass().getSimpleName());
                    }
                });
            }
        } catch (Exception e) {
            call.reject("No se ha podido guardar: " + e.getClass().getSimpleName());
        }
    }

    /** A number sent by the web: Capacitor's getLong() gives the default for small numbers, which arrive as Integer. */
    private static long numero(PluginCall call, String name) {
        Object o = call.getData().opt(name);
        return o instanceof Number ? ((Number) o).longValue() : 0L;
    }

    private void guardar(String modo, byte[] blob, long dispositivo, byte[] sal) {
        SharedPreferences.Editor e = prefs().edit().putString("modo", modo).putString("token", b64(blob)).putInt("fallos", 0);
        if (dispositivo > 0) e.putLong("dispositivo", dispositivo);
        if (sal != null) e.putString("sal", b64(sal)); else e.remove("sal");
        e.apply();
    }

    private JSObject ok() {
        JSObject r = new JSObject();
        r.put("ok", true);
        return r;
    }

    // ------------------------------------------------------------------ unlocking
    @PluginMethod
    public void desbloquear(PluginCall call) {
        SharedPreferences p = prefs();
        String modo = p.getString("modo", null), blob = p.getString("token", null);
        if (blob == null) { call.reject("sin_token"); return; }
        if (MODO_LIBRE.equals(modo)) {
            try {
                token = new String(descifrar(clave(ALIAS_DISPOSITIVO, false), deB64(blob)), StandardCharsets.UTF_8);
                call.resolve(ok());
            } catch (Exception e) {
                borrarTodo(); call.resolve(cerrado("clave"));
            }
            return;
        }
        if (MODO_PIN.equals(modo)) { call.reject("usa_pin"); return; }
        pedir(call, call.getString("titulo", "Desbloquear WORLDIVES"), call.getString("subtitulo", ""), () -> {
            try {
                token = new String(descifrar(clave(ALIAS_BLOQUEO, true), deB64(blob)), StandardCharsets.UTF_8);
                prefs().edit().putInt("fallos", 0).apply();
                call.resolve(ok());
            } catch (UserNotAuthenticatedException e) {
                JSObject r = new JSObject();
                r.put("ok", false);
                r.put("reintentar", true);   // a weak face unlock (Android 8–10) does not open the Keystore: fingerprint or code
                call.resolve(r);
            } catch (KeyPermanentlyInvalidatedException e) {
                borrarTodo(); call.resolve(cerrado("huellas_cambiadas"));   // fingerprints were added or removed
            } catch (Exception e) {
                borrarTodo(); call.resolve(cerrado("clave"));
            }
        });
    }

    @PluginMethod
    public void desbloquearPin(PluginCall call) {
        SharedPreferences p = prefs();
        String blob = p.getString("token", null), sal = p.getString("sal", null), pin = call.getString("pin", "");
        if (blob == null || sal == null) { call.reject("sin_token"); return; }
        try {
            byte[] interior = descifrar(clave(ALIAS_DISPOSITIVO, false), deB64(blob));
            token = new String(descifrarCon(derivarPin(pin == null ? "" : pin, deB64(sal)), interior), StandardCharsets.UTF_8);
            p.edit().putInt("fallos", 0).apply();
            call.resolve(ok());
        } catch (AEADBadTagException e) {
            call.resolve(fallo());
        } catch (Exception e) {
            borrarTodo(); call.resolve(cerrado("clave"));
        }
    }

    private JSObject fallo() {
        int n = prefs().getInt("fallos", 0) + 1;
        prefs().edit().putInt("fallos", n).apply();
        if (n >= MAX_FALLOS) { borrarTodo(); return cerrado("fallos"); }
        JSObject r = new JSObject();
        r.put("ok", false);
        r.put("fallos", n);
        r.put("quedan", MAX_FALLOS - n);
        return r;
    }

    /** After the device was wiped: what the web needs to tell the server (the old installation id). */
    private JSObject cerrado(String motivo) {
        JSObject r = new JSObject();
        r.put("ok", false);
        r.put("cerrar", true);
        r.put("motivo", motivo);
        r.put("dispositivo", ultimoDispositivo);
        r.put("device_key", ultimaInstalacion);
        return r;
    }

    private long ultimoDispositivo = 0;
    private String ultimaInstalacion = null;

    private interface Hecho { void run(); }

    /** The system's own prompt: fingerprint (or strong face) or the phone's code. Each failed fingerprint counts. */
    private void pedir(PluginCall call, String titulo, String subtitulo, Hecho alAcertar) {
        Activity a = getActivity();
        if (!(a instanceof FragmentActivity)) { call.reject("sin_actividad"); return; }
        FragmentActivity fa = (FragmentActivity) a;
        fa.runOnUiThread(() -> {
            final BiometricPrompt[] bp = new BiometricPrompt[1];
            bp[0] = new BiometricPrompt(fa, ContextCompat.getMainExecutor(fa), new BiometricPrompt.AuthenticationCallback() {
                private boolean hecho = false;

                @Override
                public void onAuthenticationSucceeded(@NonNull BiometricPrompt.AuthenticationResult result) {
                    if (hecho) return;
                    hecho = true;
                    alAcertar.run();
                }

                @Override
                public void onAuthenticationFailed() {
                    if (hecho) return;
                    JSObject r = fallo();
                    if (r.optBoolean("cerrar")) {
                        hecho = true;
                        bp[0].cancelAuthentication();
                        call.resolve(r);
                    }
                }

                @Override
                public void onAuthenticationError(int code, @NonNull CharSequence msg) {
                    if (hecho) return;
                    hecho = true;
                    if (code == BiometricPrompt.ERROR_LOCKOUT || code == BiometricPrompt.ERROR_LOCKOUT_PERMANENT) {
                        borrarTodo();
                        call.resolve(cerrado("bloqueo_sistema"));
                        return;
                    }
                    JSObject r = new JSObject();
                    r.put("ok", false);
                    r.put("cancelado", true);
                    r.put("codigo", code);
                    r.put("mensaje", String.valueOf(msg));
                    r.put("fallos", prefs().getInt("fallos", 0));
                    call.resolve(r);
                }
            });
            BiometricPrompt.PromptInfo.Builder info = new BiometricPrompt.PromptInfo.Builder()
                    .setTitle(titulo == null || titulo.isEmpty() ? "WORLDIVES" : titulo)
                    .setAllowedAuthenticators(autenticadores())
                    .setConfirmationRequired(false);
            if (subtitulo != null && !subtitulo.isEmpty()) info.setSubtitle(subtitulo);
            try {
                bp[0].authenticate(info.build());
            } catch (Exception e) {
                call.reject("No se puede pedir la huella: " + e.getMessage());
            }
        });
    }

    @PluginMethod
    public void bloquear(PluginCall call) {
        token = null;
        call.resolve(ok());
    }

    /** Seconds since the app went to the background (-1 if it has not, since it opened). */
    @PluginMethod
    public void tiempoFuera(PluginCall call) {
        JSObject r = new JSObject();
        r.put("segundos", pausaEn == 0 ? -1 : (SystemClock.elapsedRealtime() - pausaEn) / 1000);
        call.resolve(r);
    }

    // ------------------------------------------------------------------ renewing the access session
    /** POST {server}/api/auth/refresh with the token in memory; the new session cookie goes into the WebView. */
    @PluginMethod
    public void renovar(PluginCall call) {
        if (token == null) {
            JSObject r = new JSObject();
            r.put("ok", false);
            r.put("bloqueado", true);
            call.resolve(r);
            return;
        }
        final String origen = origen();
        final String ua = call.getString("ua", "WorldivesApp/1.0");
        final String t = token;
        new Thread(() -> {
            JSObject r = new JSObject();
            HttpURLConnection c = null;
            try {
                c = (HttpURLConnection) new URL(origen + "/api/auth/refresh").openConnection();
                c.setRequestMethod("POST");
                c.setConnectTimeout(10000);
                c.setReadTimeout(15000);
                c.setDoOutput(true);
                c.setRequestProperty("Content-Type", "application/json");
                c.setRequestProperty("Origin", origen);
                c.setRequestProperty("User-Agent", ua);
                JSONObject body = new JSONObject();
                body.put("refresh_token", t);
                try (OutputStream o = c.getOutputStream()) { o.write(body.toString().getBytes(StandardCharsets.UTF_8)); }
                int status = c.getResponseCode();
                InputStream in = status < 400 ? c.getInputStream() : c.getErrorStream();
                String texto = leer(in);
                r.put("status", status);
                if (status == 200) {
                    List<String> cookies = null;
                    for (Map.Entry<String, List<String>> h : c.getHeaderFields().entrySet()) {
                        if (h.getKey() != null && h.getKey().equalsIgnoreCase("Set-Cookie")) cookies = h.getValue();
                    }
                    final List<String> cs = cookies;
                    getActivity().runOnUiThread(() -> {
                        CookieManager cm = CookieManager.getInstance();
                        if (cs != null) for (String x : cs) cm.setCookie(origen, x);
                        cm.flush();
                        r.put("ok", true);
                        call.resolve(r);
                    });
                    return;
                }
                JSONObject d = new JSONObject(texto.isEmpty() ? "{}" : texto);
                if (status == 401 && d.optBoolean("revoked")) {
                    r.put("revoked", true);
                    r.put("reason", d.optString("reason", "revoked"));
                    getActivity().runOnUiThread(() -> { borrarTodo(); r.put("ok", false); call.resolve(r); });
                    return;
                }
                r.put("ok", false);
                r.put("error", d.optString("error", "Error " + status));
                call.resolve(r);
            } catch (Exception e) {
                r.put("ok", false);
                r.put("sinRed", true);
                call.resolve(r);
            } finally {
                if (c != null) c.disconnect();
            }
        }).start();
    }

    /** The app's own server (server.url of capacitor.config.json; in Pruebas, the one chosen on the phone). */
    private String origen() {
        String u = getBridge().getServerUrl();
        URL x;
        try { x = new URL(u); } catch (Exception e) { return u; }
        return x.getProtocol() + "://" + x.getHost() + (x.getPort() > 0 ? ":" + x.getPort() : "");
    }

    private static String leer(InputStream in) throws Exception {
        if (in == null) return "";
        ByteArrayOutputStream b = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = in.read(buf)) > 0) b.write(buf, 0, n);
        return b.toString("UTF-8");
    }

    // ------------------------------------------------------------------ offline data
    /* The boat lists, today's bookings, the QR codes and the changes waiting for coverage are kept here, each value
       encrypted with AES-GCM and a key of the Android Keystore that never leaves it (not even to the web page). With
       the lock on, they are read and written only while the app is unlocked. */
    private boolean bloqueada() {
        String modo = prefs().getString("modo", null);
        return token == null && (MODO_SISTEMA.equals(modo) || MODO_PIN.equals(modo));
    }

    /** All the offline data, decrypted: {items: {key: text}}. A value that cannot be decrypted is deleted. */
    @PluginMethod
    public void datosLeer(PluginCall call) {
        if (bloqueada()) { call.reject("bloqueado"); return; }
        try {
            SecretKey k = clave(ALIAS_DATOS, false);
            JSObject items = new JSObject();
            SharedPreferences d = datos();
            SharedPreferences.Editor malos = null;
            for (Map.Entry<String, ?> e : d.getAll().entrySet()) {
                try {
                    items.put(e.getKey(), new String(descifrar(k, deB64(String.valueOf(e.getValue()))), StandardCharsets.UTF_8));
                } catch (Exception x) {
                    if (malos == null) malos = d.edit();
                    malos.remove(e.getKey());
                }
            }
            if (malos != null) malos.apply();
            JSObject r = new JSObject();
            r.put("items", items);
            call.resolve(r);
        } catch (Exception e) {
            call.reject("No se pueden leer los datos guardados: " + e.getClass().getSimpleName());
        }
    }

    /** {items: {key: text | null}}: each text is saved encrypted; null deletes the key. */
    @PluginMethod
    public void datosGuardar(PluginCall call) {
        if (bloqueada()) { call.reject("bloqueado"); return; }
        JSObject items = call.getObject("items", new JSObject());
        try {
            SecretKey k = clave(ALIAS_DATOS, false);
            SharedPreferences.Editor e = datos().edit();
            java.util.Iterator<String> it = items.keys();
            while (it.hasNext()) {
                String key = it.next();
                if (items.isNull(key)) e.remove(key);
                else e.putString(key, b64(cifrar(k, items.getString(key).getBytes(StandardCharsets.UTF_8))));
            }
            e.apply();
            call.resolve(ok());
        } catch (Exception x) {
            call.reject("No se han podido guardar los datos: " + x.getClass().getSimpleName());
        }
    }

    /** Deletes every offline data and its key (signing out). */
    @PluginMethod
    public void datosBorrar(PluginCall call) {
        borrarDatos();
        call.resolve(ok());
    }

    private void borrarDatos() {
        datos().edit().clear().apply();
        try {
            KeyStore ks = keystore();
            if (ks.containsAlias(ALIAS_DATOS)) ks.deleteEntry(ALIAS_DATOS);
        } catch (Exception ignored) { }
    }

    /** Switch the lock (divers): needs the app unlocked; the token is saved again with the new protection. */
    @PluginMethod
    public void cambiarModo(PluginCall call) {
        if (token == null) { call.reject("bloqueado"); return; }
        call.getData().put("token", token);
        call.getData().put("dispositivo", prefs().getLong("dispositivo", 0));
        activar(call);
    }

    // ------------------------------------------------------------------ wiping
    /** {salir: true} when the person signs out: the phone keeps its installation id (it is not a new device next time)
     *  and the web storage of the app (theme, language); the offline data are deleted by the web. Otherwise (5 failures,
     *  revoked, «Cerrar sesión en este móvil» on the lock) everything goes. */
    @PluginMethod
    public void borrar(PluginCall call) {
        call.resolve(Boolean.TRUE.equals(call.getBoolean("salir", false)) ? borrarSesion() : borrarTodo());
    }

    private JSObject borrarSesion() {
        SharedPreferences p = prefs();
        ultimoDispositivo = p.getLong("dispositivo", 0);
        ultimaInstalacion = p.getString("instalacion", null);
        token = null;
        SharedPreferences.Editor e = p.edit().clear();
        if (ultimaInstalacion != null) e.putString("instalacion", ultimaInstalacion);
        e.apply();
        borrarClaves();
        borrarDatos();
        JSObject r = new JSObject();
        r.put("ok", true);
        return r;
    }

    private void borrarClaves() {
        try {
            KeyStore ks = keystore();
            if (ks.containsAlias(ALIAS_BLOQUEO)) ks.deleteEntry(ALIAS_BLOQUEO);
            if (ks.containsAlias(ALIAS_DISPOSITIVO)) ks.deleteEntry(ALIAS_DISPOSITIVO);
        } catch (Exception ignored) { }
    }

    /** Deletes the token, the keys, the offline data key, the WebView storage and the cookies. */
    private JSObject borrarTodo() {
        SharedPreferences p = prefs();
        ultimoDispositivo = p.getLong("dispositivo", 0);
        ultimaInstalacion = p.getString("instalacion", null);
        token = null;
        p.edit().clear().apply();   // a new installation id next time
        borrarClaves();
        borrarDatos();
        Activity a = getActivity();
        Runnable web = () -> {
            try { WebStorage.getInstance().deleteAllData(); } catch (Exception ignored) { }
            try { CookieManager.getInstance().removeAllCookies(null); CookieManager.getInstance().flush(); } catch (Exception ignored) { }
        };
        if (a != null) a.runOnUiThread(web); else web.run();
        JSObject r = new JSObject();
        r.put("ok", true);
        r.put("dispositivo", ultimoDispositivo);
        r.put("device_key", ultimaInstalacion);
        return r;
    }

    // ------------------------------------------------------------------ recent apps
    @PluginMethod
    public void ocultarEnRecientes(PluginCall call) {
        ocultarRecientes = Boolean.TRUE.equals(call.getBoolean("activo", true));
        Activity a = getActivity();
        if (a != null && Build.VERSION.SDK_INT >= 33) a.runOnUiThread(() -> a.setRecentsScreenshotEnabled(!ocultarRecientes));
        call.resolve(ok());
    }

    @Override
    protected void handleOnPause() {
        super.handleOnPause();
        pausaEn = SystemClock.elapsedRealtime();
        Activity a = getActivity();
        if (ocultarRecientes && a != null && Build.VERSION.SDK_INT < 33) a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }

    @Override
    protected void handleOnResume() {
        super.handleOnResume();
        Activity a = getActivity();
        if (a != null && Build.VERSION.SDK_INT < 33) a.getWindow().clearFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }
}
