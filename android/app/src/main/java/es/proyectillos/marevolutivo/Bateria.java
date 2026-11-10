package es.proyectillos.marevolutivo;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Build;
import android.webkit.WebView;

/** Pasa el nivel de batería y si está cargando a la página (window.__setBattery). */
final class Bateria extends BroadcastReceiver {
    private final WebView web;
    private float nivel = -1;
    private boolean cargando;

    Bateria(WebView web) { this.web = web; }

    void registrar(Context ctx) {
        IntentFilter f = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        Intent sticky = Build.VERSION.SDK_INT >= 33
                ? ctx.registerReceiver(this, f, Context.RECEIVER_NOT_EXPORTED)
                : ctx.registerReceiver(this, f);
        if (sticky != null) onReceive(ctx, sticky);
    }

    @Override
    public void onReceive(Context ctx, Intent i) {
        int level = i.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
        int scale = i.getIntExtra(BatteryManager.EXTRA_SCALE, 100);
        int status = i.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
        int plugged = i.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0);
        if (level < 0 || scale <= 0) return;
        nivel = level / (float) scale;
        cargando = plugged != 0 || status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL;
        pasar();
    }

    void pasar() {
        if (nivel < 0) return;
        Web.js(web, "window.__setBattery&&window.__setBattery(" + nivel + "," + cargando + ")");
    }
}
