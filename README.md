# Mar evolutivo 🌊

Fondo de pantalla vivo: un submarino amarillo recorre un mar con ocho biomas
(manglar, arrecife de coral, pradera de posidonia, naufragio, bosque de kelp,
mar abierto, fosa abisal y mar polar) donde los bichos evolucionan solos.
Tiene sol y luna reales según tu ubicación, mareas, estaciones, el tiempo real
de tu ciudad y la batería del dispositivo como batería del submarino.

**Verlo:** https://alex-og-master.github.io/mar-evolutivo/

## Como fondo de pantalla

- **Android:** app «Lively Wallpapers – With Website» con la dirección
  `https://alex-og-master.github.io/mar-evolutivo/#fondo`
  (con `#fondo` no sale ninguna interfaz; mantén pulsado 1 s para abrir el panel).
- **Windows:** [Lively Wallpaper](https://www.rocksdanister.com/lively/) con el archivo
  `windows/mar-evolutivo-windows.html`.
- **Linux (GNOME y otros):** carpeta `linux/`, ejecuta `./instalar.sh`
  (lanzador propio con GTK + WebKitGTK, todas las pantallas como panorámica).

Cada dispositivo guarda su propio mar.

## Android (app propia)

Descarga el APK: **https://github.com/Alex-og-master/mar-evolutivo/releases/download/movil/mar-evolutivo.apk**

Se compila solo con GitHub Actions cada vez que cambia algo (`.github/workflows/android.yml`).
Instálalo, abre «Mar evolutivo», mantén pulsado el mar y pulsa «Poner como fondo de pantalla».
El código de la app está en `android/` (fondo animado con un WebView dibujado en una pantalla virtual,
batería real, se pausa cuando no se ve la pantalla de inicio).
