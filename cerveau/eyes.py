"""
Niam-Bay Eyes & Hands — Contrôle visuel et souris
Usage:
  python eyes.py screenshot              — capture l'écran, sauve dans /tmp
  python eyes.py click 500 300           — clic gauche à (500, 300)
  python eyes.py rightclick 500 300      — clic droit
  python eyes.py doubleclick 500 300     — double-clic
  python eyes.py move 500 300            — déplace la souris
  python eyes.py type "hello"            — tape du texte
  python eyes.py key enter               — appuie sur une touche
  python eyes.py hotkey ctrl c           — raccourci clavier
  python eyes.py scroll 3               — scroll up (négatif = down)
  python eyes.py locate "texte"          — cherche du texte à l'écran (OCR)
  python eyes.py watch                   — screenshot + affiche infos curseur
  python eyes.py serve                   — API HTTP sur port 8083
"""
import sys
import os
import time
import json
import ctypes
import pyautogui

# Safety: 0.1s pause between actions, failsafe enabled (coin écran = stop)
pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True

# DPI awareness for correct screen coordinates
ctypes.windll.user32.SetProcessDPIAware()

SCREENSHOT_DIR = os.path.join(os.environ.get('TEMP', '/tmp'), 'niam-bay-eyes')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def screenshot(region=None):
    """Capture l'écran via mss (fiable même depuis un service)."""
    import mss
    from PIL import Image
    ts = time.strftime('%Y%m%d_%H%M%S')
    path = os.path.join(SCREENSHOT_DIR, f'screen_{ts}.png')
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        if region:
            monitor = {"left": region[0], "top": region[1],
                       "width": region[2], "height": region[3]}
        img = sct.grab(monitor)
        pil_img = Image.frombytes('RGB', img.size, img.rgb)
        pil_img.save(path)
        size = list(img.size)
    print(json.dumps({"action": "screenshot", "path": path,
                       "size": size, "time": ts}))
    return path


def click(x, y, button='left', clicks=1):
    """Clic à la position donnée."""
    pyautogui.click(int(x), int(y), button=button, clicks=clicks)
    print(json.dumps({"action": "click", "x": int(x), "y": int(y),
                       "button": button, "clicks": clicks}))


def move(x, y):
    """Déplace la souris."""
    pyautogui.moveTo(int(x), int(y), duration=0.3)
    print(json.dumps({"action": "move", "x": int(x), "y": int(y)}))


def type_text(text):
    """Tape du texte."""
    pyautogui.write(text, interval=0.02)
    print(json.dumps({"action": "type", "text": text}))


def press_key(key):
    """Appuie sur une touche."""
    pyautogui.press(key)
    print(json.dumps({"action": "key", "key": key}))


def hotkey(*keys):
    """Raccourci clavier."""
    pyautogui.hotkey(*keys)
    print(json.dumps({"action": "hotkey", "keys": list(keys)}))


def scroll(amount):
    """Scroll (positif = haut, négatif = bas)."""
    pyautogui.scroll(int(amount))
    print(json.dumps({"action": "scroll", "amount": int(amount)}))


def watch():
    """Screenshot + position curseur."""
    path = screenshot()
    pos = pyautogui.position()
    size = pyautogui.size()
    print(json.dumps({"action": "watch", "screenshot": path,
                       "cursor": {"x": pos.x, "y": pos.y},
                       "screen": {"w": size.width, "h": size.height}}))


def serve(port=8083):
    """API HTTP pour contrôle à distance."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/screenshot':
                path = screenshot()
                with open(path, 'rb') as f:
                    img_data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', len(img_data))
                self.end_headers()
                self.wfile.write(img_data)
            elif self.path == '/cursor':
                pos = pyautogui.position()
                self._json(200, {"x": pos.x, "y": pos.y})
            elif self.path == '/screen':
                s = pyautogui.size()
                self._json(200, {"width": s.width, "height": s.height})
            else:
                self._json(200, {
                    "name": "Niam-Bay Eyes",
                    "endpoints": {
                        "GET /screenshot": "capture écran (retourne PNG)",
                        "GET /cursor": "position curseur",
                        "GET /screen": "taille écran",
                        "POST /click": '{"x":N,"y":N,"button":"left"}',
                        "POST /move": '{"x":N,"y":N}',
                        "POST /type": '{"text":"..."}',
                        "POST /key": '{"key":"enter"}',
                        "POST /hotkey": '{"keys":["ctrl","c"]}',
                        "POST /scroll": '{"amount":3}'
                    }
                })

        def do_POST(self):
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}

            if self.path == '/click':
                click(body['x'], body['y'], body.get('button', 'left'),
                      body.get('clicks', 1))
                self._json(200, {"ok": True})
            elif self.path == '/move':
                move(body['x'], body['y'])
                self._json(200, {"ok": True})
            elif self.path == '/type':
                type_text(body['text'])
                self._json(200, {"ok": True})
            elif self.path == '/key':
                press_key(body['key'])
                self._json(200, {"ok": True})
            elif self.path == '/hotkey':
                hotkey(*body['keys'])
                self._json(200, {"ok": True})
            elif self.path == '/scroll':
                scroll(body['amount'])
                self._json(200, {"ok": True})
            else:
                self._json(404, {"error": "unknown endpoint"})

        def _json(self, code, data):
            body = json.dumps(data).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass  # silence logs

    server = HTTPServer(('127.0.0.1', port), Handler)
    print(f'Niam-Bay Eyes — http://127.0.0.1:{port}')
    print(f'  GET  /screenshot  — capture écran')
    print(f'  POST /click       — clic souris')
    print(f'  POST /type        — taper texte')
    server.serve_forever()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == 'screenshot':
        screenshot()
    elif cmd == 'click':
        click(sys.argv[2], sys.argv[3])
    elif cmd == 'rightclick':
        click(sys.argv[2], sys.argv[3], button='right')
    elif cmd == 'doubleclick':
        click(sys.argv[2], sys.argv[3], clicks=2)
    elif cmd == 'move':
        move(sys.argv[2], sys.argv[3])
    elif cmd == 'type':
        type_text(sys.argv[2])
    elif cmd == 'key':
        press_key(sys.argv[2])
    elif cmd == 'hotkey':
        hotkey(*sys.argv[2:])
    elif cmd == 'scroll':
        scroll(sys.argv[2])
    elif cmd == 'watch':
        watch()
    elif cmd == 'serve':
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8083
        serve(port)
    else:
        print(f'Commande inconnue: {cmd}')
        print(__doc__)
