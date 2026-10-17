package com.worldives.app;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * Tells the web whether this build carries the Firebase file of WORLDIVES (google-services.json). Without it,
 * registering for push notifications would fail, so the web does not even ask for the permission (v50.49).
 */
@CapacitorPlugin(name = "PushListo")
public class PushListoPlugin extends Plugin {

    @PluginMethod
    public void estado(PluginCall call) {
        int id = getContext().getResources().getIdentifier("google_app_id", "string", getContext().getPackageName());
        JSObject r = new JSObject();
        r.put("firebase", id != 0);
        call.resolve(r);
    }
}
