(function(){

"use strict";
var root=document.getElementById('accsg-lib');
/* Data is base64 (only A-Za-z0-9+/=) so page builders that "clean up"
   typography (smart quotes, dashes, stripped backslashes) cannot corrupt it. */
function accsgDecode(b64){
  var re=new RegExp('[^A-Za-z0-9+/=]','g');
  var clean=String(b64).replace(re,'');
  var bin=atob(clean);
  var by=new Uint8Array(bin.length);
  for(var i=0;i<bin.length;i++){by[i]=bin.charCodeAt(i);}
  return new TextDecoder('utf-8').decode(by);
}
var LIB=window.ACCSG_DATA;
var $=function(s){return root.querySelector(s)};
var el=function(t,c){var e=document.createElement(t);if(c)e.className=c;return e};
var PDFBASE=(window.ACCSG_PDFBASE||'accordion_pdfs/');
var LANGS=['en','ru','zh','ja','ko','ms','ta'];
/* diacritic-insensitive fold for search: e.g. csárdás->csardas, malagueña->malaguena */
function fold(x){return String(x).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');}
/* mode = how results are GROUPED; f = facet filters that ALL apply together
   (OR within a facet, AND across facets); letter = composer-initial filter. */
var state={lang:(window.ACCSG_LANG||'en'),mode:'composer',letter:null,q:'',sort:1,f:{genre:[],grade:[],bass:[],ensemble:[]}};

// pdf.js worker
if(window.pdfjsLib){try{pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';}catch(e){}}

// precompute -- searchable blob is diacritic-folded and now also carries the
// genre / grade / bass labels (all languages) so category words like
// "waltz", "tango", "free bass", "diploma", "grade 5" return results.
LIB.scores.forEach(function(s){
  var tr=LIB.titles[s.title_ru]||{};
  var p=[s.title_ru,s.composer,s.file.replace(/[_.]/g,' '),s.genre,s.grade,s.bass];
  LANGS.forEach(function(l){if(l!=='ru'&&tr[l])p.push(tr[l]);});
  LANGS.forEach(function(l){var d=LIB.i18n[l]||{};
    if(d['g_'+s.genre])p.push(d['g_'+s.genre]);
    var gk=/^[0-9]+$/.test(s.grade)?('grade_'+s.grade):('tier_'+s.grade);
    if(d[gk])p.push(d[gk]);
    if(d['bass_'+s.bass])p.push(d['bass_'+s.bass]);
  });
  s._blob=fold(p.join(' ')); s._tr=tr;
});

function T(k){return (LIB.i18n[state.lang]&&LIB.i18n[state.lang][k])||LIB.i18n.en[k]||k;}
function titleOf(s){return state.lang==='ru'?s.title_ru:(s._tr[state.lang]||s.title_ru);}
function genreLabel(g){return T('g_'+g)||g;}
function isNum(g){return /^[0-9]+$/.test(g);}
function gradeLabel(g){return isNum(g)?T('grade_'+g):T('tier_'+g);}
function gradeClass(g){return 'g-'+g;}
function bassLabel(b){return T('bass_'+b);}
function ensLabel(e){return T('ens_'+e);}
function bandKey(g){if(!isNum(g))return null;var n=+g;return n<=3?'band_foundation':n<=6?'band_intermediate':'band_advanced';}

/* ---------- thumbnail engine (lazy, best-effort, cached) ---------- */
var thumbCache={}; var thumbFail={}; var queue=[]; var active=0; var MAXC=3;
var io=('IntersectionObserver' in window)?new IntersectionObserver(function(ents){
  ents.forEach(function(en){ if(en.isIntersecting){ io.unobserve(en.target); enqueue(en.target); } });
},{rootMargin:'300px'}):null;

function enqueue(coverEl){ queue.push(coverEl); pump(); }
function pump(){
  while(active<MAXC && queue.length){
    var c=queue.shift(); if(!c||!c.isConnected) continue;
    var file=c.getAttribute('data-file');
    if(thumbCache[file]){ paintThumb(c,thumbCache[file]); continue; }
    if(thumbFail[file]||!window.pdfjsLib){ continue; } /* keep clean placeholder */
    active++; renderThumb(c,file);
  }
}
function paintThumb(c,dataURL){
  if(c.querySelector('img'))return;
  var img=new Image(); img.src=dataURL; img.alt='';
  c.insertBefore(img,c.firstChild);
  var ph=c.querySelector('.ph'); if(ph)ph.style.display='none';
  var sp=c.querySelector('.spin'); if(sp)sp.remove();
}
function renderThumb(c,file){
  if(!c.querySelector('.spin')){var sp=el('div','spin');sp.innerHTML='<div class="ldr"></div>';c.appendChild(sp);}
  var url=PDFBASE+file;
  var task=pdfjsLib.getDocument({url:url});
  task.promise.then(function(pdf){return pdf.getPage(1);}).then(function(page){
    var vp=page.getViewport({scale:1});
    var scale=460/vp.width; var v=page.getViewport({scale:scale});
    var cv=document.createElement('canvas'); cv.width=v.width; cv.height=v.height;
    return page.render({canvasContext:cv.getContext('2d'),viewport:v}).promise.then(function(){
      try{thumbCache[file]=cv.toDataURL('image/jpeg',0.72);}catch(e){thumbCache[file]=cv.toDataURL();}
      paintThumb(c,thumbCache[file]);
    });
  }).catch(function(){ thumbFail[file]=1; var sp=c.querySelector('.spin'); if(sp)sp.remove();
  }).then(function(){ active--; pump(); });
}

/* ---------- language ---------- */
function buildLangMenu(){
  var m=$('#accsg-langMenu'); m.innerHTML='';
  LANGS.forEach(function(l){
    var b=el('button'); b.textContent=LIB.i18n[l].lang_name; if(l===state.lang)b.className='on';
    b.onclick=function(){setLang(l);$('#accsg-langWrap').classList.remove('open');};
    m.appendChild(b);
  });
}
$('#accsg-langBtn').onclick=function(e){e.stopPropagation();var w=$('#accsg-langWrap');var o=w.classList.toggle('open');$('#accsg-langBtn').setAttribute('aria-expanded',o);};
document.addEventListener('click',function(){$('#accsg-langWrap').classList.remove('open');if(openFacet!==null){openFacet=null;buildFacets();}});
$('#accsg-langMenu').onclick=function(e){e.stopPropagation();};
function setLang(l){
  state.lang=l; $('#accsg-langCur').textContent=LIB.i18n[l].lang_name;
  root.querySelectorAll('[data-i]').forEach(function(n){n.textContent=T(n.getAttribute('data-i'));});
  $('#accsg-q').placeholder=T('search_ph');
  $('#accsg-sortLab').textContent=state.sort===1?T('az'):T('za');
  buildLangMenu(); buildFacets(); renderChips(); renderPills(); renderNote(); render();
}

/* ---------- stats ---------- */
$('#accsg-sTotal').textContent=LIB.meta.total;
$('#accsg-sComp').textContent=LIB.meta.composers;
$('#accsg-sGen').textContent=LIB.meta.genres;

/* ---------- controls ---------- */
function applyChange(){buildFacets();renderChips();renderPills();renderNote();render();}

root.querySelectorAll('#accsg-seg button').forEach(function(b){
  b.onclick=function(){root.querySelectorAll('#accsg-seg button').forEach(function(x){x.classList.remove('on');});b.classList.add('on');state.mode=b.dataset.mode;applyChange();};
});
$('#accsg-sortBtn').onclick=function(){state.sort*=-1;$('#accsg-sortLab').textContent=state.sort===1?T('az'):T('za');render();};
var qEl=$('#accsg-q');
qEl.addEventListener('input',function(){state.q=fold(qEl.value.trim());$('#accsg-searchWrap').classList.toggle('has',state.q.length>0);buildFacets();renderPills();render();});
$('#accsg-qx').onclick=function(){qEl.value='';state.q='';$('#accsg-searchWrap').classList.remove('has');buildFacets();renderPills();render();qEl.focus();};

/* ----- faceted filters: Genre + Grade + Bass all apply together ----- */
function FACETS(){return [
  {key:'genre', order:LIB.genreOrder, label:genreLabel, kind:'genre'},
  {key:'grade', order:LIB.gradeOrder, label:gradeLabel, kind:'grade'},
  {key:'bass',  order:LIB.bassOrder,  label:bassLabel,  kind:'bass'},
  {key:'ensemble', order:LIB.ensembleOrder, label:ensLabel, kind:'ensemble'}
];}
function facetTitle(k){return k==='genre'?T('tab_genre'):k==='grade'?T('tab_difficulty'):k==='ensemble'?T('tab_ensemble'):T('tab_bass');}
function matchFacet(s,key){var a=state.f[key];return !a.length||a.indexOf(s[key])>=0;}
function passExcept(s,exceptKey){
  if(state.q&&s._blob.indexOf(state.q)<0)return false;
  if(exceptKey!=='genre'&&!matchFacet(s,'genre'))return false;
  if(exceptKey!=='grade'&&!matchFacet(s,'grade'))return false;
  if(exceptKey!=='bass'&&!matchFacet(s,'bass'))return false;
  if(exceptKey!=='ensemble'&&!matchFacet(s,'ensemble'))return false;
  if(state.letter&&s.composer.charAt(0).toUpperCase()!==state.letter)return false;
  return true;
}
function passFilter(s){return passExcept(s,null);}
function facetCount(key,v){return LIB.scores.filter(function(s){return passExcept(s,key)&&s[key]===v;}).length;}
function anyFilter(){return state.f.genre.length||state.f.grade.length||state.f.bass.length||state.letter;}
function clearAll(){state.f={genre:[],grade:[],bass:[],ensemble:[]};state.letter=null;openFacet=null;applyChange();}

var openFacet=null;
function buildFacets(){
  var bar=$('#accsg-facets'); bar.innerHTML='';
  var lab=el('span','flabel'); lab.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 5h18M6 12h12M10 19h4"/></svg><span>'+T('filter_by')+'</span>'; bar.appendChild(lab);
  FACETS().forEach(function(fc){
    var sel=state.f[fc.key];
    var wrap=el('div','facet'); if(openFacet===fc.key)wrap.classList.add('open');
    var btn=el('button','facet-btn'+(sel.length?' act':''));
    var t=el('span'); t.textContent=facetTitle(fc.key); btn.appendChild(t);
    if(sel.length){var ct=el('span','fct');ct.textContent=sel.length;btn.appendChild(ct);}
    var chev=el('span'); chev.innerHTML=ICON_CHEV; btn.appendChild(chev.firstChild);
    btn.onclick=function(e){e.stopPropagation();openFacet=(openFacet===fc.key?null:fc.key);buildFacets();};
    wrap.appendChild(btn);
    var menu=el('div','facet-menu'); menu.onclick=function(e){e.stopPropagation();};
    fc.order.forEach(function(v){
      var cnt=facetCount(fc.key,v); var on=sel.indexOf(v)>=0;
      if(cnt===0&&!on)return;
      var o=el('button','opt'+(on?' on':''));
      var box=el('span','box'); box.innerHTML=ICON_CHECK; o.appendChild(box);
      if(fc.kind==='grade'){var dot=el('span','dot '+gradeClass(v));o.appendChild(dot);}
      if(fc.kind==='bass'){var ic=el('span','ico');ic.innerHTML=bassIcon(v);o.appendChild(ic);}
      var nm=el('span','onm'); nm.textContent=fc.label(v); o.appendChild(nm);
      var oc=el('span','oct'); oc.textContent=cnt; o.appendChild(oc);
      o.onclick=function(e){e.stopPropagation();var i=sel.indexOf(v);if(i>=0)sel.splice(i,1);else sel.push(v);buildFacets();renderPills();renderNote();render();};
      menu.appendChild(o);
    });
    if(sel.length){var fx=el('button','fclear');fx.textContent=T('clear_all');fx.onclick=function(e){e.stopPropagation();state.f[fc.key]=[];buildFacets();renderPills();renderNote();render();};menu.appendChild(fx);}
    wrap.appendChild(menu);
    bar.appendChild(wrap);
  });
  if(anyFilter()){var ca=el('button','clearall');ca.textContent=T('clear_all');ca.onclick=function(e){e.stopPropagation();clearAll();};bar.appendChild(ca);}
}

/* composer A-Z rail -- shown only under composer grouping */
function renderChips(){
  var c=$('#accsg-chips'); c.innerHTML='';
  if(state.mode!=='composer')return;
  var letters=[];LIB.composers.forEach(function(x){var L=x.charAt(0).toUpperCase();if(letters.indexOf(L)<0)letters.push(L);});letters.sort();
  var all=el('button','chip'+(state.letter===null?' on':''));all.textContent=T('all_composers');all.onclick=function(){state.letter=null;renderChips();renderPills();buildFacets();render();};c.appendChild(all);
  letters.forEach(function(L){var b=el('button','chip alpha'+(state.letter===L?' on':''));b.textContent=L;b.onclick=function(){state.letter=(state.letter===L?null:L);renderChips();renderPills();buildFacets();render();};c.appendChild(b);});
}

/* active-filter pills (removable) */
function renderPills(){
  var p=$('#accsg-pills'); p.innerHTML='';
  function pill(kindLabel,text,extra,onRemove){
    var pl=el('span','pill'); if(extra)pl.appendChild(extra);
    if(kindLabel){var k=el('span','pk');k.textContent=kindLabel;pl.appendChild(k);}
    var t=el('span');t.textContent=text;pl.appendChild(t);
    var x=el('button','px');x.setAttribute('aria-label','remove');x.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M6 6l12 12M18 6L6 18"/></svg>';x.onclick=onRemove;pl.appendChild(x);
    p.appendChild(pl);
  }
  state.f.genre.forEach(function(v){pill(T('tab_genre'),genreLabel(v),null,function(){rm('genre',v);});});
  state.f.grade.forEach(function(v){var d=el('span','dot '+gradeClass(v));pill(T('tab_difficulty'),gradeLabel(v),d,function(){rm('grade',v);});});
  state.f.bass.forEach(function(v){var ic=el('span');ic.style.cssText='display:inline-flex;width:12px;height:12px';ic.innerHTML=bassIcon(v);pill(T('tab_bass'),bassLabel(v),ic,function(){rm('bass',v);});});
  state.f.ensemble.forEach(function(v){pill(T('tab_ensemble'),ensLabel(v),null,function(){rm('ensemble',v);});});
  if(state.letter){pill(T('tab_composer'),state.letter,null,function(){state.letter=null;renderChips();renderPills();buildFacets();render();});}
}
function rm(key,v){var a=state.f[key];var i=a.indexOf(v);if(i>=0)a.splice(i,1);buildFacets();renderPills();renderNote();render();}

/* contextual note under the filters */
function renderNote(){
  var note=$('#accsg-diffNote');
  if(state.mode==='difficulty'||state.f.grade.length){note.style.display='flex';note.querySelector('span').textContent=T('diff_note');}
  else if(state.mode==='bass'||state.f.bass.length){note.style.display='flex';note.querySelector('span').textContent=T('bass_note');}
  else{note.style.display='none';}
}
function groupKey(s){return state.mode==='genre'?s.genre:state.mode==='difficulty'?s.grade:state.mode==='bass'?s.bass:state.mode==='ensemble'?s.ensemble:s.composer;}
function groupOrder(){if(state.mode==='genre')return LIB.genreOrder.slice();if(state.mode==='difficulty')return LIB.gradeOrder.slice();if(state.mode==='bass')return LIB.bassOrder.slice();if(state.mode==='ensemble')return LIB.ensembleOrder.slice();var cs=LIB.composers.slice();if(state.sort===-1)cs.reverse();return cs;}
function groupTitle(k){return state.mode==='genre'?genreLabel(k):state.mode==='difficulty'?gradeLabel(k):state.mode==='bass'?bassLabel(k):state.mode==='ensemble'?ensLabel(k):k;}

/* ---------- cards ---------- */
var ICON_DL='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v12M7 11l5 5 5-5M5 21h14"/></svg>';
var ICON_CLOCK='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>';
var ICON_EYE='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>';
/* bass-type glyphs: standard = stacked chord (3 dots), free = single note */
var ICON_STD='<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><circle cx="12" cy="6" r="2.3"/><circle cx="12" cy="12" r="2.3"/><circle cx="12" cy="18" r="2.3"/></svg>';
var ICON_FREE='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="8" cy="17" r="3.2" fill="currentColor" stroke="none"/><path d="M11 17V5l7-2v10"/></svg>';
function bassIcon(b){return b==='free'?ICON_FREE:ICON_STD;}
var ICON_PLAY='<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M8 5v14l11-7z"/></svg>';
var ICON_CHECK='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M5 12l5 5L20 6"/></svg>';
var ICON_CHEV='<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M6 9l6 6 6-6"/></svg>';
/* True cross-origin download. scores.accordion.sg sends Access-Control-Allow-Origin:*
   but no Content-Disposition, so a plain <a download> only *opens* the PDF cross-origin.
   Fetching it as a blob and saving via an object URL forces a real file download;
   if the fetch fails for any reason we fall back to opening it in a new tab. */
function downloadScore(s,btn){
  if(!s||!s.available)return;
  var name=(s.file||'score.pdf').split('/').pop();
  if(btn)btn.classList.add('busy');
  function done(){if(btn)btn.classList.remove('busy');}
  fetch(s.download,{mode:'cors'}).then(function(r){if(!r.ok)throw 0;return r.blob();}).then(function(b){
    var u=URL.createObjectURL(b);var a=document.createElement('a');a.href=u;a.download=name;
    document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(u);},4000);
    done();
  }).catch(function(){window.open(s.download,'_blank','noopener');done();});
}
function cover(s){
  var c=el('div','cover'+(s.available?'':' na')); c.setAttribute('data-file',s.file);
  var ph=el('div','ph');
  for(var i=0;i<4;i++){var st=el('div','staff');ph.appendChild(st);}
  var gl=el('div','glyph'); gl.innerHTML='&#119070;'; ph.appendChild(gl);
  c.appendChild(ph);
  if(s.available){
    var z=el('div','zoom'); z.innerHTML='<span>'+ICON_EYE+T('preview')+'</span>'; c.appendChild(z);
  }else{
    var na=el('div','natag'); na.innerHTML=ICON_CLOCK+'<span>'+T('unavailable')+'</span>'; c.appendChild(na);
  }
  var gb=el('div','gtag '+gradeClass(s.grade)); gb.textContent=gradeLabel(s.grade); c.appendChild(gb);
  if(s.yt){var vb=el('div','vbadge');vb.innerHTML=ICON_PLAY+'<span>'+T('listen')+'</span>';vb.title=T('video_hint');vb.onclick=function(e){e.stopPropagation();openYT(s);};c.appendChild(vb);}
  if(s.available){
    c.onclick=function(){openModal(s);};
    if(io)io.observe(c); else enqueue(c); /* only fetch thumbnails for files that exist */
  }
  return c;
}
function card(s){
  var d=el('div','card');
  d.appendChild(cover(s));
  var b=el('div','cbody');
  var tt=el('div','ttl');tt.textContent=titleOf(s);b.appendChild(tt);
  if(state.lang!=='ru'){var o=el('div','orig');o.textContent=s.title_ru;b.appendChild(o);}
  if(state.mode!=='composer'){var by=el('div','by');by.textContent=s.composer;b.appendChild(by);}
  var tags=el('div','tags');
  var gt=el('span','tag genre');gt.textContent=genreLabel(s.genre);tags.appendChild(gt);
  var bt=el('span','tag bass');bt.innerHTML=bassIcon(s.bass);var bl=el('span');bl.textContent=bassLabel(s.bass);bt.appendChild(bl);tags.appendChild(bt);
  b.appendChild(tags);
  var f=el('div','cfoot');
  if(s.available){
    var pv=el('button','btn prim');pv.innerHTML=ICON_EYE+'<span>'+T('preview')+'</span>';pv.onclick=function(){openModal(s);};f.appendChild(pv);
    var dl=el('button','btn');dl.innerHTML=ICON_DL+'<span>'+T('download')+'</span>';dl.onclick=function(){downloadScore(s,dl);};f.appendChild(dl);
  }else{
    var na=el('div','btn na');na.innerHTML=ICON_CLOCK+'<span>'+T('unavailable')+'</span>';f.appendChild(na);
  }
  if(s.yt){var ls=el('button','btn listen');ls.innerHTML=ICON_PLAY+'<span>'+T('listen')+'</span>';ls.onclick=function(){openYT(s);};f.appendChild(ls);}
  b.appendChild(f);
  d.appendChild(b);
  return d;
}
function render(){
  var res=$('#accsg-results'); res.innerHTML='';
  var items=LIB.scores.filter(passFilter);
  var groups={}; items.forEach(function(s){var k=groupKey(s);(groups[k]=groups[k]||[]).push(s);});
  var order=groupOrder().filter(function(k){return groups[k]&&groups[k].length;});
  order.forEach(function(k){
    var arr=groups[k];
    arr.sort(function(a,b){var A=titleOf(a).toLowerCase(),B=titleOf(b).toLowerCase();return A<B?-1*state.sort:A>B?1*state.sort:0;});
    var g=el('div','group');
    var h=el('div','ghead');
    if(state.mode==='difficulty'){var bd=el('span','gbadge '+gradeClass(k));h.appendChild(bd);}
    if(state.mode==='bass'){var bi=el('span','gbadge');bi.style.cssText='display:inline-flex;width:17px;height:17px;color:var(--lav)';bi.innerHTML=bassIcon(k);h.appendChild(bi);}
    var h3=el('h3');h3.textContent=groupTitle(k);h.appendChild(h3);
    if(state.mode==='difficulty'){var bk=bandKey(k);if(bk){var bn=el('span','gband');bn.textContent=T(bk);h.appendChild(bn);}}
    var gc=el('span','gc');gc.textContent=arr.length;h.appendChild(gc);
    g.appendChild(h);
    var grid=el('div','grid');
    arr.forEach(function(s){grid.appendChild(card(s));});
    g.appendChild(grid); res.appendChild(g);
  });
  var n=items.length;
  var unit=state.mode==='composer'?T('composers_word'):state.mode==='genre'?T('genres_word'):state.mode==='bass'?T('bass_label'):state.mode==='ensemble'?T('ensemble_label'):T('level_label');
  $('#accsg-resCount').textContent = n===0?'':((n===1?T('one_score'):T('n_scores').replace('{n}',n))+' · '+order.length+' '+unit);
  if(n===0){
    var e=el('div','empty');
    e.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg><p>'+T('no_results')+'</p>';
    var btn=el('button');btn.textContent=T('clear');btn.onclick=function(){qEl.value='';state.q='';$('#accsg-searchWrap').classList.remove('has');clearAll();};
    e.appendChild(btn); res.appendChild(e);
  }
}

/* ---------- modal ---------- */
var modal=$('#accsg-modal'),mView=$('#accsg-mView');
function openModal(s){
  $('#accsg-mTitle').textContent=titleOf(s);
  $('#accsg-mOrig').textContent=(state.lang!=='ru'?s.title_ru:'');
  $('#accsg-mBy').textContent=s.composer;
  var mm=$('#accsg-mMeta'); mm.innerHTML='';
  var mg=el('span','mb '+gradeClass(s.grade)); mg.textContent=gradeLabel(s.grade); mm.appendChild(mg);
  var mgn=el('span','mb genre'); mgn.textContent=genreLabel(s.genre); mm.appendChild(mgn);
  var mba=el('span','mb bass'); mba.innerHTML=bassIcon(s.bass); var mbl=el('span'); mbl.textContent=bassLabel(s.bass); mba.appendChild(mbl); mm.appendChild(mba);
  $('#accsg-mDl').href=s.download; $('#accsg-mOpen').href=s.download;
  $('#accsg-mDl').onclick=function(e){e.preventDefault();downloadScore(s,$('#accsg-mDl'));};
  mView.innerHTML='<div class="mspin"><div class="ldr"></div><span>'+T('loading')+'</span></div>';
  var ifr=document.createElement('iframe');
  ifr.setAttribute('title','PDF preview');
  ifr.onload=function(){var sp=mView.querySelector('.mspin');if(sp)sp.remove();};
  ifr.src=s.download+'#view=FitH&toolbar=1';
  mView.appendChild(ifr);
  modal.classList.add('open');
  document.documentElement.style.overflow='hidden';
}
function closeModal(){modal.classList.remove('open');mView.innerHTML='';document.documentElement.style.overflow='';}
$('#accsg-close').onclick=closeModal; $('#accsg-ov').onclick=closeModal;

/* ---------- YouTube performance popup ---------- */
var ytModal=$('#accsg-ytModal'),ytView=$('#accsg-ytView');
function openYT(s){
  $('#accsg-ytTitle').textContent=titleOf(s);
  $('#accsg-ytBy').textContent=s.composer+(state.lang!=='ru'?' · '+s.title_ru:'');
  $('#accsg-ytOpen').href='https://www.youtube.com/watch?v='+s.yt;
  ytView.innerHTML='<div class="mspin"><div class="ldr"></div></div>';
  var ifr=document.createElement('iframe');
  ifr.setAttribute('title','YouTube performance');
  ifr.setAttribute('allow','accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
  ifr.setAttribute('allowfullscreen','');
  ifr.onload=function(){var sp=ytView.querySelector('.mspin');if(sp)sp.remove();};
  ifr.src='https://www.youtube.com/embed/'+s.yt+'?rel=0&autoplay=1';
  ytView.appendChild(ifr);
  ytModal.classList.add('open');
  document.documentElement.style.overflow='hidden';
}
function closeYT(){ytModal.classList.remove('open');ytView.innerHTML='';document.documentElement.style.overflow='';}
$('#accsg-ytClose').onclick=closeYT; $('#accsg-ytOv').onclick=closeYT;

document.addEventListener('keydown',function(e){if(e.key==='Escape'){if(modal.classList.contains('open'))closeModal();if(ytModal.classList.contains('open'))closeYT();}});

/* ---------- true full-bleed (robust inside Leadpages columns) ----------
   The CSS already breaks out via width:100vw + negative margin. This also
   (a) relaxes any ancestor max-width / overflow-x that would CLIP the
   breakout, and (b) sizes the band to the exact viewport width so it never
   triggers a horizontal scrollbar. Recomputed on resize. Remove this block
   if you'd rather the widget stay inside its Leadpages column.            */
function fullBleed(){
  var band=$('.band'); if(!band) return;
  var n=root.parentElement;
  while(n && n!==document.body && n!==document.documentElement){
    var cs=getComputedStyle(n);
    if(cs.maxWidth!=='none') n.style.maxWidth='none';
    if(cs.overflowX==='hidden'||cs.overflowX==='clip'||cs.overflowX==='auto'||cs.overflowX==='scroll') n.style.overflowX='visible';
    /* remove the host section's vertical padding/margin so the dark band sits flush */
    n.style.paddingTop='0'; n.style.paddingBottom='0'; n.style.marginTop='0'; n.style.marginBottom='0';
    n=n.parentElement;
  }
  band.style.marginLeft='0'; band.style.width='auto';
  var rect=root.getBoundingClientRect();
  var vw=document.documentElement.clientWidth;
  band.style.width=vw+'px';
  band.style.marginLeft=(-rect.left)+'px';
}
window.addEventListener('resize',fullBleed);

/* ---------- init ---------- */
buildLangMenu(); setLang('en');
fullBleed(); setTimeout(fullBleed,250); setTimeout(fullBleed,1200);

})();
