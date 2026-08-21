# -*- coding: utf-8 -*-
"""
Verifie que TOUS les styles de QR de l'outil restent scannables.

Sert de filet apres chaque modification du rendu QR (formes, degrades, logo, presets).
Chaque combinaison est rendue dans un vrai Chromium, puis relue avec jsQR (le decodeur
des scanners web, proche du comportement d'un telephone), en PNG et en SVG rasterise,
a 300 px et 600 px - les deux echelles auxquelles un scan reel se produit.

Prerequis (deja installes sur le poste) :
    pip install playwright opencv-python ; python -m playwright install chromium
Lancement :
    python tests/test_qr_scan.py
jsQR est telecharge au premier lancement dans tests/.cache/ (ignore par git).
"""
import functools, http.server, itertools, os, socketserver, sys, threading, urllib.request
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.dirname(HERE)
CACHE = os.path.join(HERE, ".cache")
JSQR = os.path.join(CACHE, "jsqr.js")
JSQR_URL = "https://unpkg.com/jsqr@1.4.0/dist/jsQR.js"
PORT = 8795
TARGET = "https://bit.ly/4aQrTst"

if not os.path.exists(JSQR):
    os.makedirs(CACHE, exist_ok=True)
    print("telechargement de jsQR...")
    urllib.request.urlretrieve(JSQR_URL, JSQR)

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIR)
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
srv.RequestHandlerClass.log_message = lambda *a, **k: None
threading.Thread(target=srv.serve_forever, daemon=True).start()

DECODE = """
async (arg) => {
  const load = (src)=>new Promise((r,j)=>{const i=new Image();i.onload=()=>r(i);i.onerror=j;i.src=src;});
  const grab = (img,w)=>{const c=document.createElement('canvas');c.width=w;c.height=w;
    const x=c.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,w,w);x.drawImage(img,0,0,w,w);
    const r=jsQR(x.getImageData(0,0,w,w).data,w,w);return r?r.data:null;};
  const out={};
  const png = await load(document.getElementById('qrCanvas').toDataURL('image/png'));
  out.png300 = grab(png,300); out.png600 = grab(png,600);
  const svg = await load('data:image/svg+xml;charset=utf-8,'+encodeURIComponent(arg.svg));
  out.svg300 = grab(svg,300); out.svg600 = grab(svg,600);
  return out;
}
"""

fails = []

def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.add_init_script("localStorage.setItem('utm_who','Test');")
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:%d/index.html" % PORT)
        pg.add_script_tag(path=JSQR)
        pg.wait_for_timeout(300)
        pg.evaluate("""(t)=>{document.getElementById('brand').value='nacarat';
            currentLink={full:'https://nacarat.com/x',short:t};showResult();}""", TARGET)

        def run(label, setup):
            pg.evaluate(setup)
            pg.wait_for_timeout(180)
            r = pg.evaluate(DECODE, {"svg": pg.evaluate("buildSVG()")})
            bad = [k for k, v in r.items() if v != TARGET]
            print("%-40s %s" % (label, "ok" if not bad else "ECHEC: " + ",".join(bad)))
            if bad:
                fails.append(label)

        print("--- formes x coins x degrade (sans logo) ---")
        for mod, eye, grad in itertools.product(["square", "rounded", "dots"],
                                                ["square", "rounded", "circle"],
                                                ["none", "linear", "radial"]):
            run("%s / %s / %s" % (mod, eye, grad), """()=>{qrPreset='';if(qrLogoKind==='social')wipeLogo();
                qrOpts.mod='%s';qrOpts.eye='%s';qrOpts.grad='%s';qrOpts.fg='#1E336D';qrOpts.fg2='#457275';
                qrOpts.bg='#ffffff';qrOpts.eyeCol='';syncQrUI();renderQR();}""" % (mod, eye, grad))

        print("--- taille du logo ---")
        for sc in [12, 16, 20, 22, 24]:
            run("logo %d%%" % sc, """()=>{applyPreset(SOCIAL_PRESETS.find(p=>p.k==='instagram'));
                qrOpts.mod='square';qrOpts.logoScale=%f;syncQrUI();renderQR();}""" % (sc / 100.0))

        print("--- presets reseaux ---")
        for k in [p["k"] for p in pg.evaluate("SOCIAL_PRESETS")]:
            for mod in ["square", "dots"]:
                run("preset %s + %s" % (k, mod), """()=>{applyPreset(SOCIAL_PRESETS.find(p=>p.k==='%s'));
                    qrOpts.mod='%s';qrOpts.logoScale=0.20;syncQrUI();renderQR();}""" % (k, mod))

        b.close()
        if errs:
            print("\nerreurs JS dans la page :", errs)
            fails.extend(errs)

main()
print("\n" + ("TOUT OK" if not fails else "ECHECS : " + str(fails)))
sys.exit(1 if fails else 0)
