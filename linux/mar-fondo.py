#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mar evolutivo — lanzador de fondo de pantalla para Linux.
Abre mar-evolutivo.html detrás de los iconos del escritorio, ocupando
todas las pantallas como una sola panorámica, y le pasa la batería real.

Uso:  python3 mar-fondo.py            (fondo de pantalla)
      python3 mar-fondo.py --ajustes  (abre el mar en una ventana con el panel:
                                       ciudad, tiempo, árbol, diario… y al cerrar
                                       vuelve a ponerlo de fondo)
      python3 mar-fondo.py --debug    (muestra los mensajes de la página)
"""
import os, sys, glob, signal, subprocess, json, threading, urllib.request, urllib.parse

AJUSTES = '--ajustes' in sys.argv
VENTANA = '--ventana' in sys.argv or AJUSTES
DEBUG = '--debug' in sys.argv
# En Wayland usamos XWayland: así el escritorio respeta el tipo "fondo" de la ventana.
if not VENTANA and os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    os.environ['GDK_BACKEND'] = 'x11'

import gi
gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GLib, Gio, WebKit2

AQUI = os.path.dirname(os.path.realpath(__file__))
HTML = os.path.join(AQUI, 'mar-evolutivo.html')
DATOS = os.path.join(GLib.get_user_data_dir(), 'mar-evolutivo', 'web')
REGISTRO = os.path.join(GLib.get_user_data_dir(), 'mar-evolutivo', 'registro.log')


def preparar_registro():
    """Todo lo que pase (y los errores de la página) va a registro.log, para poder diagnosticar."""
    os.makedirs(os.path.dirname(REGISTRO), exist_ok=True)
    try:
        if os.path.getsize(REGISTRO) > 1_000_000:
            os.replace(REGISTRO, REGISTRO + '.viejo')
    except OSError:
        pass
    fd = os.open(REGISTRO, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.dup2(fd, 1); os.dup2(fd, 2)


def log(*a):
    import time
    print(time.strftime('%Y-%m-%d %H:%M:%S'), *a, flush=True)


def leer(ruta):
    try:
        with open(ruta) as f:
            return f.read().strip()
    except OSError:
        return None


def bateria():
    """Devuelve (nivel 0-1, cargando) o None si no hay batería."""
    niveles, cargando = [], False
    for b in glob.glob('/sys/class/power_supply/*'):
        tipo = leer(b + '/type')
        if tipo == 'Battery' and leer(b + '/scope') != 'Device':
            cap = leer(b + '/capacity')
            if cap and cap.isdigit():
                niveles.append(int(cap))
            if leer(b + '/status') in ('Charging', 'Full'):
                cargando = True
        elif tipo == 'Mains' and leer(b + '/online') == '1':
            cargando = True
    if not niveles:
        return None
    return sum(niveles) / len(niveles) / 100.0, cargando


class Fondo(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='Mar evolutivo')
        if not VENTANA:
            self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
            self.set_decorated(False)
            self.set_skip_taskbar_hint(True)
            self.set_skip_pager_hint(True)
            self.set_keep_below(True)
            self.stick()
        else:
            self.set_default_size(1280, 760)
            self.set_title('Mar evolutivo · ajustes' if AJUSTES else 'Mar evolutivo')
            self.connect('delete-event', self.cerrar)

        mgr = WebKit2.WebsiteDataManager(base_data_directory=DATOS,
                                         base_cache_directory=os.path.join(DATOS, 'cache'))
        ctx = WebKit2.WebContext.new_with_website_data_manager(mgr)
        self.web = WebKit2.WebView.new_with_context(ctx)
        s = self.web.get_settings()
        s.set_allow_file_access_from_file_urls(True)
        s.set_allow_universal_access_from_file_urls(True)
        s.set_enable_write_console_messages_to_stdout(True)
        s.set_enable_developer_extras(DEBUG)
        try:
            s.set_hardware_acceleration_policy(WebKit2.HardwareAccelerationPolicy.ALWAYS)
        except Exception:
            pass
        self.web.set_background_color(Gdk.RGBA(0.01, 0.03, 0.07, 1))
        self.web.connect('permission-request', self.permiso)
        self.web.connect('load-changed', self.cargado)
        self.web.connect('context-menu', lambda *a: True)
        # la página pide el tiempo a través del lanzador (así no le afectan los permisos del navegador)
        ucm = self.web.get_user_content_manager()
        ucm.register_script_message_handler('mar')
        ucm.connect('script-message-received::mar', self.mensaje)
        self.web.connect('web-process-terminated', self.proceso_muerto)
        self.pausado = False
        self.ultimo_latido = None
        self.sin_latido = 0
        self.add(self.web)

        uri = GLib.filename_to_uri(HTML, None) + ('#ajustes' if AJUSTES else '' if VENTANA else '#fondo')
        self.web.load_uri(uri)

        if not VENTANA:
            disp = Gdk.Display.get_default()
            disp.connect('monitor-added', lambda *a: self.ajustar())
            disp.connect('monitor-removed', lambda *a: self.ajustar())
            self.ajustar()
        GLib.timeout_add_seconds(20, self.pasar_bateria)
        if not VENTANA:
            self.vigilar_bloqueo()
        GLib.timeout_add_seconds(15, self.vigilante)
        log('arranca', 'ajustes' if AJUSTES else 'ventana' if VENTANA else 'fondo',
            os.environ.get('XDG_SESSION_TYPE'), os.environ.get('XDG_CURRENT_DESKTOP'))
        self.show_all()

    PERMITIDOS = ('api.open-meteo.com', 'geocoding-api.open-meteo.com')

    def mensaje(self, ucm, res):
        try:
            v = res.get_js_value() if hasattr(res, 'get_js_value') else res
            datos = json.loads(v.to_string())
            ide, url = int(datos['id']), datos['url']
        except Exception as e:
            log('mensaje raro de la página:', e)
            return
        if urllib.parse.urlparse(url).hostname not in self.PERMITIDOS:
            log('petición bloqueada:', url)
            return
        def pedir():
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'mar-evolutivo'})
                with urllib.request.urlopen(req, timeout=12) as r:
                    txt, ok = r.read().decode('utf-8'), True
            except Exception as e:
                txt, ok = str(e), False
            log('tiempo' if 'forecast' in url else 'ciudad', 'ok' if ok else 'error: ' + txt[:120])
            GLib.idle_add(lambda: (self.js('window.__reply&&window.__reply(%d,%s,%s)' % (ide, 'true' if ok else 'false', json.dumps(txt))), False)[1])
        threading.Thread(target=pedir, daemon=True).start()

    def proceso_muerto(self, web, motivo):
        log('el proceso de la página se ha cerrado:', motivo, '→ recargo')
        GLib.timeout_add(1000, lambda: (web.reload(), False)[1])

    def vigilante(self):
        """Si la imagen deja de moverse sin estar en pausa, recarga la página."""
        if self.pausado:
            self.sin_latido = 0
            return True
        def recibido(web, res, *a):
            try:
                if hasattr(web, 'evaluate_javascript_finish'):
                    v = web.evaluate_javascript_finish(res).to_double()
                else:
                    v = web.run_javascript_finish(res).get_js_value().to_double()
            except Exception as e:
                v = None
            if v is not None and v == self.ultimo_latido:
                self.sin_latido += 1
                log('la página no avanza', self.sin_latido)
                if self.sin_latido >= 2:
                    log('congelada → recargo')
                    self.sin_latido = 0
                    self.web.reload()
            else:
                self.sin_latido = 0
            self.ultimo_latido = v
        codigo = 'window.__beat||0'
        if hasattr(self.web, 'evaluate_javascript'):
            self.web.evaluate_javascript(codigo, -1, None, None, None, recibido, None)
        else:
            self.web.run_javascript(codigo, None, recibido, None)
        return True

    def vigilar_bloqueo(self):
        """Con la pantalla bloqueada o apagada el mar deja de dibujarse (gasta ~0);
        al volver se pone al día en cámara rápida."""
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except Exception:
            return
        def cambio(conn, sender, path, iface, sig, params, *a):
            try:
                activo = bool(params.unpack()[0])
            except Exception:
                return
            log('pantalla', 'bloqueada/apagada' if activo else 'de vuelta')
            self.pausado = activo
            self.ultimo_latido = None
            self.js('window.__pause&&window.__pause(%s)' % ('true' if activo else 'false'))
            if not activo:
                GLib.timeout_add(1500, lambda: (self.web.queue_draw(), self.queue_draw(), False)[2])
        for nombre, ruta in (('org.gnome.ScreenSaver', '/org/gnome/ScreenSaver'),
                             ('org.freedesktop.ScreenSaver', '/org/freedesktop/ScreenSaver')):
            bus.signal_subscribe(None, nombre, 'ActiveChanged', ruta, None, Gio.DBusSignalFlags.NONE, cambio)

    def guardar_y(self, despues):
        self.js('window.__save&&window.__save()')
        GLib.timeout_add(500, despues)

    def cerrar(self, *a):
        def fin():
            if AJUSTES:
                subprocess.Popen([sys.executable, os.path.realpath(__file__)], start_new_session=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.get_application().quit()
            return False
        self.hide()
        self.guardar_y(fin)
        return True

    def ajustar(self):
        """Ocupa el rectángulo que cubre todas las pantallas."""
        disp = Gdk.Display.get_default()
        rs = [disp.get_monitor(i).get_geometry() for i in range(disp.get_n_monitors())]
        x0 = min(r.x for r in rs); y0 = min(r.y for r in rs)
        x1 = max(r.x + r.width for r in rs); y1 = max(r.y + r.height for r in rs)
        self.move(x0, y0)
        self.set_default_size(x1 - x0, y1 - y0)
        self.resize(x1 - x0, y1 - y0)

    def permiso(self, web, req):
        # La ubicación se elige en el panel del propio mar (pestaña Tiempo).
        req.deny()
        return True

    def cargado(self, web, ev):
        if ev == WebKit2.LoadEvent.FINISHED:
            GLib.timeout_add(1500, self.pasar_bateria)

    def js(self, codigo):
        if hasattr(self.web, 'evaluate_javascript'):
            self.web.evaluate_javascript(codigo, -1, None, None, None, None, None)
        else:
            self.web.run_javascript(codigo, None, None, None)

    def pasar_bateria(self):
        b = bateria()
        if b:
            self.js('window.__setBattery&&window.__setBattery(%.3f,%s)' % (b[0], 'true' if b[1] else 'false'))
        return True


def parar_fondo():
    """Cierra el fondo de pantalla si está en marcha (para no pisar el mar guardado)."""
    yo = os.getpid()
    for d in os.listdir('/proc'):
        if not d.isdigit() or int(d) == yo:
            continue
        try:
            cmd = open('/proc/%s/cmdline' % d, 'rb').read().split(b'\0')
        except OSError:
            continue
        if any(c.endswith(b'mar-fondo.py') for c in cmd) and b'--ajustes' not in cmd:
            try:
                os.kill(int(d), signal.SIGTERM)
            except OSError:
                pass


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='es.proyectillos.MarEvolutivo' + ('.Ajustes' if AJUSTES else ''),
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.win = None

    def do_activate(self):
        if not self.win:
            self.win = Fondo(self)
            if not VENTANA:
                # al pararlo (menú «Parar» o al apagar) guarda antes de salir
                GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM,
                                     lambda: (self.win.guardar_y(lambda: self.quit() or False), True)[1])
        self.win.present() if VENTANA else None


if __name__ == '__main__':
    if not os.path.exists(HTML):
        print('No encuentro mar-evolutivo.html junto al script.')
        sys.exit(1)
    if not DEBUG:
        preparar_registro()
    if not VENTANA:
        # prioridad baja: el resto de programas (y el arranque del sistema) siempre van primero
        try:
            os.nice(10)
        except OSError:
            pass
    if AJUSTES:
        parar_fondo()
        import time; time.sleep(0.8)
    App().run([sys.argv[0]])
