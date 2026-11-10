package es.proyectillos.marevolutivo;

import android.app.Presentation;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.os.Handler;
import android.os.Looper;
import android.service.wallpaper.WallpaperService;
import android.view.SurfaceHolder;
import android.webkit.WebView;

/**
 * Fondo de pantalla animado. El WebView del mar se dibuja en una pantalla virtual
 * cuya superficie es la del propio fondo, así va con la gráfica del móvil.
 */
public class MarWallpaper extends WallpaperService {
    /** La pantalla de ajustes lo activa para que el fondo recargue la partida al volver. */
    static volatile boolean recargar = false;

    @Override
    public Engine onCreateEngine() { return new MarEngine(); }

    private class MarEngine extends Engine {
        private VirtualDisplay pantalla;
        private Presentation presentacion;
        private WebView web;
        private Bateria bateria;
        private final Handler h = new Handler(Looper.getMainLooper());

        @Override
        public void onCreate(SurfaceHolder holder) {
            super.onCreate(holder);
            setTouchEventsEnabled(false); // como fondo no se toca: así deslizar entre pantallas no hace nada raro
        }

        @Override
        public void onSurfaceChanged(SurfaceHolder holder, int format, int w, int hh) {
            super.onSurfaceChanged(holder, format, w, hh);
            int dpi = getResources().getDisplayMetrics().densityDpi;
            if (pantalla == null) {
                DisplayManager dm = (DisplayManager) getSystemService(DISPLAY_SERVICE);
                pantalla = dm.createVirtualDisplay("mar-evolutivo", w, hh, dpi, holder.getSurface(), 0);
                presentacion = new Presentation(MarWallpaper.this, pantalla.getDisplay());
                web = Web.crear(presentacion.getContext(), isPreview() ? "#fondo-nopanel-preview" : "#fondo-nopanel");
                presentacion.setContentView(web);
                presentacion.show();
                bateria = new Bateria(web);
                bateria.registrar(MarWallpaper.this);
                h.postDelayed(() -> { if (bateria != null) bateria.pasar(); }, 2500);
            } else {
                pantalla.setSurface(holder.getSurface());
                pantalla.resize(w, hh, dpi);
            }
        }

        @Override
        public void onSurfaceDestroyed(SurfaceHolder holder) {
            if (pantalla != null) pantalla.setSurface(null);
            super.onSurfaceDestroyed(holder);
        }

        @Override
        public void onVisibilityChanged(boolean visible) {
            super.onVisibilityChanged(visible);
            if (web == null) return;
            if (visible) {
                web.onResume();
                if (recargar && !isPreview()) {
                    recargar = false;
                    web.reload();
                    h.postDelayed(() -> { if (bateria != null) bateria.pasar(); }, 2500);
                } else {
                    Web.js(web, "window.__pause&&window.__pause(false)");
                    if (bateria != null) bateria.pasar();
                }
            } else {
                // sin verse, no dibuja ni gasta batería (y guarda la partida)
                Web.js(web, "window.__pause&&window.__pause(true)");
                web.onPause();
            }
        }

        @Override
        public void onDestroy() {
            if (bateria != null) { try { unregisterReceiver(bateria); } catch (Exception ignored) {} bateria = null; }
            if (web != null) { Web.js(web, "window.__save&&window.__save()"); }
            final WebView w = web; web = null;
            h.postDelayed(() -> {
                if (presentacion != null) presentacion.dismiss();
                if (w != null) w.destroy();
                if (pantalla != null) pantalla.release();
            }, 300);
            super.onDestroy();
        }
    }
}
