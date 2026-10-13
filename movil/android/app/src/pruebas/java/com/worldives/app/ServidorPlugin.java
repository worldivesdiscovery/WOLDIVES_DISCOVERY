package com.worldives.app;

import android.content.SharedPreferences;
import android.net.Uri;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.util.regex.Pattern;

/**
 * Only in WORLDIVES Pruebas: choose, read and forget the test server. Changing it restarts the app on the new address.
 * The production app does not have this class at all.
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

    private void reiniciar() {
        getActivity().runOnUiThread(() -> getActivity().recreate());
    }
}
