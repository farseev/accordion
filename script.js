/* ============================================================================
   accordion.sg — site config + shop logic
   EDIT ONLY THIS BLOCK when links / numbers / prices change.
   ========================================================================== */

const SITE = {
  whatsapp: "6580000000",          // TODO: replace with the real A&G Academy WhatsApp number (digits only, country code first)
  email: "hello@accordion.sg",
  libraryUrl: "library.html",      // swap for the real Score Library host when it goes live
  youtube: "https://www.youtube.com/@AlexFarseev"
};

/* Stripe Payment Links — one per purchasable variant.
   Leave a value as null and the card falls back to a WhatsApp reservation
   enquiry instead of pretending a checkout exists. */
const STRIPE_LINKS = {
  "as-26-48-60-2b-48":         null,
  "as-26-48-60-2b-60":         null,
  "as-26-60-2a":               null,
  "hohner-bravo-26-48":        null,
  "hohner-bravo-26-60":        null,
  "as-34-60-2a":               null,
  "as-30-60-2a":               null,
  "as-34-60-3a":               null,
  "as-34-72-3b":               null,
  "hohner-bravo-34-72":        null,
  "as-37-80-3a":               null,
  "hohner-mycolor-34-72":      null,
  "hohner-bravo-34-80":        null,
  "hohner-bravo-34-96":        null,
  "hohner-bravo-41-120":       null
};

/* Catalogue. `variants` drive the on-card toggles; each variant carries its own
   price and its own Stripe key, so the toggle always buys the right thing. */
const CATALOGUE = [
  { id:"as-26-48-60-2b", img:"as-26-48-60-2b.jpg", brand:"Accordions Singapore", name:"26 / 48–60 / 2 / B", tier:"student",
    origin:"China", keys:"26 treble keys", bass:"48 or 60 bass buttons", reeds:"2 treble reeds · 3 registers",
    blurb:"The lightest instrument we sell. Choose the bass side below — it changes the weight, which matters more than anything else for a small player.",
    variants:[{label:"48 bass", price:1556, key:"as-26-48-60-2b-48"},
              {label:"60 bass", price:1556, key:"as-26-48-60-2b-60"}] },

  { id:"as-26-60-2a", img:"as-26-60-2a.jpg", brand:"Accordions Singapore", name:"26 / 60 / 2 / A", tier:"student",
    origin:"China", keys:"26 treble keys", bass:"60 bass buttons", reeds:"2 treble reeds · 3 registers",
    blurb:"Small enough for a seven-year-old to hold properly, honest enough to take a Grade 1–3 exam on.",
    variants:[{label:"60 bass", price:1617, key:"as-26-60-2a"}] },

  { id:"hohner-bravo-26", img:"hohner-bravo-26.jpg", brand:"Hohner", name:"Bravo 26", tier:"student",
    origin:"China", keys:"26 treble keys", bass:"48 or 60 bass buttons", reeds:"2 treble reeds · 3 registers",
    blurb:"Hohner's entry Bravo. Tell us the player's age and height and we'll tell you which bass side to take.",
    variants:[{label:"48 bass", price:2244, key:"hohner-bravo-26-48"},
              {label:"60 bass", price:2244, key:"hohner-bravo-26-60"}] },

  { id:"as-34-60-2a", img:"as-34-60-2a.jpg", brand:"Accordions Singapore", name:"34 / 60 / 2 / A", tier:"student",
    origin:"China", keys:"34 treble keys", bass:"60 bass buttons", reeds:"2 treble reeds · 3 registers",
    blurb:"Full-length keys on a two-reed body — more range than a 26 without the weight of a three-reed instrument.",
    variants:[{label:"60 bass", price:2489, key:"as-34-60-2a"}] },

  { id:"as-30-60-2a", img:"as-30-60-2a.jpg", brand:"Accordions Singapore", name:"30 / 60 / 2 / A", tier:"student",
    origin:"Korea", keys:"30 treble keys", bass:"60 bass buttons", reeds:"2 treble reeds · 3 registers",
    blurb:"Korean-built: noticeably quieter action and a rounder tone. Our usual recommendation for an adult beginner.",
    variants:[{label:"60 bass", price:2625, key:"as-30-60-2a"}] },

  { id:"as-34-60-3a", img:"as-34-60-3a.jpg", brand:"Accordions Singapore", name:"34 / 60 / 3 / A", tier:"intermediate",
    origin:"China", keys:"34 treble keys", bass:"60 bass buttons", reeds:"3 treble reeds · 5 registers",
    blurb:"A third reed and five registers — the first instrument that can colour a piece rather than just play it.",
    variants:[{label:"60 bass", price:2249, key:"as-34-60-3a"}] },

  { id:"as-34-72-3b", img:"as-34-72-3b.jpg", brand:"Accordions Singapore", name:"34 / 72 / 3 / B", tier:"intermediate",
    origin:"China", keys:"34 treble keys", bass:"72 bass buttons", reeds:"3 treble reeds · 5 registers",
    blurb:"Twelve extra bass buttons open up the keys most folk and tango arrangements actually sit in.",
    variants:[{label:"72 bass", price:2249, key:"as-34-72-3b"}] },

  { id:"hohner-bravo-34-72", img:"hohner-bravo-34-72.jpg", brand:"Hohner", name:"Bravo 34 / 72", tier:"intermediate",
    origin:"China", keys:"34 treble keys", bass:"72 bass buttons", reeds:"3 treble reeds · 5 registers · 2 bass registers",
    blurb:"The mid Bravo. Hohner reeds and a proper register set at a price that still makes sense for an exam student.",
    variants:[{label:"72 bass", price:2822, key:"hohner-bravo-34-72"}] },

  { id:"as-37-80-3a", img:"as-37-80-3a.jpg", brand:"Accordions Singapore", name:"37 / 80 / 3 / A", tier:"intermediate",
    origin:"Korea", keys:"37 treble keys", bass:"80 bass buttons", reeds:"3 treble reeds · 7 registers · 3 bass registers",
    blurb:"Korean-built, seven registers, 80 basses. Close to a full-size instrument but meaningfully lighter to stand with.",
    variants:[{label:"80 bass", price:3655, key:"as-37-80-3a"}] },

  { id:"hohner-mycolor-34-72", img:"hohner-mycolor-34-72.jpg", brand:"Hohner", name:"MyColor 34 / 72", tier:"intermediate",
    origin:"China", keys:"34 treble keys", bass:"72 bass buttons", reeds:"3 treble reeds · 5 registers · 2 bass registers",
    blurb:"The one students actually want to carry to class. Same Hohner voicing, finished in colour.",
    variants:[{label:"72 bass", price:3941, key:"hohner-mycolor-34-72"}] },

  { id:"hohner-bravo-34-80", img:"hohner-bravo-34-80.jpg", brand:"Hohner", name:"Bravo 34 / 80–96", tier:"advanced",
    origin:"China", keys:"34 treble keys", bass:"80 or 96 bass buttons", reeds:"3 treble reeds · 7 registers · 3 bass registers",
    blurb:"Seven treble registers and a full bass register set. The step where exam repertoire stops fighting you.",
    variants:[{label:"80 bass", price:4157, key:"hohner-bravo-34-80"},
              {label:"96 bass", price:4157, key:"hohner-bravo-34-96"}] },

  { id:"hohner-bravo-41-120", img:"hohner-bravo-41-120.jpg", brand:"Hohner", name:"Bravo 41 / 120", tier:"advanced",
    origin:"China", keys:"41 treble keys", bass:"120 bass buttons", reeds:"3 treble reeds · 7 registers · 3 bass registers",
    blurb:"Full-size, full bass. What you buy once, for conservatory study and paid work.",
    variants:[{label:"120 bass", price:4677, key:"hohner-bravo-41-120"}] }
];

/* ------------------------------------------------------------------ helpers */
const IMG_BASE = "images/products/";
const T = (k, fb) => {
  try{
    const L = (document.documentElement.lang||"en").split("-")[0];
    const D = window.ACCSG_I18N || {};
    return (D[L] && D[L][k]) || (D.en && D.en[k]) || fb;
  }catch(e){ return fb; }
};
const waLink = (msg) => `https://wa.me/${SITE.whatsapp}?text=${encodeURIComponent(msg)}`;
const sgd = (n) => n.toLocaleString("en-SG");

window.ACCSG_hydrateWhatsApp = function(){
  document.querySelectorAll("[data-wa]").forEach(a=>{
    a.href = waLink(a.getAttribute("data-wa"));
    a.rel = "noopener"; a.target = "_blank";
  });
};
const hydrateWhatsApp = window.ACCSG_hydrateWhatsApp;

/* --------------------------------------------------------------- shop build */
function cardHTML(p){
  const opts = p.variants.map((v,i)=>
    `<button class="opt${i===0?" on":""}" data-i="${i}" type="button">${v.label}</button>`).join("");
  const showOpts = p.variants.length > 1;
  return `<article class="prod" data-id="${p.id}" data-tier="${p.tier}">
    <div class="top">
      <span class="tier">${p.tier}</span>
      ${p.img ? `<img class="shot" src="${IMG_BASE}${p.img}" alt="${p.brand} ${p.name} piano accordion"
          loading="lazy" onerror="this.parentNode.classList.add('noshot');this.remove()">`
              : ""}
      <div class="glyph">&#127900;</div>
      <div class="brand">${p.brand} · made in ${p.origin}</div>
      <h3>${p.name}</h3>
    </div>
    <div class="body">
      <p style="font-size:.92rem;color:#4a4854">${p.blurb}</p>
      <ul class="specs">
        <li><span>Treble</span><span>${p.keys}</span></li>
        <li><span>Bass</span><span>${p.bass}</span></li>
        <li><span>Reeds</span><span>${p.reeds}</span></li>
      </ul>
      ${showOpts ? `<div class="optlabel">${T("shop.bass","Choose your bass side")}</div><div class="opts">${opts}</div>` : ""}
      <div class="priceline"><span class="price">$<span class="pval">${sgd(p.variants[0].price)}</span></span><span class="cur">SGD</span></div>
      <div class="buyrow">
        <a class="btn prim buy" href="#"></a>
        <a class="btn ask" href="#" data-wa=""></a>
      </div>
      <div class="note"></div>
    </div>
  </article>`;
}

function syncCard(card, p){
  const i = +(card.querySelector(".opt.on")?.dataset.i ?? 0);
  const v = p.variants[i];
  card.querySelector(".pval").textContent = sgd(v.price);

  const link = STRIPE_LINKS[v.key];
  const buy  = card.querySelector(".buy");
  const note = card.querySelector(".note");
  const label = `${p.brand} ${p.name} (${v.label})`;

  if (link){
    buy.href = link; buy.target = "_blank"; buy.rel = "noopener";
    buy.textContent = T("shop.buy","Buy now");
    note.textContent = T("shop.secure","Secure checkout by Stripe · free delivery in Singapore");
  } else {
    buy.href = waLink(`Hi A&G Academy — I'd like to reserve the ${label} at S$${sgd(v.price)}.`);
    buy.target = "_blank"; buy.rel = "noopener";
    buy.textContent = T("shop.reserve","Reserve on WhatsApp");
    note.textContent = T("shop.pending","Card checkout for this model is being set up — reserve it and we'll send a payment link.");
  }
  const ask = card.querySelector(".ask");
  ask.textContent = T("shop.ask","Ask first");
  ask.href = waLink(`Hi A&G Academy — a question about the ${label}, please.`);
}

function buildShop(host){
  if(!host) return;
  host.innerHTML = CATALOGUE.map(cardHTML).join("");

  CATALOGUE.forEach(p=>{
    const card = host.querySelector(`[data-id="${p.id}"]`);
    card.querySelectorAll(".opt").forEach(b=>b.addEventListener("click",()=>{
      card.querySelectorAll(".opt").forEach(x=>x.classList.remove("on"));
      b.classList.add("on"); syncCard(card,p);
    }));
    syncCard(card,p);
  });

  const tiers = host.parentNode.querySelector("#tiers,.tiers");
  if(tiers) tiers.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{
    tiers.querySelectorAll("button").forEach(x=>x.classList.remove("on"));
    b.classList.add("on");
    const tv = b.dataset.tier;
    host.querySelectorAll(".prod").forEach(c=>{
      c.style.display = (tv==="all" || c.dataset.tier===tv) ? "" : "none";
    });
  }));
}

/* ------------------------------------------------- click-to-load YouTube */
function lazyVideos(){
  document.querySelectorAll(".vid[data-yt]").forEach(box=>{
    box.addEventListener("click",()=>{
      const id = box.dataset.yt;
      box.innerHTML = `<iframe src="https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0"
        title="accordion.sg performance" allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture"
        allowfullscreen></iframe>`;
    });
  });
}

function buildAllShops(){ document.querySelectorAll("#shop,.shopgrid").forEach(h=>{ if(!h.dataset.built){h.dataset.built="1"; buildShop(h);} }); }
function relabelShops(){ document.querySelectorAll("#shop,.shopgrid").forEach(host=>{
  host.querySelectorAll(".prod").forEach(card=>{
    const p = CATALOGUE.find(x=>x.id===card.dataset.id); if(p) syncCard(card,p);
    const ol = card.querySelector(".optlabel"); if(ol) ol.textContent = T("shop.bass","Choose your bass side");
  });
}); }
document.addEventListener("accsg:lang", relabelShops);
document.addEventListener("DOMContentLoaded",()=>{ window.ACCSG_hydrateWhatsApp(); buildAllShops(); lazyVideos(); });

/* blog category filter */
document.addEventListener("DOMContentLoaded",()=>{
  const segs=document.querySelectorAll("#cats,.seg.cats"); if(!segs.length) return;
  const q=new URLSearchParams(location.search).get("c");
  segs.forEach(seg=>{
    const posts=seg.parentNode.querySelector("#posts,.posts");
    const apply=(c)=>{ if(!posts) return;
      posts.querySelectorAll(".post").forEach(p=>{p.style.display=(c==="all"||p.dataset.cat===c)?"":"none";}); };
    seg.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{
      seg.querySelectorAll("button").forEach(x=>x.classList.remove("on"));
      b.classList.add("on"); apply(b.dataset.cat);
      const u=new URL(location.href);
      if(b.dataset.cat==="all") u.searchParams.delete("c"); else u.searchParams.set("c",b.dataset.cat);
      history.replaceState(null,"",u);
    }));
    if(q){const b=seg.querySelector('[data-cat="'+q+'"]'); if(b) b.click();}
  });
});

/* mobile menu */
document.addEventListener("DOMContentLoaded",()=>{
  const b=document.getElementById("burger"), n=document.getElementById("navlinks");
  if(!b||!n) return;
  b.addEventListener("click",()=>{
    const open=n.classList.toggle("open");
    b.classList.toggle("on",open);
    b.setAttribute("aria-expanded",open?"true":"false");
  });
  n.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>{
    n.classList.remove("open"); b.classList.remove("on"); b.setAttribute("aria-expanded","false");
  }));
});


/* ============================================================================
   Language runtime — every page carries all seven languages in one file.
   ?lang=xx on the URL wins; otherwise the last choice, then the browser's.
   ========================================================================== */
(function(){
  var I18N   = window.ACCSG_I18N   || {};
  var META   = window.ACCSG_META   || {title:{},desc:{}};
  var LANGS  = window.ACCSG_LANGS  || [["en","en","English"]];
  var ALIAS  = window.ACCSG_ALIAS  || {};        // lang -> lang whose block it shares
  var RELOAD = window.ACCSG_RELOAD_ON_LANG === true;
  var KEYS   = LANGS.map(function(x){return x[0];});
  var CODE   = {}; LANGS.forEach(function(x){CODE[x[0]]=x[1];});
  var KEY    = "accsg.lang";

  function store(v){ try{ localStorage.setItem(KEY,v); }catch(e){} }
  function recall(){ try{ return localStorage.getItem(KEY); }catch(e){ return null; } }

  function pick(){
    var q = new URLSearchParams(location.search).get("lang");
    if(q && KEYS.indexOf(q)>=0) return q;
    var s = recall();
    if(s && KEYS.indexOf(s)>=0) return s;
    var nav = (navigator.languages||[navigator.language||"en"]);
    for(var i=0;i<nav.length;i++){
      var n = String(nav[i]).toLowerCase();
      if(n.indexOf("zh")===0) return KEYS.indexOf("zh")>=0?"zh":"en";
      var base = n.split("-")[0];
      if(KEYS.indexOf(base)>=0) return base;
    }
    return "en";
  }

  function apply(lang, push){
    if(KEYS.indexOf(lang)<0) lang="en";
    var shown = ALIAS[lang] || lang;              // fall back to a shared block

    document.documentElement.lang = CODE[lang] || lang;

    /* the visible content block */
    var blocks = document.querySelectorAll(".lx");
    if(blocks.length){
      var hit=false;
      blocks.forEach(function(b){
        var on = b.getAttribute("data-l")===shown;
        b.hidden = !on; if(on) hit=true;
      });
      if(!hit) blocks.forEach(function(b){ b.hidden = b.getAttribute("data-l")!=="en"; });
    }

    /* articles: split the active block into hero (h1+lead) and body */
    if(window.ACCSG_SPLIT_ARTICLE){
      var host=document.getElementById("artbody");
      var act=document.querySelector('.arthead .lx[data-l="'+shown+'"]')||document.querySelector('.arthead .lx');
      if(host&&act){
        host.innerHTML="";
        var kids=[].slice.call(act.children);
        kids.forEach(function(n,i){ if(i>1) host.appendChild(n); });
        act.hidden=false;
      }
    }

    /* chrome: nav, footer, labels */
    var dict = I18N[lang] || I18N.en || {};
    document.querySelectorAll("[data-t]").forEach(function(el){
      var k = el.getAttribute("data-t");
      var v = dict[k] || (I18N.en||{})[k];
      if(v!=null) el.textContent = v;
    });
    /* WhatsApp drafts */
    document.querySelectorAll("[data-wa-t]").forEach(function(el){
      var k = el.getAttribute("data-wa-t");
      var v = dict[k] || (I18N.en||{})[k];
      if(v!=null) el.setAttribute("data-wa", v);
    });
    if(window.ACCSG_hydrateWhatsApp) window.ACCSG_hydrateWhatsApp();

    /* title + description */
    if(META.title && META.title[lang]){
      var d=document.createElement("textarea"); d.innerHTML=META.title[lang];
      document.title = d.value;
    }
    if(META.desc && META.desc[lang]){
      var m=document.querySelector('meta[name="description"]');
      var d2=document.createElement("textarea"); d2.innerHTML=META.desc[lang];
      if(m) m.setAttribute("content", d2.value);
    }

    var sel = document.getElementById("langsel");
    if(sel && sel.value!==lang) sel.value = lang;

    store(lang);
    if(push){
      var u = new URL(location.href);
      if(lang==="en") u.searchParams.delete("lang"); else u.searchParams.set("lang",lang);
      history.replaceState(null,"",u);
    }
    document.dispatchEvent(new CustomEvent("accsg:lang",{detail:{lang:lang}}));
  }

  function init(){
    var lang = pick();
    apply(lang, false);
    var sel = document.getElementById("langsel");
    if(sel) sel.addEventListener("change", function(){
      var v = sel.value;
      if(RELOAD){                      /* the Score Library builds itself once */
        store(v);
        var u = new URL(location.href); u.searchParams.set("lang", v);
        location.href = u.toString(); return;
      }
      apply(v, true);
    });
    /* internal links keep the language without needing a query string
       (localStorage carries it), so nothing to rewrite. */
  }

  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",init);
  else init();

  window.ACCSG_setLang = function(l){ apply(l,true); };
})();
