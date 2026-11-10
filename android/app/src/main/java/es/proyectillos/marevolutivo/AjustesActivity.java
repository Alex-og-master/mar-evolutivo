package es.proyectillos.marevolutivo;

import android.app.Activity;
import android.app.WallpaperInfo;
import android.app.WallpaperManager;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.widget.Toast;

/** El icono de la app: el mar en grande con su panel (ciudad, árbol, diario…). */
public class AjustesActivity extends Activity {
    private WebView web;
    private Bateria bateria;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS);
        web = Web.crear(this, "#ajustes");
        web.addJavascriptInterface(new Puente(), "MarApp");
        setContentView(web);
        bateria = new Bateria(web);
        bateria.registrar(this);
        web.setSystemUiVisibility(View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
        if (!esNuestroFondo()) {
            Toast.makeText(this, "Mantén pulsado el mar para abrir el panel. Desde ahí puedes ponerlo de fondo.", Toast.LENGTH_LONG).show();
        }
    }

    private boolean esNuestroFondo() {
        WallpaperInfo info = WallpaperManager.getInstance(this).getWallpaperInfo();
        return info != null && getPackageName().equals(info.getPackageName());
    }

    void ponerFondo() {
        try {
            Intent i = new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER);
            i.putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT, new ComponentName(this, MarWallpaper.class));
            startActivity(i);
        } catch (Exception e) {
            try { startActivity(new Intent(WallpaperManager.ACTION_LIVE_WALLPAPER_CHOOSER)); }
            catch (Exception e2) { Toast.makeText(this, "Ve a Ajustes > Fondo de pantalla y elige «Mar evolutivo»", Toast.LENGTH_LONG).show(); }
        }
    }

    private class Puente {
        @JavascriptInterface public void ponerFondo() { runOnUiThread(AjustesActivity.this::ponerFondo); }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) { web.onResume(); Web.js(web, "window.__pause&&window.__pause(false)"); }
        if (bateria != null) bateria.pasar();
    }

    @Override
    protected void onPause() {
        if (web != null) { Web.js(web, "window.__pause&&window.__pause(true);window.__save&&window.__save()"); web.onPause(); }
        MarWallpaper.recargar = true; // el fondo cogerá los cambios (ciudad, partida…) al volver
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        if (bateria != null) { try { unregisterReceiver(bateria); } catch (Exception ignored) {} }
        if (web != null) web.destroy();
        super.onDestroy();
    }
}
