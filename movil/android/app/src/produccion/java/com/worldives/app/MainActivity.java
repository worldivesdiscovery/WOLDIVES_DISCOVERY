package com.worldives.app;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

/** WORLDIVES: the web of WORLDIVES (https://worldivesdiscovery.com) inside the app, with the native plugins. */
public class MainActivity extends BridgeActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        registerPlugin(PushListoPlugin.class);
        registerPlugin(SeguridadPlugin.class);   // v50.55: fingerprint / PIN, Keystore, renewal, wipe
        super.onCreate(savedInstanceState);
    }
}
