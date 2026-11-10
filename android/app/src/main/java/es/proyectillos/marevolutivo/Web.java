package es.proyectillos.marevolutivo;

import android.annotation.SuppressLint;
import android.content.Context;
import android.webkit.GeolocationPermissions;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.webkit.WebViewAssetLoader;

/** Crea el WebView del mar. La página se sirve como https://appassets.androidplatform.net/
 *  para que guarde la partida y pueda consultar el tiempo sin problemas de permisos. */
final class Web {
    static final String URL = "https://appassets.androidplatform.net/assets/index.html";

    @SuppressLint("SetJavaScriptEnabled")
    static WebView crear(Context ctx, String hash) {
        WebView w = new WebView(ctx);
        WebSettings s = w.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(true);
        w.setBackgroundColor(0xFF020812);
        w.setVerticalScrollBarEnabled(false);
        w.setHorizontalScrollBarEnabled(false);
        final WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(ctx))
                .build();
        w.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                return loader.shouldInterceptRequest(r.getUrl());
            }
        });
        w.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback cb) {
                cb.invoke(origin, false, false); // la ciudad se elige en el panel
            }
        });
        w.loadUrl(URL + hash);
        return w;
    }

    static void js(WebView w, String code) {
        if (w != null) w.evaluateJavascript(code, null);
    }

    private Web() {}
}
