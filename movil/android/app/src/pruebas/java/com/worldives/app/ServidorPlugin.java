package com.worldives.app;

import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.util.Base64;
import android.view.PixelCopy;
import android.view.View;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.ByteArrayOutputStream;
import java.util.regex.Pattern;

/**
 * Only in WORLDIVES Pruebas: choose, read and forget the test server (changing it restarts the app on the new address),
 * and the screenshot of «Reportar fallo». The production app does not have this class at all.
 */
@CapacitorPlugin(name = "Servidor")
public class ServidorPlugin extends Plugin {

    private static final Pattern CUENTA = Pattern.compile("^[a-z0-9]+\\.prueba$");

    private SharedPreferences prefs() {
        return getContext().getSharedPreferences(MainActivity.PREFS, android.content.Context.MODE_PRIVATE);
    }

    @PluginMethod
    public void actual(PluginCall call) {
        JSObject r = new JSObject();
        r.put("url", prefs().getString(MainActivity.KEY_SERVER, null));
        call.resolve(r);
    }

    /** {url: "http://192.168.1.50:8100", cuenta: "buzo.prueba" (optional)}. */
    @PluginMethod
    public void guardar(PluginCall call) {
        String url = call.getString("url", "").trim();
        Uri u = Uri.parse(url);
        String scheme = u.getScheme();
        if (u.getHost() == null || scheme == null || !(scheme.equals("http") || scheme.equals("https"))) {
            call.reject("Escribe la dirección completa, por ejemplo http://192.168.1.50:8100");
            return;
        }
        String origin = scheme + "://" + u.getHost() + (u.getPort() > 0 ? ":" + u.getPort() : "");
        SharedPreferences.Editor e = prefs().edit().putString(MainActivity.KEY_SERVER, origin);
        String cuenta = call.getString("cuenta", "");
        if (cuenta != null && CUENTA.matcher(cuenta).matches()) e.putString(MainActivity.KEY_START, "/#/pruebas-entrar?cuenta=" + cuenta);
        else e.remove(MainActivity.KEY_START);
        e.apply();
        call.resolve();
        reiniciar();
    }

    @PluginMethod
    public void olvidar(PluginCall call) {
        prefs().edit().remove(MainActivity.KEY_SERVER).remove(MainActivity.KEY_START).apply();
        call.resolve();
        reiniciar();
    }

    /** The quick entry is done: the next start opens the app normally, with the session already open. */
    @PluginMethod
    public void inicioHecho(PluginCall call) {
        prefs().edit().remove(MainActivity.KEY_START).apply();
        call.resolve();
    }

    /** «Reportar fallo»: what is on the screen now, as a JPEG data URL (at most 720 px wide, so it fits in one request). */
    @PluginMethod
    public void captura(PluginCall call) {
        Activity a = getActivity();
        View v = getBridge().getWebView();
        a.runOnUiThread(() -> {
            int w = v.getWidth(), h = v.getHeight();
            if (w <= 0 || h <= 0) {
                call.reject("No hay pantalla que capturar");
                return;
            }
            Bitmap bmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                int[] xy = new int[2];
                v.getLocationInWindow(xy);
                Rect zona = new Rect(xy[0], xy[1], xy[0] + w, xy[1] + h);
                PixelCopy.request(a.getWindow(), zona, bmp, res -> {
                    if (res != PixelCopy.SUCCESS) v.draw(new Canvas(bmp));
                    entregar(call, bmp);
                }, new Handler(Looper.getMainLooper()));
            } else {
                v.draw(new Canvas(bmp));
                entregar(call, bmp);
            }
        });
    }

    private void entregar(PluginCall call, Bitmap bmp) {
        Bitmap out = bmp.getWidth() > 720 ? Bitmap.createScaledBitmap(bmp, 720, Math.round(bmp.getHeight() * 720f / bmp.getWidth()), true) : bmp;
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        out.compress(Bitmap.CompressFormat.JPEG, 62, bytes);
        JSObject r = new JSObject();
        r.put("captura", "data:image/jpeg;base64," + Base64.encodeToString(bytes.toByteArray(), Base64.NO_WRAP));
        call.resolve(r);
    }

    private void reiniciar() {
        getActivity().runOnUiThread(() -> getActivity().recreate());
    }
}
