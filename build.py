import base64, sys
import json as _j
src = open('src/app.html').read().replace('/*@ICONS@*/{}', open('src/icons.json').read())
weights = {'Regular':400,'Medium':500,'Semibold':600}
def face(w, url): return '@font-face{font-family:"Open Runde";font-style:normal;font-weight:%d;font-display:swap;src:url(%s) format("woff2")}' % (weights[w], url)
inline = ''.join(face(w, 'data:font/woff2;base64,' + base64.b64encode(open(f'fonts/OR-{w}.woff2','rb').read()).decode()) for w in weights)
open('dist-artifact.html','w').write(src.replace('/*@FONTS@*/', inline))
print('artifact', len(open('dist-artifact.html').read())//1024, 'KB')

# ---------- PWA build -> docs/ (served by GitHub Pages) ----------
import os, shutil, json, hashlib
out = 'docs'
shutil.rmtree(out, ignore_errors=True); os.makedirs(out + '/fonts'); os.makedirs(out + '/icons'); os.makedirs(out + '/vendor')
for w in weights: shutil.copy(f'fonts/OR-{w}.woff2', f'{out}/fonts/')
shutil.copy('fonts/OFL.txt', f'{out}/fonts/')
for f in os.listdir('icons'): shutil.copy('icons/' + f, f'{out}/icons/')
shutil.copy('vendor/supabase.js', f'{out}/vendor/')
shutil.copy('src/backend-supabase.js', f'{out}/backend-supabase.js')
sb = json.load(open('supabase.json')) if os.path.exists('supabase.json') else {'url': '', 'key': ''}
open(f'{out}/config.js', 'w').write('window.LEDGER_SUPABASE = ' + json.dumps(sb) + ';\nwindow.LEDGER_ORDER = ["supabase", "local"];\n')
faces = ''.join(face(w, f'fonts/OR-{w}.woff2') for w in weights)
body = src.replace('/*@FONTS@*/', faces + '\n:root{padding-top:env(safe-area-inset-top,0px)}body{margin:0}[hidden]{display:none!important}img{max-width:100%}')
title_end = body.index('</title>') + len('</title>')
head_extra = '''<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#F4F5F7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0A0B0D" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Runway">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="preload" href="fonts/OR-Semibold.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="fonts/OR-Regular.woff2" as="font" type="font/woff2" crossorigin>
'''
head = body[:title_end]; rest = body[title_end:]
style_end = rest.index('</style>') + len('</style>')
style = rest[:style_end]; content = rest[style_end:]
scripts = '<script src="config.js"></script><script src="vendor/supabase.js"></script><script src="backend-supabase.js"></script>\n'
sw = "<script>if('serviceWorker' in navigator){addEventListener('load',()=>navigator.serviceWorker.register('sw.js'))}</script>\n"
content = content.replace('<script>\n/* ================= PURE LOGIC', scripts + '<script>\n/* ================= PURE LOGIC', 1)
html = '<!doctype html>\n<html lang="en">\n<head>\n' + head_extra + head + '\n' + style + '\n</head>\n<body>\n' + content + sw + '</body>\n</html>\n'
open(f'{out}/index.html', 'w').write(html)
json.dump({
  'name': 'Runway', 'short_name': 'Runway', 'start_url': './', 'scope': './', 'display': 'standalone',
  'background_color': '#F4F5F7', 'theme_color': '#0C0E12', 'description': 'Monthly budget: payday split, bills, everyday spending.',
  'icons': [
    {'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
    {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
    {'src': 'icons/maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]
}, open(f'{out}/manifest.webmanifest', 'w'), indent=2)
shell = ['./', 'index.html', 'config.js', 'backend-supabase.js', 'vendor/supabase.js', 'manifest.webmanifest'] + [f'fonts/OR-{w}.woff2' for w in weights] + ['icons/' + f for f in os.listdir('icons')]
ver = hashlib.sha1(''.join(open(os.path.join(out, p if p != './' else 'index.html'), 'rb').read().hex()[:4000] for p in shell).encode()).hexdigest()[:10]
open(f'{out}/sw.js', 'w').write(f'''const CACHE = 'runway-{ver}';
const SHELL = {json.dumps(shell)};
self.addEventListener('install', e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); }});
self.addEventListener('activate', e => {{ e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); }});
self.addEventListener('fetch', e => {{
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return; // Supabase calls always go to the network
  if (e.request.mode === 'navigate' || u.pathname.endsWith('/index.html') || u.pathname.endsWith('/config.js')) {{
    e.respondWith(fetch(e.request).then(r => {{ const c = r.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); return r; }}).catch(() => caches.match(e.request).then(r => r || caches.match('index.html'))));
    return;
  }}
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
}});
''')
open(f'{out}/.nojekyll', 'w').write('')
print('pwa ok', ver)
