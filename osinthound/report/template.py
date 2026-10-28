"""
report/template.py
===================
Plantilla HTML del informe (cadena con tokens {{...}} que `reporter.py` sustituye).
Se mantiene aparte para no mezclar el diseno con la logica. El CSS y el JS van
inline para que el informe sea un unico fichero autocontenido; solo vis-network
(grafo) se carga desde CDN.
"""

HTML = r"""<!doctype html>
<html lang="es" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}} · OSINT Hound</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
:root{
  --bg:#0a0d13; --bg2:#0e121b; --panel:#141a25; --panel2:#1a2130;
  --line:#243043; --line2:#2e3c52;
  --ink:#e8edf5; --muted:#9db1c7; --dim:#6b7c93;
  --gold:#f2b544; --teal:#56c5b5; --blue:#6ea8fe; --violet:#b98cf0;
  --red:#e5534b; --green:#64c98a; --amber:#f2b544;
  --radius:16px; --radius-sm:10px;
  --shadow:0 10px 40px -12px rgba(0,0,0,.6);
  --mono:'JetBrains Mono',ui-monospace,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  font-family:'Inter',system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  background:
    radial-gradient(1200px 600px at 80% -10%, rgba(242,181,68,.08), transparent 60%),
    radial-gradient(1000px 500px at -10% 10%, rgba(86,197,181,.07), transparent 55%),
    var(--bg);
  color:var(--ink); line-height:1.55; -webkit-font-smoothing:antialiased;
}
a{color:var(--teal);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px 80px}

/* ---------- Hero ---------- */
.hero{
  position:relative;overflow:hidden;margin:0 0 26px;
  border-bottom:1px solid var(--line);
  background:linear-gradient(180deg, rgba(20,26,37,.85), rgba(10,13,19,.4));
}
.hero-inner{max-width:1180px;margin:0 auto;padding:40px 20px 34px;position:relative;z-index:2}
.brand{display:flex;align-items:center;gap:12px;font-weight:800;letter-spacing:.2px;
  font-size:14px;color:var(--muted);text-transform:uppercase}
.brand .dot{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;
  background:linear-gradient(135deg,var(--gold),#d9932f);color:#1a1205;font-size:16px}
.h-title{font-size:clamp(26px,4vw,40px);font-weight:800;margin:16px 0 6px;letter-spacing:-.5px}
.h-sub{color:var(--muted);font-family:var(--mono);font-size:14px}
.h-meta{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
.chip{display:inline-flex;align-items:center;gap:7px;font-size:12.5px;color:var(--muted);
  background:var(--panel);border:1px solid var(--line);padding:6px 11px;border-radius:999px}
.chip b{color:var(--ink);font-weight:600}
.expo{position:absolute;right:20px;top:40px;text-align:right;z-index:2}
.expo .lab{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--dim)}
.expo .val{font-size:22px;font-weight:800;margin-top:2px}
.expo.low .val{color:var(--green)} .expo.med .val{color:var(--amber)}
.expo.high .val{color:var(--red)} .expo.min .val{color:var(--teal)}
.meter{width:170px;height:7px;border-radius:999px;background:var(--panel2);margin-top:8px;overflow:hidden}
.meter i{display:block;height:100%;border-radius:999px;
  background:linear-gradient(90deg,var(--teal),var(--amber),var(--red))}

/* ---------- Stat tiles ---------- */
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:0 0 26px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:16px 18px;position:relative;overflow:hidden}
.tile::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--accent,var(--teal))}
.tile .n{font-size:28px;font-weight:800;letter-spacing:-.5px}
.tile .l{font-size:12.5px;color:var(--muted);margin-top:2px}
.tile .ic{position:absolute;right:12px;top:12px;font-size:18px;opacity:.5}

/* ---------- Tabs ---------- */
.tabs{display:flex;gap:4px;flex-wrap:wrap;border-bottom:1px solid var(--line);margin:0 0 22px;
  position:sticky;top:0;background:linear-gradient(180deg,var(--bg),rgba(10,13,19,.9));
  z-index:5;padding-top:4px}
.tab{appearance:none;border:0;background:transparent;color:var(--muted);font-family:inherit;
  font-size:13.5px;font-weight:600;padding:11px 15px;cursor:pointer;border-bottom:2px solid transparent;
  border-radius:8px 8px 0 0;transition:.15s}
.tab:hover{color:var(--ink);background:var(--panel)}
.tab.active{color:var(--gold);border-bottom-color:var(--gold)}
.tab .c{font-size:11px;background:var(--panel2);color:var(--muted);border-radius:999px;
  padding:1px 7px;margin-left:6px;font-weight:600}
.panel{display:none;animation:fade .25s ease}
.panel.active{display:block}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}

/* ---------- Graph ---------- */
.graph-wrap{display:grid;grid-template-columns:1fr 300px;gap:16px}
@media(max-width:860px){.graph-wrap{grid-template-columns:1fr}}
#graph{height:560px;background:
  radial-gradient(600px 300px at 50% 0%, rgba(86,197,181,.05),transparent),
  var(--bg2);border:1px solid var(--line);border-radius:var(--radius);position:relative}
.toolbar{position:absolute;top:12px;left:12px;display:flex;gap:6px;flex-wrap:wrap;z-index:4}
.tbtn{font-family:inherit;font-size:12px;font-weight:600;color:var(--muted);
  background:rgba(20,26,37,.9);border:1px solid var(--line2);border-radius:8px;
  padding:6px 10px;cursor:pointer;backdrop-filter:blur(6px)}
.tbtn:hover{color:var(--ink);border-color:var(--teal)}
.tbtn.on{color:var(--gold);border-color:var(--gold)}
.legend{position:absolute;bottom:12px;left:12px;display:flex;gap:12px;flex-wrap:wrap;
  background:rgba(20,26,37,.85);border:1px solid var(--line);border-radius:10px;
  padding:8px 12px;font-size:11.5px;color:var(--muted);backdrop-filter:blur(6px)}
.legend span{display:inline-flex;align-items:center;gap:5px}
.legend i{width:9px;height:9px;border-radius:50%}
.inspector{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:18px;min-height:200px}
.inspector h4{margin:0 0 4px;font-size:15px}
.inspector .ph{color:var(--dim);font-size:13px}
.inspector .row{display:flex;justify-content:space-between;gap:10px;font-size:12.5px;
  padding:7px 0;border-bottom:1px solid var(--line)}
.inspector .row .k{color:var(--muted)} .inspector .row .v{text-align:right;word-break:break-word}

/* ---------- Cards ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius-sm);
  padding:15px 16px;transition:.15s}
.card:hover{border-color:var(--line2);transform:translateY(-1px)}
.card.possible{border-style:dashed;border-color:#4a4226;background:
  linear-gradient(0deg,rgba(242,181,68,.04),transparent)}
.card .ct{display:flex;align-items:center;gap:8px;font-weight:600;font-size:14.5px}
.card .ct .em{font-size:16px}
.card .cu{font-family:var(--mono);font-size:12px;color:var(--muted);margin:6px 0 0;word-break:break-all}
.card .rows{margin-top:10px;font-size:12.5px}
.card .rows div{display:flex;justify-content:space-between;gap:10px;padding:3px 0}
.card .rows .k{color:var(--dim)} .card .rows .v{text-align:right;color:var(--ink);word-break:break-word}
.badge{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;
  padding:2px 8px;border-radius:999px;margin-left:auto}
.badge.ok{background:rgba(100,201,138,.14);color:var(--green)}
.badge.maybe{background:rgba(242,181,68,.14);color:var(--amber)}
.badge.breach{background:rgba(229,83,75,.16);color:var(--red)}
.group-h{display:flex;align-items:center;gap:10px;margin:22px 0 12px;font-size:13px;
  text-transform:uppercase;letter-spacing:.6px;color:var(--dim);font-weight:700}
.group-h::after{content:"";flex:1;height:1px;background:var(--line)}
.empty{color:var(--dim);font-size:13.5px;padding:30px;text-align:center;
  border:1px dashed var(--line);border-radius:var(--radius-sm)}

/* ---------- Limitations ---------- */
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--amber);
  border-radius:var(--radius-sm);padding:16px 18px;margin:0 0 14px}
.note h4{margin:0 0 8px;font-size:14.5px;color:var(--ink)}
.note ul{margin:0;padding-left:20px;color:var(--muted);font-size:13.5px}
.note li{margin:5px 0}
.foot{margin-top:40px;padding-top:20px;border-top:1px solid var(--line);
  color:var(--dim);font-size:12px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
.k-link{font-family:var(--mono);font-size:12px}
</style>
</head>
<body>
<header class="hero">
  <div class="hero-inner">
    <div class="brand"><span class="dot">🐺</span> OSINT Hound · Informe de recoleccion</div>
    <div class="expo {{EXPO_CLASS}}">
      <div class="lab">Exposicion</div>
      <div class="val">{{EXPO_LABEL}}</div>
      <div class="meter"><i style="width:{{EXPO_PCT}}%"></i></div>
    </div>
    <h1 class="h-title">{{TITLE}}</h1>
    <div class="h-sub">{{SUBTITLE}}</div>
    <div class="h-meta">{{HERO_CHIPS}}</div>
  </div>
</header>

<main class="wrap">
  <section class="tiles">{{STAT_TILES}}</section>

  <nav class="tabs">{{TABS_NAV}}</nav>
  {{TABS_CONTENT}}

  <div class="foot">
    <span>Generado por <b>OSINT Hound v{{VERSION}}</b> · {{GENERATED}}</span>
    <span class="k-link">Solo fuentes abiertas · uso etico y legal</span>
  </div>
</main>

<script>
const GRAPH = {{GRAPH_JSON}};
const META  = {{META_JSON}};

/* ---- Tabs ---- */
document.querySelectorAll('.tab').forEach(t=>{
  t.addEventListener('click',()=>{
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
    t.classList.add('active');
    document.getElementById('panel-'+t.dataset.tab).classList.add('active');
    if(t.dataset.tab==='grafo' && network) setTimeout(()=>network.fit(),50);
  });
});

/* ---- Graph (vis-network) ---- */
let network=null, physicsOn=true, treeMode=false;
function nodeTitle(n){
  let m=n.meta||{}; let s=n.label.replace(/^[^ ]+ /,'');
  return s;
}
function buildGraph(){
  if(typeof vis==='undefined'){ document.getElementById('graph').innerHTML=
    '<div class="empty" style="margin:40px">No se pudo cargar vis-network (sin conexion). '+
    'Los datos del grafo estan igualmente en el JSON exportado.</div>'; return; }
  const nodes=new vis.DataSet(GRAPH.nodes);
  const edges=new vis.DataSet(GRAPH.edges);
  const opts={
    nodes:{font:{color:'#e8edf5',size:13,face:'Inter'},borderWidth:1,
      scaling:{min:8,max:34}},
    edges:{font:{color:'#9db1c7',size:10,strokeWidth:0,face:'Inter'},
      smooth:{type:'continuous'},arrows:{to:{enabled:false}},width:1.2},
    physics:{enabled:true,barnesHut:{gravitationalConstant:-9000,springLength:140,
      springConstant:.04,damping:.5},stabilization:{iterations:180}},
    interaction:{hover:true,tooltipDelay:120,navigationButtons:false},
    layout:{improvedLayout:true}
  };
  network=new vis.Network(document.getElementById('graph'),{nodes,edges},opts);
  network.on('selectNode',p=>showNode(nodes.get(p.nodes[0])));
  network.on('deselectNode',clearNode);
}
function showNode(n){
  const box=document.getElementById('insp');
  let rows='';
  const m=n.meta||{};
  for(const k in m){
    let v=m[k]; if(v===null||v==='')continue;
    if(typeof v==='object') v=JSON.stringify(v);
    rows+=`<div class="row"><span class="k">${k}</span><span class="v">${v}</span></div>`;
  }
  const url=(m.url||'');
  box.innerHTML=`<h4>${n.label}</h4>`+
    `<div class="ph">${n.confidence==='possible'?'⚠ POSIBLE · pendiente de revision':'● Confirmado'} · ${n.type}</div>`+
    (url?`<div style="margin:8px 0"><a href="${url}" target="_blank" rel="noopener">${url}</a></div>`:'')+
    (rows||'<div class="ph" style="margin-top:10px">Sin metadatos adicionales.</div>');
}
function clearNode(){document.getElementById('insp').innerHTML=
  '<h4>Inspector</h4><div class="ph">Pulsa un nodo del grafo para ver sus metadatos, evidencias y el enlace a la fuente.</div>';}

function toggleTree(){
  treeMode=!treeMode;
  document.getElementById('b-tree').classList.toggle('on',treeMode);
  network.setOptions(treeMode?
    {layout:{hierarchical:{enabled:true,direction:'UD',sortMethod:'directed',
      levelSeparation:120,nodeSpacing:140}},physics:false}:
    {layout:{hierarchical:{enabled:false}},physics:{enabled:physicsOn}});
  setTimeout(()=>network.fit(),60);
}
function togglePhysics(){physicsOn=!physicsOn;
  document.getElementById('b-phys').classList.toggle('on',physicsOn);
  if(!treeMode)network.setOptions({physics:{enabled:physicsOn}});}
function fitGraph(){network.fit({animation:true});}
function exportPNG(){
  const c=document.querySelector('#graph canvas'); if(!c)return;
  const a=document.createElement('a'); a.download='osint_hound_grafo.png';
  a.href=c.toDataURL('image/png'); a.click();
}
function exportJSON(){
  const blob=new Blob([JSON.stringify({meta:META,graph:GRAPH},null,2)],
    {type:'application/json'});
  const a=document.createElement('a'); a.download='osint_hound_grafo.json';
  a.href=URL.createObjectURL(blob); a.click();
}
window.addEventListener('load',()=>{buildGraph();clearNode();});
</script>
</body>
</html>
"""
