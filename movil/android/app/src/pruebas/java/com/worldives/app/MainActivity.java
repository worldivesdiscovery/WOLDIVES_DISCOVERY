package com.worldives.app;

import android.content.SharedPreferences;
import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.CapConfig;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;

/**
 * WORLDIVES Pruebas. Without a saved server it opens the entry screen packed in the app (assets/public/index.html),
 * where the tester writes the address of the test server (the computer that runs the «pruebas» zip). With a saved
 * server, the app loads that server, like the production app loads https://worldivesdiscovery.com.
 */
public class MainActivity extends BridgeActivity {

    static final String PREFS = "worldives_pruebas";
    static final String KEY_SERVER = "servidor";
    static final String KEY_START = "inicio";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        registerPlugin(ServidorPlugin.class);
        registerPlugin(PushListoPlugin.class);
        registerPlugin(SeguridadPlugin.class);   // v50.55: fingerprint / PIN, Keystore, renewal, wipe
        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        String server = prefs.getString(KEY_SERVER, null);
        if (server != null) {
            String start = prefs.getString(KEY_START, null);
            prefs.edit().remove(KEY_START).apply();   // the quick entry with a test account happens once
            try {
                config = runtimeConfig(server, start);
            } catch (Exception e) {
                prefs.edit().remove(KEY_SERVER).apply();   // a broken address: back to the entry screen
            }
        }
        super.onCreate(savedInstanceState);
    }

    /** The packed capacitor.config.json with server.url set to the chosen server (and, once, a start path). */
    private CapConfig runtimeConfig(String server, String start) throws Exception {
        String json;
        try (InputStream in = getAssets().open("capacitor.config.json")) {
            json = new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
        JSONObject cfg = new JSONObject(json);
        JSONObject srv = cfg.optJSONObject("server");
        if (srv == null) srv = new JSONObject();
        srv.put("url", server);
        if (start != null && !start.isEmpty()) srv.put("appStartPath", start);
        cfg.put("server", srv);
        File dir = new File(getFilesDir(), "configuracion");
        if (!dir.exists() && !dir.mkdirs()) throw new IllegalStateException("no se puede guardar la configuración");
        try (FileOutputStream out = new FileOutputStream(new File(dir, "capacitor.config.json"))) {
            out.write(cfg.toString().getBytes(StandardCharsets.UTF_8));
        }
        return CapConfig.loadFromFile(this, dir.getAbsolutePath());
    }
}
