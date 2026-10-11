(() => {
  const state = { me: null, meta: null, points: [], centers: [], map: null, layers: {}, markers: [], markerLayer: null, mapMode: 'street', lastPath: '' };
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const escapeHtml = (v='') => String(v).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const fmtDate = v => { if(!v) return '—'; return new Date(v).toLocaleDateString(wdLocale()); };
  const LANG_KEY = 'wod-language';
  // The 10 languages of the site (v50.33), each with its name in its own language.
  const LANGS = { es:'Español', en:'English', fr:'Français', de:'Deutsch', it:'Italiano', pt:'Português', pl:'Polski', nl:'Nederlands', zh:'中文', ru:'Русский' };
  // Retired languages: Japanese and Korean → English, traditional Chinese → simplified Chinese.
  const LANG_RETIRED = { ja:'en', ko:'en', zt:'zh' };
  // ---------------------------------------------------------------------------
  // Idiomas (v50.28). Cada idioma vive en /assets/i18n/<idioma>.json y solo se descarga el que se usa.
  // «exact»: frase completa → traducción. «patterns»: frases con partes variables ({n} número, {x} texto).
  // Todo lo que se pinta en la página (también lo que llega después: ventanas, avisos, listas) se traduce al vuelo.
  // ---------------------------------------------------------------------------
  const WD_I18N_VERSION='50.33';
  const WD_LOCALES={es:'es-ES',en:'en-GB',fr:'fr-FR',de:'de-DE',it:'it-IT',pt:'pt-PT',pl:'pl-PL',nl:'nl-NL',zh:'zh-CN',ru:'ru-RU'};
  // Plural forms (Polish and Russian have several): a translation may be {one,few,many,other}.
  const wdPlural=(tpl,n)=>{ if(typeof tpl!=='object'||!tpl) return tpl; let k='other'; try{ k=new Intl.PluralRules(wdLocale()).select(Number(String(n).replace(/[^\d.-]/g,''))||0); }catch{} return tpl[k]??tpl.other??Object.values(tpl)[0]; };
  const I18N={};
  let I18N_PACK=null; const I18N_CACHE=new Map();
  function wdLocale(){ return WD_LOCALES[currentLanguage()]||'es-ES'; }
  function i18nPattern(k){ const names=[]; const src=k.replace(/[.*+?^$()|[\]\\]/g,'\\$&').replace(/\{(\w+)\}/g,(m,n)=>{ names.push(n); return n==='n'?'(\\d(?:[\\d.,: +\\u2212-]*\\d)?%?)':'(.{1,60}?)'; }); return {re:new RegExp('^'+src+'$','s'),names}; }
  async function loadLanguagePack(){
    const lang=currentLanguage(); if(lang==='es') return;
    try{ const r=await fetch(`/assets/i18n/${lang}.json?v=${WD_I18N_VERSION}`); if(!r.ok) throw new Error(r.status); const d=await r.json();
      const vals=new Set(); Object.values(d.exact||{}).concat((d.patterns||[]).map(x=>x[1])).forEach(v=>typeof v==='object'?Object.values(v).forEach(x=>vals.add(x)):vals.add(v));
      I18N_PACK={values:vals,exact:d.exact||{},patterns:(d.patterns||[]).map(([k,v])=>[i18nPattern(k),v]).sort((a,b)=>b[0].re.source.length-a[0].re.source.length)}; I18N_CACHE.clear();
    }catch(e){ console.warn('No se ha podido cargar el idioma',lang,e); }
  }
  function i18nCore(s,depth=0){
    if(!I18N_PACK) return null;
    const ex=I18N_PACK.exact[s]; if(ex!=null) return typeof ex==='object'?wdPlural(ex,1):ex;
    if(/[\d]/.test(s)||s.length>3){ for(const [p,tpl0] of I18N_PACK.patterns){ const m=p.re.exec(s); if(m){ const ni=p.names.indexOf('n'); let out=wdPlural(tpl0,ni>=0?m[ni+1]:1); let tpl=out; p.names.forEach((n,i)=>{ const v=m[i+1]; const tv=(depth<2&&!/^[\d\s.,:%€$+-]+$/.test(v))?(i18nCore(v,depth+1)??v):v; out=out.replace('{'+n+'}',()=>tv); }); return out; } } }
    const end=s.match(/^(.*?)([.:!?…]+)$/s); if(end&&end[1]){ const ex2=I18N_PACK.exact[end[1]]; if(ex2!=null) return ex2+end[2]; }
    return null;
  }
  // Mixed text ("Jávea · España", "Reservas · 3 personas"): every piece is translated or left alone only when it is a proper name.
  const I18N_SMALL=/^(de|del|la|las|el|los|y|e|d'|da|do|dos|das|di|von|van|der|den|du|le|les|al|(el|al|ad|an)-\S+)$/i;
  const looksProper=p=>{ if(/\d/.test(p)) return true; const w=p.replace(/[(),.«»"']/g,' ').split(/\s+/).filter(Boolean); return w.length>0&&w.every(x=>I18N_SMALL.test(x)||/^[\p{Lu}\d]/u.test(x)||/^[^\p{L}]+$/u.test(x)); };
  function i18nSegments(s){
    const parts=s.split(/(\s·\s|\s—\s|\s–\s|,\s|:\s|\s\|\s|\s\/\s|\s*→\s*|\s×\s|\.\s)/); if(parts.length<2) return null;
    let changed=false, blocked=false;
    const out=parts.map((p,i)=>{ if(i%2||!p.trim()) return p; const core=p.trim(); if(!/\p{L}/u.test(core)) return p; const t=i18nCore(core); if(t==null){ if(!looksProper(core)) blocked=true; return p; } changed=true; return p.replace(core,t); });
    return changed&&!blocked?out.join(''):null;
  }
  // Translation audit (tools/i18n_collect.py): with localStorage «wd-i18n-debug»=1 every untranslated text is recorded.
  try{ if(localStorage.getItem('wd-i18n-debug')==='1') window.__wdI18nMisses=new Set(); }catch{}
  function currentLanguage(){
    if(currentLanguage.v) return currentLanguage.v;
    let lang=null;
    try{ const q=new URLSearchParams(location.search).get('lang'); if(q){ lang=LANG_RETIRED[q]||q; if(LANGS[lang]) localStorage.setItem(LANG_KEY,lang); } }catch{}
    if(!LANGS[lang]){ try{ lang=localStorage.getItem(LANG_KEY); }catch{} }
    if(lang&&LANG_RETIRED[lang]){ lang=LANG_RETIRED[lang]; try{ localStorage.setItem(LANG_KEY,lang); }catch{} }
    if(!LANGS[lang]){
      // First visit: the browser's language if the site has it; a retired one falls back to English.
      const nav=(navigator.languages||[navigator.language||'es']).map(x=>String(x).toLowerCase());
      lang='es'; for(const l of nav){ const base=l.startsWith('zh-tw')||l.startsWith('zh-hk')||l.startsWith('zh-hant')?'zt':l.split('-')[0]; const c=LANG_RETIRED[base]||base; if(LANGS[c]){ lang=c; break; } }
    }
    return currentLanguage.v=lang;
  }
  function translateString(value){
    if(value==null||currentLanguage()==='es'||!I18N_PACK) return value;
    const raw=String(value); const trimmed=raw.trim(); if(!trimmed||!/\p{L}/u.test(trimmed)) return raw;
    const core=trimmed.replace(/[\u00a0\u202f]/g,' ');
    let out=I18N_CACHE.get(core);
    if(out===undefined){ out=i18nCore(core); if(out==null) out=i18nSegments(core); I18N_CACHE.set(core,out); if(window.__wdI18nMisses){ if(out!=null) I18N_PACK.values.add(out); else if(!looksProper(core)&&!I18N_PACK.values.has(core)&&!/^[^A-Za-zÀ-ÿ]*$/.test(core)) window.__wdI18nMisses.add(core); } }
    if(out==null) return raw;
    const at=raw.indexOf(trimmed); return raw.slice(0,at)+out+raw.slice(at+trimmed.length);
  }
  const t=value=>translateString(value);
  const I18N_SKIP='script,style,textarea,code,pre,[translate="no"],.notranslate';
  const I18N_SKIP_ATTR='[translate="no"],.notranslate';
  function translateTextNode(n){ const p=n.parentElement; if(!p||p.closest(I18N_SKIP)) return; const raw=n.nodeValue; if(!raw||!raw.trim()) return; const out=translateString(raw); if(out!==raw) n.nodeValue=out; }
  function translateAttrs(el){ for(const a of ['placeholder','aria-label','title','alt']){ if(!el.hasAttribute||!el.hasAttribute(a)) continue; const v=el.getAttribute(a), o=translateString(v); if(o!==v) el.setAttribute(a,o); } if(el.tagName==='INPUT'&&/^(button|submit)$/i.test(el.type)){ const o=translateString(el.value); if(o!==el.value) el.value=o; } }
  function translateTree(root=document){
    if(currentLanguage()==='es'||!I18N_PACK||!root) return;
    if(root.nodeType===3){ translateTextNode(root); return; }
    if(root.nodeType!==1&&root!==document) return;
    if(root.nodeType===1&&root.closest&&root.closest(I18N_SKIP_ATTR)) return;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT); const nodes=[]; while(walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(translateTextNode);
    if(root.nodeType===1) translateAttrs(root);
    (root.querySelectorAll?root:document).querySelectorAll('[placeholder],[aria-label],[title],img[alt],input[type=submit],input[type=button]').forEach(el=>{ if(!el.closest(I18N_SKIP_ATTR)) translateAttrs(el); });
  }
  let i18nObserver=null;
  function observeTranslations(){
    if(i18nObserver||currentLanguage()==='es'||!I18N_PACK||!window.MutationObserver) return;
    i18nObserver=new MutationObserver(muts=>{ for(const m of muts){ if(m.type==='childList') m.addedNodes.forEach(n=>translateTree(n)); else if(m.type==='attributes'&&m.target.nodeType===1&&!m.target.closest(I18N_SKIP_ATTR)) translateAttrs(m.target); } });
    i18nObserver.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['placeholder','aria-label','title']});
  }
  function applyLanguage(){
    const lang=currentLanguage();
    document.documentElement.lang=lang==='zh'?'zh-Hans':lang;
    const sel=$('#language-select'); if(sel) sel.value=lang;
    translateTree(document.body); document.title=translateString(document.title);
    observeTranslations();
    if(typeof window.__wdRebindLanguage==='function') window.__wdRebindLanguage();
  }
  function initLanguage(){
    const sel=$('#language-select'); if(!sel || sel.__bound) return;
    sel.__bound=true; sel.value=currentLanguage();
    sel.onchange=()=>{ try{ localStorage.setItem(LANG_KEY,sel.value); }catch{} if(state.me) fetch('/api/account/language',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lang:sel.value}),keepalive:true}).catch(()=>{}); location.href=location.pathname+'?lang='+encodeURIComponent(sel.value)+location.hash; };
  }
  const api = async (url, options={}) => { const r = await fetch(url, options); let d=null; try{d=await r.json();}catch{} if(!r.ok){ if(d?.plan_required) planToastNext=true; const e=new Error(d?.error==='consent_required'?'Confirma que quieres compartir tus datos con el centro.':(d?.error || `Error ${r.status}`)); e.status=r.status; e.data=d; throw e; } if(d===null) throw new Error('Respuesta no válida del servidor.'); return d; };
  const postJSON = (url, data, method='POST') => api(url,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  let planToastNext=false;
  function toast(msg){ const t=$('#toast'); t.textContent=translateString(msg);
    if(planToastNext){ planToastNext=false; t.insertAdjacentHTML('beforeend',' <a href="#/planes" class="toast-link">'+escapeHtml(translateString('Ver planes'))+'</a>'); } t.classList.add('show'); clearTimeout(toast.t); toast.t=setTimeout(()=>t.classList.remove('show'),2800); }
  function initials(name=''){ return name.split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase() || '?'; }
  // Sends the visitor to log in and brings them back to where they were afterwards.
  // Imágenes de la web: el administrador las cambia desde «Imágenes de la web»; estos son los valores de respaldo.
  const MEDIA_DEFAULTS={'hero:explorar':'/assets/images/micronesia.webp','hero:home':'/assets/images/portada-arrecife.webp','hero:centros':'/assets/images/BUCEADORES.webp','hero:puntos':'/assets/images/australia.webp','hero:tipos':'/assets/images/fondo.webp','hero:experiencias':'/assets/images/maldivas.webp','hero:top10':'/assets/images/tailandia.webp','hero:auth':'/assets/images/logbook1.webp'};
  // Visitors in the southern hemisphere live the seasons the other way round: the admin can give them their own look.
  function visitorHemisphere(){ let tz=''; try{ tz=Intl.DateTimeFormat().resolvedOptions().timeZone||''; }catch{}
    return /^(Australia|Antarctica)\/|^Pacific\/(Auckland|Chatham|Fiji|Tahiti|Noumea|Efate|Tongatapu|Apia|Rarotonga|Port_Moresby|Guadalcanal)|^America\/(Argentina|Santiago|Sao_Paulo|Montevideo|Asuncion|La_Paz|Lima|Recife|Bahia|Fortaleza|Belem|Maceio|Cuiaba|Campo_Grande|Punta_Arenas)|^Africa\/(Johannesburg|Maputo|Harare|Windhoek|Gaborone|Lusaka|Luanda|Dar_es_Salaam|Maseru|Mbabane|Blantyre|Lubumbashi)|^Indian\/(Mauritius|Reunion|Antananarivo|Mayotte|Comoro)|^Asia\/(Jakarta|Makassar|Jayapura|Dili)/.test(tz)?'s':'n'; }
  const THEME_ACCENTS={oceano:{label:'Océano',v:['#0b7a89','#12a5b5','#07364a','#e3f1f2']},coral:{label:'Coral',v:['#b9483f','#de6d5b','#3f1d1a','#fbe9e5']},tropical:{label:'Tropical',v:['#0e8466','#1fae86','#0b3a31','#e1f4ec']},
    atardecer:{label:'Atardecer',v:['#a85a12','#d98a2b','#3b2412','#fbefdf']},invierno:{label:'Invierno',v:['#3a6898','#5b8fc4','#13263f','#e6eef7']},abisal:{label:'Abisal',v:['#4b4fa8','#6d71d1','#171a3d','#ebebf8']}};
  function themePreviewId(){ try{ return sessionStorage.getItem('wd_theme_preview')||''; }catch{ return ''; } }
  function applySiteTheme(){
    const t=state.theme, root=document.documentElement, acc=THEME_ACCENTS[t?.accent]||null;
    ['--sea','--sea-2','--deep','--sea-soft'].forEach((k,i)=>{ if(acc&&t.accent!=='oceano') root.style.setProperty(k,acc.v[i]); else root.style.removeProperty(k); });
    root.dataset.theme=t?.accent||'';
    $('#wd-theme-preview')?.remove();
    if(t?.preview) document.body.insertAdjacentHTML('beforeend',`<div class="th-preview-bar" id="wd-theme-preview" role="status"><span>${wdIcon('eye',16)} Vista previa del tema <b>${escapeHtml(t.name)}</b> · solo la ves tú</span><button type="button" class="btn" id="wd-theme-exit">Salir de la vista previa</button></div>`);
    $('#wd-theme-exit')?.addEventListener('click',async()=>{ try{ sessionStorage.removeItem('wd_theme_preview'); }catch{} await loadSiteMedia(); route(); });
  }
  async function loadSiteMedia(){
    const pv=themePreviewId();
    try{ const d=await api('/api/site-media?h='+visitorHemisphere()+(pv?'&theme='+encodeURIComponent(pv):'')); state.media=d.items||{}; state.theme=d.theme||null; }catch{ state.media=state.media||{}; }
    if(document.body) applySiteTheme(); return state.media; }
  const media=(key,fallback)=>state.media?.[key]?.url||fallback||MEDIA_DEFAULTS[key]||'/assets/images/fondo.webp';
  const mediaCredit=key=>state.media?.[key]?.credit||'';
  const heroImg=(key,fallback)=>`<img class="tp-hero-img" src="${escapeHtml(media(key,fallback))}" alt="">${mediaCredit(key)?`<span class="hero-credit">${escapeHtml(mediaCredit(key))}</span>`:''}`;
  // Una página que tarda en cargar no debe pintar encima de la siguiente si el visitante ya se ha ido.
  const navGuard=()=>{ const h=location.hash; return ()=>location.hash===h; };
  function goLogin(){ const h=location.hash||'#/'; location.hash=/^#\/(login|registro)/.test(h)?'#/login':'#/login?next='+encodeURIComponent(h); }
  function wdSearchClears(root){
    $$('.cd-field input[type=search]',root).forEach(inp=>{ if(inp.nextElementSibling?.classList.contains('cd-x')) return;
      const b=document.createElement('button'); b.type='button'; b.className='cd-x'; b.setAttribute('aria-label','Borrar búsqueda'); b.textContent='×'; b.hidden=!inp.value;
      inp.after(b); inp.addEventListener('input',()=>{ b.hidden=!inp.value; });
      b.onclick=()=>{ inp.value=''; b.hidden=true; inp.dispatchEvent(new Event('input',{bubbles:true})); inp.focus(); }; });
  }
  function setApp(html){ const current=(location.hash||'').replace(/^#\/?/,'').split('?')[0]; const showBack=!!current && !['home','admin','area','cuenta','logbook','recompensas','mis-puntos'].includes(current); const back=showBack?`<button class="global-back" type="button" id="global-back" aria-label="Volver a la pantalla anterior"><span aria-hidden="true">←</span><span>Volver</span></button>`:''; $('#app').innerHTML=back+html; wdSearchClears($('#app')); translateTree($('#app')); $('#app').focus({preventScroll:true}); window.scrollTo(0,0); const backBtn=$('#global-back'); if(backBtn) backBtn.onclick=()=>{ if(history.length>1) history.back(); else location.hash='#/'; }; }
  function cardImg(country){ const map={España:'/assets/images/fondo1.webp',Egipto:'/assets/images/egipto.webp',Australia:'/assets/images/australia.webp',México:'/assets/images/mexico.webp',Maldivas:'/assets/images/maldivas.webp',Ecuador:'/assets/images/galapagos.webp','Costa Rica':'/assets/images/california.webp'}; return map[country] || '/assets/images/fondo.webp'; }
  function centerLogo(c){ const u=String(c?.logo_url||'').trim(); if(!u || /^https?:\/\/[^/]+\/?$/i.test(u)) return ''; return u; }
  function centerLogoMarkup(c,size='56px'){ const src=centerLogo(c); if(!src) return centerMonogram(c,size); return `<img class="center-logo" src="${escapeHtml(src)}" alt="Logo de ${escapeHtml(c.name)}" style="width:${size};height:${size};object-fit:contain;border-radius:12px;background:#fff;padding:6px" loading="lazy" data-fallback="next">${centerMonogram(c,size).replace('<span ','<span hidden ')}`; }

  async function loadMe(){ try{ const d=await api('/api/me'); state.me=d.authenticated?d:null; renderAccount(); setTimeout(legalAcceptGate,400); return d; }catch{state.me=null; renderAccount();}}
  function closeTransientMenus(){ const menu=$('#account-dropdown'), toggle=$('#account-toggle'); menu?.classList.remove('open'); toggle?.setAttribute('aria-expanded','false'); $('#main-nav')?.classList.remove('open'); }
  function renderAccount(){ const slot=$('#account-slot'); if(!slot) return; if(!state.me){ slot.innerHTML='<a class="account-link" href="#/login"><span>Iniciar sesión</span></a>'; translateTree(slot); return; } const u=state.me.user; const role=u.role; const management=role==='admin'?'<a href="#/admin">👑 Administración</a>':role==='center'?'<a href="#/admin">🏪 Gestionar mi centro</a>':role==='freelance'?'<a href="#/admin">🧭 Gestionar mis servicios</a>':''; const personalLinks=role==='center'?'<a href="#/admin">🏪 Gestionar mi centro</a>':`<a href="#/area">${wdIcon('home',16)}Mi área</a>`; slot.innerHTML=`<div class="account-menu"><button class="account-link account-toggle" id="account-toggle" type="button" aria-expanded="false"><span class="avatar">${escapeHtml(initials(u.fullname))}</span><span class="label" translate="no">${escapeHtml(u.fullname.split(' ')[0])}</span><span class="account-chevron">⌄</span></button><div class="account-dropdown" id="account-dropdown"><div class="account-dropdown-head"><strong>${escapeHtml(u.fullname)}</strong><small>${escapeHtml(role==='admin'?'Administrador':role==='center'?'Centro de buceo':role==='freelance'?'Profesional / freelance':'Buceador / cliente')}</small></div>${personalLinks}<a href="#/cuenta">${wdIcon('user',16)}Mi cuenta</a><a href="#/logbook">${wdIcon('book',16)}Log Book</a><a href="#/recompensas">${wdIcon('gift',16)}Recompensas</a><a href="#/mis-puntos">${wdIcon('star',16)}Mis puntos</a>${management && role!=='center'?management:''}<button type="button" id="account-logout">Cerrar sesión</button></div></div>`; const toggle=$('#account-toggle'),menu=$('#account-dropdown'); toggle.onclick=e=>{e.stopPropagation(); const open=menu.classList.toggle('open'); toggle.setAttribute('aria-expanded',open?'true':'false');}; if(!window.__wdAccountClickBound){ document.addEventListener('click',()=>closeTransientMenus()); window.__wdAccountClickBound=true; } $('#account-logout').onclick=async()=>{closeTransientMenus();await postJSON('/api/auth/logout',{});await loadMe();location.hash='#/';}; translateTree(slot); }
  function navMobile(){ $('#mobile-menu')?.addEventListener('click',()=>$('#main-nav').classList.toggle('open')); $$('#main-nav a').forEach(a=>a.addEventListener('click',()=>$('#main-nav').classList.remove('open'))); }

  async function loadMeta(){ if(!state.meta) state.meta=await api('/api/meta'); return state.meta; }
  // Marca en la cabecera la sección en la que está el visitante.
  function markNav(name){ const section={punto:'puntos',centro:'centros',experiencia:'experiencias',experienciareserva:'experiencias',reservar:'centros'}[name]||name; $$('#main-nav a').forEach(a=>{ const on=a.getAttribute('href')==='#/'+section; a.classList.toggle('active',on); if(on) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current'); }); }
  function route(){ document.querySelectorAll('.wd-modal').forEach(m=>m.remove()); clearTimeout(route.gate); route.gate=setTimeout(legalAcceptGate,700); const hash=location.hash.replace(/^#\/?/,'') || ''; if(hash.startsWith('checkin/')) return renderCheckin(hash.split('/')[1]); if(hash.startsWith('promo/')) return renderPromoPage(hash.split('/')[1].split('?')[0]); if(hash.startsWith('legal/')||hash==='legal'){ closeTransientMenus(); markNav('legal'); return renderLegal(hash.slice(6).split('?')[0]).catch(err=>{console.error(err);}); } const [name, qs] = hash.split('?'); const routes={home:renderHome,explorar:renderExplorer,puntos:renderPoints,punto:renderPointPage,centros:renderCenters,centro:renderCenterDetail,tipos:renderTypes,experiencias:renderExperiences,top10:renderTop10,experiencia:renderExperienceDetail,profesional:renderProfessional,experienciareserva:renderExperienceBooking,area:renderArea,reserva:renderBookingDetail,verificarreserva:renderPublicBookingVerification,'pago-ok':renderPaymentSuccess,cuenta:renderAccountPage,login:renderLogin,registro:renderRegister,reservar:renderBooking,virtual:renderVirtual,logbook:renderLogbook,recompensas:renderRewards,'mis-puntos':renderMyPoints,monedero:()=>location.replace('#/mis-puntos'),'como-funcionan-los-puntos':renderPointsInfo,baja:renderUnsubscribe,admin:renderAdmin,privacidad:()=>location.replace('#/legal/privacidad'),recuperar:renderForgot,restablecer:renderReset,setup:renderSetup,'verificar-email':renderVerifyEmail,'eliminar-cuenta':renderConfirmDeletion,planes:renderPlans,'mi-plan':renderMyPlanRoute,equipo:renderTeamJoin}; const fn=routes[name||'home']||renderHome; closeTransientMenus(); markNav(name||'home'); return Promise.resolve(fn(new URLSearchParams(qs||''))).catch(err=>{console.error(err);setApp('<section class="page"><div class="empty"><h2>No se ha podido abrir esta sección</h2><p>'+escapeHtml(err?.message||'La sección ha encontrado un error.')+'</p><div class="page-actions" style="justify-content:center"><button class="btn" type="button" data-reload>Reintentar</button><a class="btn btn-primary" href="#/">Volver al inicio</a></div></div></section>');}); }
  window.addEventListener('hashchange', route);
  // CSP (script-src 'self'): no inline handlers in the markup. These delegated listeners replace them.
  document.addEventListener('click',e=>{ if(e.target.closest?.('[data-reload]')) location.reload(); });
  document.addEventListener('submit',e=>{ if(e.target.matches?.('form[data-nosubmit]')) e.preventDefault(); },true);
  document.addEventListener('error',e=>{ const img=e.target; if(img?.tagName==='IMG'&&img.dataset.fallback==='next'){ if(img.nextElementSibling) img.nextElementSibling.hidden=false; img.remove(); } },true);

  const zoneCenters={Europa:[43,10,4],Caribe:[18,-72,4],América:[12,-75,3], 'África y Mar Rojo':[12,35,4],Asia:[10,105,3],Oceanía:[-18,145,3]};
  function regionGroups(points){ const groups={}; points.forEach(p=>{const z=p.zone||'Otros'; const country=p.country||'Sin país'; groups[z]??={name:z,count:0,countries:{}}; groups[z].count++; groups[z].countries[country]??={name:country,count:0}; groups[z].countries[country].count++;}); return Object.values(groups).sort((a,b)=>b.count-a.count); }
  function focusMapPoints(points){ const ids=new Set(points.map(p=>String(p.id))); const L_=state.markerLayer; if(!L_) return; const keep=(state.markerIndex||[]).filter(x=>ids.has(x.id)).map(x=>x.m); if(L_.clearLayers&&L_.addLayers){ L_.clearLayers(); L_.addLayers(keep); return; } (state.markerIndex||[]).forEach(({m,id})=>{ if(ids.has(id)) m.addTo(L_); else L_.removeLayer(m); }); }
  function setupZones(el, points){ const groups=regionGroups(points); el.innerHTML=groups.map((z,i)=>`<div class="zone-group"><button class="zone-btn" type="button" aria-expanded="false" data-zone="${escapeHtml(z.name)}"><span class="zone-number">${String(i+1).padStart(2,'0')}</span><span>${escapeHtml(z.name)}</span><span class="zone-count">${z.count}</span><span class="zone-chevron">⌄</span></button><div class="zone-country-list">${Object.values(z.countries).sort((a,b)=>a.name.localeCompare(b.name,'es')).map(c=>`<button class="zone-country-btn" type="button" data-zone="${escapeHtml(z.name)}" data-country="${escapeHtml(c.name)}"><span>${escapeHtml(c.name)}</span><span>${c.count}</span></button>`).join('')}</div></div>`).join(''); $$('.zone-btn',el).forEach(b=>b.addEventListener('click',()=>{const group=b.closest('.zone-group'); const isOpen=group.classList.contains('open'); $$('.zone-group',el).forEach(g=>{g.classList.remove('open'); const btn=$('.zone-btn',g); if(btn) btn.setAttribute('aria-expanded','false');}); if(!isOpen){group.classList.add('open'); b.setAttribute('aria-expanded','true'); const zonePts=state.points.filter(p=>(p.zone||'')===b.dataset.zone); focusMapPoints(zonePts); const v=zoneCenters[b.dataset.zone]||[20,0,2]; if(state.map){if(zonePts.length>1) state.map.fitBounds(L.latLngBounds(zonePts.map(p=>[p.latitude,p.longitude])),{padding:[45,45],maxZoom:v[2],animate:true,duration:.8}); else state.map.setView([v[0],v[1]],v[2],{animate:true,duration:.8});}} $$('.zone-btn',el).forEach(x=>x.classList.remove('active')); if(!isOpen)b.classList.add('active');})); $$('.zone-country-btn',el).forEach(b=>b.addEventListener('click',()=>{const pts=state.points.filter(p=>(p.zone||'')===b.dataset.zone && (p.country||'')===b.dataset.country && p.latitude!=null && p.longitude!=null); $$('.zone-country-btn',el).forEach(x=>x.classList.remove('active')); b.classList.add('active'); focusMapPoints(pts); if(pts.length===1&&state.map){state.map?.flyTo([pts[0].latitude,pts[0].longitude],12,{animate:true,duration:.8});} else if(pts.length>1&&state.map){state.map.fitBounds(L.latLngBounds(pts.map(p=>[p.latitude,p.longitude])),{padding:[45,45],maxZoom:9,animate:true,duration:.8});} })); }
  function bindMapModeButtons(){ $$('.map-toolbar button').forEach(btn=>btn.addEventListener('click',()=>{ $$('.map-toolbar button').forEach(x=>x.classList.remove('active')); btn.classList.add('active'); setMapMode(btn.dataset.mapmode); })); }
  function setMapMode(mode){ if(!state.map) return; state.mapMode=mode; Object.entries(state.layers).forEach(([k,l])=>{ if(state.map.hasLayer(l)) state.map.removeLayer(l); }); const layer=state.layers[mode]||state.layers.street; layer.addTo(state.map); if(mode==='world'){state.map.flyTo([20,0],state.map.getMinZoom(),{animate:true,duration:.7});} }
  const WD_WORLD=[[-85.05,-180],[85.05,180]];
  function wdLimitMap(map){
    try{
      const world=L.latLngBounds(WD_WORLD);
      map.setMaxBounds(world); map.options.maxBoundsViscosity=1; map.options.worldCopyJump=false;
      const fit=()=>{ try{ const z=map.getBoundsZoom(L.latLngBounds([[-58,-180],[78,180]]),false); const minZ=Math.max(1,Math.floor(z*4)/4); map.setMinZoom(minZ); if(map.getZoom()<minZ) map.setZoom(minZ,{animate:false}); }catch(e){} };
      map.whenReady(fit); map.on('resize',fit); setTimeout(fit,0);
    }catch(e){ console.warn('mapa',e); }
    return map;
  }
  function wdTileDefaults(){ if(!window.L||wdTileDefaults.done) return; wdTileDefaults.done=true; try{ L.TileLayer.prototype.options.noWrap=true; L.TileLayer.prototype.options.bounds=L.latLngBounds(WD_WORLD); }catch(e){} }
  // Maps (v50.36): own base map (Protomaps PMTiles, © OpenStreetMap contributors) served by our server; the satellite
  // view (Esri) passes through our server and only appears when it is configured and within the monthly limit;
  // GEBCO bathymetry is loaded only when the visitor chooses it. /api/map/config says what is available.
  let WD_MAP_CFG=null;
  async function loadMapConfig(){ try{ WD_MAP_CFG=await api('/api/map/config'); }catch{ WD_MAP_CFG={basemap:{type:'none'},satellite:{enabled:false},bathymetry:null}; } return WD_MAP_CFG; }
  function wdBaseLayer(){
    const b=WD_MAP_CFG?.basemap||{type:'none'};
    if(b.type==='pmtiles'&&window.protomapsL&&window.WD_MAP_FLAVOR){ const lang=currentLanguage(); const f=window.WD_MAP_FLAVOR;
      try{ return protomapsL.leafletLayer({url:b.url,paintRules:protomapsL.paintRules(f),labelRules:protomapsL.labelRules(f,lang==='zh'?'zh-Hans':lang),backgroundColor:f.background,maxDataZoom:b.max_data_zoom||15,maxZoom:19,attribution:b.attribution}); }catch(e){ console.warn('mapa base',e); } }
    if(b.type==='osm-dev') return L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:b.attribution});
    return L.layerGroup();
  }
  function makeLayers(){ wdTileDefaults(); const c=WD_MAP_CFG||{}; const out={street:wdBaseLayer()};
    if(c.satellite?.enabled) out.satellite=L.tileLayer(c.satellite.url,{maxZoom:c.satellite.max_zoom||19,attribution:c.satellite.attribution});
    if(c.bathymetry) out.marine=L.tileLayer.wms(c.bathymetry.url,{layers:c.bathymetry.layers,format:'image/png',transparent:true,version:'1.3.0',attribution:c.bathymetry.attribution});
    return out; }
  // Map markers (v50.33): the dive flag inside a small circle. 19 px on desktop, 23 px on touch screens, with a
  // 44 px invisible touch target on phones. Same icon on every map; clusters keep the same round style.
  const WD_TOUCH=(()=>{ try{ return matchMedia('(pointer:coarse)').matches; }catch{ return false; } })();
  function pointIcon(p,{active=false}={}){ const box=WD_TOUCH?44:(active?34:28); const label=escapeHtml(p?.name||'Punto de buceo');
    return L.divIcon({className:`wd-pin-wrap${active?' is-active':''}${WD_TOUCH?' is-touch':''}`,html:`<span class="wd-pin" role="img" aria-label="${label}"></span>`,iconSize:[box,box],iconAnchor:[box/2,box/2]}); }
  function wdClusterIcon(cluster){ const n=cluster.getChildCount(); const size=n<10?30:n<100?36:44; return L.divIcon({className:'wd-cluster-wrap',html:`<span class="wd-cluster" style="width:${size}px;height:${size}px" role="img" aria-label="${n} puntos de buceo">${n>999?Math.round(n/100)/10+'k':n}</span>`,iconSize:[size,size],iconAnchor:[size/2,size/2]}); }
  function wdMarkerLayer(){ return L.markerClusterGroup?L.markerClusterGroup({iconCreateFunction:wdClusterIcon,showCoverageOnHover:false,maxClusterRadius:42,disableClusteringAtZoom:11,chunkedLoading:true,spiderfyOnMaxZoom:true,zoomToBoundsOnClick:true}):L.layerGroup(); }
  function wdSelectMarker(m){ if(state.selectedMarker) state.selectedMarker.getElement()?.classList.remove('is-selected'); state.selectedMarker=m; m?.getElement()?.classList.add('is-selected'); }
  function initMap(id, points, center, zoom){ if(state.map){state.map.remove();state.map=null;} if(!window.L){ const el=document.getElementById(id); state.markerIndex=[]; if(el) el.innerHTML='<div class="map-fallback"><strong>El mapa no está disponible ahora mismo</strong><span>Puedes seguir explorando los puntos en formato lista.</span><a class="btn" href="#/puntos">Ver puntos de buceo</a></div>'; state.markers=[]; return null; } wdTileDefaults(); const map=wdLimitMap(L.map(id,{zoomControl:false,scrollWheelZoom:'center',dragging:true,doubleClickZoom:true,touchZoom:true,boxZoom:false,keyboard:true,zoomAnimation:true,markerZoomAnimation:true,zoomSnap:.25,zoomDelta:.5})).setView(center,zoom); map.addControl(L.control.zoom({position:'bottomright'})); state.map=map; state.layers=makeLayers(); state.layers.street.addTo(map); $$('[data-mapmode="satellite"]').forEach(x=>x.hidden=!state.layers.satellite); $$('[data-mapmode="marine"]').forEach(x=>x.hidden=!state.layers.marine); state.markerLayer=wdMarkerLayer().addTo(map); state.markers=[]; state.markerIndex=[]; const batch=[]; points.forEach(p=>{ if(p.latitude==null||p.longitude==null) return; const m=L.marker([p.latitude,p.longitude],{icon:pointIcon(p),riseOnHover:true,title:p.name,alt:p.name,keyboard:true}); batch.push(m); state.markerIndex.push({m,id:String(p.id)}); m.on('click',()=>{ wdSelectMarker(m); openPointDrawer(p); }); if(!WD_TOUCH) m.bindTooltip(escapeHtml(p.name),{direction:'top',offset:[0,-10],opacity:.95}); state.markers.push(m); }); if(state.markerLayer.addLayers) state.markerLayer.addLayers(batch); else batch.forEach(m=>m.addTo(state.markerLayer)); return map; }
  function openPointDrawer(p){ const d=$('#home-drawer') || $('#explore-drawer'); if(!d){ location.hash=pointHref(p.id); return; } const depth=depthText(p); d.innerHTML=`<button class="close" type="button" aria-label="Cerrar">×</button><p class="eyebrow">${escapeHtml(p.zone||'Punto de buceo')}</p><h3>${escapeHtml(p.name)}</h3><p class="cd-place">${wdIcon('pin',14)}${escapeHtml(placeText(p)||p.country||'')}</p><div class="pt-facts">${p.dive_type?`<span>${escapeHtml(p.dive_type)}</span>`:''}${depth?`<span>${wdIcon('depth',14)}${escapeHtml(depth)}</span>`:''}${p.difficulty?`<span>${wdIcon('level',14)}${escapeHtml(p.difficulty)}</span>`:''}</div><div class="drawer-actions"><a class="btn btn-primary" href="${pointHref(p.id)}">Ver ficha del punto</a><a class="btn" href="#/top10?lat=${p.latitude}&lon=${p.longitude}&label=${encodeURIComponent(p.name)}">Top 10 de la zona</a></div>`; d.classList.add('open'); $('.close',d).onclick=()=>d.classList.remove('open'); try{ state.map?.flyTo([p.latitude,p.longitude],Math.max(Number(state.map.getZoom())||2,11),{duration:.8}); }catch(e){ console.warn('mapa',e); } }
  function bindHomeSearch(){
    const input=$('#home-search'),btn=$('#home-search-btn'),res=$('#home-search-results'),clear=$('#home-search-clear');
    if(!input||!btn||!res) return;
    let timer=null, lastQuery='', selected=null;
    // Keep the suggestions inside the screen: never taller than the room left below the search box.
    const fit=()=>{ const room=Math.floor(window.innerHeight-res.getBoundingClientRect().top-16); res.style.maxHeight=Math.max(220,Math.min(440,room))+'px'; if(room<220) window.scrollBy({top:220-room+16,behavior:'smooth'}); };
    const normalize=v=>String(v||'').toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
    const score=(item,q)=>{const n=normalize(item.name), z=normalize(q); let s=0; if(n===z)s+=100; if(n.startsWith(z))s+=60; if(n.includes(z))s+=35; [item.city,item.region,item.subregion,item.country,item.description].forEach(v=>{if(normalize(v).includes(z))s+=10}); return s;};
    const pointMatches=q=>(state.points||[]).filter(p=>{const hay=normalize([p.name,p.country,p.region,p.subregion,p.description].join(' '));return hay.includes(normalize(q));}).sort((a,b)=>score(b,q)-score(a,q));
    const centerMatches=async q=>{try{ let d; try{ d=await api('/api/center-directory?'+new URLSearchParams({q,per_page:'8'})); }catch(err){ if(err.status!==404) throw err; d=await legacyCenterDirectory(new URLSearchParams({q,per_page:'8'})); } return (d.items||[]).sort((a,b)=>score(b,q)-score(a,q)); }catch{return [];}};
    const render=(q,centers=[])=>{
      const points=pointMatches(q);
      const shownPoints=points.slice(0,8), shownCenters=centers.slice(0,6);
      if(!shownPoints.length&&!shownCenters.length){res.innerHTML=`<div class="search-empty"><span class="search-empty-icon">⌕</span><div><strong>No hemos encontrado coincidencias</strong><small>Prueba con el nombre de un punto, una ciudad, una isla o un centro de buceo.</small></div></div>`;res.hidden=false;fit();return;}
      const pointBlock=shownPoints.length?`<div class="search-group"><div class="search-group-head"><span>Puntos de buceo</span><b>${points.length}</b></div>${shownPoints.map(p=>`<button class="search-result search-result-point" data-kind="point" data-id="${p.id}" type="button"><span class="search-result-icon">📍</span><span class="search-result-copy"><strong>${escapeHtml(p.name)}</strong><small>${escapeHtml(p.subregion||p.region||'')} · ${escapeHtml(p.country||'')}</small></span><span class="search-arrow">→</span></button>`).join('')}</div>`:'';
      const centerBlock=shownCenters.length?`<div class="search-group"><div class="search-group-head"><span>Centros de buceo</span><b>${centers.length}</b></div>${shownCenters.map(c=>`<button class="search-result search-result-center" data-kind="center" data-id="${c.id}" type="button"><span class="search-result-icon">🤿</span><span class="search-result-copy"><strong>${escapeHtml(c.name)}</strong><small>${escapeHtml(c.city||c.region||'')} · ${escapeHtml(c.country||'')}</small></span><span class="search-arrow">→</span></button>`).join('')}</div>`:'';
      const more=points.length>8||centers.length>6?`<div class="search-more"><span>${points.length+centers.length} resultados</span><span>Afina la búsqueda o pulsa Buscar para explorar el mapa</span></div>`:'';
      res.innerHTML=pointBlock+centerBlock+more;res.hidden=false;fit();
      $$('.search-result',res).forEach(b=>b.onclick=()=>{
        const kind=b.dataset.kind, id=b.dataset.id;
        selected={kind,id};
        if(kind==='point'){
          const p=state.points.find(x=>String(x.id)===id); if(p) input.value=p.name;
        }else{
          const c=centers.find(x=>String(x.id)===id); if(c) input.value=c.name;
        }
        // Seleccionar una sugerencia NO desplaza ni hace zoom: el movimiento al mapa
        // ocurre únicamente cuando el usuario pulsa «Buscar».
        res.hidden=true; lastQuery=''; input.focus();
      });
    };
    let revealed=false;
    const revealOnMap=(points,centers)=>{
      revealed=true;
      const mapEl=$('#home-map-section')||$('#home-map');
      if(!mapEl) return;
      const top=mapEl.getBoundingClientRect().top+window.scrollY-82;
      window.scrollTo({top,behavior:'smooth'});
      setTimeout(()=>{
        if(!state.map) return;
        const validPoints=(points||[]).filter(p=>p.latitude!=null&&p.longitude!=null);
        const validCenters=(centers||[]).filter(c=>c.latitude!=null&&c.longitude!=null);
        const targets=[...validPoints.map(p=>({lat:+p.latitude,lng:+p.longitude,point:p})),...validCenters.map(c=>({lat:+c.latitude,lng:+c.longitude,center:c}))];
        if(!targets.length){focusMapPoints(state.points);return;}
        if(validPoints.length===1&&validCenters.length===0){
          focusMapPoints(validPoints);
          state.map?.flyTo([+validPoints[0].latitude,+validPoints[0].longitude],Math.max(state.map.getZoom(),14),{animate:true,duration:1.25,easeLinearity:.25});
          setTimeout(()=>openPointDrawer(validPoints[0]),900);
        }else if(targets.length===1){
          state.map?.flyTo([targets[0].lat,targets[0].lng],Math.max(state.map.getZoom(),13),{animate:true,duration:1.25,easeLinearity:.25});
          if(targets[0].point)setTimeout(()=>openPointDrawer(targets[0].point),900);
        }else{
          state.map?.flyToBounds(L.latLngBounds(targets.map(t=>[t.lat,t.lng])),{padding:[70,70],maxZoom:13,animate:true,duration:1.25,easeLinearity:.25});
          focusMapPoints(validPoints.length?validPoints:state.points);
        }
      },420);
    };
    const search=async(reveal=false)=>{
      const q=input.value.trim();
      if(q.length<2){res.hidden=true;return;}
      try{
        const centers=await centerMatches(q);
        const points=pointMatches(q);
        render(q,centers);
        if(reveal&&(points.length||centers.length)) revealOnMap(points,centers);
      }catch(e){
        render(q,[]);
        const points=pointMatches(q);
        if(reveal&&points.length) revealOnMap(points,[]);
      }
    };
    input.addEventListener('input',()=>{selected=null;clearTimeout(timer);const has=input.value.trim().length>0;if(clear)clear.hidden=!has;if(input.value.trim().length<2){res.hidden=true;return;}timer=setTimeout(()=>search(false),140);});
    input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();lastQuery='';search(true);}});
    btn.onclick=()=>{lastQuery='';selected=null;search(true);};
    const resetMap=()=>{ if(!revealed) return; revealed=false; try{ $('#home-drawer')?.classList.remove('open'); focusMapPoints(state.points||[]); state.map?.flyTo([20,0],2,{animate:true,duration:.9}); }catch(e){ console.warn('mapa',e); } };
    if(clear)clear.onclick=()=>{input.value='';selected=null;clear.hidden=true;res.hidden=true;resetMap();input.focus();};
    input.addEventListener('input',()=>{ if(!input.value.trim()) resetMap(); });
    document.addEventListener('click',e=>{if(!res.contains(e.target)&&e.target!==input&&e.target!==btn)res.hidden=true;});
  }

  const listFilterTemplate=(title,copy,fields)=>`<section class="page"><div class="breadcrumb"><a href="#/">Inicio</a> / ${escapeHtml(title)}</div><p class="eyebrow">WORLDIVES DISCOVERY</p><h1>${escapeHtml(title)}</h1><p class="lead">${escapeHtml(copy)}</p><div class="list-layout" style="margin-top:28px"><aside class="filter-panel"><h3>Filtrar</h3>${fields}<button id="apply-filter" class="btn btn-primary" style="width:100%">Aplicar filtros</button><button id="clear-filter" class="btn" style="width:100%;margin-top:7px">Limpiar</button></aside><div><div id="result-list" class="result-list"></div></div></div></section>`;
  // Tipos de buceo: el servidor es la fuente (/api/dive-types). Esta lista solo sirve de respaldo
  // si el servidor que responde es anterior a la v50.23 (por ejemplo, no se ha reiniciado tras actualizar).
  const DIVE_TYPE_FALLBACK=[['Arrecifes','Todos los niveles',5,25],['Paredes','Intermedio',10,40],['Pecios y naufragios','Intermedio',12,40],['Cuevas y cavernas','Formación específica',5,30],['Cenotes','Formación específica',5,40],['Muck','Todos los niveles',3,20],['Canales','Intermedio',10,30],['Cañones','Avanzado',15,40],['Pináculos','Intermedio',8,35],['Corrientes y deriva','Avanzado',10,30],['Aguas profundas','Avanzado',30,40],['Nocturnas','Intermedio',3,18],['Lagos','Todos los niveles',3,30],['Pilares','Todos los niveles',5,25],['Playa y esnórquel','Iniciación',0,10]];
  const wdKey=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim().replace(/\s+/g,'-');
  const wdFold=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  function warnOutdatedServer(){ console.warn('WORLDIVES: el servidor no tiene las rutas de la v50.23. Reinicia app/server.py tras copiar la actualización.'); if(['admin','center'].includes(state.me?.user?.role) && !window.__wdOutdatedWarned){ window.__wdOutdatedWarned=true; toast('Aviso: el servidor sigue con la versión anterior. Detén y vuelve a arrancar app/server.py para activar la v50.23.'); } }
  async function legacyDiveTypes(){
    const lists=await Promise.all(DIVE_TYPE_FALLBACK.map(([label])=>api('/api/dive-points?'+new URLSearchParams({type:label})).then(d=>d.items||[]).catch(()=>[])));
    const all=(await api('/api/dive-points').catch(()=>({items:[]}))).items||[];
    const items=DIVE_TYPE_FALLBACK.map(([label,level,dmin,dmax],i)=>{ const pts=lists[i]; const byC={}; pts.forEach(p=>byC[p.country]=(byC[p.country]||0)+1); const top=Object.entries(byC).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,4).map(([name,count])=>({name,count}));
      return {key:wdKey(label),slug:label.toLowerCase(),label,level,cert:'',depth_min:dmin,depth_max:dmax,summary:`Puntos del catálogo clasificados como «${label}».`,count:pts.length,countries:Object.keys(byC).length,centers:0,top_countries:top}; });
    return {items,totals:{points:all.length,countries:new Set(all.map(p=>p.country)).size},legacy:true};
  }
  let __legacyCenters=null;
  async function legacyCenterDirectory(qs){
    if(!__legacyCenters) __legacyCenters=(await api('/api/centers')).items||[];
    let rows=__legacyCenters.slice(); const q=wdFold(qs.get('q')).trim();
    if(q){ const words=q.split(/\s+/); rows=rows.filter(c=>{ const t=wdFold([c.name,c.city,c.region,c.specialties,c.tagline].join(' ')); return words.every(w=>t.includes(w)); }); }
    const facet={}; rows.forEach(c=>facet[c.country]=(facet[c.country]||0)+1);
    const country=qs.get('country'); if(country) rows=rows.filter(c=>c.country===country);
    if((qs.get('only')||'').includes('reviews')) rows=rows.filter(c=>Number(c.review_count)>0);
    const sort=qs.get('sort')||'recommended', name=c=>wdFold(c.name);
    rows.sort(sort==='rating'?(a,b)=>(!b.review_count-!a.review_count)||(b.rating_average-a.rating_average)||name(a).localeCompare(name(b)):sort==='reviews'?(a,b)=>(b.review_count-a.review_count)||name(a).localeCompare(name(b)):(a,b)=>(!!b.cover_url-!!a.cover_url)||(b.review_count-a.review_count)||name(a).localeCompare(name(b)));
    const per=Number(qs.get('per_page')||12), page=Number(qs.get('page')||1);
    return {items:rows.slice((page-1)*per,page*per),total:rows.length,page,per_page:per,countries:Object.entries(facet).sort((a,b)=>b[1]-a[1]).map(([name,count])=>({name,count})),legacy:true};
  }
  const POINT_COUNTRY_IMAGES={Egipto:'egipto',Maldivas:'maldivas',Australia:'australia',Tailandia:'tailandia',Ecuador:'galapagos',Micronesia:'micronesia'};
  function pointImg(p){ const c=POINT_COUNTRY_IMAGES[p.country]; if(c) return `/assets/images/${c}.webp`; if(/cenote/i.test(p.name||'')||/cenote/i.test(p.dive_type||'')) return '/assets/images/mexico.webp'; const pool=['/assets/images/fondosuperior.webp','/assets/images/BUCEADORES.webp','/assets/images/australia.webp','/assets/images/micronesia.webp','/assets/images/tailandia.webp','/assets/images/fondo.webp']; if(/cueva|cavern|t[uú]nel/i.test(p.dive_type||'')) return '/assets/images/fondo.webp'; return /pecio|wreck/i.test((p.dive_type||'')+' '+(p.name||''))?'/assets/images/logbook1.webp':pool[Math.abs(Number(p.id||0))%pool.length]; }
  function certificationGuidance(p, userCertification){
    const level=(userCertification||'').toUpperCase();
    const diff=(p.difficulty||'').toLowerCase(); const dt=(p.dive_type||'').toLowerCase();
    let rec='OWD', label='Adecuada para iniciación', note='Para una inmersión de iniciación o recreativa sencilla, una certificación de entrada suele ser suficiente, siempre según el centro y las condiciones reales.';
    if(p.recommended_certification_name) rec=p.recommended_certification_name;
    if(dt.includes('cenote')||dt.includes('cueva')||dt.includes('canyon')||dt.includes('cañón')) { rec=p.recommended_certification_name||'CAVE / CAVERN'; label='Formación específica'; note='Este tipo de entorno puede requerir formación específica adicional y experiencia previa. El centro debe confirmar los requisitos exactos.'; }
    else if(dt.includes('pecio')||dt.includes('wreck')) { rec=p.recommended_certification_name||'ESPECIALIDAD'; label='Especialidad recomendable'; note='Para penetración o procedimientos específicos de pecios pueden ser necesarias especialidades adicionales. La ficha no sustituye los requisitos del operador.'; }
    else if(diff==='avanzado'||Number(p.max_depth||0)>30) { rec=p.recommended_certification_name||'RESCUE'; label='Perfil avanzado'; note='Por profundidad o complejidad, se recomienda experiencia avanzada y formación adecuada antes de reservar.'; }
    else if(diff==='intermedio'||Number(p.max_depth||0)>18) { rec=p.recommended_certification_name||'AOWD'; label='Perfil intermedio'; note='Suele encajar mejor con un buceador con formación avanzada y experiencia reciente.'; }
    const has=level && level===String(rec).toUpperCase();
    const personal=level ? `<div class="notice ${has?'success':'warning'}" style="margin-top:12px"><strong>Tu perfil: ${escapeHtml(userCertification)}.</strong> ${has?'Tu nivel coincide con la orientación de esta ficha.':'Esta ficha recomienda '+escapeHtml(rec)+'. Antes de reservar, confirma con el centro que tu certificación y experiencia son adecuadas.'}</div>` : `<p style="margin-top:10px;color:var(--muted)">Añade tu nivel de certificación en <a href="#/cuenta">Mi cuenta</a> y WORLDIVES podrá personalizar esta orientación.</p>`;
    return `<section class="notice certification-guidance" style="margin-top:20px"><p class="eyebrow">FORMACIÓN Y ADECUACIÓN</p><h3>${escapeHtml(label)}</h3><div class="data-grid" style="margin-top:12px"><div class="data-item"><span>Orientación</span><strong>${escapeHtml(rec)}</strong></div><div class="data-item"><span>Dificultad del punto</span><strong>${escapeHtml(p.difficulty||'Por confirmar')}</strong></div></div><p style="margin-top:12px">${escapeHtml(note)}</p>${personal}</section>`;
  }
async function renderVirtual(params){
  const id=Number(params.get('experience')||0); const pointId=Number(params.get('point')||0); const data=pointId?await api('/api/dive-points/'+pointId+'/virtual').catch(()=>({items:[]})):{items:[]}; const v=(data.items||[]).find(x=>x.id===id);
  if(!v){setApp('<section class="page"><div class="empty"><h2>Recorrido no encontrado</h2><p>Esta experiencia todavía no está disponible.</p><a class="btn btn-primary" href="#/puntos">Volver a puntos</a></div></section>');return;}
  const type=v.experience_type;
  // G3: only https:// links from the allowed providers are ever embedded, and only after the visitor clicks
  // «Cargar vídeo» (the provider receives the visitor's IP and may set its own cookies).
  const embedOk=wdEmbedAllowed(v.url,data.embed_domains);
  let body='';
  if(type==='video360' && embedOk){ body=`<div class="virtual-frame virtual-consent" id="virtual-consent"><div class="virtual-consent-box"><div class="virtual-empty-icon">360°</div><h2>Vídeo de un servicio externo</h2><p>Al cargarlo te conectarás con <strong>${escapeHtml(wdHost(v.url))}</strong>, que recibirá tu dirección IP y puede usar sus propias cookies. <a href="#/legal/cookies">Más información</a>.</p><button class="btn btn-primary" type="button" id="virtual-load">Cargar vídeo</button></div></div>`; }
  else if(type==='streetview' && embedOk){ body=`<div class="virtual-frame virtual-link-card"><p class="eyebrow">STREET VIEW</p><h2>Visita virtual</h2><p>Esta experiencia se abre en el visor del proveedor (${escapeHtml(wdHost(v.url))}), en una pestaña nueva.</p><a class="btn btn-primary" target="_blank" rel="noopener noreferrer" href="${escapeHtml(v.url)}">Abrir Street View</a></div>`; }
  else if(v.media_path && type==='video360'){ body=`<div class="virtual-frame"><video src="${escapeHtml(v.media_path)}" controls playsinline preload="metadata" class="virtual-video" title="${escapeHtml(v.title)}"></video></div>`; }
  else if(v.media_path){ body=`<div class="virtual-frame"><img src="${escapeHtml(v.media_path)}" alt="${escapeHtml(v.title)}" class="panorama-placeholder"></div>`; }
  else { body=`<div class="virtual-frame virtual-link-card"><div class="virtual-empty-icon">360°</div><h2>Experiencia preparada</h2><p>Este espacio está preparado para incorporar el archivo 360° de la inmersión.</p></div>`; }
  setApp(`<section class="page virtual-view-page"><div class="breadcrumb"><a href="#/punto?id=${pointId}">Volver a ${escapeHtml((await api('/api/dive-points/'+pointId)).item.name)}</a></div><p class="eyebrow">WORLDIVES DISCOVERY · RECORRIDO VIRTUAL</p><h1>${escapeHtml(v.title)}</h1><p class="lead">${escapeHtml(v.description||'Explora la inmersión antes de entrar al agua.')}</p>${body}</section>`);
  $('#virtual-load')?.addEventListener('click',()=>{ const box=$('#virtual-consent'); if(!box||!wdEmbedAllowed(v.url,data.embed_domains)) return; box.classList.remove('virtual-consent'); box.innerHTML=''; const f=document.createElement('iframe'); f.src=v.url; f.title=v.title||'Recorrido virtual'; f.allow='autoplay; fullscreen; xr-spatial-tracking'; f.allowFullscreen=true; f.referrerPolicy='strict-origin-when-cross-origin'; f.setAttribute('sandbox','allow-scripts allow-same-origin allow-presentation allow-popups'); box.appendChild(f); });
}
// G3: same rule as the server (wod.security.embed_allowed): https and an allowed provider (host suffix + optional path).
const WD_EMBED_DEFAULT=['youtube-nocookie.com','player.vimeo.com','google.com/maps'];
function wdHost(u){ try{ return new URL(u).hostname; }catch{ return ''; } }
function wdEmbedAllowed(u,domains){ if(!u) return false; let p; try{ p=new URL(String(u)); }catch{ return false; } if(p.protocol!=='https:'||p.username||p.password) return false; const host=p.hostname.toLowerCase(); return (domains&&domains.length?domains:WD_EMBED_DEFAULT).some(rule=>{ const [h,...rest]=String(rule).split('/'); const path=rest.join('/'); return (host===h||host.endsWith('.'+h)) && (!path||p.pathname.startsWith('/'+path)); }); }
  function centerRatingMarkup(c, compact=false){
    const avg=Number(c.rating_average||0); const count=Number(c.review_count||0);
    if(!count) return `<span class="center-rating empty-rating"><span class="stars muted-stars">★★★★★</span><span>Sin reseñas todavía</span></span>`;
    const rounded=Math.round(avg); const stars='★★★★★'.split('').map((_,i)=>`<span class="star ${i<rounded?'filled':''}">★</span>`).join('');
    return `<span class="center-rating" aria-label="${avg.toFixed(1)} de 5 estrellas, ${count} reseñas"><span class="stars">${stars}</span><strong>${avg.toFixed(1)}</strong><span>${count} ${count===1?'reseña':'reseñas'}</span></span>`;
  }
  function reviewCard(r,ri={}){
    const rating=Math.max(1,Math.min(5,Number(r.rating||0))); const stars='★★★★★'.split('').map((_,i)=>`<span class="star ${i<rating?'filled':''}">★</span>`).join('');
    const date=r.created_at?new Date(r.created_at).toLocaleDateString(wdLocale(),{day:'numeric',month:'short',year:'numeric'}):'';
    const reply=r.reply_body?`<div class="review-reply"><p class="review-reply-h">${wdIcon('message',14)} Respuesta del centro${r.reply_at?` · <time>${escapeHtml(new Date(r.reply_at).toLocaleDateString(wdLocale(),{day:'numeric',month:'short',year:'numeric'}))}</time>`:''}</p><p>${escapeHtml(r.reply_body)}</p></div>`:'';
    const acts=[ri.can_reply?`<button type="button" class="btn-link rv-reply" data-id="${r.id}">${r.reply_body?'Editar respuesta':'Responder'}</button>`:'',
      ri.is_admin?`<button type="button" class="btn-link rv-hide" data-id="${r.id}">Ocultar reseña</button>`:'',
      `<button type="button" class="wd-report" data-report="review" data-report-id="${r.id}">${wdIcon('alert',13)} Denunciar</button>`].filter(Boolean).join('');
    return `<article class="review-card" id="review-${r.id}"><div class="review-head"><div><strong>${escapeHtml((r.fullname||'Buceador').split(' ')[0])}</strong>${r.verified?'<span class="verified-review">✓ Inmersión verificada</span>':''}</div><time>${escapeHtml(date)}</time></div><div class="review-stars">${stars}</div>${r.title?`<h4>${escapeHtml(r.title)}</h4>`:''}${r.body?`<p>${escapeHtml(r.body)}</p>`:''}${reply}<div class="review-actions">${acts}</div></article>`;
  }
  // «Denunciar»: any button with data-report="review|center|point|experience|photo|promotion|profile" and data-report-id.
  async function openReportModal(type,id,label){
    const info=await legalInfo(); const me=state.me?.user; const esc=escapeHtml;
    const {el,close}=wdOpenModal({id:'report-modal',title:'Denunciar contenido',subtitle:label?esc(label):'Revisaremos la denuncia y te comunicaremos la decisión.',
      body:`<form id="rpm-form" class="form-grid"><div class="field full"><label for="rpm-reason">Motivo</label><select id="rpm-reason" required><option value="">Elige un motivo…</option>${Object.entries(info.reasons||{}).map(([k,v])=>`<option value="${k}">${esc(v)}</option>`).join('')}</select></div>
        <div class="field full"><label for="rpm-details">Explica por qué es ilegal o incumple las normas</label><textarea id="rpm-details" rows="4" minlength="20" maxlength="3000" required></textarea></div>
        ${me?'':`<div class="field"><label for="rpm-name">Tu nombre</label><input id="rpm-name" maxlength="120"></div><div class="field"><label for="rpm-email">Tu email (para comunicarte la decisión)</label><input id="rpm-email" type="email" maxlength="160"></div>`}
        <label class="lg-check full"><input type="checkbox" id="rpm-faith" required> <span>Declaro que la información es exacta y que la envío de buena fe.</span></label></form>`,
      footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="rpm-send">Enviar denuncia</button>'});
    translateTree(el);
    $('#rpm-send',el).onclick=async()=>{ if(!$('#rpm-form',el).reportValidity()) return; const btn=$('#rpm-send',el); btn.disabled=true;
      try{ const r=await postJSON('/api/reports',{reason:$('#rpm-reason',el).value,details:$('#rpm-details',el).value,target_type:type,target_id:+id,target_url:location.href,
          name:$('#rpm-name',el)?.value||'',email:$('#rpm-email',el)?.value||'',good_faith:$('#rpm-faith',el).checked});
        delete el.dataset.dirty; close(); toast(`Denuncia recibida (${r.ref}). La revisaremos con diligencia.`); }
      catch(err){ toast(err.message); btn.disabled=false; } };
  }
  document.addEventListener('click',e=>{ const b=e.target.closest('[data-report]'); if(!b) return; e.preventDefault(); openReportModal(b.dataset.report,b.dataset.reportId,b.dataset.reportLabel||''); });
  async function renderCenterDetail(params){
    const id=Number(params?.get?.('id')||params||0);
    if(!id){setApp('<section class="page"><div class="empty"><h2>Centro no encontrado</h2><a class="btn btn-primary" href="#/centros">Volver a centros</a></div></section>');return;}
    const still=navGuard(); const d=await api('/api/centers/'+id),c=d.item; if(!still()) return;
    const reviews=d.reviews||[]; const reviewInfo=d.review||{};
    const reviewSummary=centerRatingMarkup(c);
    const reviewForm=reviewInfo.can_review ? `<form id="center-review-form" class="review-form"><div class="field"><label>Tu valoración</label><div class="star-picker" id="review-stars" role="radiogroup" aria-label="Selecciona una valoración">${[1,2,3,4,5].map(n=>`<button type="button" class="pick-star" data-rating="${n}" aria-label="${n} estrellas">★</button>`).join('')}</div></div><div class="field"><label for="review-title">Título <span>(opcional)</span></label><input id="review-title" maxlength="120" value="${escapeHtml(reviewInfo.current?.title||'')}" placeholder="¿Qué destacarías de tu experiencia?"></div><div class="field"><label for="review-body">Tu reseña <span>(opcional)</span></label><textarea id="review-body" maxlength="1200" placeholder="Cuéntale a otros buceadores cómo fue la experiencia.">${escapeHtml(reviewInfo.current?.body||'')}</textarea></div><div class="form-actions"><button class="btn btn-primary" type="submit">${reviewInfo.current?'Actualizar mi reseña':'Publicar reseña'}</button></div></form>` : `<div class="review-gate"><strong>${escapeHtml(reviewInfo.reason||'Podrás dejar una reseña verificada cuando tengas una reserva pagada o confirmada con este centro.')}</strong>${reviewInfo.current?`<p>Ya tienes una reseña publicada. Si vuelves a esta sección podrás editarla.</p>`:''}</div>`;
    const esc=escapeHtml; const services=(d.services||[]).slice().sort((a,b)=>(a.service_type==='alquiler_equipo')-(b.service_type==='alquiler_equipo')||((b.next_slots||[]).length>0)-((a.next_slots||[]).length>0)||String(a.title).localeCompare(String(b.title),'es')); const exps=d.experiences||[]; const gallery=c.gallery||[];
    const socials=[['instagram_url','Instagram'],['facebook_url','Facebook'],['youtube_url','YouTube'],['tiktok_url','TikTok'],['twitter_url','X']].filter(x=>c[x[0]]);
    const typeLabel=v=>(SERVICE_TYPES.find(x=>x.value===v)||{label:'Actividad'}).label;
    const svcCard=s=>{const isRental=s.service_type==='alquiler_equipo'; const slots=s.next_slots||[];
      const off=s.bookable===false;
      return `<article class="cp-service" style="--svc:${esc(s.color||'#0b7a89')}"><div class="cp-service-head"><span class="cp-service-icon">${wdIcon(s.service_type,22)}</span><div><h3>${esc(s.title)}</h3><p>${esc(typeLabel(s.service_type))}${s.duration_minutes?' · '+esc(wdDuration(s.duration_minutes)):''}</p>${isRental?'':wdModeTag(s)}</div><div class="cp-price"><strong>${wdMoney(s.price,s.currency)}</strong><small>${isRental?'tarifa base':'por persona'}</small></div></div>
        ${s.description?`<p class="cp-service-desc">${esc(s.description)}</p>`:''}
        ${isRental||off?'':`<div class="cp-slots">${slots.length?slots.map(sl=>`${Number(sl.spots_available)<=0?`<span class="cp-slot is-full" aria-disabled="true"><strong>${esc(wdDay(sl.slot_date))}</strong><span>${esc(sl.slot_time)}</span><small>Completa</small></span>`:`<a class="cp-slot" href="#/reservar?center=${c.id}&service=${s.id}&slot=${sl.id}"><strong>${esc(wdDay(sl.slot_date))}</strong><span>${esc(sl.slot_time)}</span><small>${sl.spots_available} plazas</small></a>`}`).join(''):'<span class="cp-slots-empty">Próximas fechas por anunciar. Puedes solicitarla igualmente.</span>'}</div>`}
        ${off?`<span class="btn cp-book is-disabled" aria-disabled="true">No admite reservas ahora mismo</span>`:`<a class="btn ${isRental?'':'btn-primary'} cp-book" href="#/reservar?center=${c.id}&service=${s.id}">${isRental?'Añadir a una reserva':s.booking_mode==='payment'?(Number(s.price)>0?'Reservar y pagar':'Reservar'):'Enviar solicitud'}</a>`}</article>`;};
    setApp(`<section class="cp">
      <div class="cp-hero ${c.cover_url?'has-cover':''}" style="${c.cover_url?`--cover:url('${esc(c.cover_url)}')`:''}">
        <div class="cp-hero-inner">
          <div class="breadcrumb cp-crumb"><a href="#/centros">Centros</a> / ${esc(c.name)}</div>
          <div class="cp-id">${centerLogoMarkup(c,'88px')}<div><h1>${esc(c.name)}</h1>${c.tagline?`<p class="cp-tagline">${esc(c.tagline)}</p>`:''}<div class="cp-hero-meta">${reviewSummary}${c.city||c.country?`<span>${wdIcon('globe',15)}${esc([c.city,c.region,c.country].filter(Boolean).join(', '))}</span>`:''}</div></div></div>
          <div class="cp-hero-actions"><a class="btn btn-primary" href="#/reservar?center=${c.id}">Reservar</a>${c.phone?`<a class="btn cp-ghost" href="tel:${esc(String(c.phone).replace(/\s+/g,''))}">Llamar</a>`:''}${c.email?`<a class="btn cp-ghost" href="mailto:${esc(c.email)}">Escribir</a>`:''}</div>
        </div>
      </div>
      <div class="cp-facts">${[['Idiomas',c.languages],['Horario',c.opening_hours],['Especialidades',c.specialties],['Puntos de buceo',d.points.length?String(d.points.length):'']].filter(x=>x[1]).map(x=>`<div><span>${x[0]}</span><strong>${esc(x[1])}</strong></div>`).join('')}</div>
      <div class="cp-layout">
        <article class="cp-main">
          ${c.description?`<section class="cp-section"><h2>Sobre el centro</h2><p class="cp-about">${esc(c.description)}</p></section>`:''}
          <section class="cp-section"><h2>Actividades y precios</h2>${services.length?`<div class="cp-services">${services.map(svcCard).join('')}</div>`:'<div class="empty">Este centro todavía no ha publicado actividades. Puedes contactar directamente para reservar.</div>'}</section>
          ${exps.length?`<section class="cp-section"><h2>Viajes y experiencias</h2><div class="cp-exps">${exps.map(e=>`<a class="cp-exp" href="#/experiencia?id=${e.travel_offer_id}"><span>${esc(e.destination_title||'')}</span><strong>${esc(e.title)}</strong><small>${e.start_date?esc(wdDay(e.start_date))+' · ':''}${e.price!=null?wdMoney(e.price,e.currency):'Precio a consultar'}</small></a>`).join('')}</div></section>`:''}
          ${gallery.length?`<section class="cp-section"><h2>Galería</h2><div class="cp-gallery">${gallery.map((u,i)=>`<button type="button" class="cp-photo" data-i="${i}"><img src="${esc(u)}" alt="Foto ${i+1} de ${esc(c.name)}" loading="lazy"></button>`).join('')}</div></section>`:''}
          <section class="reviews-section cp-section" id="cp-reviews"><div class="reviews-head"><div><h2>Reseñas</h2><p>Opiniones de buceadores que han completado una inmersión con este centro.</p></div><div class="review-summary-box">${reviewSummary}</div></div>${reviewForm}<div class="reviews-list">${reviews.length?reviews.map(r=>reviewCard(r,reviewInfo)).join(''):'<div class="empty"><h3>Aún no hay reseñas</h3><p>Cuando los primeros buceadores completen una inmersión y compartan su experiencia, aparecerán aquí.</p></div>'}</div></section>
        </article>
        <aside class="cp-side">
          <section class="cp-card"><h3>Contacto</h3><dl>${c.phone?`<div><dt>Teléfono</dt><dd><a href="tel:${esc(String(c.phone).replace(/\s+/g,''))}">${esc(c.phone)}</a></dd></div>`:''}${c.email?`<div><dt>Email</dt><dd><a href="mailto:${esc(c.email)}">${esc(c.email)}</a></dd></div>`:''}${c.website?`<div><dt>Web</dt><dd><a href="${esc(c.website)}" target="_blank" rel="noopener">${esc(String(c.website).replace(/^https?:\/\//,'').replace(/\/$/,''))}</a></dd></div>`:''}${c.address?`<div><dt>Dirección</dt><dd>${esc(c.address)}</dd></div>`:''}</dl>
            ${c.latitude&&c.longitude?`<a class="btn cp-map" target="_blank" rel="noopener" href="https://www.openstreetmap.org/?mlat=${c.latitude}&mlon=${c.longitude}#map=15/${c.latitude}/${c.longitude}">Ver en el mapa</a>`:''}
            ${socials.length?`<div class="cp-socials">${socials.map(x=>`<a href="${esc(c[x[0]])}" target="_blank" rel="noopener noreferrer">${x[1]}</a>`).join('')}</div>`:''}
            <a class="btn btn-primary cp-side-book" href="#/reservar?center=${c.id}">Reservar con ${esc(c.name)}</a>
            <button type="button" class="wd-report" data-report="center" data-report-id="${c.id}" data-report-label="${esc(c.name)}">${wdIcon('alert',13)} Denunciar contenido</button></section>
          <section class="cp-card"><h3>Dónde bucea</h3>${d.points.length?`<ul class="cp-points">${d.points.slice(0,10).map(p=>`<li><a href="#/punto?id=${p.id}">${esc(p.name)}</a><span>${esc(p.region||p.country||'')}</span></li>`).join('')}</ul>`:'<p class="cp-muted">Este centro aún no ha indicado sus puntos habituales.</p>'}</section>
        </aside>
      </div>
    </section>`);
    $$('.cp-photo').forEach(b=>b.onclick=()=>{let i=+b.dataset.i; const show=()=>{const {el}=wdOpenModal({id:'cp-lightbox',size:'lg',title:esc(c.name),subtitle:`Foto ${i+1} de ${gallery.length}`,body:`<img class="cp-lightbox-img" src="${esc(gallery[i])}" alt="">`,footer:`<button type="button" class="wd-report" data-report="photo" data-report-id="${c.id}" data-report-label="Foto ${i+1} de ${esc(c.name)}">${wdIcon('alert',13)} Denunciar foto</button>`+(gallery.length>1?`<button type="button" class="btn" id="cp-prev">Anterior</button><button type="button" class="btn" id="cp-next">Siguiente</button>`:'')}); el.querySelector('#cp-prev')?.addEventListener('click',()=>{i=(i-1+gallery.length)%gallery.length;show();}); el.querySelector('#cp-next')?.addEventListener('click',()=>{i=(i+1)%gallery.length;show();});}; show();});
    $$('.rv-reply').forEach(b=>b.onclick=()=>{ const r=reviews.find(x=>x.id===+b.dataset.id)||{};
      const {el,close}=wdOpenModal({id:'review-reply',title:'Responder a la reseña',subtitle:'Una única respuesta pública. Puedes editarla o borrarla.',
        body:`<div class="field"><label for="rr-body">Tu respuesta</label><textarea id="rr-body" rows="5" maxlength="1000">${esc(r.reply_body||'')}</textarea><small>Sé respetuoso y no incluyas datos personales del cliente.</small></div>`,
        footer:`${r.reply_body?'<button type="button" class="btn danger" id="rr-del">Borrar respuesta</button>':''}<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="rr-save">Publicar respuesta</button>`});
      const save=async body=>{ try{ await postJSON(`/api/reviews/${r.id}/reply`,{body}); delete el.dataset.dirty; close(); toast(body?'Respuesta publicada.':'Respuesta borrada.'); renderCenterDetail(new URLSearchParams({id:String(id)})); }catch(err){ toast(err.message); } };
      $('#rr-save',el).onclick=()=>save($('#rr-body',el).value); $('#rr-del',el)?.addEventListener('click',()=>save('')); });
    $$('.rv-hide').forEach(b=>b.onclick=()=>{
      const {el,close}=wdOpenModal({id:'review-hide',title:'Ocultar reseña',subtitle:'Se enviará el motivo a quien la escribió.',
        body:`<div class="field"><label for="rh-why">Motivo</label><textarea id="rh-why" rows="4" maxlength="1000" required placeholder="Qué norma incumple y por qué."></textarea></div>`,
        footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn danger" id="rh-ok">Ocultar</button>'});
      $('#rh-ok',el).onclick=async()=>{ try{ await postJSON(`/api/admin/reviews/${b.dataset.id}/moderate`,{active:false,reason:$('#rh-why',el).value}); delete el.dataset.dirty; close(); toast('Reseña ocultada.'); renderCenterDetail(new URLSearchParams({id:String(id)})); }catch(err){ toast(err.message); } }; });
    if(c.online_booking===false){
      $$('.cp-page a[href^="#/reservar"], .cp a[href^="#/reservar"]').forEach(a=>{ const b=document.createElement('button'); b.type='button'; b.className=a.className.replace('cp-slot','btn cp-book'); b.textContent=translateString('Solicitar información'); b.onclick=()=>openInfoRequest({center_id:c.id,name:c.name}); a.replaceWith(b); });
      $$('.cp-slots').forEach(x=>x.remove());
      $('.cp-services')?.insertAdjacentHTML('beforebegin',`<div class="notice">${wdIcon('info',16)} Este centro todavía no tiene reserva online en WORLDIVES. Puedes enviarle una solicitud de información.</div>`);
    } else {
      $$('.cp a[href^="#/reservar"]').forEach(a=>a.addEventListener('click',()=>{ postJSON('/api/stats/track',{event:'book_click',type:'center',id:c.id}).catch(()=>{}); }));
    }
    if(c.reviews_off) $('#cp-reviews')?.remove();
    if(params?.get?.('resena')) setTimeout(()=>{ const r=$('#cp-reviews'); if(r){ r.scrollIntoView({behavior:'smooth',block:'start'}); $('#review-title')?.focus({preventScroll:true}); } },250);
    if(reviewInfo.can_review){
      let selected=Number(reviewInfo.current?.rating||0);
      const paint=()=>$$('.pick-star').forEach(b=>b.classList.toggle('selected',Number(b.dataset.rating)<=selected));
      $$('.pick-star').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.rating);paint();}); paint();
      $('#center-review-form').onsubmit=async e=>{e.preventDefault(); if(!selected){toast('Selecciona una valoración de 1 a 5 estrellas.');return;} try{await postJSON(`/api/centers/${id}/reviews`,{rating:selected,title:$('#review-title').value,body:$('#review-body').value});toast('Tu reseña se ha guardado.');await renderCenterDetail(new URLSearchParams({id:String(id)}));}catch(err){toast(err.message)}};
    }
  }

  // ---------------------------------------------------------------------------
  // Directorio público de centros: búsqueda en servidor, filtros rápidos y paginación.
  // ---------------------------------------------------------------------------
  const WD_SEA_IMAGES=['/assets/images/fondosuperior.webp','/assets/images/BUCEADORES.webp','/assets/images/australia.webp','/assets/images/logbook1.webp','/assets/images/galapagos.webp','/assets/images/fondo.webp'];
  const WD_COUNTRY_IMAGES={Egipto:'/assets/images/egipto.webp',Australia:'/assets/images/australia.webp','México':'/assets/images/mexico.webp',Maldivas:'/assets/images/maldivas.webp',Ecuador:'/assets/images/galapagos.webp',Tailandia:'/assets/images/tailandia.webp',Micronesia:'/assets/images/micronesia.webp'};
  function centerCoverImg(c){ return c.cover_url || WD_COUNTRY_IMAGES[c.country] || WD_SEA_IMAGES[Math.abs(Number(c.id||0))%WD_SEA_IMAGES.length]; }
  function centerMonogram(c,size='52px'){
    const stop=/^(de|del|la|el|los|las|y|s\.?l\.?|centro|buceo|diving|dive|center|centre|club|escuela|scuba)$/i;
    const words=String(c.name||'').replace(/[^\p{L}\p{N} ]/gu,' ').split(/\s+/).filter(Boolean);
    const strong=words.filter(w=>!stop.test(w)); const use=strong.length?strong:words;
    const ini=((use[0]||'?')[0]+(use[1]?.[0]||'')).toUpperCase();
    const hue=[192,200,176,210,168,220][Math.abs(Number(c.id||0))%6];
    return `<span class="wd-monogram" style="width:${size};height:${size};--h:${hue}" aria-hidden="true">${escapeHtml(ini)}</span>`;
  }
  function centerSpecialties(c){ return String(c.specialties||'').split(/\s*[·;,|]\s*/).map(s=>s.trim()).filter(Boolean); }
  function centerCard(c){
    const id=encodeURIComponent(c.id), online=Number(c.services_count||0)>0, reviews=Number(c.review_count||0);
    const tags=centerSpecialties(c).filter(t=>!/^buceo recreativo$/i.test(t));
    const place=[c.city,c.country].filter(Boolean).map(escapeHtml).join(' · ');
    const rating=reviews?`<span class="cd-rating"><span class="cd-star">★</span><strong>${Number(c.rating_average||0).toFixed(1)}</strong><span>(${reviews})</span></span>`:'<span class="cd-rating is-new">Sin reseñas aún</span>';
    return `<article class="cd-card">
      <a class="cd-media" href="#/centro?id=${id}" tabindex="-1" aria-hidden="true"><img src="${escapeHtml(centerCoverImg(c))}" alt="" loading="lazy">
        <span class="cd-badges">${c.instant?'<span class="cd-badge is-live">Confirmación inmediata</span>':online?'<span class="cd-badge">Bajo petición</span>':''}${Number(c.spots_week||0)>0?'<span class="cd-badge">Plazas esta semana</span>':''}</span></a>
      <div class="cd-body">
        <div class="cd-id"><span class="cd-logo">${centerLogoMarkup(c,'48px')}</span><div><h3><a href="#/centro?id=${id}">${escapeHtml(c.name)}</a></h3><p class="cd-place">${wdIcon('pin',14)}${place||'Ubicación por confirmar'}</p></div></div>
        <div class="cd-line">${rating}${Number(c.point_count||0)?`<span class="cd-dot">${c.point_count} ${Number(c.point_count)===1?'punto':'puntos'} de buceo</span>`:''}</div>
        <p class="cd-desc">${escapeHtml(c.tagline||c.description||'Centro de buceo en '+(c.city||c.country||'el catálogo')+'.')}</p>
        ${tags.length?`<div class="cd-tags">${tags.slice(0,3).map(t=>`<span>${escapeHtml(t)}</span>`).join('')}${tags.length>3?`<span class="more">+${tags.length-3}</span>`:''}</div>`:''}
      </div>
      <div class="cd-foot">
        <div class="cd-fact"><small>Desde</small><strong>${c.price_from?wdMoney(c.price_from):'<span class="muted">Consultar</span>'}</strong></div>
        <div class="cd-fact"><small>Próxima salida</small><strong>${c.next_slot?escapeHtml(wdDay(c.next_slot)):'<span class="muted">Bajo petición</span>'}</strong></div>
        <a class="btn ${online?'btn-primary':''} cd-cta" href="${online?`#/reservar?center=${id}`:`#/centro?id=${id}`}">${online?'Reservar':'Ver centro'}</a>
      </div>
    </article>`;
  }
  const CD_FLAGS=[['instant','Confirmación inmediata'],['online','Reserva online'],['week','Plazas esta semana'],['courses','Cursos'],['try','Bautizos'],['trips','Viajes'],['reviews','Con reseñas']];
  const CD_SORTS=[['recommended','Recomendados'],['rating','Mejor valorados'],['reviews','Más reseñas'],['price','Precio más bajo'],['name','Nombre A-Z']];
  async function renderCenters(params){
    params=params instanceof URLSearchParams?params:new URLSearchParams();
    const st={point:/^\d+$/.test(params.get('point')||'')?params.get('point'):'',q:params.get('q')||'',country:params.get('country')||'',type:params.get('type')||'',sort:CD_SORTS.some(s=>s[0]===params.get('sort'))?params.get('sort'):'recommended',only:new Set((params.get('only')||'').split(',').filter(k=>CD_FLAGS.some(f=>f[0]===k))),page:1};
    const typesRes=await api('/api/dive-types').catch(()=>({items:DIVE_TYPE_FALLBACK.map(([label])=>({key:wdKey(label),label,count:1}))}));
    const types=(typesRes.items||[]).filter(t=>t.count>0||t.centers>0);
    setApp(`<section class="cd-page">
      <header class="tp-hero cd-hero">${heroImg('hero:centros')}<div class="tp-hero-in cd-hero-in">
        <p class="eyebrow">Directorio</p><h1>Centros de buceo</h1>
        <p class="lead">Compara centros, consulta sus próximas salidas y reserva directamente con ellos.</p>
        <form class="cd-search" id="cd-search" role="search">
          <label class="cd-field cd-field-q">${wdIcon('search',18)}<span class="sr-only">Buscar</span><input id="cd-q" type="search" autocomplete="off" placeholder="Centro, ciudad o especialidad" value="${escapeHtml(st.q)}"></label>
          <label class="cd-field">${wdIcon('pin',18)}<span class="sr-only">País</span><select id="cd-country"><option value="">Todos los países</option>${st.country?`<option selected>${escapeHtml(st.country)}</option>`:''}</select></label>
          <button class="btn btn-primary" type="submit">Buscar</button>
        </form>
      </div></header>
      <div class="cd-wrap">
        <div class="cd-toolbar">
          <div class="cd-chips" role="group" aria-label="Filtros rápidos">${CD_FLAGS.map(([k,l])=>`<button type="button" class="cd-chip" data-flag="${k}" aria-pressed="${st.only.has(k)}">${l}</button>`).join('')}</div>
          <div class="cd-tools">
            <label><span class="sr-only">Tipo de buceo</span><select id="cd-type"><option value="">Cualquier tipo de buceo</option>${types.map(t=>`<option value="${t.key}" ${t.key===st.type?'selected':''}>${escapeHtml(t.label)}</option>`).join('')}</select></label>
            <label><span class="sr-only">Ordenar</span><select id="cd-sort">${CD_SORTS.map(([k,l])=>`<option value="${k}" ${k===st.sort?'selected':''}>${l}</option>`).join('')}</select></label>
          </div>
        </div>
        <div class="cd-results-head"><p id="cd-count" aria-live="polite">Buscando centros…</p><button type="button" class="cd-clear" id="cd-clear" hidden>Quitar filtros</button></div>
        <div class="cd-grid" id="cd-grid"></div>
        <div class="cd-more"><button class="btn" type="button" id="cd-more" hidden>Mostrar más centros</button></div>
        <aside class="cd-owner"><div><p class="eyebrow">Para centros de buceo</p><h2>Tu escaparate y tu motor de reservas</h2><p>Publica salidas, cursos y viajes con plazas reales, cobra online y gestiona la agenda y los clientes desde un único panel.</p></div><a class="btn btn-primary" href="#/registro">Dar de alta mi centro</a></aside>
      </div>
    </section>`);
    const grid=$('#cd-grid'), more=$('#cd-more'), count=$('#cd-count'), clear=$('#cd-clear');
    let seq=0, loaded=0, countriesFilled=false;
    const skeleton=n=>Array.from({length:n},()=>'<div class="cd-card is-skeleton" aria-hidden="true"><div class="cd-media"></div><div class="cd-body"><i></i><i></i><i></i></div></div>').join('');
    const hasFilters=()=>!!(st.point||st.q||st.country||st.type||st.only.size);
    const load=async(append=false)=>{
      const mine=++seq;
      if(!append){ st.page=1; loaded=0; grid.innerHTML=skeleton(6); more.hidden=true; }
      more.disabled=true;
      const qs=new URLSearchParams({point:st.point,q:st.q,country:st.country,type:st.type,only:[...st.only].join(','),sort:st.sort,page:String(st.page),per_page:'12'});
      for(const k of [...qs.keys()]) if(!qs.get(k)) qs.delete(k);
      let d;
      try{ try{ d=await api('/api/center-directory?'+qs); } catch(err){ if(err.status!==404) throw err; warnOutdatedServer(); d=await legacyCenterDirectory(qs); } }
      catch(err){ if(mine!==seq) return; grid.innerHTML=`<div class="empty cd-empty"><h3>No hemos podido cargar los centros</h3><p>${escapeHtml(err.message)}</p><button class="btn" type="button" id="cd-retry">Reintentar</button></div>`; $('#cd-retry').onclick=()=>load(); count.textContent=''; return; }
      if(mine!==seq) return;
      if(!countriesFilled || !append){
        const sel=$('#cd-country'); sel.innerHTML='<option value="">Todos los países</option>'+(d.countries||[]).map(c=>`<option value="${escapeHtml(c.name)}" ${c.name===st.country?'selected':''}>${escapeHtml(c.name)} (${c.count})</option>`).join('')+(st.country&&!(d.countries||[]).some(c=>c.name===st.country)?`<option selected value="${escapeHtml(st.country)}">${escapeHtml(st.country)}</option>`:'');
        countriesFilled=true;
      }
      if(d.legacy){ $$('.cd-chip').forEach(b=>{ if(b.dataset.flag!=='reviews') b.hidden=true; }); const tl=$('#cd-type')?.closest('label'); if(tl) tl.hidden=true; }
      const html=(d.items||[]).map(centerCard).join('');
      if(append) grid.insertAdjacentHTML('beforeend',html); else grid.innerHTML=html;
      loaded+=(d.items||[]).length;
      if(!d.total){ grid.innerHTML=`<div class="empty cd-empty"><h3>${hasFilters()?'No hay centros con estos filtros':'Todavía no hay centros en esta zona'}</h3><p>${hasFilters()?'Prueba con otra zona o quita algún filtro.':'Estamos sumando centros verificados.'}</p><a class="btn" href="#/registro">¿Tienes un centro? Únete a WORLDIVES</a>${hasFilters()?'<button class="btn btn-primary" type="button" id="cd-empty-clear">Quitar filtros</button>':''}</div>`; $('#cd-empty-clear')?.addEventListener('click',reset); }
      count.innerHTML=d.total?`<strong>${d.total.toLocaleString(wdLocale())}</strong> ${d.total===1?'centro':'centros'}${st.country?' en '+escapeHtml(st.country):''}`:'';
      more.hidden=loaded>=d.total; more.disabled=false; more.textContent=`Mostrar más centros (${(d.total-loaded).toLocaleString(wdLocale())})`;
      clear.hidden=!hasFilters();
      const url=new URLSearchParams(qs); url.delete('page'); url.delete('per_page'); if(url.get('sort')==='recommended') url.delete('sort');
      try{ history.replaceState(null,'','#/centros'+(url.toString()?'?'+url:'')); }catch{}
    };
    const reset=()=>{ st.point='';st.q='';st.country='';st.type='';st.only.clear(); $('#cd-q').value=''; $('#cd-type').value=''; $$('.cd-chip').forEach(b=>b.setAttribute('aria-pressed','false')); load(); };
    let timer=null;
    $('#cd-q').addEventListener('input',e=>{ clearTimeout(timer); timer=setTimeout(()=>{ st.q=e.target.value.trim(); load(); },350); });
    $('#cd-search').onsubmit=e=>{ e.preventDefault(); clearTimeout(timer); st.q=$('#cd-q').value.trim(); st.country=$('#cd-country').value; load(); };
    $('#cd-country').onchange=e=>{ st.country=e.target.value; load(); };
    $('#cd-type').onchange=e=>{ st.type=e.target.value; load(); };
    $('#cd-sort').onchange=e=>{ st.sort=e.target.value; load(); };
    $$('.cd-chip').forEach(b=>b.onclick=()=>{ const k=b.dataset.flag; st.only.has(k)?st.only.delete(k):st.only.add(k); b.setAttribute('aria-pressed',String(st.only.has(k))); load(); });
    clear.onclick=reset;
    more.onclick=()=>{ st.page+=1; load(true); };
    await load();
  }
  function centerRow(c){ return centerCard(c); }

  // ---------------------------------------------------------------------------
  // Tipos de buceo: portada visual y ficha de cada tipo (puntos, centros, nivel).
  // ---------------------------------------------------------------------------
  const TYPE_IMAGES={arrecifes:'fondosuperior','paredes':'australia','pecios-y-naufragios':'logbook1','cuevas-y-cavernas':'galapagos',cenotes:'mexico',muck:'tailandia',canales:'egipto',canones:'fondo','pinaculos':'BUCEADORES','corrientes-y-deriva':'fondo1','aguas-profundas':'california',nocturnas:'micronesia',lagos:'fondo','pilares':'BUCEADORES','playa-y-esnorquel':'maldivas'};
  const typeImg=t=>media('type:'+t.key,`/assets/images/${TYPE_IMAGES[t.key]||'fondo'}.webp`);
  const TYPE_LEVELS=[['all','Todos'],['start','Para empezar'],['mid','Con experiencia'],['adv','Avanzado y técnico']];
  const typeLevel=t=>/todos los niveles|iniciaci/i.test(t.level)?'start':/intermedio/i.test(t.level)?'mid':'adv';
  const typeDepth=t=>`${t.depth_min}–${t.depth_max}${t.depth_max>=40?'+':''} m`;
  function typeDepthBar(t){ const max=40, a=Math.min(max,t.depth_min)/max*100, b=Math.min(max,t.depth_max)/max*100; return `<span class="tp-depth" title="Profundidad habitual: ${typeDepth(t)}"><span class="tp-depth-track"><span style="left:${a}%;width:${Math.max(4,b-a)}%"></span></span><small>${typeDepth(t)}</small></span>`; }
  function typeCard(t){
    return `<a class="tp-card ${t.count?'':'is-empty'}" href="#/tipos?t=${encodeURIComponent(t.key)}" data-level="${typeLevel(t)}">
      <span class="tp-card-media"><img src="${typeImg(t)}" alt="" loading="lazy"></span>
      <span class="tp-card-level">${escapeHtml(t.level)}</span>
      <span class="tp-card-body"><strong>${escapeHtml(t.label)}</strong><span class="tp-card-sum">${escapeHtml(t.summary)}</span>
        <span class="tp-card-meta"><span>${t.count?`${t.count} ${t.count===1?'punto':'puntos'} · ${t.countries} ${t.countries===1?'país':'países'}`:'Aún sin puntos en el catálogo'}</span>${typeDepthBar(t)}</span></span>
    </a>`;
  }
  async function renderTypes(params){
    params=params instanceof URLSearchParams?params:new URLSearchParams();
    if(params.get('t')) return renderTypeDetail(params.get('t'));
    let d; try{ d=await api('/api/dive-types'); } catch(err){ if(err.status!==404) throw err; warnOutdatedServer(); d=await legacyDiveTypes(); }
    const items=d.items||[], totals=d.totals||{};
    const ordered=[...items.filter(t=>t.count>0),...items.filter(t=>!t.count)];
    const byLevel=k=>ordered.filter(t=>typeLevel(t)===k&&t.count>0);
    const guide=[['start','Primeras inmersiones','Con el Open Water ya puedes disfrutar de estas inmersiones.'],['mid','Con algo de experiencia','Recomendable el Advanced y unas cuantas inmersiones registradas.'],['adv','Avanzado y técnico','Exigen formación específica, más gas o procedimientos especiales.']];
    setApp(`<section class="tp-page">
      <header class="tp-hero">${heroImg('hero:tipos')}<div class="tp-hero-in">
        <p class="eyebrow">Tipos de buceo</p><h1>¿Qué inmersión te apetece?</h1>
        <p class="lead">Arrecifes, pecios, cuevas, derivas… Elige un tipo de buceo y te mostramos dónde hacerlo, qué nivel necesitas y qué centros te llevan.</p>
        <div class="tp-hero-stats"><span><strong>${Number(totals.points||0).toLocaleString(wdLocale())}</strong> puntos</span><span><strong>${totals.countries||0}</strong> países</span><span><strong>${items.filter(t=>t.count>0).length}</strong> tipos con puntos</span></div>
      </div></header>
      <div class="tp-wrap">
        <div class="tp-filter" role="group" aria-label="Filtrar por nivel">${TYPE_LEVELS.map(([k,l],i)=>`<button type="button" class="cd-chip" data-level="${k}" aria-pressed="${i===0}">${l}</button>`).join('')}</div>
        <div class="tp-grid" id="tp-grid">${ordered.map(typeCard).join('')}</div>
        <section class="tp-guide"><div class="tp-guide-head"><p class="eyebrow">Según tu nivel</p><h2>¿Por dónde empiezo?</h2></div>
          <div class="tp-guide-grid">${guide.map(([k,title,txt])=>`<div class="tp-guide-col"><h3>${title}</h3><p>${txt}</p><ul>${byLevel(k).map(t=>`<li><a href="#/tipos?t=${encodeURIComponent(t.key)}">${escapeHtml(t.label)}</a><span>${t.count}</span></li>`).join('')||'<li class="muted">Próximamente</li>'}</ul></div>`).join('')}</div>
        </section>
      </div>
    </section>`);
    $$('.tp-filter .cd-chip').forEach(b=>b.onclick=()=>{ $$('.tp-filter .cd-chip').forEach(x=>x.setAttribute('aria-pressed',String(x===b))); const k=b.dataset.level; $$('#tp-grid .tp-card').forEach(c=>{ c.hidden=k!=='all'&&c.dataset.level!==k; }); });
  }
  function typePointCard(p){
    const depth=p.max_depth?`${p.min_depth?Math.round(p.min_depth)+'–':''}${Math.round(p.max_depth)} m`:'';
    const where=[p.region&&p.region!==p.country?p.region:'',p.country].filter(Boolean).map(escapeHtml).join(' · ');
    return `<a class="tp-point" href="${pointHref(p.id)}"><img src="${escapeHtml((p.photo&&!PLACEHOLDER_IMG.test(p.photo)?p.photo:"")||WD_COUNTRY_IMAGES[p.country]||WD_SEA_IMAGES[Math.abs(Number(p.id||0))%WD_SEA_IMAGES.length])}" alt="" loading="lazy"><span><strong>${escapeHtml(p.name)}</strong><small>${where}</small><small class="tp-point-meta">${[depth,p.difficulty].filter(Boolean).map(escapeHtml).join(' · ')}</small></span></a>`;
  }
  async function renderTypeDetail(key){
    let d;
    const still=navGuard(); try{ d=await api('/api/dive-types/'+encodeURIComponent(key)); }
    catch(err){ if(!still()) return; const legacy=err.status===404 && DIVE_TYPE_FALLBACK.find(t=>wdKey(t[0])===key); if(legacy && /Endpoint/.test(err.message)){ warnOutdatedServer(); location.hash='#/puntos?type='+encodeURIComponent(legacy[0]); return; } setApp(`<section class="page"><div class="empty"><h2>Tipo de buceo no encontrado</h2><p>${escapeHtml(err.message)}</p><a class="btn btn-primary" href="#/tipos">Ver todos los tipos</a></div></section>`); return; }
    if(!still()) return; const t=d.item, pts=d.points||[], centers=d.centers||[];
    const scopeNote=d.centers_scope==='country'?'Todavía ningún centro ha marcado este tipo de inmersión; estos centros trabajan en los países donde se hace.':d.centers_scope==='mixed'?'Incluye centros que trabajan en los mismos países donde se practica.':'';
    const pointsLink=`#/puntos?type=${encodeURIComponent(t.label)}`;
    setApp(`<section class="tp-page tp-detail">
      <header class="tp-hero tp-dhero"><img class="tp-hero-img" src="${typeImg(t)}" alt=""><div class="tp-hero-in">
        <nav class="tp-crumbs"><a href="#/tipos">Tipos de buceo</a><span>/</span>${escapeHtml(t.label)}</nav>
        <h1>${escapeHtml(t.label)}</h1><p class="lead">${escapeHtml(t.summary)}</p>
        <div class="tp-actions">${t.count?`<a class="btn btn-primary" href="${pointsLink}">Ver ${t.count===1?'el punto':`los ${t.count} puntos`}</a>`:''}<a class="btn btn-light" href="#/centros?type=${encodeURIComponent(t.key)}">Buscar centros</a></div>
      </div></header>
      <div class="tp-facts"><div><small>Nivel</small><strong>${escapeHtml(t.level)}</strong></div><div><small>Certificación recomendada</small><strong>${escapeHtml(t.cert)}</strong></div><div><small>Profundidad habitual</small><strong>${typeDepth(t)}</strong></div><div><small>En el catálogo</small><strong>${t.count?`${t.count} ${t.count===1?'punto':'puntos'} · ${t.countries} ${t.countries===1?'país':'países'}`:'Próximamente'}</strong></div></div>
      <div class="tp-wrap tp-dbody">
        <div class="tp-main">
          <section class="tp-block"><h2>Cómo es</h2><p class="tp-body">${escapeHtml(t.body)}</p>
            <div class="tp-two"><div class="tp-note"><h3>Qué necesitas</h3><p>${escapeHtml(t.need)}</p></div><div class="tp-note is-tip"><h3>Consejo</h3><p>${escapeHtml(t.tip)}</p></div></div></section>
          <section class="tp-block"><div class="tp-block-head"><h2>Dónde hacerlo</h2>${t.count>9?`<a href="${pointsLink}">Ver los ${t.count} puntos →</a>`:''}</div>
            ${pts.length?`<div class="tp-points">${pts.slice(0,9).map(typePointCard).join('')}</div>`:'<div class="empty">Aún no hay puntos catalogados de este tipo. Los centros pueden proponer nuevos puntos desde su panel.</div>'}</section>
          <section class="tp-block"><div class="tp-block-head"><h2>Centros que te llevan</h2>${centers.length?`<a href="#/centros?type=${encodeURIComponent(t.key)}">Ver todos →</a>`:''}</div>
            ${scopeNote?`<p class="tp-scope">${scopeNote}</p>`:''}
            ${centers.length?`<div class="cd-grid is-compact">${centers.slice(0,6).map(centerCard).join('')}</div>`:'<div class="empty"><p>Todavía no hay centros en esta zona.</p><a class="btn" href="#/registro">¿Tienes un centro? Únete a WORLDIVES</a></div>'}</section>
        </div>
        <aside class="tp-side">
          ${(t.top_countries||[]).length?`<div class="tp-side-card"><h3>Países con más puntos</h3><ol class="tp-countries">${t.top_countries.map(c=>`<li><a href="${pointsLink}&country=${encodeURIComponent(c.name)}">${escapeHtml(c.name)}</a><span>${c.count}</span></li>`).join('')}</ol></div>`:''}
          <div class="tp-side-card"><h3>Profundidad habitual</h3><div class="tp-gauge" aria-hidden="true"><span class="tp-gauge-band" style="top:${Math.min(40,t.depth_min)/40*100}%;height:${Math.max(4,(Math.min(40,t.depth_max)-Math.min(40,t.depth_min))/40*100)}%"></span>${[0,10,20,30,40].map(m=>`<i style="top:${m/40*100}%">${m} m</i>`).join('')}</div><p class="tp-gauge-label">${typeDepth(t)}</p></div>
        </aside>
      </div>
      ${(d.related||[]).length?`<section class="tp-wrap tp-related"><h2>Otros tipos de buceo</h2><div class="tp-grid is-small">${d.related.map(typeCard).join('')}</div></section>`:''}
    </section>`);
  }
  // ===========================================================================
  // Páginas públicas v50.24 — portada, Explorar, Puntos, ficha de punto,
  // Experiencias y Top 10, con el mismo lenguaje visual que Centros y Tipos.
  // ===========================================================================
  const LEVEL_LABELS={start:'Para empezar',mid:'Intermedio',adv:'Avanzado'};
  // Imágenes genéricas del catálogo inicial: no cuentan como foto real del punto.
  const PLACEHOLDER_IMG=/\/assets\/images\/(fondo1\.webp|buceador\d\.png|[123]\.(webp|png))$/;
  const typeLabelByKey=k=>(DIVE_TYPE_FALLBACK.find(t=>wdKey(t[0])===k)||[k])[0];
  const pointHref=id=>`#/punto?id=${encodeURIComponent(id)}`;
  const depthText=p=>p.max_depth?`${p.min_depth!=null&&p.min_depth!==''?Math.round(p.min_depth)+'–':''}${Math.round(p.max_depth)} m`:'';
  const placeText=p=>[p.subregion||p.region,p.country].filter((x,i,a)=>x&&a.indexOf(x)===i).join(' · ');

  // Capa ligera del mapa (todos los puntos con coordenadas) compartida por portada, Explorar y Top 10.
  let __mapLayer=null, __mapLayerAt=0;
  async function loadMapLayer(){
    if(__mapLayer && Date.now()-__mapLayerAt<60000) return __mapLayer;
    try{ const d=await api('/api/dive-points/map'); __mapLayer=d.fields?{...d,items:d.rows.map(r=>Object.fromEntries(d.fields.map((f,i)=>[f,r[i]])))}:d; }
    catch(err){
      if(err.status!==404 && err.status!==400) throw err;  // servidores anteriores a la v50.24
      warnOutdatedServer(); const items=((await api('/api/dive-points')).items||[]).filter(p=>p.latitude!=null&&p.longitude!=null);
      __mapLayer={items,zones:regionGroups(items).map(z=>({name:z.name,count:z.count,subregions:[]})),total:items.length};
    }
    __mapLayerAt=Date.now(); return __mapLayer;
  }

  // Directorio de puntos en el servidor; respaldo en el navegador si el servidor es anterior a la v50.24.
  async function fetchPointDirectory(qs){
    try{ return await api('/api/point-directory?'+qs); }
    catch(err){
      if(err.status!==404) throw err;
      warnOutdatedServer();
      const type=qs.get('type'); const label=type?typeLabelByKey(type):'';
      let rows=(await api('/api/dive-points?'+new URLSearchParams(label?{type:label}:{}))).items||[];
      const q=wdFold(qs.get('q')).trim(); if(q){ const w=q.split(/\s+/); rows=rows.filter(p=>{const t=wdFold([p.name,p.country,p.region,p.subregion,p.zone,p.dive_type,p.description].join(' ')); return w.every(x=>t.includes(x));}); }
      const zf={}; rows.forEach(p=>zf[p.zone||'Otros']=(zf[p.zone||'Otros']||0)+1);
      if(qs.get('zone')) rows=rows.filter(p=>(p.zone||'Otros')===qs.get('zone'));
      const cf={}; rows.forEach(p=>cf[p.country]=(cf[p.country]||0)+1);
      if(qs.get('country')) rows=rows.filter(p=>p.country===qs.get('country'));
      const per=Number(qs.get('per_page')||12), page=Number(qs.get('page')||1);
      return {items:rows.slice((page-1)*per,page*per),total:rows.length,zones:Object.entries(zf).map(([name,count])=>({name,count})),countries:Object.entries(cf).sort((a,b)=>b[1]-a[1]).map(([name,count])=>({name,count})),legacy:true};
    }
  }

  // Descripción útil aunque el catálogo solo tenga una frase genérica.
  function pointAbout(p){
    const d=String(p.description||'').trim();
    if(d && !/cat[aá]logo inicial|pendiente de (verificaci|ampliar|completar)|ubicaci[oó]n de referencia/i.test(d)) return d;
    const depth=depthText(p); const where=placeText(p)||p.country||'';
    return `${p.dive_type?p.dive_type+' en ':'Punto de buceo en '}${where}.${depth?` Profundidad entre ${depth}.`:''}${p.difficulty?` Nivel ${String(p.difficulty).toLowerCase()}.`:''} Consulta con el centro las condiciones del día antes de reservar.`;
  }
  function pointCard(p){
    const types=(p.types||[]).slice(0,2).map(typeLabelByKey), depth=depthText(p);
    const pending=p.verification_status && p.verification_status!=='verified';
    return `<article class="cd-card pt-card">
      <a class="cd-media" href="${pointHref(p.id)}" tabindex="-1" aria-hidden="true"><img src="${escapeHtml(p.photo||pointImg(p))}" alt="" loading="lazy">
        <span class="cd-badges">${types.map(t=>`<span class="cd-badge">${escapeHtml(t)}</span>`).join('')}</span></a>
      <div class="cd-body pt-body">
        <h3><a href="${pointHref(p.id)}">${escapeHtml(p.name)}</a></h3>
        <p class="cd-place">${wdIcon('pin',14)}${escapeHtml(placeText(p)||p.country||'')}</p>
        <div class="pt-facts">${p.difficulty?`<span>${wdIcon('level',14)}${escapeHtml(p.difficulty)}</span>`:''}${p.dive_type?`<span>${escapeHtml(p.dive_type)}</span>`:''}${pending?'<span class="muted">Ubicación por verificar</span>':''}</div>
        ${p.excerpt?`<p class="cd-desc">${escapeHtml(p.excerpt)}</p>`:''}
      </div>
      <div class="cd-foot pt-foot">
        <div class="cd-fact"><small>Profundidad</small><strong>${depth?escapeHtml(depth):'<span class="muted">Por confirmar</span>'}</strong></div>
        <div class="cd-fact"><small>Centros</small><strong>${p.centers_count?`${p.centers_count} ${p.centers_count==1?'centro':'centros'}`:'<span class="muted">Por asociar</span>'}</strong></div>
        <a class="btn cd-cta" href="${pointHref(p.id)}">Ver punto</a>
      </div>
    </article>`;
  }

  function sectionHead(eyebrow,title,link,linkText){ return `<div class="hm-head"><div><p class="eyebrow">${eyebrow}</p><h2>${title}</h2></div>${link?`<a class="hm-link" href="${link}">${linkText} →</a>`:''}</div>`; }

  // ---------------------------------------------------------------- Portada
  function homeTemplate(){return `<section class="hm-page">
    <header class="tp-hero hm-hero">${heroImg('hero:home')}<div class="tp-hero-in">
      ${state.theme?.ribbon?`<p class="hm-ribbon">${wdIcon('star',14)}<span>${escapeHtml(state.theme.ribbon)}</span></p>`:''}<p class="eyebrow">WORLDIVES DISCOVERY</p>
      <h1>Encuentra tu próxima inmersión</h1>
      <p class="lead">Puntos de buceo de todo el mundo, centros que reservan al momento y viajes organizados. Busca un lugar o empieza por el mapa.</p>
      <div class="hm-search"><div class="searchbar"><div class="search-input-wrap">${wdIcon('search',18)}<input id="home-search" type="search" placeholder="Punto, centro, isla o ciudad" aria-label="Buscar" autocomplete="off"><button id="home-search-clear" class="search-clear" type="button" aria-label="Borrar búsqueda" hidden>×</button></div><button id="home-search-btn" class="btn btn-primary" type="button">Buscar</button><div id="home-search-results" class="search-results" hidden></div></div></div>
      <div class="hm-quick"><a href="#/top10">${wdIcon('pin',15)}Cerca de mí</a><a href="#/tipos?t=pecios-y-naufragios">Pecios</a><a href="#/tipos?t=cuevas-y-cavernas">Cuevas</a><a href="#/tipos?t=arrecifes">Arrecifes</a><a href="#/centros?only=online">Centros con reserva online</a></div>
      <div class="tp-hero-stats" id="hm-stats"></div>
    </div></header>
    <section class="hm-section hm-mapband" id="home-map-section"><div class="tp-wrap">
      ${sectionHead('Exploración','¿Dónde quieres bucear?','#/explorar','Abrir el explorador')}
      <div class="map-panel hm-map"><aside class="zone-panel"><h3>Zonas del mundo</h3><div id="home-zones" class="zone-list"></div></aside><div class="map-wrap"><div class="map-toolbar"><button class="active" data-mapmode="street">Mapa</button><button data-mapmode="satellite">Satélite</button><button data-mapmode="marine">Relieve marino</button><button data-mapmode="world">Mundo</button></div><div id="home-map" class="map-card"></div><div id="home-drawer" class="point-drawer"></div></div></div>
    </div></section>
    <section class="hm-section"><div class="tp-wrap">${sectionHead('Tipos de buceo','¿Qué inmersión te apetece?','#/tipos','Ver todos los tipos')}<div class="tp-grid is-small" id="hm-types"></div></div></section>
    <section class="hm-section hm-alt hm-offers" id="hm-offers" hidden><div class="tp-wrap">${sectionHead('Destacado','Ofertas y viajes')}<div class="hm-offer-grid" id="hm-offer-grid"></div></div></section>
    <section class="hm-network" id="hm-network" hidden aria-labelledby="hm-network-title">
      <div class="tp-wrap hm-network-head"><div><p class="eyebrow">Red WORLDIVES</p><h2 id="hm-network-title">Centros asociados</h2><p id="hm-network-sub"></p></div><a class="btn btn-primary" href="#/registro">Dar de alta mi centro</a></div>
      <div class="hm-marquee" id="hm-centers-band"></div>
      <div class="hm-sponsors" id="hm-sponsors" hidden><p class="hm-partners-title">Patrocinadores y colaboradores <span class="hm-sponsored-tag">Patrocinado</span></p><div class="hm-marquee is-reverse" id="hm-marquee"></div></div>
      <p class="tp-wrap hm-network-foot">¿Tienes un centro de buceo? Date de alta y aparecerás aquí, con tu escaparate y tu motor de reservas.<span id="hm-brand-link"></span></p>
    </section>
  </section>`}

  async function renderHome(){
    state.points=[]; setApp(homeTemplate()); bindHomeSearch();
    // The visitor may leave before a block arrives: only paint into this page while it is on screen.
    const root=$('.hm-page'); const alive=()=>document.body.contains(root); const put=(sel,html)=>{ if(!alive()) return; const el=$(sel); if(el) el.innerHTML=html; };
    // Each block loads on its own: one slow or failed block never leaves the page empty.
    loadMapLayer().then(layer=>{ if(!alive()) return; state.points=layer.items; setupZones($('#home-zones'),layer.items); initMap('home-map',layer.items,[20,0],2); bindMapModeButtons(); }).catch(err=>put('#home-map',`<div class="map-fallback"><strong>No se ha podido cargar el mapa</strong><span>${escapeHtml(err.message)}</span></div>`));
    api('/api/dive-types').then(d=>{
      const t=d.totals||{}; put('#hm-stats',`<span><strong>${Number(t.points||0).toLocaleString(wdLocale())}</strong> puntos de buceo</span><span><strong>${t.countries||0}</strong> países</span><span><strong>${t.centers||0}</strong> centros</span>`);
      put('#hm-types',(d.items||[]).filter(x=>x.count>0).sort((a,b)=>b.count-a.count).slice(0,6).map(typeCard).join(''));
    }).catch(()=>{ const sec=alive()&&$('#hm-types')?.closest('.hm-section'); if(sec) sec.hidden=true; loadMapLayer().then(l=>put('#hm-stats',`<span><strong>${l.items.length.toLocaleString(wdLocale())}</strong> puntos de buceo</span><span><strong>${new Set(l.items.map(p=>p.country)).size}</strong> países</span>`)).catch(()=>{}); });
    api('/api/site-promos').then(d=>{ if(!alive()) return;
      const offers=(d.offers||[]).slice(0,3), partners=d.partners||[], contact=d.contact||{};
      if(offers.length){ $('#hm-offer-grid').innerHTML=offers.map(offerCard).join(''); $('#hm-offer-grid').dataset.count=offers.length; $('#hm-offers').hidden=false; }
      const centers=d.centers||[];
      if(centers.length){ $('#hm-centers-band').innerHTML=marqueeTrack(centers.map(c=>`<a class="hm-cl" href="#/centro?id=${c.id}" title="${escapeHtml(c.name)}">${centerLogoMarkup({...c,logo_url:c.logo},'42px')}<span><strong>${escapeHtml(c.name)}</strong><small>${escapeHtml([c.city,c.country].filter(Boolean).join(' · '))}</small></span></a>`),2.6);
        const n=Number(d.center_total||centers.length); $('#hm-network-sub').textContent=`${n.toLocaleString(wdLocale())} ${n===1?'centro':'centros'} de buceo con reserva directa en WORLDIVES.`; $('#hm-network').hidden=false; }
      if(partners.length){ $('#hm-marquee').innerHTML=partnerMarquee(partners); $('#hm-sponsors').hidden=false; $('#hm-network').hidden=false; }
      if(contact.email) $('#hm-brand-link').innerHTML=` ¿Eres una marca o un destino? <a href="mailto:${escapeHtml(contact.email)}?subject=${encodeURIComponent('Colaborar con WORLDIVES')}">Escríbenos</a>.`;
    }).catch(()=>{});
  }

  // ---------------------------------------------------------------- Explorar
  function explorerTemplate(){return `<section class="cd-page ex2-page">
    <header class="tp-hero ex2-hero">${heroImg('hero:explorar')}<div class="tp-hero-in">
      <p class="eyebrow">Explorar</p><h1>El mapa del buceo</h1>
      <p class="lead">Todos los puntos de buceo en un solo mapa. Elige una zona, acércate y abre cualquier punto para ver su ficha y los centros que bucean allí.</p>
      <div class="tp-hero-stats"><span><strong id="ex-stat-points">—</strong>puntos de buceo</span><span><strong id="ex-stat-countries">—</strong>países</span><span><strong id="ex-stat-zones">—</strong>zonas del mundo</span></div>
    </div></header>
    <div class="ex-page">
    <div class="ex-layout">
      <aside class="ex-side">
        <div class="ex-side-head"><h2>Filtra el mapa</h2><p>Busca por nombre, zona o país, o elige un tipo de inmersión.</p></div>
        <label class="cd-field ex-filter">${wdIcon('search',18)}<span class="sr-only">Buscar en el mapa</span><input id="ex-q" type="search" placeholder="Filtrar puntos del mapa" autocomplete="off"></label>
        <div class="ex-types" id="ex-types"></div>
        <p class="ex-count" id="ex-count" aria-live="polite"></p>
        <p class="ex-legend"><span class="wd-pin" aria-hidden="true"></span>Punto de buceo · toca para ver la ficha</p>
        <div class="ex-zones-head">Zonas</div>
        <div id="explore-zones" class="zone-list"></div>
      </aside>
      <div class="map-wrap ex-map"><div class="map-toolbar"><button class="active" data-mapmode="street">Mapa</button><button data-mapmode="satellite">Satélite</button><button data-mapmode="marine">Relieve marino</button><button data-mapmode="world">Mundo</button></div><div id="explore-map" class="map-card"></div><div id="explore-drawer" class="point-drawer"></div></div>
    </div></div></section>`}
  async function renderExplorer(params){
    setApp(explorerTemplate());
    let layer; try{ layer=await loadMapLayer(); }catch(err){ $('#explore-map').innerHTML=`<div class="map-fallback"><strong>No se ha podido cargar el mapa</strong><span>${escapeHtml(err.message)}</span></div>`; return; }
    state.points=layer.items; setupZones($('#explore-zones'),layer.items); initMap('explore-map',layer.items,[30,-10],3); bindMapModeButtons();
    const nf=v=>Number(v).toLocaleString(wdLocale()); $('#ex-stat-points').textContent=nf(layer.items.length); $('#ex-stat-countries').textContent=nf(new Set(layer.items.map(p=>p.country).filter(Boolean)).size); $('#ex-stat-zones').textContent=nf(new Set(layer.items.map(p=>p.zone).filter(Boolean)).size);
    const fixed=[['','Todos'],['arrecifes','Arrecifes'],['paredes','Paredes'],['pecios-y-naufragios','Pecios'],['cuevas-y-cavernas','Cuevas'],['muck','Muck'],['pinaculos','Pináculos'],['aguas-profundas','Profundas']];
    let active='';
    $('#ex-types').innerHTML=fixed.map(([k,l],i)=>`<button type="button" class="cd-chip" data-t="${k}" aria-pressed="${i===0}">${l}</button>`).join('');
    const apply=()=>{ const q=wdFold($('#ex-q').value).trim(); const words=q?q.split(/\s+/):[];
      const pts=state.points.filter(p=>{ const t=wdFold([p.name,p.country,p.region,p.subregion,p.zone,p.dive_type].join(' ')); return words.every(w=>t.includes(w)) && (!active || !p.types || p.types.includes(active)); });
      $('#ex-count').textContent=`${pts.length.toLocaleString(wdLocale())} ${pts.length===1?'punto':'puntos'} en el mapa`;
      try{ focusMapPoints(pts); if(state.map && pts.length && pts.length<state.points.length && window.L){ state.map.fitBounds(L.latLngBounds(pts.map(p=>[p.latitude,p.longitude])),{padding:[50,50],maxZoom:11,animate:true}); } }catch(e){ console.warn('mapa',e); } };
    let timer=null; $('#ex-q').addEventListener('input',()=>{ clearTimeout(timer); timer=setTimeout(apply,250); });
    $$('#ex-types .cd-chip').forEach(b=>b.onclick=()=>{ $$('#ex-types .cd-chip').forEach(x=>x.setAttribute('aria-pressed',String(x===b))); active=b.dataset.t; apply(); });
    $('#ex-count').textContent=`${state.points.length.toLocaleString(wdLocale())} puntos en el mapa`;
    const focus=params?.get?.('point'); if(focus){ const p=state.points.find(x=>String(x.id)===String(focus)); if(p) setTimeout(()=>openPointDrawer(p),400); }
  }

  // ---------------------------------------------------------------- Puntos de buceo
  const PT_LEVELS=[['start','Para empezar'],['mid','Intermedio'],['adv','Avanzado']];
  const PT_SORTS=[['recommended','Recomendados'],['name','Nombre A-Z'],['depth','Más profundos'],['shallow','Menos profundos'],['rating','Mejor valorados']];
  async function renderPoints(params){
    params=params instanceof URLSearchParams?params:new URLSearchParams();
    if(params.get('point')){ location.replace('#/punto?id='+encodeURIComponent(params.get('point'))); return; }
    const rawType=params.get('type')||''; const typeKey=rawType?(DIVE_TYPE_FALLBACK.some(t=>wdKey(t[0])===rawType)?rawType:wdKey(rawType)):'';
    const st={q:params.get('q')||'',zone:params.get('zone')||'',country:params.get('country')||'',type:typeKey,level:PT_LEVELS.some(l=>l[0]===params.get('level'))?params.get('level'):'',only:params.get('only')==='centers'?'centers':'',sort:PT_SORTS.some(s=>s[0]===params.get('sort'))?params.get('sort'):'recommended',page:1};
    setApp(`<section class="cd-page pt-page">
      <header class="tp-hero pt-hero">${heroImg('hero:puntos')}<div class="tp-hero-in">
        <p class="eyebrow">Catálogo</p><h1>Puntos de buceo</h1>
        <p class="lead">Arrecifes, pecios, cuevas y paredes de todo el mundo, con su profundidad, su nivel y los centros que te llevan.</p>
        <form class="cd-search" id="pt-search" role="search">
          <label class="cd-field cd-field-q">${wdIcon('search',18)}<span class="sr-only">Buscar</span><input id="pt-q" type="search" autocomplete="off" placeholder="Punto, isla, zona o país" value="${escapeHtml(st.q)}"></label>
          <label class="cd-field">${wdIcon('globe',18)}<span class="sr-only">Zona</span><select id="pt-zone"><option value="">Todo el mundo</option>${st.zone?`<option selected>${escapeHtml(st.zone)}</option>`:''}</select></label>
          <button class="btn btn-primary" type="submit">Buscar</button>
        </form>
      </div></header>
      <div class="cd-wrap">
        <div class="cd-toolbar">
          <div class="cd-chips" role="group" aria-label="Nivel">${PT_LEVELS.map(([k,l])=>`<button type="button" class="cd-chip" data-level="${k}" aria-pressed="${st.level===k}">${l}</button>`).join('')}<button type="button" class="cd-chip" data-only="centers" aria-pressed="${st.only==='centers'}">Con centro que lo ofrece</button><button type="button" class="cd-chip" data-only="instant" aria-pressed="${st.only==='instant'}">Confirmación inmediata</button></div>
          <div class="cd-tools">
            <label><span class="sr-only">Tipo de buceo</span><select id="pt-type"><option value="">Cualquier tipo</option>${DIVE_TYPE_FALLBACK.map(([l])=>`<option value="${wdKey(l)}" ${wdKey(l)===st.type?'selected':''}>${escapeHtml(l)}</option>`).join('')}</select></label>
            <label><span class="sr-only">País</span><select id="pt-country"><option value="">Todos los países</option></select></label>
            <label><span class="sr-only">Ordenar</span><select id="pt-sort">${PT_SORTS.map(([k,l])=>`<option value="${k}" ${k===st.sort?'selected':''}>${l}</option>`).join('')}</select></label>
          </div>
        </div>
        <div class="cd-results-head"><p id="pt-count" aria-live="polite">Buscando puntos…</p><button type="button" class="cd-clear" id="pt-clear" hidden>Quitar filtros</button></div>
        <div class="cd-grid" id="pt-grid"></div>
        <div class="cd-more"><button class="btn" type="button" id="pt-more" hidden>Mostrar más puntos</button></div>
      </div>
    </section>`);
    const grid=$('#pt-grid'), more=$('#pt-more'), count=$('#pt-count'), clear=$('#pt-clear');
    let seq=0, loaded=0;
    const skeleton=n=>Array.from({length:n},()=>'<div class="cd-card is-skeleton" aria-hidden="true"><div class="cd-media"></div><div class="cd-body"><i></i><i></i><i></i></div></div>').join('');
    const hasFilters=()=>!!(st.q||st.zone||st.country||st.type||st.level||st.only);
    const fillSelect=(sel,list,current,allLabel)=>{ sel.innerHTML=`<option value="">${allLabel}</option>`+(list||[]).map(x=>`<option value="${escapeHtml(x.name)}" ${x.name===current?'selected':''}>${escapeHtml(x.name)} (${x.count})</option>`).join('')+(current&&!(list||[]).some(x=>x.name===current)?`<option selected value="${escapeHtml(current)}">${escapeHtml(current)}</option>`:''); };
    const load=async(append=false)=>{
      const mine=++seq;
      if(!append){ st.page=1; loaded=0; grid.innerHTML=skeleton(6); more.hidden=true; }
      more.disabled=true;
      const qs=new URLSearchParams({q:st.q,zone:st.zone,country:st.country,type:st.type,level:st.level,only:st.only,sort:st.sort,page:String(st.page),per_page:'12'});
      for(const k of [...qs.keys()]) if(!qs.get(k)) qs.delete(k);
      let d;
      try{ d=await fetchPointDirectory(qs); }
      catch(err){ if(mine!==seq) return; grid.innerHTML=`<div class="empty cd-empty"><h3>No hemos podido cargar los puntos</h3><p>${escapeHtml(err.message)}</p><button class="btn" type="button" id="pt-retry">Reintentar</button></div>`; $('#pt-retry').onclick=()=>load(); count.textContent=''; return; }
      if(mine!==seq) return;
      if(!append){ fillSelect($('#pt-zone'),d.zones,st.zone,'Todo el mundo'); fillSelect($('#pt-country'),d.countries,st.country,'Todos los países'); }
      const html=(d.items||[]).map(pointCard).join('');
      if(append) grid.insertAdjacentHTML('beforeend',html); else grid.innerHTML=html;
      loaded+=(d.items||[]).length;
      if(!d.total){ grid.innerHTML=`<div class="empty cd-empty"><h3>No hay puntos con estos filtros</h3><p>Prueba con otra zona o quita algún filtro.</p>${hasFilters()?'<button class="btn btn-primary" type="button" id="pt-empty-clear">Quitar filtros</button>':''}</div>`; $('#pt-empty-clear')?.addEventListener('click',reset); }
      count.innerHTML=d.total?`<strong>${d.total.toLocaleString(wdLocale())}</strong> ${d.total===1?'punto':'puntos'}${st.type?' · '+escapeHtml(typeLabelByKey(st.type)):''}${st.country?' en '+escapeHtml(st.country):st.zone?' en '+escapeHtml(st.zone):''}`:'';
      more.hidden=loaded>=d.total; more.disabled=false; more.textContent=`Mostrar más puntos (${(d.total-loaded).toLocaleString(wdLocale())})`;
      clear.hidden=!hasFilters();
      const url=new URLSearchParams(qs); url.delete('page'); url.delete('per_page'); if(url.get('sort')==='recommended') url.delete('sort');
      try{ history.replaceState(null,'','#/puntos'+(url.toString()?'?'+url:'')); }catch{}
    };
    const reset=()=>{ Object.assign(st,{q:'',zone:'',country:'',type:'',level:'',only:''}); $('#pt-q').value=''; $('#pt-type').value=''; $$('.pt-page .cd-chip').forEach(b=>b.setAttribute('aria-pressed','false')); load(); };
    let timer=null;
    $('#pt-q').addEventListener('input',e=>{ clearTimeout(timer); timer=setTimeout(()=>{ st.q=e.target.value.trim(); load(); },350); });
    $('#pt-search').onsubmit=e=>{ e.preventDefault(); clearTimeout(timer); st.q=$('#pt-q').value.trim(); load(); };
    $('#pt-zone').onchange=e=>{ st.zone=e.target.value; st.country=''; load(); };
    $('#pt-country').onchange=e=>{ st.country=e.target.value; load(); };
    $('#pt-type').onchange=e=>{ st.type=e.target.value; load(); };
    $('#pt-sort').onchange=e=>{ st.sort=e.target.value; load(); };
    $$('.pt-page [data-level]').forEach(b=>b.onclick=()=>{ st.level=st.level===b.dataset.level?'':b.dataset.level; $$('.pt-page [data-level]').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.level===st.level))); load(); });
    $$('.pt-page [data-only]').forEach(b=>b.onclick=e=>{ const k=e.currentTarget.dataset.only; st.only=st.only===k?'':k; $$('.pt-page [data-only]').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.only===st.only))); load(); });
    clear.onclick=reset; more.onclick=()=>{ st.page+=1; load(true); };
    await load();
  }

  // ---------------------------------------------------------------- Ficha de punto
  async function renderPointPage(params){
    const id=Number(params?.get?.('id')||0);
    if(!id){ location.replace('#/puntos'); return; }
    return renderPointDetail(id);
  }
  async function renderPointDetail(id){
    if(!/^#\/punto\?/.test(location.hash)){ location.hash='#/punto?id='+encodeURIComponent(id); return; }
    const still=navGuard(); let d; try{ d=await api('/api/dive-points/'+id+'?lang='+currentLanguage()); }
    catch(err){ if(!still()) return; setApp(`<section class="page"><div class="empty"><h2>Punto de buceo no encontrado</h2><p>${escapeHtml(err.message)}</p><a class="btn btn-primary" href="#/puntos">Ver todos los puntos</a></div></section>`); return; }
    const p=d.item, photos=(d.photos||[]).filter(ph=>!PLACEHOLDER_IMG.test(ph.image_path||'')), nearby=d.nearby||[], types=(d.types||[]);
    const [me,virtual,pc]=await Promise.all([api('/api/me').catch(()=>({})),api('/api/dive-points/'+id+'/virtual').catch(()=>({items:[]})),api('/api/dive-points/'+id+'/centers').catch(()=>({items:[],mode:'exact'}))]);
    if(!still()) return; const currentCert=me.profile?.certification_name||'';
    const cover=photos[0]?.image_path||pointImg(p), depth=depthText(p);
    const pending=p.verification_status && p.verification_status!=='verified';
    const lat=Number(p.latitude), lng=Number(p.longitude), hasGeo=Number.isFinite(lat)&&Number.isFinite(lng);
    const osm=hasGeo?`https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=15/${lat}/${lng}`:'';
    const labels={panorama:'360° interactivo',video360:'Vídeo 360°',streetview:'Street View',external360:'Experiencia 360°'};
    const vt=(virtual.items||[]).map(v=>{ const ext=v.experience_type==='streetview'; const href=ext?(v.url||'#'):`#/virtual?experience=${v.id}&point=${p.id}`;
      return `<article class="pp-virtual"><span class="pp-virtual-mark">360°</span><div><p class="eyebrow">${escapeHtml(labels[v.experience_type]||'Recorrido virtual')}</p><h3>${escapeHtml(v.title)}</h3><p>${escapeHtml(v.description||'Recorre esta inmersión antes de entrar al agua.')}</p><a class="btn btn-primary" href="${escapeHtml(href)}" ${ext?'target="_blank" rel="noopener"':''}>${ext?'Abrir Street View':'Entrar en el recorrido'}</a></div></article>`; }).join('');
    const centers=pc.items||[];
    const centerRowHtml=c=>`<article class="pp-center"><span class="pp-center-logo">${centerLogoMarkup(c,'48px')}</span><div class="pp-center-main"><a href="#/centro?id=${c.id}"><strong>${escapeHtml(c.name)}</strong></a><small>${escapeHtml([c.city,c.country].filter(Boolean).join(' · '))}${c.distance_km!=null?' · a '+Number(c.distance_km).toLocaleString(wdLocale(),{maximumFractionDigits:1})+' km':''}</small>${centerRatingMarkup(c)}${c.instant?'<span class="wd-mode is-pay">Confirmación inmediata disponible</span>':Number(c.services_count)>0?'<span class="wd-mode is-req">Reservas bajo petición</span>':''}</div><div class="pp-center-actions"><a class="btn" href="#/centro?id=${c.id}">Ver centro</a>${Number(c.services_count)>0?`<a class="btn btn-primary" href="#/reservar?center=${c.id}">Reservar</a>`:''}</div></article>`;
    setApp(`<section class="tp-page pp-page">
      <header class="tp-hero tp-dhero"><img class="tp-hero-img" src="${escapeHtml(cover)}" alt=""><div class="tp-hero-in">
        <nav class="tp-crumbs"><a href="#/puntos">Puntos de buceo</a><span>/</span>${p.zone?`<a href="#/puntos?zone=${encodeURIComponent(p.zone)}">${escapeHtml(p.zone)}</a><span>/</span>`:''}${escapeHtml(p.name)}</nav>
        <h1>${escapeHtml(p.name)}</h1>
        <p class="lead pp-place">${wdIcon('pin',16)} ${escapeHtml(placeText(p)||p.country||'')}</p>
        <div class="pp-tags">${types.map(k=>`<a class="pp-tag" href="#/tipos?t=${encodeURIComponent(k)}">${escapeHtml(typeLabelByKey(k))}</a>`).join('')||(p.dive_type?`<span class="pp-tag">${escapeHtml(p.dive_type)}</span>`:'')}</div>
        <div class="tp-actions">${centers.length?`<a class="btn btn-primary" href="#pp-centers" data-scroll="pp-centers">${pc.mode==='exact'?'Centros que te llevan':'Centros cercanos'}</a>`:''}${osm?`<a class="btn btn-light" href="${osm}" target="_blank" rel="noopener">Abrir en el mapa</a>`:''}</div>
      </div></header>
      <div class="tp-facts"><div><small>Profundidad</small><strong>${depth||'Por confirmar'}</strong></div><div><small>Nivel</small><strong>${escapeHtml(p.difficulty||'Por confirmar')}</strong></div><div><small>Tipo</small><strong>${escapeHtml(p.dive_type||'—')}</strong></div><div><small>Coordenadas</small><strong>${hasGeo?`${lat.toFixed(4)}, ${lng.toFixed(4)}`:'—'}</strong></div></div>
      <div class="tp-wrap tp-dbody">
        <div class="tp-main">
          ${pending?'<div class="notice warning pp-notice"><strong>Posición de referencia.</strong> La coordenada de este punto está pendiente de verificación local. Un centro o el equipo de WORLDIVES puede confirmarla.</div>':''}
          <section class="tp-block"><h2>Sobre el punto</h2>${p.description_lang?`<div class="tp-body" translate="no" lang="${escapeHtml(p.description_lang)}">${String(p.description).split(/\n{2,}/).map(x=>`<p>${escapeHtml(x)}</p>`).join('')}</div>`:`<p class="tp-body">${escapeHtml(pointAbout(p))}</p>`}${p.access_info&&!/pendientes? de completar/i.test(p.access_info)?`<div class="tp-note"><h3>Acceso y condiciones</h3><p>${escapeHtml(p.access_info)}</p></div>`:''}</section>
          <section class="tp-block pp-cert">${certificationGuidance(p,currentCert)}</section>
          ${photos.length>1?`<section class="tp-block"><h2>Fotos</h2><div class="pp-gallery">${photos.map(ph=>`<a href="${escapeHtml(ph.image_path)}" target="_blank" rel="noopener"><img src="${escapeHtml(ph.image_path)}" alt="${escapeHtml(ph.caption||p.name)}" loading="lazy"></a>`).join('')}</div></section>`:''}
          <section class="tp-block"><h2>Recorrido virtual</h2>${vt?`<div class="pp-virtuals">${vt}</div>`:'<div class="pp-empty"><span class="pp-virtual-mark">360°</span><p>Este punto aún no tiene recorrido 360°. Cuando un centro lo publique, podrás visitarlo antes de reservar.</p></div>'}</section>
          <section class="tp-block" id="pp-centers"><div class="tp-block-head"><h2>${pc.mode==='exact'?'Centros que bucean aquí':'Centros cercanos'}</h2>${centers.length?`<a href="#/centros?point=${p.id}">Ver en el directorio →</a>`:''}</div>
            ${pc.mode!=='exact'&&centers.length?'<p class="tp-scope">Ningún centro tiene todavía este punto en su operativa; estos trabajan a menos de 60 km.</p>':''}
            ${centers.length?`<div class="pp-centers">${centers.map(centerRowHtml).join('')}</div>`:'<div class="empty"><p>Todavía no hay centros en esta zona.</p><a class="btn" href="#/registro">¿Tienes un centro? Únete a WORLDIVES</a></div>'}</section>
          ${nearby.length?`<section class="tp-block"><div class="tp-block-head"><h2>Puntos cercanos</h2></div><div class="tp-points">${nearby.map(n=>typePointCard(n).replace('</small></span></a>',`</small><small class="tp-point-meta">a ${Number(n.distance_km).toLocaleString(wdLocale(),{maximumFractionDigits:1})} km</small></span></a>`)).join('')}</div></section>`:''}
        </div>
        <aside class="tp-side">
          <div class="tp-side-card pp-mapcard"><h3>Ubicación</h3><div id="pp-map" class="pp-map">${hasGeo?'':'<div class="map-fallback">Sin coordenadas</div>'}</div>${osm?`<a class="btn" href="${osm}" target="_blank" rel="noopener">Abrir en OpenStreetMap</a>`:''}</div>
          <div class="tp-side-card"><h3>¿La posición no es exacta?</h3><p class="pp-small">Propón una corrección: pasa a revisión antes de publicarse.</p>${state.me?'<button id="suggest-pos" class="btn btn-primary" type="button">Proponer nueva posición</button>':`<a class="btn btn-primary" href="#/login?next=${encodeURIComponent(location.hash)}">Inicia sesión para proponerla</a>`}<div id="suggest-form"></div></div>
          <button type="button" class="wd-report" data-report="point" data-report-id="${p.id}" data-report-label="${escapeHtml(p.name)}">${wdIcon('alert',13)} Denunciar contenido</button>
        </aside>
      </div>
    </section>`);
    $$('[data-scroll]').forEach(a=>a.onclick=e=>{ e.preventDefault(); document.getElementById(a.dataset.scroll)?.scrollIntoView({behavior:'smooth',block:'start'}); });
    if(hasGeo && window.L){ try{ const m=(wdTileDefaults(),wdLimitMap(L.map('pp-map',{zoomControl:true,scrollWheelZoom:false,attributionControl:true}))).setView([lat,lng],12); wdBaseLayer().addTo(m); L.marker([lat,lng],{icon:pointIcon(p,{active:true}),title:p.name,alt:p.name,zIndexOffset:1000}).addTo(m); }catch(e){ console.warn(e); } }
    else if(hasGeo){ $('#pp-map').innerHTML=`<div class="map-fallback"><strong>${lat.toFixed(4)}, ${lng.toFixed(4)}</strong></div>`; }
    $('#suggest-pos')?.addEventListener('click',()=>{ $('#suggest-form').innerHTML=`<div class="form-grid pp-suggest"><div class="field"><label>Latitud</label><input id="s-lat" type="number" step="0.000001" value="${hasGeo?lat:''}"></div><div class="field"><label>Longitud</label><input id="s-lon" type="number" step="0.000001" value="${hasGeo?lng:''}"></div><div class="field full"><label>Motivo</label><textarea id="s-note" placeholder="Qué ves en el mapa y por qué propones moverlo…"></textarea></div></div><button class="btn btn-primary" id="s-save" type="button">Enviar propuesta</button>`; $('#s-save').onclick=async()=>{ try{ await postJSON('/api/dive-points/'+id+'/suggest',{latitude:+$('#s-lat').value,longitude:+$('#s-lon').value,note:$('#s-note').value}); toast('Propuesta enviada.'); $('#suggest-form').innerHTML='<div class="notice">Propuesta registrada y pendiente de revisión.</div>'; }catch(e){ toast(e.message); } }; });
  }

  // ---------------------------------------------------------------- Experiencias
  let __travel=null, __travelAt=0;
  async function loadTravelDirectory(){
    if(__travel && Date.now()-__travelAt<60000) return __travel;
    try{ __travel=await api('/api/travel-directory'); }
    catch(err){ if(err.status!==404) throw err; warnOutdatedServer(); const meta=await loadMeta(); __travel={items:(meta.travel||[]).map(o=>({...o,experiences:null})),kinds:[...new Set((meta.travel||[]).map(o=>o.kind).filter(Boolean))]}; }
    __travelAt=Date.now(); return __travel;
  }
  function destinationCard(o){
    const n=o.experiences;
    return `<article class="cd-card dst-card">
      <a class="cd-media" href="#/experiencia?id=${o.id}" tabindex="-1" aria-hidden="true"><img src="${escapeHtml(o.image_path||WD_COUNTRY_IMAGES[o.region]||'/assets/images/fondo.webp')}" alt="" loading="lazy"><span class="cd-badges">${o.kind?`<span class="cd-badge">${escapeHtml(o.kind)}</span>`:''}${n?`<span class="cd-badge is-live">${n} ${n===1?'experiencia':'experiencias'}</span>`:''}</span></a>
      <div class="cd-body dst-body"><h3><a href="#/experiencia?id=${o.id}">${escapeHtml(o.title)}</a></h3><p class="cd-place">${wdIcon('globe',14)}${escapeHtml(o.region||'')}</p><p class="cd-desc">${escapeHtml(o.summary||o.description||'Experiencias de buceo organizadas por centros y profesionales.')}</p></div>
      <div class="cd-foot"><div class="cd-fact"><small>Desde</small><strong>${o.price_from?wdMoney(o.price_from,o.currency):'<span class="muted">Consultar</span>'}</strong></div><div class="cd-fact"><small>Próxima salida</small><strong>${o.next_date?escapeHtml(wdDay(o.next_date)):'<span class="muted">Por anunciar</span>'}</strong></div><a class="btn ${n?'btn-primary':''} cd-cta" href="#/experiencia?id=${o.id}">${n?'Ver viajes':'Ver destino'}</a></div>
    </article>`;
  }
  async function renderExperiences(params){
    params=params instanceof URLSearchParams?params:new URLSearchParams();
    setApp(`<section class="cd-page ex-page-list">
      <header class="tp-hero">${heroImg('hero:experiencias')}<div class="tp-hero-in">
        <p class="eyebrow">Experiencias</p><h1>Viajes y vida a bordo</h1>
        <p class="lead">Destinos de buceo con salidas organizadas por centros y profesionales. Reservas directamente con quien organiza.</p>
        <form class="cd-search ex-search" id="exs-form" role="search"><label class="cd-field cd-field-q">${wdIcon('search',18)}<span class="sr-only">Buscar destino</span><input id="exs-q" type="search" placeholder="Destino, país o región" value="${escapeHtml(params.get('q')||'')}" autocomplete="off"></label><button class="btn btn-primary" type="submit">Buscar</button></form>
      </div></header>
      <div class="cd-wrap">
        <div class="cd-toolbar"><div class="cd-chips" id="exs-kinds" role="group" aria-label="Tipo de experiencia"></div><div class="cd-tools"><label><span class="sr-only">Ordenar</span><select id="exs-sort"><option value="recommended">Con más salidas</option><option value="price">Precio más bajo</option><option value="date">Próxima salida</option><option value="name">Nombre A-Z</option></select></label></div></div>
        <div class="cd-results-head"><p id="exs-count" aria-live="polite">Cargando destinos…</p></div>
        <div class="cd-grid" id="exs-grid"></div>
        <aside class="cd-owner"><div><p class="eyebrow">Para centros y profesionales</p><h2>Publica tus viajes</h2><p>Crea un viaje o una vida a bordo desde «Servicios y tarifas» y aparecerá aquí con sus fechas, plazas y precio actualizados.</p></div><a class="btn btn-primary" href="#/registro">Empezar a publicar</a></aside>
      </div></section>`);
    let d; try{ d=await loadTravelDirectory(); }catch(err){ $('#exs-grid').innerHTML=`<div class="empty cd-empty"><h3>No hemos podido cargar las experiencias</h3><p>${escapeHtml(err.message)}</p></div>`; $('#exs-count').textContent=''; return; }
    const st={kind:params.get('kind')||'',q:params.get('q')||'',sort:params.get('sort')||'recommended'};
    $('#exs-sort').value=st.sort;
    $('#exs-kinds').innerHTML=['',...(d.kinds||[])].map(k=>`<button type="button" class="cd-chip" data-kind="${escapeHtml(k)}" aria-pressed="${k===st.kind}">${escapeHtml(k||'Todas')}</button>`).join('');
    const draw=()=>{ const q=wdFold(st.q).trim(); let rows=(d.items||[]).filter(o=>(!st.kind||o.kind===st.kind)&&(!q||q.split(/\s+/).every(w=>wdFold([o.title,o.region,o.kind,o.summary].join(' ')).includes(w))));
      const by={price:(a,b)=>(a.price_from==null)-(b.price_from==null)||(a.price_from||0)-(b.price_from||0),date:(a,b)=>(!a.next_date)-(!b.next_date)||String(a.next_date||'').localeCompare(String(b.next_date||'')),name:(a,b)=>a.title.localeCompare(b.title,'es'),recommended:(a,b)=>(b.experiences||0)-(a.experiences||0)||a.title.localeCompare(b.title,'es')};
      rows=rows.slice().sort(by[st.sort]||by.recommended);
      $('#exs-grid').innerHTML=rows.map(destinationCard).join('')||'<div class="empty cd-empty"><h3>No hay destinos con esta búsqueda</h3><p>Prueba con otro país o quita el filtro.</p></div>';
      $('#exs-count').innerHTML=`<strong>${rows.length}</strong> ${rows.length===1?'destino':'destinos'}`;
      const url=new URLSearchParams(Object.entries(st).filter(([k,v])=>v&&!(k==='sort'&&v==='recommended'))); try{ history.replaceState(null,'','#/experiencias'+(url.toString()?'?'+url:'')); }catch{} };
    $$('#exs-kinds .cd-chip').forEach(b=>b.onclick=()=>{ st.kind=b.dataset.kind; $$('#exs-kinds .cd-chip').forEach(x=>x.setAttribute('aria-pressed',String(x===b))); draw(); });
    let timer=null; $('#exs-q').addEventListener('input',e=>{ clearTimeout(timer); timer=setTimeout(()=>{ st.q=e.target.value; draw(); },200); });
    $('#exs-form').onsubmit=e=>{ e.preventDefault(); st.q=$('#exs-q').value; draw(); };
    $('#exs-sort').onchange=e=>{ st.sort=e.target.value; draw(); };
    draw();
  }
  function tripCard(e){
    const org=e.provider_type==='center'||e.center_id?(e.center_name||e.provider_name||'Centro de buceo'):(e.provider_name||'Profesional independiente');
    const dates=e.departures?(e.departures.length?e.departures.slice(0,3).map(x=>escapeHtml(wdDay(x.slot_date))).join(' · '):'Por anunciar'):(e.start_date?escapeHtml(wdFullDate(e.start_date))+(e.end_date?' – '+escapeHtml(wdFullDate(e.end_date)):''):'Por confirmar');
    const spots=e.spots_available!=null?Number(e.spots_available):null;
    return `<article class="ex-trip">
      ${e.image_url?`<img class="ex-trip-img" src="${escapeHtml(e.image_url)}" alt="" loading="lazy">`:''}
      <div class="ex-trip-main">
        <p class="eyebrow">${e.provider_type==='freelance'?'Profesional independiente':'Centro de buceo'} · <a href="${e.center_id?`#/centro?id=${e.center_id}`:`#/profesional?id=${e.provider_user_id}`}">${escapeHtml(org)}</a></p>
        <h3>${escapeHtml(e.title)}</h3>
        ${e.summary||e.description?`<p class="ex-trip-desc">${escapeHtml(e.summary||e.description)}</p>`:''}
        ${e.includes?`<p class="ex-trip-inc"><strong>Incluye:</strong> ${escapeHtml(e.includes)}</p>`:''}
      </div>
      <div class="ex-trip-side">
        <div class="cd-fact"><small>${e.departures?'Próximas salidas':'Fechas'}</small><strong>${dates}</strong></div>
        <div class="cd-fact"><small>Precio</small><strong>${e.price!=null&&e.price!==''?wdMoney(e.price,e.currency):'<span class="muted">Consultar</span>'}</strong></div>
        <div class="cd-fact"><small>Plazas</small><strong>${spots!=null?(spots>0?`${spots} libres`:'<span class="muted">Completo</span>'):'<span class="muted">Consultar</span>'}</strong></div>
        ${e.book_url?`<a class="btn btn-primary" href="${escapeHtml(e.book_url)}">Reservar plaza</a>`:spots===0?'<span class="btn" aria-disabled="true">Completo</span>':`<button class="btn btn-primary book-experience" type="button" data-id="${e.id}">Solicitar plaza</button>`}
        <button type="button" class="wd-report" data-report="experience" data-report-id="${e.id}" data-report-label="${escapeHtml(e.title)}">${wdIcon('alert',13)} Denunciar</button>
      </div>
    </article>`;
  }
  async function renderExperienceDetail(params){
    const id=Number(params.get('id')||0); if(!id){ location.replace('#/experiencias'); return; }
    const still=navGuard(); let d; try{ d=await api('/api/travel-offers/'+id); }catch(err){ if(!still()) return; setApp(`<section class="page"><div class="empty"><h2>Destino no encontrado</h2><p>${escapeHtml(err.message)}</p><a class="btn btn-primary" href="#/experiencias">Ver todos los destinos</a></div></section>`); return; }
    if(!still()) return; const o=d.offer, items=d.experiences||[];
    const prices=items.map(e=>Number(e.price)).filter(n=>n>0);
    setApp(`<section class="tp-page">
      <header class="tp-hero tp-dhero"><img class="tp-hero-img" src="${escapeHtml(o.image_path||'/assets/images/fondo.webp')}" alt=""><div class="tp-hero-in">
        <nav class="tp-crumbs"><a href="#/experiencias">Experiencias</a><span>/</span>${escapeHtml(o.title)}</nav>
        <h1>${escapeHtml(o.title)}</h1><p class="lead">${escapeHtml(o.summary||o.description||'Experiencias de buceo en este destino.')}</p>
      </div></header>
      <div class="tp-facts"><div><small>Tipo</small><strong>${escapeHtml(o.kind||'Viaje')}</strong></div><div><small>Destino</small><strong>${escapeHtml(o.region||'—')}</strong></div><div><small>Viajes publicados</small><strong>${items.length}</strong></div><div><small>Desde</small><strong>${prices.length?wdMoney(Math.min(...prices),items[0]?.currency):'Consultar'}</strong></div></div>
      <div class="tp-wrap tp-dbody">
        <div class="tp-main">
          ${o.description&&o.summary?`<section class="tp-block"><h2>El destino</h2><p class="tp-body">${escapeHtml(o.description)}</p></section>`:''}
          <section class="tp-block"><h2>Viajes disponibles</h2>${items.length?`<div class="ex-trips">${items.map(tripCard).join('')}</div>`:`<div class="empty"><h3>Todavía no hay viajes publicados</h3><p>Cuando un centro o profesional publique una propuesta para ${escapeHtml(o.title)}, aparecerá aquí.</p></div>`}</section>
        </div>
        <aside class="tp-side"><div class="tp-side-card"><h3>Cómo funciona</h3><ol class="ex-how"><li>Cada viaje lo publica un centro o un profesional, con sus fechas, plazas y precio.</li><li>Reservas o solicitas plaza directamente con quien organiza.</li><li>Te confirma por la plataforma y lo ves en «Mi área».</li></ol></div>
          <div class="tp-side-card"><h3>¿Organizas viajes aquí?</h3><p class="pp-small">Publícalo desde tu panel y aparecerá en este destino.</p><a class="btn" href="#/registro">Publicar un viaje</a></div></aside>
      </div>
    </section>`);
    $$('.book-experience').forEach(b=>b.onclick=async()=>{ const me=await api('/api/me').catch(()=>({})); const target='#/experienciareserva?id='+b.dataset.id; if(!me.authenticated){ location.hash='#/login?next='+encodeURIComponent(target); return; } location.hash=target; });
  }

  // ---------------------------------------------------------------- Top 10
  function top10Card(p, index){
    const rating=Number(p.rating_average||0), reviews=Number(p.review_count||0), depth=depthText(p);
    return `<article class="tt-card">
      <span class="tt-rank" aria-label="Puesto ${index+1}">${index+1}</span>
      <a class="tt-media" href="${pointHref(p.id)}" tabindex="-1" aria-hidden="true"><img src="${escapeHtml(p.photo||pointImg(p))}" alt="" loading="lazy"></a>
      <div class="tt-main">
        <p class="eyebrow">${escapeHtml((p.types||[]).map(typeLabelByKey)[0]||p.dive_type||'Punto de buceo')}</p>
        <h3><a href="${pointHref(p.id)}">${escapeHtml(p.name)}</a></h3>
        <p class="cd-place">${wdIcon('pin',14)}${escapeHtml(placeText(p))}</p>
        <div class="pt-facts">${depth?`<span>${wdIcon('depth',14)}${escapeHtml(depth)}</span>`:''}${p.difficulty?`<span>${wdIcon('level',14)}${escapeHtml(p.difficulty)}</span>`:''}${reviews?`<span class="cd-rating"><span class="cd-star">★</span><strong>${rating.toFixed(1)}</strong>(${reviews})</span>`:''}${p.centers_count?`<span>${p.centers_count} ${p.centers_count==1?'centro':'centros'}</span>`:''}</div>
      </div>
      <div class="tt-side"><span class="tt-dist">${Number(p.distance_km||0).toLocaleString(wdLocale(),{maximumFractionDigits:1})} km</span><a class="btn btn-primary" href="${pointHref(p.id)}">Ver inmersión</a></div>
    </article>`;
  }
  async function renderTop10(params){
    params=params instanceof URLSearchParams?params:new URLSearchParams();
    setApp(`<section class="cd-page tt-page">
      <header class="tp-hero">${heroImg('hero:top10')}<div class="tp-hero-in">
        <p class="eyebrow">Top 10</p><h1>¿Te apetece bucear?</h1>
        <p class="lead">Los 10 mejores puntos de buceo cerca de ti, ordenados por valoración y distancia.</p>
        <div class="tt-locate"><div class="tt-loc-text"><strong id="tt-title">Usa tu ubicación o elige una zona</strong><small id="tt-sub">Tu ubicación solo se usa para calcular este ranking: no la guardamos.</small></div>
          <label class="tt-radius"><span>Radio</span><select id="tt-radius"><option value="25">25 km</option><option value="50">50 km</option><option value="100" selected>100 km</option><option value="250">250 km</option><option value="500">500 km</option></select></label>
          <div class="tt-btns"><button id="tt-locate" class="btn btn-primary" type="button">${wdIcon('target',16)} Usar mi ubicación</button><button id="tt-pick" class="btn tt-pick" type="button">${wdIcon('map',16)} Elegir en el mapa</button></div></div>
        <form class="tt-search" id="tt-search" role="search"><label class="cd-field">${wdIcon('search',18)}<span class="sr-only">Buscar una localidad</span><input id="tt-q" type="search" placeholder="O escribe una localidad: Dénia, Jávea, Cartagena…" list="tt-places" autocomplete="off"></label><datalist id="tt-places"></datalist><button class="btn btn-primary" type="submit">Buscar</button></form>
      </div></header>
      <div class="cd-wrap">
        <div class="tt-zones"><span>O elige una zona:</span><div class="cd-chips" id="tt-zones"></div></div>
        <div id="tt-status" class="tt-status" aria-live="polite"></div>
        <div id="tt-list" class="tt-list"></div>
      </div></section>`);
    const status=$('#tt-status'), list=$('#tt-list'), title=$('#tt-title'), sub=$('#tt-sub');
    let last=null;
    const remember=v=>{ try{ localStorage.setItem('wd_top10',JSON.stringify(v)); }catch{} };
    const load=async(lat,lon,label,acc)=>{
      last={lat,lon,label,acc}; const radius=$('#tt-radius').value;
      title.textContent=label?`Top 10 cerca de ${label}`:'Top 10 cerca de ti'; sub.textContent=`Hasta ${radius} km a la redonda`+(acc?` · precisión de tu ubicación: ${acc>=1000?'± '+Math.round(acc/1000)+' km':'± '+Math.round(acc)+' m'}.`:'.');
      list.innerHTML=Array.from({length:3},()=>'<div class="tt-card is-skeleton"></div>').join(''); status.innerHTML='';
      try{
        const d=await api('/api/top-dives?'+new URLSearchParams({lat,lon,radius}));
        const items=d.items||[];
        status.innerHTML=items.length?(d.has_reviews?'Ordenado por la valoración de los centros que bucean en cada punto y por cercanía.':'Aún no hay reseñas en esta zona: el orden combina el catálogo y la cercanía.'):'';
        const nx=d.nearest; const bigger=[...$('#tt-radius').options].map(o=>+o.value).find(v=>nx&&v>=nx.distance_km);
        list.innerHTML=items.length?items.map(top10Card).join(''):`<div class="empty cd-empty"><h3>No hay puntos a menos de ${radius} km</h3>${nx?`<p>El punto de buceo más cercano es <a href="${pointHref(nx.id)}">${escapeHtml(nx.name)}</a> (${escapeHtml([nx.subregion||nx.region,nx.country].filter(Boolean).join(', '))}), a ${Math.round(nx.distance_km).toLocaleString(wdLocale())} km.</p>${bigger?`<button type="button" class="btn btn-primary" id="tt-widen" data-r="${bigger}">Ver el Top 10 a ${bigger} km</button>`:''}`:'<p>Amplía el radio o elige otra zona.</p>'}</div>`;
        $('#tt-widen')?.addEventListener('click',e=>{ $('#tt-radius').value=e.target.dataset.r; load(last.lat,last.lon,last.label,last.acc); });
      }catch(e){ list.innerHTML=`<div class="empty cd-empty"><h3>No hemos podido calcular el Top 10</h3><p>${escapeHtml(e.message)}</p></div>`; }
    };
    $('#tt-radius').onchange=()=>{ if(last) load(last.lat,last.lon,last.label,last.acc); };
    // Ubicación precisa: se escucha el GPS unos segundos y se queda la lectura más precisa. Si el navegador solo da una
    // posición aproximada (por la conexión a internet, típica en ordenadores), no se calcula un ranking engañoso: se avisa.
    let watchId=null;
    const stopWatch=()=>{ if(watchId!=null){ try{ navigator.geolocation.clearWatch(watchId); }catch{} watchId=null; } };
    const kmTxt=m=>m>=1000?`${Math.round(m/1000).toLocaleString(wdLocale())} km`:`${Math.round(m)} m`;
    const imprecise=(pos)=>{ const {latitude:la,longitude:lo,accuracy:acc}=pos.coords;
      title.textContent='Tu ubicación no es precisa'; sub.textContent=`Tu navegador solo sabe dónde estás con un margen de ± ${kmTxt(acc)}.`;
      list.innerHTML=''; status.innerHTML=`<div class="tt-warn">${wdIcon('alert',20)}<div><strong>Así no podemos saber qué tienes cerca.</strong><p>Tu navegador ha calculado una ubicación aproximada (± ${kmTxt(acc)}), seguramente a partir de tu conexión a internet y no del GPS. Pasa a menudo en ordenadores. Para ver de verdad los puntos más cercanos, elige tu posición en el mapa o escribe tu localidad.</p>
        <div class="tt-warn-actions"><button type="button" class="btn btn-primary" id="tt-warn-pick">${wdIcon('map',15)} Elegir en el mapa</button><button type="button" class="btn" id="tt-warn-search">${wdIcon('search',15)} Escribir mi localidad</button><button type="button" class="btn tt-warn-anyway" id="tt-warn-anyway">Usar igualmente</button></div></div></div>`;
      translateTree(status);
      $('#tt-warn-pick').onclick=()=>pick({lat:la,lon:lo}); $('#tt-warn-search').onclick=()=>{ $('#tt-q').focus(); $('#tt-q').scrollIntoView({behavior:'smooth',block:'center'}); };
      $('#tt-warn-anyway').onclick=()=>load(la,lo,'',acc);
    };
    const locate=()=>{
      if(!navigator.geolocation){ status.textContent='Tu navegador no permite obtener la ubicación. Elige en el mapa o escribe tu localidad.'; return; }
      stopWatch(); title.textContent='Buscando tu ubicación…'; sub.textContent='Puede tardar unos segundos. Si te lo pide, permite el acceso a la ubicación.';
      $$('#tt-zones .cd-chip').forEach(x=>x.setAttribute('aria-pressed','false'));
      let best=null, done=false;
      const finish=()=>{ if(done) return; done=true; stopWatch(); clearTimeout(timer);
        if(!best){ title.textContent='Ubicación no disponible'; sub.textContent='No se ha podido obtener. Elige en el mapa o escribe tu localidad.'; return; }
        remember({geo:true}); const acc=best.coords.accuracy;
        if(acc>20000) imprecise(best); else load(best.coords.latitude,best.coords.longitude,'',acc);
      };
      const timer=setTimeout(finish,12000);
      watchId=navigator.geolocation.watchPosition(pos=>{ if(!best||pos.coords.accuracy<best.coords.accuracy) best=pos; sub.textContent=`Afinando tu ubicación… ± ${kmTxt(best.coords.accuracy)}`; if(pos.coords.accuracy<=100) finish(); },
        err=>{ if(best){ finish(); return; } done=true; stopWatch(); clearTimeout(timer); title.textContent='Ubicación no disponible'; sub.textContent=err&&err.code===1?'Has denegado el permiso de ubicación. Elige en el mapa o escribe tu localidad.':'No se ha podido obtener. Elige en el mapa o escribe tu localidad.'; },
        {enableHighAccuracy:true,maximumAge:0,timeout:12000});
    };
    let layerItems=[];
    const pick=start=>wdPickOnMap({start:start||last,onPick:(la,lo)=>{ const np=wdNearestPlace(layerItems,la,lo); const lab=np&&np.km<40?np.name:''; remember({pick:{lat:la,lon:lo,label:lab}}); $$('#tt-zones .cd-chip').forEach(x=>x.setAttribute('aria-pressed','false')); load(la,lo,lab); }});
    $('#tt-locate').onclick=locate; $('#tt-pick').onclick=()=>pick();
    $('#tt-search').onsubmit=async e=>{ e.preventDefault(); const q=$('#tt-q').value.trim(); if(!q) return; const f=wdFold(q);
      const local=places.find(p=>wdFold(p.name)===f)||places.find(p=>wdFold(p.name).startsWith(f));
      if(local){ remember({pick:{lat:local.lat,lon:local.lon,label:local.name}}); load(local.lat,local.lon,local.name); return; }
      try{ title.textContent='Buscando la localidad…'; const g=await wdGeocode(q); if(!g){ title.textContent='No hemos encontrado esa localidad'; sub.textContent='Prueba con otro nombre o elige en el mapa.'; return; }
        remember({pick:g}); load(g.lat,g.lon,g.label); }catch(err){ title.textContent='No se ha podido buscar'; sub.textContent='Comprueba la conexión o elige en el mapa.'; } };
    let places=[];
    // Zonas: centro de cada subzona con más puntos, calculado de la capa del mapa.
    let areas=[];
    try{ const layer=await loadMapLayer(); layerItems=layer.items; const by={}; layer.items.forEach(p=>{ const k=p.subregion||p.region||p.country; if(!k) return; const a=by[k]??={name:k,lat:0,lon:0,n:0}; a.lat+=Number(p.latitude); a.lon+=Number(p.longitude); a.n++; }); areas=Object.values(by).filter(a=>a.n>=3).sort((a,b)=>b.n-a.n).slice(0,10).map(a=>({name:a.name,lat:a.lat/a.n,lon:a.lon/a.n}));
      const pl={}; layer.items.forEach(p=>{ String(p.subregion||'').split('·').map(s=>s.trim()).filter(Boolean).forEach(k=>{ const a=pl[k]??={name:k,lat:0,lon:0,n:0}; a.lat+=Number(p.latitude); a.lon+=Number(p.longitude); a.n++; }); });
      places=Object.values(pl).map(a=>({name:a.name,lat:a.lat/a.n,lon:a.lon/a.n})).sort((a,b)=>a.name.localeCompare(b.name));
      $('#tt-places').innerHTML=places.map(p=>`<option value="${escapeHtml(p.name)}"></option>`).join(''); }catch{}
    $('#tt-zones').innerHTML=areas.map((a,i)=>`<button type="button" class="cd-chip" data-i="${i}" aria-pressed="false">${escapeHtml(a.name)}</button>`).join('');
    $$('#tt-zones .cd-chip').forEach(b=>b.onclick=()=>{ const a=areas[+b.dataset.i]; $$('#tt-zones .cd-chip').forEach(x=>x.setAttribute('aria-pressed',String(x===b))); remember({area:a.name}); load(a.lat,a.lon,a.name); });
    let saved=null; try{ saved=JSON.parse(localStorage.getItem('wd_top10')||'null'); }catch{}
    const lat=Number(params.get('lat')), lon=Number(params.get('lon'));
    if(Number.isFinite(lat)&&Number.isFinite(lon)&&params.get('lat')) load(lat,lon,params.get('label')||'');
    else if(saved?.area){ const i=areas.findIndex(a=>a.name===saved.area); if(i>=0) $$('#tt-zones .cd-chip')[i].click(); }
    else if(saved?.pick&&Number.isFinite(+saved.pick.lat)) load(+saved.pick.lat,+saved.pick.lon,saved.pick.label||'');
    else if(saved?.geo) locate();
    else if(areas[0]){ status.textContent='Pulsa «Usar mi ubicación» o elige una zona para ver su Top 10.'; }
  }

  async function renderProfessional(params){ const id=Number(params.get('id')||0); if(!id){setApp('<section class="page"><div class="empty"><h2>Profesional no encontrado</h2></div></section>');return;} const p=await api('/api/providers/'+id); const c=p.center||{}; const socialSource=p.role==='freelance'?p.socials:c; const socials=[['instagram_url','Instagram','◎'],['facebook_url','Facebook','f'],['twitter_url','X / Twitter','𝕏'],['youtube_url','YouTube','▶'],['tiktok_url','TikTok','♪']].filter(x=>socialSource&&socialSource[x[0]]); setApp(`<section class="page"><div class="breadcrumb"><a href="#/experiencias">Experiencias</a> / Profesional</div><div class="detail"><article class="detail-main"><p class="eyebrow">${p.role==='center'?'CENTRO DE BUCEO':'PROFESIONAL / FREELANCE'}</p><div style="display:flex;align-items:center;gap:16px">${p.role==='center'?centerLogoMarkup(c,'84px'):(p.avatar_url?`<img src="${escapeHtml(p.avatar_url)}" alt="" style="width:84px;height:84px;object-fit:cover;border-radius:50%">`: '')}<h1>${escapeHtml(c.name||p.fullname)}</h1></div>${c.city?`<div class="point-meta"><span class="meta-badge">${escapeHtml(c.city)}</span><span class="meta-badge">${escapeHtml(c.country||'')}</span></div>`:''}<p class="lead">${escapeHtml(c.description||p.provider_bio||'Profesional de buceo en WORLDIVES DISCOVERY.')}</p>${socials.length?`<div class="provider-socials">${socials.map(x=>`<a class="social-chip" href="${escapeHtml(socialSource[x[0]])}" target="_blank" rel="noopener noreferrer"><span>${x[2]}</span>${x[1]}</a>`).join('')}</div>`:''}<div class="data-grid"><div class="data-item"><span>Especialidad</span><strong>${escapeHtml(c.specialties||'Buceo y experiencias')}</strong></div><div class="data-item"><span>Web</span><strong>${c.website?`<a href="${escapeHtml(c.website)}" target="_blank" rel="noopener">Visitar</a>`:'—'}</strong></div><div class="data-item"><span>Contacto</span><strong>${escapeHtml(c.email||c.phone||'Disponible a través de WORLDIVES DISCOVERY')}</strong></div></div><div id="pro-services"></div><div class="page-actions"><a class="btn" href="#\/experiencias">Volver a experiencias</a></div></article></div></section>`);
    // Fase 2.7: a freelance professional without a centre takes bookings (and online payments) for his own services.
    if(p.role==='freelance'){ try{ const sv=(await api('/api/provider-services?provider_id='+id)).items.filter(x=>!x.center_id&&x.service_type!=='alquiler_equipo'); const m=$('#pro-services');
      if(m&&sv.length){ m.innerHTML=`<h2 style="margin-top:26px">Servicios</h2><div class="cp-services">${sv.map(x=>`<article class="cp-service"><div><strong>${escapeHtml(x.title)}</strong><small>${escapeHtml(x.mode_label||'')}</small>${x.description?`<p>${escapeHtml(x.description)}</p>`:''}</div><div class="cp-service-side"><b>${wdMoney(x.price,x.currency)}</b><small>por persona</small>${(x.slots||[]).length&&x.bookable!==false?`<a class="btn btn-primary cp-book" href="#/reservar?provider=${id}&service=${x.id}">${x.booking_mode==='payment'?'Reservar y pagar':'Enviar solicitud'}</a>`:'<small>Sin salidas programadas</small>'}</div></article>`).join('')}</div>`; translateTree(m); } }catch{}
      const m=$('#pro-services');
      if(p.online_booking===false&&m){ m.querySelectorAll('a.cp-book').forEach(x=>x.remove()); m.insertAdjacentHTML('beforeend',`<div class="notice" style="margin-top:16px">${wdIcon('info',16)} Este profesional todavía no tiene reserva online en WORLDIVES. <button type="button" class="btn btn-primary" id="pro-info">Solicitar información</button></div>`); translateTree(m);
        $('#pro-info').onclick=()=>openInfoRequest({provider_user_id:id,name:p.fullname}); }
      else m?.querySelectorAll('a.cp-book').forEach(x=>x.addEventListener('click',()=>postJSON('/api/stats/track',{event:'book_click',type:'freelance',id}).catch(()=>{}))); } }
  function authCard(title, inner){ return `<section class="auth-split">
    <aside class="auth-visual">${heroImg('hero:auth')}<div class="auth-visual-in"><p class="eyebrow">WORLDIVES DISCOVERY</p><h2>Tu buceo, en un solo sitio</h2><ul><li>Reserva con centros de todo el mundo</li><li>Tu titulación y tu Log Book siempre contigo</li><li>Recompensas por cada inmersión</li></ul></div></aside>
    <div class="auth-panel"><div class="auth-card"><h1>${escapeHtml(title)}</h1>${inner}</div></div>
  </section>`; }

  // Same legal information as the dive booking screen: who provides it, final price, no 14-day withdrawal, policy.
  function expLegalBlock(e){ const esc=escapeHtml, p=e.provider_legal||{};
    return `<div class="bk-legal eb-legal"><p><b>Prestado por ${esc(p.name||e.center_name||e.provider_name||'el organizador')}${p.country?', '+esc(p.country):''}.</b> WORLDIVES DISCOVERY es la plataforma de reservas: no organiza ni presta la actividad.</p>
      <p>Precio final fijado por el organizador, impuestos incluidos.</p>
      ${p.policy_text?`<p><b>Política de cancelación.</b> <span translate="no">${esc(p.policy_text)}</span>${p.policy_note?' '+esc(p.policy_note):''}</p>`:''}
      <p>Las actividades de ocio con fecha concreta no tienen derecho de desistimiento de 14 días (art. 103.l del TRLGDCU); se aplica la política de cancelación del organizador.</p>
      <label class="lg-check"><input type="checkbox" id="eb-accept" required> <span>Acepto las <a href="#/legal/condiciones-reserva" target="_blank" rel="noopener">condiciones de reserva</a> y la política de cancelación del organizador.</span></label></div>`; }
  async function renderExperienceBooking(params){
    const id=Number(params.get('id')||0); if(!id){location.hash='#/experiencias';return;}
    let e; try{ e=(await api('/api/travel-experiences/'+id+'?lang='+currentLanguage())).item; }catch(err){ setApp('<section class="page"><div class="empty"><h2>Experiencia no disponible</h2><p>Puede que se haya completado o que el organizador la haya retirado.</p><a class="btn btn-primary" href="#/experiencias">Ver otras experiencias</a></div></section>'); return; }
    if(e.book_url){ location.hash=e.book_url; return; }  // trips sold as a service use the booking engine
    if(!state.me){ location.hash='#/login?next='+encodeURIComponent('#/experienciareserva?id='+id); return; }
    const max=e.spots_available!=null?Math.max(0,Number(e.spots_available)):99;
    setApp(`<section class="page auth"><div class="auth-card"><p class="eyebrow">SOLICITAR EXPERIENCIA</p><h1 style="font-size:40px">${escapeHtml(e.title)}</h1><p class="lead" style="font-size:15px">${escapeHtml(e.destination_title||'')} · ${escapeHtml(e.center_name||e.provider_name||'Organizador')}</p>
      <div class="data-grid" style="margin-top:14px"><div class="data-item"><span>Fechas</span><strong>${e.start_date?escapeHtml(wdFullDate(e.start_date))+(e.end_date?' – '+escapeHtml(wdFullDate(e.end_date)):''):'Por confirmar'}</strong></div><div class="data-item"><span>Precio por persona</span><strong>${e.price!=null?wdMoney(e.price,e.currency):'Consultar'}</strong></div><div class="data-item"><span>Plazas libres</span><strong>${e.spots_available!=null?escapeHtml(String(e.spots_available)):'Consultar'}</strong></div></div>
      ${max<=0?'<div class="empty" style="margin-top:18px">Esta experiencia está completa.</div>':`<form id="experience-booking-form" style="margin-top:20px"><div class="field"><label for="eb-participants">Participantes</label><input id="eb-participants" type="number" min="1" max="${max}" value="1" required></div><div class="field"><label for="eb-notes">Mensaje para el organizador</label><textarea id="eb-notes" placeholder="Certificación, equipo, dudas…"></textarea></div>${expLegalBlock(e)}<div class="form-actions"><button class="btn btn-primary">Enviar solicitud</button><a class="btn" href="#/experiencia?id=${e.travel_offer_id}">Volver</a></div></form>`}</div></section>`);
    $('#experience-booking-form')?.addEventListener('submit',async ev=>{ev.preventDefault();if(!$('#eb-accept')?.checked){toast('Acepta las condiciones para enviar la solicitud.');return;}try{const created=await postJSON('/api/experience-bookings',{travel_experience_id:id,participants:+$('#eb-participants').value,notes:$('#eb-notes').value}); if(created.payment_required){const pay=await postJSON('/api/payments/checkout',{experience_booking_id:created.id}).catch(()=>null); if(pay?.checkout_url){location.href=pay.checkout_url;return;}} toast('Solicitud enviada. El organizador te responderá en tu área.');location.hash='#/area';}catch(err){toast(err.message)}});
  }

  async function renderLogin(){ if((await api('/api/me')).authenticated){location.hash='#/cuenta';return;} const st=await api('/api/setup/status').catch(()=>({})); const nextParam = new URLSearchParams(location.hash.split('?')[1]||'').get('next'); if(nextParam) sessionStorage.setItem('wd_after_login', nextParam.startsWith('#')?nextParam:'#'+nextParam);
    setApp(authCard('Iniciar sesión',`<p class="lead" style="font-size:15px">Entra para gestionar tus documentos, reservas y Log Book.</p><form id="login-form"><div class="field"><label for="login">Email o usuario</label><input id="login" required autocomplete="username"></div><div class="field"><label for="password">Contraseña</label><input id="password" type="password" required autocomplete="current-password"></div><div class="field" id="totp-field" hidden><label for="totp">Código de verificación (6 cifras) o código de recuperación</label><input id="totp" inputmode="numeric" autocomplete="one-time-code" maxlength="20"></div><p class="lg-forgot"><a href="#/recuperar">¿Has olvidado tu contraseña?</a></p><div class="form-actions"><button class="btn btn-primary" type="submit">Entrar</button></div></form>${st.registration_open===false?'':'<p style="margin-top:18px;font-size:13px;color:var(--muted)">¿No tienes cuenta? <a href="#/registro" style="color:var(--sea);font-weight:800">Crear cuenta</a></p>'}${st.setup_allowed?'<div class="notice" style="margin-top:16px">Primera instalación: <a href="#/setup" style="font-weight:800">crear cuenta administradora</a>.</div>':''}`));
    let challenge=null;
    $('#login-form').onsubmit=async e=>{e.preventDefault();try{const body={login:$('#login').value,password:$('#password').value}; if(challenge){ body.totp_challenge=challenge; body.totp_code=$('#totp').value.trim(); } const r=await postJSON('/api/auth/login',body); if(r.totp_required){ challenge=r.challenge; $('#totp-field').hidden=false; $('#totp').required=true; $('#totp').focus(); toast('Escribe el código de tu aplicación de verificación.'); return; } await loadMe(); const next=sessionStorage.getItem('wd_after_login'); sessionStorage.removeItem('wd_after_login'); location.hash=r.totp_setup_required?'#/cuenta?seguridad=1':(next||'#/'); toast(r.totp_setup_required?'Activa la verificación en dos pasos para usar la administración.':'Sesión iniciada.');}catch(err){toast(err.message)}}; }
  async function renderRegister(){ const nextParam = new URLSearchParams(location.hash.split('?')[1]||'').get('next'); if(nextParam) sessionStorage.setItem('wd_after_login', nextParam.startsWith('#')?nextParam:'#'+nextParam); const st=await api('/api/setup/status').catch(()=>({}));
    if(st.registration_open===false){ setApp(authCard('Registro cerrado','<div class="notice">Esta es una versión de demostración: no se pueden crear cuentas nuevas.</div><p><a class="btn" href="#/login">Iniciar sesión</a></p>')); return; }
    const preType=new URLSearchParams(location.hash.split('?')[1]||'').get('tipo');
    setApp(authCard('Crear cuenta',`<p class="lead" style="font-size:15px">Crea tu perfil y elige el tipo de cuenta que corresponde a tu actividad.</p><form id="register-form" novalidate><div class="form-grid"><div class="field full"><label for="r-name">Nombre completo</label><input id="r-name" required autocomplete="name"></div><div class="field"><label for="r-email">Email</label><input id="r-email" type="email" required autocomplete="email"></div><div class="field"><label for="r-user">Usuario</label><input id="r-user" required autocomplete="username" pattern="[A-Za-z0-9._-]{3,40}"><small>De 3 a 40 letras, números, punto o guion.</small></div><div class="field full"><label for="r-type">Tipo de cuenta</label><select id="r-type"><option value="recreational">Buceador / cliente</option><option value="center">Centro de buceo</option><option value="freelance">Profesional / freelance</option></select><small>El centro gestiona su ficha, puntos y reservas. El profesional/freelance gestiona su perfil y sus experiencias. El buceador usa el Log Book, las reservas y los Puntos.</small></div><div id="center-fields" class="form-grid full" hidden><div class="field full" id="r-center-name-wrap"><label for="r-center-name">Nombre del centro</label><input id="r-center-name" placeholder="Ej. Centro de Buceo Xàbia" autocomplete="organization"></div><div class="field"><label for="r-phone">Teléfono de contacto</label><input id="r-phone" type="tel" autocomplete="tel"></div><div class="field"><label for="r-city">Ciudad</label><input id="r-city" autocomplete="address-level2"></div><div class="field full"><label for="r-website">Web (opcional)</label><input id="r-website" type="url" placeholder="https://…" autocomplete="url"></div><div class="field full" id="r-invite-wrap" hidden><label for="r-invite">Código de invitación</label><input id="r-invite" autocomplete="off"></div><div class="notice full">Las cuentas profesionales se activan cuando comprobamos que el centro o el profesional es quien dice ser (email del dominio del centro, llamada a su teléfono público o documento). Mientras tanto la cuenta funciona como cuenta de buceador.</div></div><div class="field"><label for="r-pass">Contraseña</label><input id="r-pass" type="password" minlength="10" required autocomplete="new-password"></div><div class="field"><label for="r-pass2">Repite la contraseña</label><input id="r-pass2" type="password" minlength="10" required autocomplete="new-password"></div></div><div class="lg-accept"><label class="lg-check" for="r-terms"><input type="checkbox" id="r-terms" required><span>He leído y acepto las <a href="#/legal/condiciones-buceadores" target="_blank" rel="noopener">condiciones de uso</a> y la <a href="#/legal/privacidad" target="_blank" rel="noopener">política de privacidad</a>. Soy mayor de 18 años.</span></label><label class="lg-check" for="r-pro-terms" id="r-pro-wrap" hidden><input type="checkbox" id="r-pro-terms"><span>Acepto las <a href="#/legal/condiciones-centros" target="_blank" rel="noopener">condiciones para centros y profesionales</a>.</span></label><label class="lg-check" for="r-marketing"><input type="checkbox" id="r-marketing"><span>Quiero recibir novedades y ofertas de WORLDIVES por email (opcional; puedes darte de baja en cualquier momento).</span></label></div><div class="form-actions"><button class="btn btn-primary">Crear cuenta</button></div></form>`));
    const type=$('#r-type'),cf=$('#center-fields'); if(['center','freelance'].includes(preType)) type.value=preType;
    const pilot=st.pilot_mode; const toggleCenter=()=>{const center=type.value==='center'; const pro=['center','freelance'].includes(type.value); cf.hidden=!pro; $('#r-center-name-wrap').hidden=!center; $('#r-center-name').required=center; $('#r-phone').required=pro; $('#r-pro-wrap').hidden=!pro; $('#r-pro-terms').required=pro; $('#r-invite-wrap').hidden=!(pro&&pilot);}; type.onchange=toggleCenter; toggleCenter();
    $('#register-form').onsubmit=async e=>{e.preventDefault(); const f=e.target; if(!f.reportValidity()) return; if($('#r-pass').value!==$('#r-pass2').value){toast('Las contraseñas no coinciden.');return;} try{const r=await postJSON('/api/auth/register',{fullname:$('#r-name').value,email:$('#r-email').value,username:$('#r-user').value,password:$('#r-pass').value,account_type:type.value,center_name:$('#r-center-name').value,phone:$('#r-phone').value,city:$('#r-city').value,website:$('#r-website').value,invite_code:$('#r-invite').value,accept_terms:$('#r-terms').checked,accept_pro_terms:$('#r-pro-terms').checked,accept_marketing:$('#r-marketing').checked,lang:currentLanguage()});await loadMe(); const next=sessionStorage.getItem('wd_after_login'); sessionStorage.removeItem('wd_after_login'); location.hash=r.provider_verification?'#/cuenta':(next||'#/area'); toast(r.provider_verification?'Cuenta creada. Tu solicitud profesional está pendiente de verificación: te avisaremos por email.':'Cuenta creada. Revisa tu email para confirmar la dirección.');}catch(err){toast(err.message)}}; }

  async function renderSetup(){
    let st={};
    try {
      const me=await api('/api/me');
      if(me.authenticated){ location.hash='#/'; return; }
      st=await api('/api/setup/status');
    } catch(e){ toast(e.message); }
    if(!st.setup_allowed){ setApp(authCard('Instalación ya configurada', '<div class="notice">La instalación desde la web no está disponible. El administrador se crea en el servidor con <code>python app/server.py --create-admin</code>. <a href="#/login" style="font-weight:800;color:var(--sea)">Iniciar sesión</a>.</div>')); return; }
    setApp(authCard('Configurar WORLDIVES',`<p class="lead" style="font-size:15px">Es la primera puesta en marcha. Esta cuenta tendrá acceso de administración y podrás cambiar roles después.</p><form id="setup-form"><div class="form-grid"><div class="field full"><label for="s-name">Nombre</label><input id="s-name" required></div><div class="field"><label for="s-email">Email</label><input id="s-email" type="email" required></div><div class="field"><label for="s-user">Usuario</label><input id="s-user" required></div><div class="field full"><label for="s-pass">Contraseña (10+ caracteres)</label><input id="s-pass" type="password" minlength="10" required autocomplete="new-password"></div></div><div class="form-actions"><button class="btn btn-primary">Crear administrador</button></div></form>`));
    $('#setup-form').onsubmit=async e=>{e.preventDefault(); try{await postJSON('/api/setup',{fullname:$('#s-name').value,email:$('#s-email').value,username:$('#s-user').value,password:$('#s-pass').value});await loadMe();location.hash='#/cuenta?seguridad=1';toast('Administrador creado. Activa ahora la verificación en dos pasos.');}catch(err){toast(err.message)}};
  }

  // One set of booking states everywhere (same labels as the server, emails and PDFs).
  const WD_STATES={requested:['Solicitada','warn'],pending:['Solicitada','warn'],accepted_pending_payment:['Aceptada · pendiente de pago','warn'],payment_in_progress:['Pago en curso','muted'],confirmed:['Confirmada','good'],rejected:['Rechazada','bad'],expired:['Caducada','muted'],cancelled:['Cancelada','bad'],completed:['Completada','good']};
  function bookingStatus(status,label){ const x=WD_STATES[status]||[status||'—','muted']; return [label||x[0],x[1]]; }
  function experienceStatus(status){ const map={requested:['Solicitud enviada','warn'],confirmed:['Confirmada','good'],rejected:['No disponible','bad'],cancelled:['Cancelada','bad'],completed:['Completada','good']}; return map[status]||[status||'Solicitud enviada','warn']; }
  // «12/10 18:30» for deadlines (local time of the activity).
  function wdDeadline(v){ if(!v) return ''; const d=new Date(String(v).length<=16?String(v):v); if(isNaN(d)) return String(v); return d.toLocaleString(wdLocale(),{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}); }
  function daysUntil(date){ if(!date)return null; const d=new Date(date+'T00:00:00'); const today=new Date(); today.setHours(0,0,0,0); return Math.ceil((d-today)/86400000); }
  function areaDate(date,time=''){ return date ? `${fmtDate(date)}${time?' · '+escapeHtml(time):''}` : 'Fecha por confirmar'; }

  // ---------------------------------------------------------------------------
  // Área personal (v50.29): misma cabecera y navegación en todas las secciones de la cuenta.
  // ---------------------------------------------------------------------------
  const ACC_TABS=[['area','Mi área','home'],['logbook','Log Book','book'],['recompensas','Recompensas','gift'],['mis-puntos','Mis puntos','star'],['cuenta','Mi cuenta','user']];
  const ROLE_LABEL={admin:'Administrador',center:'Centro de buceo',freelance:'Profesional freelance',diver:'Buceador'};
  function accountShell(active,{eyebrow='',title='',lead='',actions=''},inner){
    const u=state.me?.user||{}, esc=escapeHtml, pro=['center','freelance','admin'].includes(u.role);
    const tabs=ACC_TABS.map(([k,l,i])=>{ const href=k==='area'&&pro?'#/admin':'#/'+k; const label=k==='area'&&pro?(u.role==='admin'?'Administración':u.role==='center'?'Mi centro':'Mi panel'):l;
      return `<a class="acc-tab ${k===active?'is-on':''}" href="${href}" ${k===active?'aria-current="page"':''}>${wdIcon(i,17)}<span>${label}</span></a>`; }).join('');
    return `<section class="acc-page"><header class="acc-hero" style="--acc-img:url('${esc(media('hero:centros'))}')"><div class="acc-hero-in">
        <div class="acc-id"><span class="acc-avatar" translate="no">${esc(initials(u.fullname||''))}</span><div><strong translate="no">${esc(u.fullname||'')}</strong><small>${esc(ROLE_LABEL[u.role]||'Buceador')}</small>${u.email&&!String(u.email).endsWith('.local')?`<small translate="no">${esc(u.email)}</small>`:''}</div></div>
        <a class="acc-level" id="acc-level" href="#/recompensas" hidden></a></div>
        <nav class="acc-tabs" aria-label="Secciones de mi cuenta">${tabs}</nav></header>
      <div class="acc-body"><div class="acc-head"><div>${eyebrow?`<p class="eyebrow">${eyebrow}</p>`:''}<h1>${title}</h1>${lead?`<p class="lead">${lead}</p>`:''}</div>${actions?`<div class="acc-actions">${actions}</div>`:''}</div>${inner}</div></section>`;
  }
  async function fillAccountLevel(d){
    const tabs=$('.acc-tabs'), on=$('.acc-tab.is-on'); if(tabs&&on) tabs.scrollLeft=Math.max(0,on.offsetLeft-(tabs.clientWidth-on.offsetWidth)/2);
    try{ if(!d){ if(state.accLevel&&Date.now()-state.accLevel.at<60000) d=state.accLevel.d; else { d=await api('/api/rewards'); } } state.accLevel={d,at:Date.now()};
      const el=$('#acc-level'); if(!el) return; el.innerHTML=`${wdIcon('star',15)}<span><b>${escapeHtml(d.level.name)}</b><small>${Number(d.balance??d.points).toLocaleString(wdLocale())} puntos</small></span>`; el.hidden=false; }catch{}
  }
  const accKpi=(icon,value,label,href,warn)=>`<${href?(href.startsWith('#acc')?`button type="button" data-jump="${href.slice(1)}"`:`a href="${href}"`):'div'} class="acc-kpi ${warn?'is-warn':''}"><span class="acc-kpi-ic">${wdIcon(icon,18)}</span><span><strong>${value}</strong><small>${label}</small></span></${href?(href.startsWith('#acc')?'button':'a'):'div'}>`;
  function accDate(date){ if(!date) return '<span class="acc-date"><b>—</b></span>'; const d=wdParseDate(date); return `<span class="acc-date"><b>${d.getDate()}</b><small>${escapeHtml(d.toLocaleDateString(wdLocale(),{month:'short'}).replace('.',''))}</small></span>`; }
  function profileCompletion(p,docs){ const checks=[['Teléfono',p?.phone],['Titulación',p?.certification_id],['Fecha de nacimiento',p?.date_of_birth],['Contacto de emergencia',p?.emergency_contact_name&&p?.emergency_contact_phone],['Tallas de equipo',p?.suit_size||p?.bcd_size],['Documentación',(docs||[]).length]];
    const done=checks.filter(c=>c[1]).length; return {pct:Math.round(done*100/checks.length),missing:checks.filter(c=>!c[1]).map(c=>c[0])}; }

  async function renderArea(){
    const me=await api('/api/me'); if(!me.authenticated){goLogin();return;} state.me=me; if(me.user.role==='center'){location.hash='#/admin';return;}
    const d=await api('/api/me/area'); const esc=escapeHtml, today=wdToday();
    const bookings=d.bookings||[], experiences=d.experience_bookings||[], messages=d.messages||[];
    const live=b=>!['completed','cancelled','rejected','expired'].includes(b.status)&&(b.booking_date||'9999')>=today;
    const upcoming=bookings.filter(live).sort((a,b)=>String(a.booking_date+a.booking_time).localeCompare(String(b.booking_date+b.booking_time)));
    const past=bookings.filter(b=>!live(b));
    const upcomingExp=experiences.filter(e=>!['completed','cancelled','rejected'].includes(e.status));
    const next=upcoming[0]; const comp=profileCompletion(me.profile,me.documents);
    const expiring=(me.documents||[]).filter(x=>x.expires_at&&daysUntil(x.expires_at)<45).length;
    const toPay=upcoming.filter(b=>Number(b.price)>0&&(b.payment_status==='review'||['accepted_pending_payment','payment_in_progress'].includes(b.status))).length;
    const bkRow=b=>{ const st=bookingStatus(b.status,b.status_label); const due=b.status==='accepted_pending_payment'&&b.payment_deadline?`<small class="acc-due">${wdIcon('clock',13)} Paga antes del ${esc(wdDeadline(b.payment_deadline))}</small>`:b.status==='requested'&&b.response_deadline?`<small class="acc-due">${wdIcon('clock',13)} El centro responde antes del ${esc(wdDeadline(b.response_deadline))}</small>`:''; return `<a class="acc-row" href="#/reserva?id=${b.id}">${accDate(b.booking_date)}<span class="acc-row-main"><strong>${esc(b.service_title||'Inmersión')} · ${esc(b.center_name)}</strong><small>${esc([b.booking_time,b.point_name||'Punto a concretar',`${b.participants} buceador${b.participants==1?'':'es'}`].filter(Boolean).join(' · '))}</small><small class="acc-mode">${esc(b.mode_label||'')}</small>${due}</span><span class="acc-row-tags"><span class="status ${st[1]}">${esc(st[0])}</span>${Number(b.price)>0?wdPayment(b.payment_status):''}</span><span class="acc-chev">${wdIcon('arrow',16)}</span></a>`; };
    const nextCard=next?(()=>{ const n=daysUntil(next.booking_date), st=bookingStatus(next.status,next.status_label); const when=n===0?'Hoy':n===1?'Mañana':`En ${n} días`; const maps=next.center_address?`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent([next.center_address,next.city].filter(Boolean).join(', '))}`:'';
      return `<article class="acc-next"><div class="acc-next-when"><span>${esc(when)}</span>${accDate(next.booking_date)}</div><div class="acc-next-main"><p class="eyebrow">TU PRÓXIMA INMERSIÓN</p><h2>${esc(next.service_title||'Inmersión')}</h2><p class="acc-next-meta">${wdIcon('calendar',15)} ${esc(wdLongDay(next.booking_date))}${next.booking_time?' · '+esc(next.booking_time):''}<br>${wdIcon('pin',15)} ${esc(next.center_name)}${next.point_name?' · '+esc(next.point_name):''}</p>
        <div class="acc-next-tags"><span class="status ${st[1]}">${esc(st[0])}</span>${Number(next.price)>0?wdPayment(next.payment_status):''}</div>
        <div class="page-actions"><a class="btn btn-primary" href="#/reserva?id=${next.id}">Ver reserva y QR</a><a class="btn" href="/api/bookings/${next.id}/receipt.pdf" target="_blank" rel="noopener">${wdIcon('download',15)} PDF sin conexión</a>${maps?`<a class="btn" href="${esc(maps)}" target="_blank" rel="noopener">${wdIcon('pin',15)} Cómo llegar</a>`:''}</div></div></article>`; })()
      :`<article class="acc-next is-empty"><div class="acc-next-main"><p class="eyebrow">TU PRÓXIMA INMERSIÓN</p><h2>¿Dónde buceamos?</h2><p>Busca un centro, elige salida y reserva en un minuto.</p><div class="page-actions"><a class="btn btn-primary" href="#/centros">Buscar centros</a><a class="btn" href="#/top10">Cerca de mí</a></div></div></article>`;
    setApp(accountShell('area',{eyebrow:'MI ÁREA',title:`Hola, <span translate="no">${esc(me.user.fullname.split(' ')[0])}</span>`,lead:'Tus reservas, viajes, avisos y documentación en un solo sitio.',actions:'<a class="btn btn-primary" href="#/centros">Reservar una inmersión</a>'},`
      <div class="acc-kpis">${accKpi('calendar',upcoming.length,'próximas reservas','#acc-bookings')}${accKpi('card',toPay,'pagos pendientes',null,toPay>0)}${accKpi('message',d.unread_messages||0,'avisos sin leer','#acc-messages',(d.unread_messages||0)>0)}${accKpi('shield',(me.documents||[]).length,expiring?`documentos · ${expiring} caducan pronto`:'documentos','#/cuenta?docs=1',expiring>0)}</div>
      <div class="acc-grid"><div class="acc-col">${nextCard}
        <section class="acc-card" id="acc-bookings"><div class="acc-card-head"><h2>Mis reservas</h2><div class="acc-seg" role="tablist"><button type="button" class="is-on" data-seg="up">Próximas <b>${upcoming.length}</b></button><button type="button" data-seg="past">Historial <b>${past.length}</b></button></div></div>
          <div class="acc-list" data-list="up">${upcoming.length?upcoming.map(bkRow).join(''):'<p class="acc-empty">No tienes reservas próximas.</p>'}</div>
          <div class="acc-list" data-list="past" hidden>${past.length?past.map(bkRow).join(''):'<p class="acc-empty">Aquí verás las inmersiones que ya has hecho.</p>'}</div><button type="button" class="btn acc-more" id="acc-more" hidden></button></section>
        <section class="acc-card"><div class="acc-card-head"><h2>Viajes y vida a bordo</h2><a class="cb-link" href="#/experiencias">Explorar</a></div>
          <div class="acc-list">${experiences.length?experiences.map(e=>{ const st=experienceStatus(e.status); return `<div class="acc-row">${accDate(e.start_date)}<span class="acc-row-main"><strong>${esc(e.title)}</strong><small>${esc([e.destination_title,e.center_name||e.provider_name,e.end_date?'hasta '+fmtDate(e.end_date):''].filter(Boolean).join(' · '))}</small></span><span class="acc-row-tags"><span class="status ${st[1]}">${esc(st[0])}</span></span></div>`; }).join(''):'<p class="acc-empty">Las solicitudes de viajes y cruceros de buceo aparecerán aquí.</p>'}</div></section></div>
      <aside class="acc-col">
        <section class="acc-card acc-profile"><div class="acc-card-head"><h2>Tu ficha de buceador</h2><b>${comp.pct}%</b></div><div class="acc-bar"><i style="width:${comp.pct}%"></i></div>
          <p>${comp.pct===100?'Todo listo: los centros reciben tus datos al reservar y no tendrás que repetirlos.':'Complétala y los centros prepararán tu equipo y documentación antes de que llegues.'}</p>${comp.missing.length?`<ul class="acc-missing">${comp.missing.map(m=>`<li>${esc(m)}</li>`).join('')}</ul>`:''}<a class="btn ${comp.pct<100?'btn-primary':''}" href="#/cuenta">${comp.pct<100?'Completar mi ficha':'Revisar mi ficha'}</a></section>
        <section class="acc-card" id="acc-messages"><div class="acc-card-head"><h2>Avisos</h2>${d.unread_messages?`<span class="status warn">${d.unread_messages} sin leer</span>`:''}</div>
          <div class="acc-msgs">${messages.length?messages.slice(0,8).map(m=>`<article class="acc-msg ${m.read_at?'':'is-unread'}" data-message-id="${m.id}"><div><strong>${esc(m.subject)}</strong><p>${esc(m.body)}</p><small>${esc(m.sender_name||'WORLDIVES')} · ${fmtDate(m.created_at)}${m.booking_id?` · <a href="#/reserva?id=${m.booking_id}">Ver reserva</a>`:''}</small>${m.kind==='notice'&&(m.contact_phone||m.contact_email)?`<small class="acc-msg-contact">Para responder, contacta directamente: ${m.contact_phone?`<a href="tel:${esc(m.contact_phone)}">${esc(m.contact_phone)}</a>`:''}${m.contact_phone&&m.contact_email?' · ':''}${m.contact_email?`<a href="mailto:${esc(m.contact_email)}">${esc(m.contact_email)}</a>`:''}</small>`:''}</div>${m.read_at?'':`<button class="acc-mark mark-message" type="button" aria-label="Marcar como leído">${wdIcon('check',15)}</button>`}</article>`).join(''):'<p class="acc-empty">No tienes avisos. Si un centro necesita avisarte de algo sobre una reserva, lo verás aquí y por email.</p>'}</div><p class="acc-help">Los avisos no admiten respuesta por WORLDIVES: si necesitas contestar, usa el teléfono o el email del centro.</p></section>
        <section class="acc-card"><div class="acc-card-head"><h2>Documentación</h2><a class="cb-link" href="#/cuenta?docs=1">Gestionar</a></div>
          ${(me.documents||[]).length?(me.documents||[]).map(x=>{ const n=x.expires_at?daysUntil(x.expires_at):null; const cls=n!==null&&n<0?'bad':n!==null&&n<45?'warn':'good'; return `<div class="acc-doc"><span>${wdIcon('shield',16)}<span><strong>${esc(x.title)}</strong><small>${esc(x.document_type)}</small></span></span><span class="status ${cls}">${n===null?'Sin caducidad':n<0?'Caducado':n<45?`Caduca en ${n} días`:'Vigente'}</span></div>`; }).join(''):'<p class="acc-empty">Sube tu titulación y tu seguro para reservar más rápido.</p>'}</section>
      </aside></div>`));
    fillAccountLevel(); $$('[data-jump]').forEach(b=>b.onclick=()=>document.getElementById(b.dataset.jump)?.scrollIntoView({behavior:'smooth',block:'start'}));
    const LIM=6; const clip=()=>{ const list=$('#acc-bookings [data-list]:not([hidden])'); const rows=$$('.acc-row',list); rows.forEach((r,i)=>r.hidden=i>=LIM&&!list.dataset.all); const more=$('#acc-more'); more.hidden=rows.length<=LIM||!!list.dataset.all; more.textContent=`Ver las ${rows.length} reservas`; };
    $('#acc-more').onclick=()=>{ $('#acc-bookings [data-list]:not([hidden])').dataset.all='1'; clip(); }; clip();
    $$('.acc-seg button').forEach(b=>b.onclick=()=>{ $$('.acc-seg button').forEach(x=>x.classList.toggle('is-on',x===b)); $$('#acc-bookings [data-list]').forEach(l=>l.hidden=l.dataset.list!==b.dataset.seg); clip(); });
    $$('.mark-message').forEach(btn=>btn.onclick=async()=>{const id=+btn.closest('[data-message-id]').dataset.messageId;try{await postJSON('/api/messages/read',{id});const row=btn.closest('.acc-msg'); row.classList.remove('is-unread'); btn.remove();}catch(e){toast(e.message)}});
  }

  async function renderAccountPage(){
    const d=await api('/api/me'); if(!d.authenticated){ goLogin(); return; } state.me=d;
    const profile=d.profile||{}, meta=await loadMeta(), esc=escapeHtml, u=d.user;
    const certs=(meta.certifications||[]).filter(c=>!String(c.name).includes('CAVE')&&!String(c.name).includes('TEC')&&!String(c.name).includes('NITROX'));
    const comp=profileCompletion(profile,d.documents);
    const f=(id,label,value,attrs='')=>`<div class="field"><label for="${id}">${label}</label><input id="${id}" value="${esc(value??'')}" ${attrs}></div>`;
    setApp(accountShell('cuenta',{eyebrow:'MI CUENTA',title:'Tu ficha de buceador',lead:'Rellénala una vez: cada centro con el que reserves recibe tus datos, titulación y tallas para prepararlo todo antes de que llegues.'},`
      <div class="acc-grid"><div class="acc-col">
        <form id="profile-form" class="acc-form">
          <section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('user',18)} Datos personales</h2><span class="acc-pct">${comp.pct}% completa</span></div><div class="form-grid">
            ${f('p-fullname','Nombre y apellidos',u.fullname,'required maxlength="120" autocomplete="name"')}${f('p-phone','Teléfono',profile.phone,'type="tel" autocomplete="tel"')}
            ${f('p-country','País',profile.country,'autocomplete="country-name"')}${f('p-city','Ciudad',profile.city,'autocomplete="address-level2"')}
            <div class="field"><label for="p-dob">Fecha de nacimiento <span class="opt">(opcional)</span></label><input id="p-dob" type="date" value="${esc(profile.date_of_birth||'')}" aria-describedby="p-dob-help"><small id="p-dob-help">Algunos centros la necesitan para el seguro de la actividad y para comprobar la edad mínima de cada curso.</small></div>
            <div class="field"><label for="p-lang">Idioma preferido</label><select id="p-lang">${Object.entries(LANGS).map(([code,label])=>`<option value="${code}" ${profile.preferred_language===code||(!profile.preferred_language&&code==='es')?'selected':''}>${label}</option>`).join('')}</select></div></div></section>
          <section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('shield',18)} Titulación y seguridad</h2></div><div class="form-grid">
            <div class="field"><label for="p-cert">Nivel de certificación</label><select id="p-cert"><option value="">Selecciona tu nivel</option>${certs.map(c=>`<option value="${c.id}" ${String(c.id)===String(profile.certification_id||'')?'selected':''}>${esc(c.name)}</option>`).join('')}</select></div><div></div>
            ${f('p-emergency-name','Contacto de emergencia (opcional)',profile.emergency_contact_name,'placeholder="Nombre y apellidos"')}${f('p-emergency-phone','Teléfono de emergencia (opcional)',profile.emergency_contact_phone,'type="tel"')}
            <p class="acc-help full">El centro solo lo usará si te pasa algo durante la actividad. Lo verá únicamente un centro con el que reserves tú o con el que compartas tus datos.</p></div></section>
          <section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('alquiler_equipo',18)} Equipo y tallas</h2></div><div class="form-grid">
            <div class="field"><label for="p-equipment">¿Sueles alquilar equipo?</label><select id="p-equipment"><option value="0" ${!profile.equipment_required?'selected':''}>No, llevo el mío</option><option value="1" ${profile.equipment_required?'selected':''}>Sí, lo alquilo</option></select></div>
            <div class="field"><label for="p-suit-type">Tipo de traje</label><select id="p-suit-type"><option value="">Selecciona</option>${['Neopreno húmedo','Semiseco','Seco','Rashguard / lycra','Otro'].map(x=>`<option ${profile.suit_type===x?'selected':''}>${x}</option>`).join('')}</select></div>
            ${f('p-suit-size','Talla de traje',profile.suit_size,'placeholder="S, M, L, XL…"')}${f('p-boot-size','Talla de botas',profile.boot_size,'placeholder="EU 39, 42…"')}
            ${f('p-bcd-size','Talla de chaleco (BCD)',profile.bcd_size,'placeholder="S, M, L…"')}${f('p-fin-size','Talla de aletas',profile.fin_size)}
            ${f('p-mask-size','Máscara',profile.mask_size,'placeholder="Graduada, estándar…"')}${f('p-weight','Lastre habitual en kg (opcional)',profile.usual_weight_kg,'type="number" min="0" max="50" step="0.5" aria-describedby="p-weight-help"')}<small id="p-weight-help" class="acc-help">Es el lastre (los plomos) que sueles llevar, no tu peso corporal: así el centro te prepara el cinturón.</small>
            ${f('p-tank','Botella',profile.tank_preference,'placeholder="12 L, 15 L, aluminio…"')}${f('p-computer','Ordenador',profile.computer_preference)}
            <div class="field full"><label for="p-equipment-notes">Observaciones de equipo</label><textarea id="p-equipment-notes" rows="2">${esc(profile.equipment_notes||'')}</textarea></div>
            <div class="field full"><label for="p-notes">Notas para los centros</label><textarea id="p-notes" rows="2" placeholder="Alergias, experiencia reciente, preferencias…">${esc(profile.notes||'')}</textarea></div></div></section>
          <div class="acc-save"><span>Los cambios se aplican a tus próximas reservas.</span><button class="btn btn-primary" type="submit">Guardar mi ficha</button></div>
        </form></div>
      <aside class="acc-col">
        <section class="acc-card" id="acc-docs"><div class="acc-card-head"><h2>${wdIcon('receipt',18)} Documentación</h2></div><p class="acc-help">Titulación, seguro y otros documentos útiles. Solo los ve un centro con el que tú reserves o con el que compartas tus datos.</p><div class="notice warn" role="note"><strong>No subas certificados médicos.</strong> Son datos de salud: entrégalos directamente al centro de buceo.</div>
          <div class="checklist">${d.documents.map(doc=>docItem(doc)).join('')||'<p class="acc-empty">Todavía no has subido documentos.</p>'}</div>
          <details class="acc-upload" ${d.documents.length?'':'open'}><summary>${wdIcon('plus',15)} Subir documento</summary><form id="doc-form" enctype="multipart/form-data">
            <div class="field"><label for="doc-type">Tipo</label><select id="doc-type" name="document_type"><option>Titulación</option><option>Seguro</option><option>Documento de identidad</option><option>Documento adicional</option></select></div>
            <div class="field"><label for="doc-title">Título</label><input id="doc-title" name="title" placeholder="Seguro DAN 2026…" required></div>
            <div class="field"><label for="doc-exp">Caducidad</label><input id="doc-exp" name="expires_at" type="date"></div>
            <div class="field"><label for="doc-file">Archivo (PDF o imagen, máximo 10 MB)</label><input id="doc-file" name="file" type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" required></div>
            <button class="btn btn-primary" type="submit">Subir documento</button></form></details></section>
        ${d.center_links.length?`<section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('pin',18)} Mis centros</h2></div>${d.center_links.map(c=>`<a class="acc-doc" href="#/centro?id=${c.center_id}"><span><span><strong>${esc(c.center_name)}</strong><small>${esc([c.city,c.country].filter(Boolean).join(', '))}</small></span></span><small>${c.last_checkin?'Última visita '+fmtDate(c.last_checkin):''}</small></a>`).join('')}</section>`:''}
        <section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('lock',18)} Seguridad</h2></div>
          <form id="pw-form" class="acc-pw"><div class="field"><label for="pw-cur">Contraseña actual</label><input id="pw-cur" type="password" autocomplete="current-password" required></div><div class="field"><label for="pw-new">Nueva contraseña</label><input id="pw-new" type="password" autocomplete="new-password" minlength="10" required><small>Mínimo 10 caracteres. Se cerrarán tus otras sesiones.</small></div><button class="btn" type="submit">Cambiar contraseña</button></form>
          <button class="btn acc-logout" type="button" id="logout">Cerrar sesión</button></section>
        ${accountEmailCard(u)}${accountSharesCard()}${proRequestCard(u)}${accountSecurityCard(u)}
        ${marketingCard(u)}${accountPrivacyCard(u)}
        ${['admin','center','freelance'].includes(u.role)?`<section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('chart',18)} Gestión</h2></div><p class="acc-help">${u.role==='admin'?'Tu cuenta tiene acceso al panel de administración.':'Gestiona tus servicios, reservas y cobros.'}</p><a class="btn btn-primary" href="#/admin">Abrir el panel</a></section>`:''}
      </aside></div>`));
    bindAccountPrivacy(); fillAccountLevel(); if(location.hash.includes('docs=1')) setTimeout(()=>$('#acc-docs')?.scrollIntoView({behavior:'smooth'}),200);
    $('#profile-form').onsubmit=async e=>{e.preventDefault(); const btn=e.target.querySelector('[type=submit]'); btn.disabled=true;
      try{ const name=$('#p-fullname').value.trim(); if(name&&name!==u.fullname){ await postJSON('/api/account/identity',{fullname:name}); }
        await postJSON('/api/account/profile',{phone:$('#p-phone').value,country:$('#p-country').value,city:$('#p-city').value,preferred_language:$('#p-lang').value,certification_id:$('#p-cert').value||null,notes:$('#p-notes').value,date_of_birth:$('#p-dob').value,emergency_contact_name:$('#p-emergency-name').value,emergency_contact_phone:$('#p-emergency-phone').value,equipment_required:$('#p-equipment').value==='1',suit_type:$('#p-suit-type').value,suit_size:$('#p-suit-size').value,boot_size:$('#p-boot-size').value,bcd_size:$('#p-bcd-size').value,fin_size:$('#p-fin-size').value,mask_size:$('#p-mask-size').value,usual_weight_kg:$('#p-weight').value||null,tank_preference:$('#p-tank').value,computer_preference:$('#p-computer').value,equipment_notes:$('#p-equipment-notes').value});
        toast('Ficha guardada.'); await loadMe(); renderAccountPage(); }catch(err){ toast(err.message); btn.disabled=false; } };
    $('#doc-form').onsubmit=async e=>{e.preventDefault(); const file=$('#doc-file').files[0]; if(file&&file.size>10*1024*1024){ toast('El archivo pesa demasiado. Máximo 10 MB.'); return; } if(/m[eé]dic|salud/i.test($('#doc-title').value)){ toast('No subas certificados médicos a WORLDIVES: entrégalos directamente al centro de buceo.'); return; } try{await api('/api/account/documents',{method:'POST',body:new FormData(e.target)});toast('Documento subido.');renderAccountPage();}catch(err){toast(err.message)}};
    bindAccountExtras(d); bindMarketingCard();
    $$('[data-docdel]').forEach(b=>b.onclick=async()=>{ if(!confirm('¿Eliminar este documento?')) return; try{await postJSON('/api/account/documents/delete',{id:+b.dataset.docdel});toast('Documento eliminado.');renderAccountPage();}catch(err){toast(err.message)}});
    $('#pw-form').onsubmit=async e=>{e.preventDefault(); try{ await postJSON('/api/account/password',{current_password:$('#pw-cur').value,new_password:$('#pw-new').value}); toast('Contraseña cambiada.'); e.target.reset(); }catch(err){ toast(err.message); } };
    $('#logout').onclick=async()=>{await postJSON('/api/auth/logout',{});await loadMe();location.hash='#/';};
  }
  function docItem(doc){const expired=doc.expires_at && new Date(doc.expires_at)<new Date(); const days=doc.expires_at?Math.ceil((new Date(doc.expires_at)-Date.now())/86400000):null; const st=expired?'bad':days!==null&&days<45?'warn':'good'; const tx=expired?'Caducado':days!==null?`Caduca en ${days} días`:'Sin caducidad'; return `<div class="doc-card"><div><strong>${escapeHtml(doc.title)}</strong><div style="font-size:12px;color:var(--muted)">${escapeHtml(doc.document_type)} · ${escapeHtml(doc.original_name)}</div></div><div class="doc-actions"><span class="status ${st}">${tx}</span><a class="btn" href="/api/documents/file/${doc.id}" target="_blank" rel="noopener">Abrir</a><button class="btn" type="button" data-docdel="${doc.id}">Eliminar</button></div></div>`}

  // ---------------------------------------------------------------------------
  // Reserva tu inmersión (v50.27): actividad → fecha y hora → buceadores → equipo → extras, con resumen y precio siempre a la vista
  // ---------------------------------------------------------------------------
  const BK_EQUIP_ICONS={
    fins:'<path d="M8 3c-2 4-3 9-2 14l2 4h3l1-5 1 5h3l2-4c1-5 0-10-2-14z"/>',
    mask:'<path d="M3 9a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v3a3 3 0 0 1-3 3h-3l-2-2h-2l-2 2H6a3 3 0 0 1-3-3z"/>',
    wetsuit:'<path d="M9 3h6l1 4 3 2-1 6-2-1v7h-3l-1-6-1 6H8v-7l-2 1-1-6 3-2z"/>',
    regulator:'<circle cx="12" cy="12" r="5"/><path d="M12 7V3M7 12H3M17 12h4M12 17v4"/>',
    bcd:'<path d="M7 4h10l2 4v10l-3 2H8l-3-2V8z"/><path d="M9 4v16M15 4v16"/>',
    tank:'<rect x="8" y="6" width="8" height="15" rx="4"/><path d="M10 6V3h4v3M12 3h4"/>',
    computer:'<rect x="6" y="5" width="12" height="14" rx="3"/><path d="M9 10h6M9 14h4M6 9H3M6 15H3"/>',
    full_kit:'<path d="M4 8h16l-1 12H5z"/><path d="M9 8V5a3 3 0 0 1 6 0v3"/>'};
  const bkEquipIcon=code=>`<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${BK_EQUIP_ICONS[code]||BK_EQUIP_ICONS.full_kit}</svg>`;
  // What each booking mode means for the diver (v50.32).
  const bkModeText=(s,online)=>s.booking_mode==='payment'
    ?[s.mode_label||'Pago al reservar · confirmación inmediata','Pagas ahora con tarjeta y la reserva queda confirmada al momento, sin esperar al centro. Te guardamos las plazas unos minutos mientras pagas.']
    :[s.mode_label||'Bajo petición','No se cobra nada hasta que el centro acepte. '+(online?'Si acepta, te avisaremos para pagar online antes del plazo que te indiquemos.':'Si acepta, pagarás directamente en el centro el día de la actividad.')];

  async function renderBookingCenterPicker(){
    let centers=[]; try{ centers=(await api('/api/centers')).items||[]; }catch(err){ setApp(`<section class="page"><div class="empty"><h2>No se han podido cargar los centros</h2><p>${escapeHtml(err.message)}</p></div></section>`); return; }
    setApp(`<section class="bk-page bk-pick"><div class="bk-pick-head"><p class="eyebrow">Reservar</p><h1>¿Con qué centro quieres bucear?</h1><p class="lead">Busca por nombre o por ciudad. También puedes reservar desde la ficha de cualquier centro.</p>
      <label class="cd-field bk-pick-search">${wdIcon('search',18)}<span class="sr-only">Buscar centro</span><input id="bk-pick-q" type="search" autocomplete="off" placeholder="Centro, ciudad o país"></label></div><div class="bk-pick-grid" id="bk-pick-grid"></div></section>`);
    const draw=()=>{ const words=wdFold($('#bk-pick-q').value).trim().split(/\s+/).filter(Boolean); const list=centers.filter(c=>{ const t=wdFold([c.name,c.city,c.region,c.country].join(' ')); return words.every(w=>t.includes(w)); });
      $('#bk-pick-grid').innerHTML=list.slice(0,30).map(c=>`<a class="bk-pick-card" href="#/reservar?center=${c.id}">${centerLogoMarkup(c,'48px')}<span><strong>${escapeHtml(c.name)}</strong><small>${escapeHtml([c.city,c.country].filter(Boolean).join(', '))}</small></span><span class="bk-pick-go">→</span></a>`).join('')+(list.length>30?`<p class="bk-pick-more">${list.length-30} centros más: afina la búsqueda.</p>`:'')||'<div class="empty">No hay centros con ese nombre.</div>'; };
    let t; $('#bk-pick-q').oninput=()=>{ clearTimeout(t); t=setTimeout(draw,120); }; draw(); $('#bk-pick-q').focus();
  }

  async function renderBooking(params){
    const cid=Number(params.get('center')||0), providerId=Number(params.get('provider')||0);
    if(!cid&&!providerId) return renderBookingCenterPicker();
    const esc=escapeHtml;
    setApp(`<section class="bk-page"><div class="bk-loading">${wdIcon('calendar',22)} Preparando la reserva…</div></section>`);
    let root=$('.bk-page'); const alive=()=>document.body.contains(root);
    const none=Promise.resolve({items:[]});
    // A freelance professional without a centre (Fase 2.7) is booked like a centre without equipment or extras.
    const [cR,sR,eR,xR]=await Promise.allSettled(cid?[api('/api/centers/'+cid),api('/api/provider-services?provider_id=0&center_id='+cid),api('/api/center-equipment?center_id='+cid),api('/api/center-extras?center_id='+cid)]
      :[api('/api/providers/'+providerId).then(p=>({item:{id:0,name:p.fullname,city:'',country:'',logo_url:p.avatar_url||'',cover_url:'',freelance:true,online_booking:p.online_booking}})),api('/api/provider-services?provider_id='+providerId),none,none]);
    if(!alive()) return;
    if(cR.status!=='fulfilled'){ setApp(`<section class="page"><div class="empty"><h2>Centro no encontrado</h2><p>Puede que ya no esté publicado.</p><a class="btn btn-primary" href="#/reservar">Elegir otro centro</a></div></section>`); return; }
    const center=cR.value.item;
    if(center.online_booking===false){ // free listing (Fase 6.3): information request instead of booking, never «sin plazas»
      setApp(`<section class="page"><div class="empty"><h2>${esc(center.name)}</h2><p>Este centro todavía no tiene reserva online en WORLDIVES. Envíale una solicitud de información y te contestará directamente.</p><div class="form-actions" style="justify-content:center"><button type="button" class="btn btn-primary" id="bk-info">Solicitar información</button><a class="btn" href="${cid?`#/centro?id=${cid}`:`#/profesional?id=${providerId}`}">Volver</a></div></div></section>`);
      $('#bk-info').onclick=()=>openInfoRequest({center_id:cid||null,provider_user_id:cid?null:providerId,name:center.name}); return; }
    const services=(sR.status==='fulfilled'?sR.value.items||[]:[]).filter(s=>(cid?String(s.center_id)===String(cid):!s.center_id)&&s.service_type!=='alquiler_equipo');
    if(!cid&&services[0]) center.online_payments=!!services[0].payments_ready;
    const equipment=(eR.status==='fulfilled'?eR.value.items||[]:[]).filter(e=>e.price!=null&&e.price!=='');
    const extras=xR.status==='fulfilled'?xR.value.items||[]:[];
    const hasNitroxExtra=extras.some(x=>/nitrox/i.test(x.name));
    // Selection state (restored from a draft when the diver had to sign in first)
    const st={service:0,point:0,date:'',slot:0,pax:1,rent:false,qty:{},extras:new Set(),nitrox:false,guide:false,pickup:false,sizes:'',notes:'',guideNotes:''};
    try{ const dr=JSON.parse(sessionStorage.getItem('wd_booking_draft')||'null'); if(dr&&Number(dr.center)===cid){ Object.assign(st,dr.st,{extras:new Set(dr.st.extras||[])}); sessionStorage.removeItem('wd_booking_draft'); } }catch{}
    if(params.get('service')) st.service=Number(params.get('service'));
    if(params.get('slot')) st.slot=Number(params.get('slot'));
    if(!services.some(s=>s.id===st.service)) st.service=0;
    const bookable=services.filter(s=>(s.slots||[]).some(sl=>Number(sl.spots_available)>0));
    if(!st.service&&bookable.length===1) st.service=bookable[0].id;
    const svc=()=>services.find(s=>s.id===st.service);
    const allSlots=()=>(svc()?.slots||[]).filter(sl=>!st.point||(sl.points||[]).some(p=>Number(p.id)===st.point));
    const slotObj=()=>allSlots().find(sl=>sl.id===st.slot);
    const maxPax=()=>{ const s=svc(), sl=slotObj(); return Math.max(1,Math.min(sl?Number(sl.spots_available):99, s?.max_participants?Number(s.max_participants):99, 30)); };
    const cover=center.cover_url||media('hero:centros')||'';
    const place=[center.city,center.country].filter(Boolean).join(', ');
    setApp(`<section class="bk-page">
      <header class="bk-hero">${cover?`<img class="bk-hero-img" src="${esc(cover)}" alt="">`:''}<div class="bk-hero-in">
        <a class="bk-back" href="${cid?`#/centro?id=${cid}`:`#/profesional?id=${providerId}`}">← ${esc(center.name)}</a>
        <div class="bk-hero-id">${centerLogoMarkup(center,'64px')}<div><p class="eyebrow">Reserva tu inmersión</p><h1>${esc(center.name)}</h1><p class="bk-hero-meta">${place?`<span>${wdIcon('pin',15)}${esc(place)}</span>`:''}${Number(center.review_count)?`<span>★ ${Number(center.rating_average||0).toFixed(1)} · ${center.review_count} opiniones</span>`:''}${center.online_payments?'<span>'+wdIcon('card',15)+'Pago seguro online</span>':''}</p></div></div>
      </div></header>
      <div class="bk-layout">
        <div class="bk-main">
          <section class="bk-step" data-step="1"><header><span class="bk-num">1</span><div><h2>Elige la actividad</h2><p>Precio por persona.</p></div></header><div class="bk-services" id="bk-services"></div></section>
          <section class="bk-step" data-step="2"><header><span class="bk-num">2</span><div><h2>Fecha y hora</h2><p id="bk-date-hint">Elige primero la actividad.</p></div></header>
            <div class="bk-points" id="bk-points"></div><div class="bk-dates-wrap"><button type="button" class="bk-scroll" data-dir="-1" aria-label="Fechas anteriores">‹</button><div class="bk-dates" id="bk-dates"></div><button type="button" class="bk-scroll" data-dir="1" aria-label="Más fechas">›</button></div><div class="bk-times" id="bk-times"></div></section>
          <section class="bk-step" data-step="3"><header><span class="bk-num">3</span><div><h2>Buceadores</h2><p id="bk-pax-hint">¿Cuántas personas venís?</p></div></header>
            <div class="bk-pax"><button type="button" class="bk-pax-btn" data-d="-1" aria-label="Una persona menos">−</button><output id="bk-pax" aria-live="polite">1</output><button type="button" class="bk-pax-btn" data-d="1" aria-label="Una persona más">+</button><span id="bk-pax-label">persona</span></div></section>
          <section class="bk-step" data-step="4"><header><span class="bk-num">4</span><div><h2>Equipo</h2><p>${equipment.length?'Precio por unidad. Indica cuántas necesitáis de cada pieza.':'Este centro no alquila equipo por piezas: consulta con ellos si lo necesitas.'}</p></div></header>
            ${equipment.length?`<div class="bk-seg" role="radiogroup" aria-label="Equipo"><button type="button" data-rent="0" role="radio">Llevamos nuestro equipo</button><button type="button" data-rent="1" role="radio">Necesito alquilar</button></div>
            <div class="bk-equip" id="bk-equip">${equipment.map(e=>`<div class="bk-item" data-code="${esc(e.code)}"><span class="bk-item-icon">${bkEquipIcon(e.code)}</span><span class="bk-item-txt"><strong>${esc(e.label)}</strong><small>${wdMoney(e.price)} / unidad</small></span><span class="bk-qty"><button type="button" data-q="-1" aria-label="Quitar ${esc(e.label)}">−</button><output>0</output><button type="button" data-q="1" aria-label="Añadir ${esc(e.label)}">+</button></span></div>`).join('')}</div>
            <label class="bk-field bk-sizes" id="bk-sizes-wrap"><span>Tallas y medidas</span><input id="bk-sizes" maxlength="300" placeholder="Ej.: neopreno M y L · aletas 40 y 43 · 1,75 m / 70 kg"></label>`:''}
          </section>
          <section class="bk-step" data-step="5"><header><span class="bk-num">5</span><div><h2>Extras y peticiones</h2><p>Opcional.</p></div></header>
            ${extras.length?`<div class="bk-extras">${extras.map(x=>`<button type="button" class="bk-extra" data-id="${x.id}" aria-pressed="false"><span class="bk-check" aria-hidden="true"></span><span><strong>${esc(x.name)}</strong>${x.description?`<small>${esc(x.description)}</small>`:''}</span><em>${wdMoney(x.price)}<small>/ persona</small></em></button>`).join('')}</div>`:''}
            <div class="bk-toggles">${hasNitroxExtra?'':`<label class="bk-toggle"><input type="checkbox" id="bk-nitrox"><span></span>Quiero bucear con nitrox <small>El centro te indica el precio</small></label>`}<label class="bk-toggle"><input type="checkbox" id="bk-guide"><span></span>Necesito un guía o instructor dedicado</label><label class="bk-toggle"><input type="checkbox" id="bk-pickup"><span></span>Necesito recogida o traslado</label></div>
            <label class="bk-field" id="bk-guide-wrap" hidden><span>¿Qué necesitas del guía?</span><input id="bk-guide-notes" maxlength="500" placeholder="Idioma, nivel, fotografía, acompañamiento…"></label>
            <label class="bk-field"><span>Nota para el centro</span><textarea id="bk-notes" rows="2" maxlength="1500" placeholder="Nivel, número de inmersiones, alergias, hora de llegada…"></textarea></label>
          </section>
        </div>
        <aside class="bk-summary" id="bk-summary"></aside>
      </div>
      <div class="bk-bar" id="bk-bar"><div><small>Total</small><strong id="bk-bar-total">—</strong></div><button type="button" class="btn btn-primary bk-go" id="bk-bar-go">Continuar</button></div>
    </section>`);
    root=$('.bk-page');
    // ---- render pieces
    const drawServices=()=>{ $('#bk-services').innerHTML=services.map(s=>{ const free=(s.slots||[]).filter(sl=>Number(sl.spots_available)>0); const next=free[0]; const ok=free.length&&s.bookable!==false;
        return `<button type="button" class="bk-svc ${s.id===st.service?'is-on':''}" data-id="${s.id}" ${ok?'':'disabled'} aria-pressed="${s.id===st.service}" style="--c:${esc(s.color||'#0b7a89')}">
          <span class="bk-svc-icon">${wdIcon(s.service_type,22)}</span>
          <span class="bk-svc-txt"><strong>${esc(s.title)}</strong><small>${s.duration_minutes?esc(wdDuration(s.duration_minutes)):''}</small>${wdModeTag(s)}<small class="bk-svc-next">${s.bookable===false?'No admite reservas ahora mismo':next?`Próxima: ${esc(wdDay(next.slot_date))} · ${esc(next.slot_time)}`:'Sin salidas próximas'}</small></span>
          <span class="bk-svc-price"><strong>${wdMoney(s.price,s.currency)}</strong><small>por persona</small></span></button>`; }).join('')||`<div class="bk-empty">Este centro todavía no ha publicado actividades con reserva online.${center.phone?` Llámales al <a href="tel:${esc(String(center.phone).replace(/\s+/g,''))}">${esc(center.phone)}</a>.`:''}</div>`; };
    const drawPoints=()=>{ const used=new Map(); (svc()?.slots||[]).forEach(sl=>(sl.points||[]).forEach(p=>used.set(Number(p.id),p.name))); const box=$('#bk-points');
      if(used.size<2){ box.innerHTML=''; box.hidden=true; if(st.point&&!used.has(st.point)) st.point=0; return; }
      box.hidden=false; box.innerHTML=`<span class="bk-points-label">Punto:</span><button type="button" class="cd-chip" data-point="0" aria-pressed="${!st.point}">Todos</button>`+[...used].map(([id,n])=>`<button type="button" class="cd-chip" data-point="${id}" aria-pressed="${st.point===id}">${esc(n)}</button>`).join(''); };
    const drawDates=()=>{ const s=svc(); const strip=$('#bk-dates'), times=$('#bk-times');
      if(!s){ $('#bk-date-hint').textContent='Elige primero la actividad.'; strip.innerHTML=''; times.innerHTML=''; $('.bk-dates-wrap').hidden=true; return; }
      const byDate={}; allSlots().forEach(sl=>(byDate[sl.slot_date]??=[]).push(sl)); const dates=Object.keys(byDate).sort();
      if(!dates.length){ $('#bk-date-hint').textContent='No hay salidas próximas para esta selección.'; strip.innerHTML=''; times.innerHTML=''; $('.bk-dates-wrap').hidden=true; return; }
      $('.bk-dates-wrap').hidden=false;
      if(!byDate[st.date]){ const withFree=dates.find(d=>byDate[d].some(sl=>Number(sl.spots_available)>0)); const viaSlot=dates.find(d=>byDate[d].some(sl=>sl.id===st.slot)); st.date=viaSlot||withFree||dates[0]; }
      $('#bk-date-hint').textContent=`${dates.length} ${dates.length===1?'día con salida':'días con salida'}. Las plazas se actualizan al momento.`;
      strip.innerHTML=dates.map(d=>{ const dt=wdParseDate(d); const free=byDate[d].reduce((n,sl)=>n+Math.max(0,Number(sl.spots_available)),0);
        return `<button type="button" class="bk-date ${d===st.date?'is-on':''} ${free?'':'is-full'}" data-date="${d}" aria-pressed="${d===st.date}"><small>${esc(dt.toLocaleDateString(wdLocale(),{weekday:'short'}).replace('.',''))}</small><strong>${dt.getDate()}</strong><small>${esc(dt.toLocaleDateString(wdLocale(),{month:'short'}).replace('.',''))}</small><em>${free?(free<=3?`${free} ${free===1?'plaza':'plazas'}`:'Disponible'):'Completo'}</em></button>`; }).join('');
      const list=byDate[st.date]||[]; if(st.slot&&!list.some(sl=>sl.id===st.slot)) st.slot=0; if(!st.slot){ const f=list.filter(sl=>Number(sl.spots_available)>0); if(f.length===1) st.slot=f[0].id; }
      times.innerHTML=`<p class="bk-times-day">${esc(wdLongDay(st.date))}</p><div class="bk-times-grid">`+list.map(sl=>{ const n=Number(sl.spots_available), tot=Number(sl.spots_total||n), end=plEndTime(sl.slot_time,s.duration_minutes); const pct=tot?Math.round((tot-n)/tot*100):0;
        return `<button type="button" class="bk-time ${sl.id===st.slot?'is-on':''}" data-slot="${sl.id}" ${n<=0?'disabled':''} aria-pressed="${sl.id===st.slot}"><strong>${esc(sl.slot_time)}${end?`<small>–${end}</small>`:''}</strong><span>${esc((sl.points||[]).map(p=>p.name).join(' · ')||'Punto según condiciones del mar')}</span><span class="bk-time-occ"><i style="width:${pct}%"></i></span><em class="${n<=0?'':n<=3?'is-hot':''}">${n<=0?'Completa':n===1?'¡Última plaza!':n<=3?`Quedan ${n} plazas`:`${n} plazas libres`}</em></button>`; }).join('')+'</div>';
      const sc=strip.querySelector('.is-on'); if(sc) sc.scrollIntoView({block:'nearest',inline:'center'}); };
    const drawPax=()=>{ st.pax=Math.max(1,Math.min(maxPax(),st.pax)); $('#bk-pax').textContent=st.pax; $('#bk-pax-label').textContent=st.pax===1?'persona':'personas';
      const sl=slotObj(), s=svc(); $('#bk-pax-hint').textContent=sl?`Quedan ${sl.spots_available} plazas en esta salida${s?.max_participants?` · máximo ${s.max_participants} por reserva`:''}.`:'¿Cuántas personas venís?';
      $$('.bk-pax-btn').forEach(b=>b.disabled=(b.dataset.d==='-1'&&st.pax<=1)||(b.dataset.d==='1'&&st.pax>=maxPax()));
      Object.keys(st.qty).forEach(k=>{ if(st.qty[k]>st.pax) st.qty[k]=st.pax; }); };
    const drawEquip=()=>{ if(!equipment.length) return; $$('.bk-seg button').forEach(b=>{ const on=(b.dataset.rent==='1')===st.rent; b.setAttribute('aria-checked',String(on)); b.classList.toggle('is-on',on); });
      $('#bk-equip').hidden=!st.rent; $('#bk-sizes-wrap').hidden=!st.rent;
      $$('#bk-equip .bk-item').forEach(it=>{ const q=st.qty[it.dataset.code]||0; it.querySelector('output').textContent=q; it.classList.toggle('is-on',q>0); it.querySelector('[data-q="-1"]').disabled=q<=0; it.querySelector('[data-q="1"]').disabled=q>=st.pax; }); };
    const equipCodes=()=>st.rent?Object.entries(st.qty).filter(([,q])=>q>0).map(([c,q])=>`${c}:${q}`):[];
    let quote=null, qSeq=0, qTimer=0;
    const drawSummary=()=>{ const s=svc(), sl=slotObj(); const ready=!!(s&&sl);
      const lines=quote?.lines||[]; const total=quote?.total||0; const dep=Number(quote?.deposit||0);
      const online=!!(s?s.payments_ready:center.online_payments), paid=total>0, payMode=s?.booking_mode==='payment';
      const cta=!ready?(s?'Elige fecha y hora':'Elige una actividad'):s.bookable===false?'No disponible':!payMode?'Enviar solicitud':paid?(dep>0?`Reservar y pagar la señal: ${wdMoney(dep,quote?.currency)}`:`Reservar y pagar ${wdMoney(total,quote?.currency)}`):'Reservar';
      const policyText=s?.policy?.text||center.cancellation_text||'', policyNote=s?.policy?.note||center.cancellation_note||'';
      const modeTxt=s?bkModeText(s,online):null;
      const payPanel=!s||!paid?'':(payMode||online)?`<div class="pay-trust"><div class="pay-trust-head">${wdIcon('lock',16)}<strong>${payMode?'Pago 100 % seguro':'No se cobra nada hasta que el centro acepte'}</strong></div>
          <ul><li>${wdIcon('shield',14)}Cobro procesado por Stripe, con cifrado y verificación 3D Secure.</li><li>${wdIcon('card',14)}Tus datos de tarjeta nunca pasan por WORLDIVES ni por el centro.</li><li>${wdIcon('check',14)}${payMode?'Confirmación al momento, recibo y justificante PDF.':'Cuando el centro acepte, te avisamos para pagar online antes del plazo.'}</li></ul>
          <div class="pay-brands" aria-label="Tarjetas aceptadas"><span>VISA</span><span>Mastercard</span><span>AMEX</span><span>Apple Pay</span><span>Google Pay</span></div></div>`
        :`<div class="pay-trust is-desk"><div class="pay-trust-head">${wdIcon('wallet',16)}<strong>Pagas en el centro</strong></div><ul><li>${wdIcon('check',14)}No se te cobra nada ahora.</li><li>${wdIcon('card',14)}Abonas ${ready&&quote?wdMoney(total,quote.currency):'el importe'} directamente al centro el día de la actividad.</li></ul></div>`;
      $('#bk-summary').innerHTML=`<div class="bk-card">
        <div class="bk-card-head">${centerLogoMarkup(center,'40px')}<div><strong>${esc(center.name)}</strong><small>${esc(place)}</small></div></div>
        <dl class="bk-sum">
          <div><dt>Actividad</dt><dd>${s?esc(s.title):'<em>Sin elegir</em>'}</dd></div>
          <div><dt>Fecha</dt><dd>${sl?`${esc(wdLongDay(sl.slot_date))}<br><b>${esc(sl.slot_time)}${plEndTime(sl.slot_time,s.duration_minutes)?' – '+plEndTime(sl.slot_time,s.duration_minutes):''}</b>`:'<em>Sin elegir</em>'}</dd></div>
          ${sl&&(sl.points||[]).length?`<div><dt>Punto</dt><dd>${esc(sl.points.map(p=>p.name).join(' · '))}</dd></div>`:''}
          <div><dt>Buceadores</dt><dd>${st.pax}</dd></div>
        </dl>
        ${lines.length&&ready?`<table class="bk-lines">${lines.map(l=>`<tr><td>${esc(l.label)}<small>${l.qty} × ${wdMoney(l.unit,quote.currency)}</small></td><td>${wdMoney(l.total,quote.currency)}</td></tr>`).join('')}</table>`:''}
        <div class="bk-total"><span>Total</span><strong>${ready&&quote?wdMoney(total,quote.currency):'—'}</strong></div>
        ${ready&&dep>0&&online?`<div class="bk-deposit"><span>${payMode?'Señal que pagas ahora':'Señal online si el centro acepta'}</span><b>${wdMoney(dep,quote.currency)}</b><span>Resto a pagar en el centro</span><b>${wdMoney(quote.due_at_center,quote.currency)}</b></div>`:''}
        <button type="button" class="btn btn-primary bk-go" ${ready?'':'disabled'}>${esc(cta)}</button>
        ${modeTxt?`<p class="bk-mode"><b>${esc(modeTxt[0])}.</b> ${esc(modeTxt[1])}</p>`:''}${payPanel}
        ${policyText?`<div class="bk-policy">${wdIcon('calendar',15)}<p><b>Política de cancelación.</b> ${esc(policyText)}${policyNote?' '+esc(policyNote):''}</p></div>`:''}
        <div class="bk-legal"><p><b>Prestado por ${esc(center.legal_name||center.name)}${center.country?', '+esc(center.country):''}.</b> WORLDIVES DISCOVERY es la plataforma de reservas: no organiza ni presta la actividad.</p><p>Precio final fijado por el centro, impuestos incluidos.</p><p>Las actividades de ocio con fecha concreta no tienen derecho de desistimiento de 14 días (art. 103.l del TRLGDCU); se aplica la política de cancelación del centro.</p><p>Al reservar aceptas las <a href="#/legal/condiciones-reserva" target="_blank" rel="noopener">condiciones de reserva</a> y las <a href="#/legal/condiciones-buceadores" target="_blank" rel="noopener">condiciones de uso</a>.</p></div>
        <ul class="bk-trust"><li>${wdIcon('users',15)}Tus datos y tu certificación llegan al centro con la reserva.</li>${center.phone?`<li>${wdIcon('clock',15)}¿Dudas? <a href="tel:${esc(String(center.phone).replace(/\s+/g,''))}">${esc(center.phone)}</a></li>`:''}</ul>
      </div>`;
      $('#bk-bar-total').textContent=ready&&quote?wdMoney(total,quote.currency):'—'; const bb=$('#bk-bar-go'); bb.textContent=ready?cta:'Continuar'; bb.disabled=!!(ready&&s.bookable===false);
      $$('.bk-step').forEach(x=>{ const n=+x.dataset.step; x.classList.toggle('is-done',(n===1&&!!s)||(n===2&&!!sl)||(n===3&&!!sl)); x.classList.toggle('is-locked',n>1&&!s); });
      const go=$('#bk-summary .bk-go'); go.onclick=submit; if(s&&s.bookable===false) go.disabled=true; };
    const refreshQuote=()=>{ clearTimeout(qTimer); qTimer=setTimeout(async()=>{ const s=svc(); if(!s){ quote=null; drawSummary(); return; } const my=++qSeq;
      const q=new URLSearchParams({center_id:String(cid||0),service_id:String(s.id),slot_id:String(st.slot||0),participants:String(st.pax),extras:[...st.extras].join(','),equipment:equipCodes().join(',')});
      try{ const r=await api('/api/booking-quote?'+q); if(my!==qSeq||!alive()) return; quote=r; }catch{ quote=null; } drawSummary(); },120); };
    const redraw=()=>{ drawServices(); drawPoints(); drawDates(); drawPax(); drawEquip(); drawSummary(); refreshQuote(); };
    // ---- events
    root.addEventListener('click',e=>{ const t=e.target.closest('button'); if(!t||!root.contains(t)) return;
      if(t.matches('.bk-svc')){ st.service=+t.dataset.id; st.slot=0; st.date=''; st.point=0; redraw(); if(window.innerWidth<900) $('[data-step="2"]').scrollIntoView({behavior:'smooth',block:'start'}); return; }
      if(t.matches('#bk-points .cd-chip')){ st.point=+t.dataset.point; st.slot=0; st.date=''; redraw(); return; }
      if(t.matches('.bk-date')){ st.date=t.dataset.date; st.slot=0; redraw(); return; }
      if(t.matches('.bk-time')){ st.slot=+t.dataset.slot; redraw(); return; }
      if(t.matches('.bk-scroll')){ $('#bk-dates').scrollBy({left:Number(t.dataset.dir)*320,behavior:'smooth'}); return; }
      if(t.matches('.bk-pax-btn')){ st.pax+=Number(t.dataset.d); drawPax(); drawEquip(); drawSummary(); refreshQuote(); return; }
      if(t.matches('.bk-seg button')){ st.rent=t.dataset.rent==='1'; drawEquip(); refreshQuote(); return; }
      if(t.closest('.bk-qty')){ const code=t.closest('.bk-item').dataset.code; st.qty[code]=Math.max(0,Math.min(st.pax,(st.qty[code]||0)+Number(t.dataset.q))); drawEquip(); refreshQuote(); return; }
      if(t.matches('.bk-extra')){ const id=+t.dataset.id; st.extras.has(id)?st.extras.delete(id):st.extras.add(id); t.setAttribute('aria-pressed',String(st.extras.has(id))); refreshQuote(); return; }
      if(t.matches('#bk-bar-go')){ if(slotObj()) submit(); else $(`[data-step="${svc()?2:1}"]`).scrollIntoView({behavior:'smooth',block:'start'}); return; }
    });
    const syncInputs=()=>{ st.nitrox=!!$('#bk-nitrox')?.checked; st.guide=$('#bk-guide').checked; st.pickup=$('#bk-pickup').checked; st.notes=$('#bk-notes').value; st.sizes=$('#bk-sizes')?.value||''; st.guideNotes=$('#bk-guide-notes').value; $('#bk-guide-wrap').hidden=!st.guide; };
    root.addEventListener('input',syncInputs); root.addEventListener('change',syncInputs);
    // restore draft inputs
    if($('#bk-nitrox')) $('#bk-nitrox').checked=st.nitrox; $('#bk-guide').checked=st.guide; $('#bk-pickup').checked=st.pickup; $('#bk-notes').value=st.notes; if($('#bk-sizes')) $('#bk-sizes').value=st.sizes; $('#bk-guide-notes').value=st.guideNotes; $('#bk-guide-wrap').hidden=!st.guide;
    $$('.bk-extra').forEach(b=>b.setAttribute('aria-pressed',String(st.extras.has(+b.dataset.id))));
    let sending=false;
    async function submit(){ if(sending) return; const s=svc(), sl=slotObj(); if(!s||!sl){ toast(s?'Elige la fecha y la hora.':'Elige una actividad.'); return; }
      syncInputs();
      if(!state.me){ try{ sessionStorage.setItem('wd_booking_draft',JSON.stringify({center:cid,st:{...st,extras:[...st.extras]}})); }catch{} toast('Inicia sesión o crea tu cuenta para terminar la reserva. Guardamos lo que has elegido.'); location.hash='#/login?next='+encodeURIComponent(`#/reservar?center=${cid}&service=${s.id}&slot=${sl.id}`); return; }
      if(st.pax>Number(sl.spots_available)){ toast(`Solo quedan ${sl.spots_available} plazas en esta salida.`); return; }
      const codes=equipCodes(); const items=st.rent?equipment.filter(e=>st.qty[e.code]>0).map(e=>`${e.label} ×${st.qty[e.code]}`).join(', '):'';
      const point=(sl.points||[]).find(p=>Number(p.id)===st.point)||(sl.points||[])[0]||null;
      sending=true; $$('.bk-go').forEach(b=>{ b.disabled=true; b.dataset.label=b.textContent; b.textContent='Reservando…'; });
      try{ const created=await postJSON('/api/bookings',{center_id:cid||null,service_id:s.id,slot_id:sl.id,dive_point_id:point?Number(point.id):null,dive_point_name:point?.name||'',booking_date:sl.slot_date,booking_time:sl.slot_time,participants:st.pax,
          needs_equipment:codes.length>0,equipment_items:items,equipment_codes:codes,equipment_notes:st.sizes,extra_ids:[...st.extras],needs_guide:st.guide,guide_notes:st.guideNotes,nitrox:st.nitrox,pickup:st.pickup,notes:st.notes});
        if(created.checkout_url){ $$('.bk-go').forEach(b=>{ b.textContent='Abriendo el pago seguro…'; }); location.href=created.checkout_url; return; }
        toast(created.status==='confirmed'?'¡Reserva confirmada!':'Solicitud enviada. No se cobra nada hasta que el centro acepte.'); location.hash='#/reserva?id='+created.id;
      }catch(err){ toast(err.message); sending=false; $$('.bk-go').forEach(b=>{ b.disabled=false; if(b.dataset.label) b.textContent=b.dataset.label; }); }
    }
    redraw();
    if(st.slot&&slotObj()) setTimeout(()=>$('.bk-time.is-on')?.scrollIntoView({block:'center',behavior:'smooth'}),200);
  }

  // Payment card shown on the diver's booking: paid receipt, secure pay button, or «pay at the centre».
  const CARD_BRANDS={visa:'Visa',mastercard:'Mastercard',amex:'American Express',discover:'Discover',jcb:'JCB',unionpay:'UnionPay',diners:'Diners'};
  function bookingPaymentCard(b,pay,{own,canPay,cancelled}){
    const esc=escapeHtml, amount=wdMoney(b.price,b.currency), price=Number(b.price||0);
    if(!(price>0)) return '';
    const dead=['cancelled','rejected','expired'].includes(b.status);
    const paid=Number(b.paid_online||0), refunded=Number(b.refunded_online||0);
    const refundsList=(b.refunds||[]).length?`<ul class="pay-refunds">${b.refunds.map(r=>`<li>${wdIcon('receipt',13)} ${esc(fmtDate(r.created_at))} · ${esc(wdMoney(r.amount,r.currency))} ${r.status==='pending'?'(en curso)':r.status==='failed'?'(fallida)':''}${r.note?' · '+esc(r.note):''}</li>`).join('')}</ul>`:'';
    const pdf=`<a class="btn" href="/api/bookings/${b.id}/receipt.pdf" target="_blank" rel="noopener">${wdIcon('download',15)} Justificante PDF</a>`;
    if(refunded>0&&refunded>=paid-0.005){
      return `<section class="pay-card is-refunded"><div class="pay-card-icon">${wdIcon('receipt',22)}</div><div class="pay-card-main"><p class="eyebrow">PAGO DEVUELTO</p><h3>Devuelto · ${esc(wdMoney(refunded,b.currency))}</h3>
        <p>${own?'El importe se ha devuelto a la misma tarjeta. Según tu banco, lo verás en 5–10 días hábiles.':'Todo lo pagado online se ha devuelto al cliente.'}</p>${refundsList}<div class="page-actions">${pdf}</div></div></section>`;
    }
    if(['proposed','failed'].includes(b.refund_status)&&Number(b.refund_proposed||0)>0){
      return `<section class="pay-card is-refunded"><div class="pay-card-icon">${wdIcon('clock',22)}</div><div class="pay-card-main"><p class="eyebrow">DEVOLUCIÓN PENDIENTE</p><h3>${esc(wdMoney(b.refund_proposed,b.currency))}</h3>
        <p>${own?`Según la política de cancelación te corresponde esta devolución. Se la hemos pedido a ${esc(b.center_name)}, que la hace desde su cuenta; te avisaremos por email cuando esté hecha.`:'El cliente canceló. Según tu política de cancelación le corresponde esta devolución: hazla con el botón «Devolver».'}</p>${refundsList}</div></section>`;
    }
    if(['paid','deposit_paid','partially_refunded'].includes(b.payment_status)&&paid>0){
      const when=pay?.paid_at?new Date(pay.paid_at).toLocaleString(wdLocale(),{dateStyle:'medium',timeStyle:'short'}):'';
      const card=pay?.card_last4?`${CARD_BRANDS[pay.card_brand]||esc(pay.card_brand||'Tarjeta')} ···· ${esc(pay.card_last4)}`:(b.payment_method?esc(b.payment_method):'Registrado por el centro');
      const due=Number(b.amount_due||0);
      return `<section class="pay-card is-paid"><div class="pay-card-icon">${wdIcon('check',22)}</div><div class="pay-card-main"><p class="eyebrow">PAGO</p><h3>${b.payment_status==='deposit_paid'||(Number(b.deposit_amount||0)>0&&due>0.005)?'Señal pagada':'Pagado'} · ${esc(wdMoney(paid,b.currency))}</h3>
        <dl class="pay-facts">${when?`<div><dt>Fecha</dt><dd>${esc(when)}</dd></div>`:''}<div><dt>Método</dt><dd>${card}</dd></div>${pay?.reference?`<div><dt>Ref. del pago</dt><dd>${esc(pay.reference)}</dd></div>`:''}${due>0.005&&!dead?`<div><dt>Resto en el centro</dt><dd>${esc(wdMoney(due,b.currency))}</dd></div>`:''}${refunded>0?`<div><dt>Devuelto</dt><dd>${esc(wdMoney(refunded,b.currency))}</dd></div>`:''}</dl>
        ${refundsList}<div class="page-actions">${pay?.receipt_url?`<a class="btn" href="${esc(pay.receipt_url)}" target="_blank" rel="noopener">${wdIcon('receipt',15)} Recibo de Stripe</a>`:''}${pdf}</div></div></section>`;
    }
    if(b.payment_status==='paid'){
      return `<section class="pay-card is-paid"><div class="pay-card-icon">${wdIcon('check',22)}</div><div class="pay-card-main"><p class="eyebrow">PAGO</p><h3>Pagado · ${esc(amount)}</h3><dl class="pay-facts"><div><dt>Método</dt><dd>${esc(b.payment_method||'Registrado por el centro')}</dd></div></dl><div class="page-actions">${pdf}</div></div></section>`;
    }
    if(dead) return '';
    const payNow=Number(b.pay_now||b.price||0), deposit=payNow>0&&payNow<price;
    if(canPay) return `<section class="pay-card is-due">${cancelled?`<div class="notice warning pay-cancelled"><strong>No se ha completado el pago.</strong> No se te ha cobrado nada.${b.status==='accepted_pending_payment'?` Puedes pagar hasta el ${escapeHtml(wdDeadline(b.payment_deadline))}.`:''}</div>`:''}<div class="pay-card-icon">${wdIcon('lock',22)}</div><div class="pay-card-main"><p class="eyebrow">PAGO PENDIENTE</p><h3>${esc(wdMoney(payNow,b.currency))}${deposit?` <small>señal de ${esc(amount)}</small>`:''}</h3>
        <p>${b.status==='accepted_pending_payment'?`El centro ha aceptado tu solicitud y te guarda la plaza. Paga antes del ${escapeHtml(wdDeadline(b.payment_deadline))} para confirmarla.`:'Completa el pago para confirmar tu plaza al momento.'}${deposit?` El resto, ${esc(wdMoney(price-payNow,b.currency))}, se paga en el centro.`:''}</p>
        <button class="btn btn-primary" type="button" id="booking-pay-now">${deposit?'Pagar la señal de forma segura':'Pagar ahora de forma segura'}</button>
        <ul class="pay-points"><li>${wdIcon('shield',14)}Stripe procesa el cobro con cifrado y 3D Secure</li><li>${wdIcon('card',14)}Pagas directamente al centro: ni WORLDIVES ni el centro ven tu tarjeta</li><li>${wdIcon('check',14)}Confirmación inmediata y justificante PDF</li></ul></div></section>`;
    if(b.payment_status==='pending') return `<section class="pay-card is-due"><div class="pay-card-icon">${wdIcon('clock',22)}</div><div class="pay-card-main"><p class="eyebrow">PAGO EN CURSO</p><h3>${esc(wdMoney(payNow,b.currency))}</h3><p>Estamos esperando la confirmación del banco. Si has cerrado la ventana de pago, vuelve a intentarlo en unos minutos.</p></div></section>`;
    if(b.payment_status==='review') return `<section class="pay-card is-due"><div class="pay-card-icon">${wdIcon('alert',22)}</div><div class="pay-card-main"><p class="eyebrow">PAGO EN REVISIÓN</p><h3>${esc(amount)}</h3><p>Hemos recibido un pago que no coincide con el importe de la reserva. Lo estamos revisando y te escribiremos; no hace falta que pagues otra vez.</p></div></section>`;
    if(own&&['requested','pending'].includes(b.status)) return `<section class="pay-card"><div class="pay-card-icon">${wdIcon('clock',22)}</div><div class="pay-card-main"><p class="eyebrow">PAGO</p><h3>${esc(amount)}</h3><p>No se cobra nada hasta que el centro confirme la plaza.${b.payment_status==='required'?` Te avisaremos para pagar online${deposit?` la señal (${esc(wdMoney(payNow,b.currency))})`:''}.`:''}</p></div></section>`;
    return `<section class="pay-card"><div class="pay-card-icon">${wdIcon('wallet',22)}</div><div class="pay-card-main"><p class="eyebrow">PAGO EN EL CENTRO</p><h3>${esc(amount)}</h3><p>${own?'Pagas directamente al centro el día de la actividad (efectivo o tarjeta, según el centro).':'El buceador paga en el centro.'}</p></div></section>`;
  }
  // Provider: refund part or all of what the diver paid online (Fase 2.4). Partial refunds never cancel the booking.
  async function openRefundModal(id,after){
    let b; try{ b=(await api('/api/bookings/'+id)).booking; }catch(e){ toast(e.message); return; }
    const max=Number(b.refundable||0); if(!(max>0)){ toast('Esta reserva no tiene pagos online por devolver.'); return; }
    const sug=Number(b.refund_proposed||0)>0&&['proposed','failed'].includes(b.refund_status)?Math.min(max,Number(b.refund_proposed)):max;
    const {el,close}=wdOpenModal({id:'refund-modal',title:'Devolver dinero al cliente',subtitle:`Se devuelve desde tu cuenta de Stripe a la misma tarjeta. Puedes devolver hasta ${wdMoney(max,b.currency)}.`,
      body:`<div class="field"><label for="rf-amount">Importe a devolver (${escapeHtml(b.currency||'EUR')})</label><input id="rf-amount" type="number" min="0.01" step="0.01" max="${max}" value="${sug.toFixed(2)}"></div>
        <p class="acc-help">${escapeHtml(b.cancellation_text||'')}</p><p class="acc-help">Una devolución parcial no cancela la reserva. Para cancelarla usa «Cancelar reserva».</p>
        <div class="field"><label for="rf-note">Nota para el cliente (opcional)</label><input id="rf-note" maxlength="300" placeholder="Ej.: devolución por cancelación con 24 h de antelación"></div>`,
      footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="rf-ok">Devolver</button>'});
    $('#rf-ok',el).onclick=async e=>{ const btn=e.currentTarget; btn.disabled=true; try{ await postJSON(`/api/bookings/${id}/refund`,{amount:$('#rf-amount',el).value,note:$('#rf-note',el).value}); close(); toast('Devolución hecha. El cliente recibe un email.'); after&&after(); }catch(err){ toast(err.message); btn.disabled=false; } };
  }
  // Provider cancels a booking: everything paid online is refunded unless it sets a smaller amount.
  async function openProviderCancelModal(id,after){
    let b; try{ b=(await api('/api/bookings/'+id)).booking; }catch(e){ toast(e.message); return; }
    const max=Number(b.refundable||0);
    const {el,close}=wdOpenModal({id:'center-cancel-modal',title:'Cancelar la reserva',subtitle:'El cliente recibe un email con el motivo. Las plazas vuelven a quedar libres.',
      body:`${max>0?`<div class="cx-summary">${wdIcon('receipt',20)}<p>Si cancelas tú, al cliente le corresponde la devolución de todo lo pagado: <b>${wdMoney(max,b.currency)}</b>. Se hace desde tu cuenta de Stripe.</p></div>
        <div class="field"><label for="cc-amount">Importe a devolver (${escapeHtml(b.currency||'EUR')})</label><input id="cc-amount" type="number" min="0" step="0.01" max="${max}" value="${max.toFixed(2)}"></div>`:''}
        <div class="field"><label for="cc-reason">Motivo</label><input id="cc-reason" maxlength="300" placeholder="Ej.: previsión de mal estado del mar"></div>`,
      footer:'<button type="button" class="btn" data-modal-close>No cancelar</button><button type="button" class="btn danger" id="cc-ok">Cancelar la reserva</button>'});
    $('#cc-ok',el).onclick=async e=>{ const btn=e.currentTarget; btn.disabled=true; try{ const r=await postJSON(`/api/bookings/${id}/status`,{status:'cancelled',reason:$('#cc-reason',el).value,refund_amount:$('#cc-amount',el)?.value}); close(); toast(r.refund==='refunded'?'Reserva cancelada y dinero devuelto.':r.refund==='refund_pending'?'Reserva cancelada. La devolución no se pudo hacer: revísala en Cobros y pagos.':'Reserva cancelada.'); after&&after(); }catch(err){ toast(err.message); btn.disabled=false; } };
  }
  function bookingReviewPrompt(b){
    const ok=!['cancelled','rejected'].includes(b.status)&&(b.payment_status==='paid'||['confirmed','completed'].includes(b.status));
    return ok?`<div class="review-cta">${wdIcon('star',18)}<div><strong>¿Qué tal con ${escapeHtml(b.center_name)}?</strong><small>Tu opinión ayuda a otros buceadores y aparece como reseña verificada.</small></div><a class="btn" href="#/centro?id=${b.center_id}&resena=1">Escribir reseña</a></div>`:'';
  }

  // ---------------------------------------------------------------------------
  // Promociones con QR (v50.29)
  // ---------------------------------------------------------------------------
  const PROMO_STATE={active:['Activa','good'],used:['Utilizada','muted'],expired:['Caducada','bad'],revoked:['Anulada','bad'],ended:['Finalizada','muted'],upcoming:['Próximamente','warn']};
  const promoDate=s=>s?wdParseDate(s).toLocaleDateString(wdLocale(),{day:'numeric',month:'short',year:'numeric'}):'';
  const promoCode=c=>String(c||'').replace(/(.{5})(?=.)/,'$1 ');
  const promoPill=st=>{ const x=PROMO_STATE[st]||[st,'muted']; return `<span class="pr-pill is-${x[1]}">${escapeHtml(x[0])}</span>`; };
  function promoTicket(p,{big=false,link=true}={}){
    const esc=escapeHtml, live=p.state==='active';
    return `<article class="pr-ticket ${live?'':'is-off'} ${big?'is-big':''}">${link?`<a class="pr-ticket-link" href="#/promo/${esc(p.code)}" aria-label="Ver promoción ${esc(p.title)}"></a>`:''}
      <div class="pr-ticket-main"><div class="pr-ticket-top"><span class="pr-issuer">${wdIcon('gift',14)} ${esc(p.issuer?.name||'')}</span>${promoPill(p.state)}</div>
        <h3>${esc(p.title)}</h3>${p.value_text?`<p class="pr-value">${esc(p.value_text)}</p>`:''}
        <dl class="pr-meta"><div><dt>Válida hasta</dt><dd>${esc(promoDate(p.valid_until))}</dd></div><div><dt>Usos</dt><dd>${Number(p.uses||0)} de ${Number(p.max_uses||1)}</dd></div>${(p.centers||[]).length>1?`<div><dt>Centros</dt><dd>${p.centers.length}</dd></div>`:''}</dl></div>
      <div class="pr-ticket-qr">${live||big?`<img src="/api/promo/${esc(p.code)}/qr.svg" alt="QR de la promoción" loading="lazy">`:`<span class="pr-qr-off">${wdIcon('qr',30)}</span>`}<code>${esc(promoCode(p.code))}</code></div></article>`;
  }
  function promoValidation(p){
    const esc=escapeHtml, ok=p.state==='active';
    return `<section class="pr-check ${ok?'is-ok':'is-bad'}"><div class="pr-check-head"><div class="pr-check-icon">${wdIcon(ok?'check':'alert',30)}</div><div><p class="eyebrow">${ok?'CÓDIGO VÁLIDO':'NO SE PUEDE USAR'}</p><h2>${ok?'Promoción activa':esc(p.state_text)}</h2>
      ${p.viewer==='center_other'?'<p>Esta promoción no está activa en tu centro.</p>':''}</div></div>
      <div class="pr-check-body"><h3>${esc(p.title)}</h3>${p.value_text?`<p class="pr-value">${esc(p.value_text)}</p>`:''}${p.description?`<p>${esc(p.description)}</p>`:''}
        <dl class="pr-facts"><div><dt>Titular</dt><dd>${esc(p.holder||'—')}${p.holder_email&&!String(p.holder_email).endsWith('.local')?`<small>${esc(p.holder_email)}</small>`:''}</dd></div><div><dt>Código</dt><dd><code>${esc(promoCode(p.code))}</code></dd></div>
          <div><dt>Válida</dt><dd>${p.valid_from?`del ${esc(promoDate(p.valid_from))} `:''}hasta el ${esc(promoDate(p.valid_until))}</dd></div><div><dt>Usos</dt><dd>${Number(p.uses||0)} de ${Number(p.max_uses||1)}</dd></div>
          <div class="is-wide"><dt>Válida en</dt><dd>${(p.centers||[]).map(c=>`<span class="pr-center">${esc(c.name)}${c.city?` · ${esc(c.city)}`:''}</span>`).join('')}</dd></div></dl>
        ${p.conditions?`<p class="pr-cond"><b>Condiciones:</b> ${esc(p.conditions)}</p>`:''}
        ${p.can_redeem?`<form class="pr-redeem" id="pr-redeem"><input id="pr-note" maxlength="200" placeholder="Nota interna (opcional): curso, material entregado…"><button class="btn btn-primary" type="submit">${wdIcon('check',16)} Canjear ahora</button></form>`:''}
        ${(p.redemptions||[]).length?`<div class="pr-history"><strong>Historial de usos</strong>${p.redemptions.map(r=>`<div><span>${esc(new Date(r.created_at).toLocaleString(wdLocale(),{dateStyle:'medium',timeStyle:'short'}))}</span><span>${esc(r.center_name)}${r.note?` · ${esc(r.note)}`:''}</span></div>`).join('')}</div>`:''}
      </div></section>`;
  }
  function bindPromoRedeem(p,after){
    $('#pr-redeem')?.addEventListener('submit',async e=>{ e.preventDefault(); const btn=e.target.querySelector('button'); btn.disabled=true;
      try{ const r=await postJSON(`/api/promo/${encodeURIComponent(p.code)}/redeem`,{note:$('#pr-note').value}); toast('Promoción canjeada.'); after(r.promo); }catch(err){ toast(err.message); btn.disabled=false; } });
  }
  async function renderPromoPage(code){
    code=String(code||'').toUpperCase().replace(/[^A-Z0-9]/g,'');
    let p; try{ p=await api('/api/promo/'+encodeURIComponent(code)); }catch(err){ setApp(`<section class="page pay-ok-page"><div class="pay-ok-card is-warn"><div class="pay-ok-icon is-warn">${wdIcon('alert',30)}</div><h1>Código no encontrado</h1><p>${escapeHtml(err.message)}</p><div class="page-actions"><a class="btn btn-primary" href="#/">Ir al inicio</a></div></div></section>`); return; }
    const draw=p=>{
      if(p.viewer==='holder') setApp(`<section class="page pr-page"><div class="breadcrumb"><a href="#/recompensas">Recompensas</a> / Mi promoción</div><div class="pr-holder"><p class="eyebrow">TU PROMOCIÓN</p><h1>${escapeHtml(p.title)}</h1><p class="lead">Enseña este QR en ${(p.centers||[]).length>1?'cualquiera de los centros de la promoción':escapeHtml(p.issuer.name)}. El centro lo escanea y lo valida al momento.</p>${promoTicket(p,{big:true,link:false})}
          ${p.description?`<p>${escapeHtml(p.description)}</p>`:''}${p.conditions?`<p class="pr-cond"><b>Condiciones:</b> ${escapeHtml(p.conditions)}</p>`:''}
          <div class="pr-where"><strong>Válida en</strong>${(p.centers||[]).map(c=>`<a class="pr-center" href="#/centro?id=${c.id}">${escapeHtml(c.name)}${c.city?` · ${escapeHtml(c.city)}`:''}</a>`).join('')}</div></div></section>`);
      else if(p.viewer==='public') setApp(`<section class="page pr-page"><div class="pr-public">${promoValidation(p)}<p class="pr-note">${state.me?'Este código pertenece a otra persona. Solo su titular y los centros de la promoción ven los detalles.':'¿Eres el centro? <a href="#/login?next='+encodeURIComponent('#/promo/'+p.code)+'">Inicia sesión</a> para validarlo y canjearlo.'}</p></div></section>`);
      else { setApp(`<section class="page pr-page"><div class="breadcrumb"><a href="#/admin?tab=qr">Promociones</a> / Validar código</div>${promoValidation(p)}</section>`); bindPromoRedeem(p,draw); }
    };
    draw(p);
  }
  function renderPromoChecker(mountId){
    const mount=document.getElementById(mountId);
    mount.innerHTML=`<section class="cb-module pr-checker"><div class="cb-module-head"><div><p class="eyebrow">VALIDAR</p><h2>Comprobar un código promocional</h2><p>Escanea el QR del cliente con la cámara del móvil (se abre esta misma comprobación) o escribe aquí el código de 10 caracteres.</p></div></div>
      <form id="pr-check-form" class="pr-check-form"><input id="pr-check-code" autocomplete="off" autocapitalize="characters" maxlength="80" placeholder="Ej. AUQ8R 49G4G o el enlace del QR" aria-label="Código promocional"><button class="btn btn-primary" type="submit">Comprobar</button></form><div id="pr-check-out"></div></section>`;
    $('#pr-check-form').onsubmit=async e=>{ e.preventDefault(); const raw=$('#pr-check-code').value; const m=raw.match(/promo\/([A-Za-z0-9]+)/); const code=(m?m[1]:raw).toUpperCase().replace(/[^A-Z0-9]/g,''); if(code.length<6){ toast('Escribe el código completo.'); return; }
      const out=$('#pr-check-out'); try{ const p=await api('/api/promo/'+code); const draw=p=>{ out.innerHTML=promoValidation(p); bindPromoRedeem(p,draw); }; draw(p); }catch(err){ out.innerHTML=`<div class="notice warning" style="margin-top:14px"><strong>${escapeHtml(err.message)}</strong></div>`; } };
  }
  async function renderCenterPromos(mountId,center){
    const mount=document.getElementById(mountId); if(!mount) return; const refresh=()=>renderCenterPromos(mountId,center); const esc=escapeHtml;
    let d; try{ d=await api('/api/center/promotions'); }catch(err){ mount.innerHTML=`<div class="empty"><h3>No se han podido cargar las promociones</h3><p>${esc(err.message)}</p></div>`; return; }
    const today=new Date().toISOString().slice(0,10);
    const card=p=>{ const live=p.status==='active'&&!p.expired;
      return `<article class="pr-card ${live?'':'is-off'}" data-id="${p.id}"><div class="pr-card-head"><div><h3>${esc(p.title)}</h3>${p.value_text?`<p class="pr-value">${esc(p.value_text)}</p>`:''}</div>${live?'<span class="pr-pill is-good">Activa</span>':p.status!=='active'?'<span class="pr-pill is-muted">Finalizada</span>':'<span class="pr-pill is-bad">Caducada</span>'}</div>
        <dl class="pr-meta"><div><dt>Caduca</dt><dd>${esc(promoDate(p.valid_until))}</dd></div><div><dt>Usos por cliente</dt><dd>${p.uses_per_code}</dd></div><div><dt>Clientes</dt><dd>${p.codes_count}</dd></div><div><dt>Canjes</dt><dd>${p.redemptions}</dd></div></dl>
        ${p.partners.length?`<div class="pr-partners"><span>También en:</span>${p.partners.map(x=>`<span class="pr-center is-${x.status}" title="${x.status==='accepted'?'Ha aceptado':x.status==='declined'?'Ha rechazado':'Invitación pendiente'}">${esc(x.name)} · ${x.status==='accepted'?'✓':x.status==='declined'?'✕':'pendiente'}</span>`).join('')}</div>`:''}
        <div class="pr-card-actions">${live?`<button type="button" class="btn btn-primary pr-assign">${wdIcon('users',15)} Dar a clientes</button>`:''}<button type="button" class="btn pr-codes">Ver códigos</button><button type="button" class="btn pr-edit">Editar</button><button type="button" class="btn pr-toggle">${p.status==='active'?'Finalizar':'Reactivar'}</button></div></article>`; };
    const inv=d.network.filter(x=>x.status==='invited'), net=d.network.filter(x=>x.status==='accepted');
    mount.innerHTML=`<section class="cb-module pr-module"><div class="cb-module-head"><div><p class="eyebrow">FIDELIZACIÓN</p><h2>Promociones con QR</h2><p>Crea una promoción, dásela a clientes de tu base y cada uno recibe en su app un QR personal con caducidad. Puedes invitar a otros centros (por ejemplo, de tu misma cadena) para que también la acepten.</p></div><button type="button" class="btn btn-primary" id="pr-new">${wdIcon('plus',16)} Nueva promoción</button></div>
      ${inv.length?`<div class="pr-invites"><strong>${wdIcon('message',16)} Invitaciones de otros centros</strong>${inv.map(x=>`<div class="pr-invite" data-id="${x.id}"><div><b>${esc(x.title)}</b><small>${esc(x.issuer_name)}${x.issuer_city?` · ${esc(x.issuer_city)}`:''} · hasta el ${esc(promoDate(x.valid_until))}${x.value_text?` · ${esc(x.value_text)}`:''}</small></div><button type="button" class="btn btn-primary pr-acc">Aceptar</button><button type="button" class="btn pr-dec">Rechazar</button></div>`).join('')}</div>`:''}
      ${d.items.length?`<div class="pr-grid">${d.items.map(card).join('')}</div>`:`<div class="empty pr-empty">${wdIcon('gift',34)}<h3>Aún no tienes promociones</h3><p>Ejemplo: «Curso Open Water + 1 año de equipo gratis», válido hasta el 30 de junio.</p></div>`}
      ${net.length?`<h3 class="pr-sub">Promociones de otros centros que aceptas</h3><div class="pr-netlist">${net.map(x=>`<div><b>${esc(x.title)}</b><small>${esc(x.issuer_name)} · hasta el ${esc(promoDate(x.valid_until))}</small></div>`).join('')}</div>`:''}</section>`;
    $('#pr-new').onclick=()=>openPromoEditor(null,refresh);
    $$('.pr-invite',mount).forEach(r=>{ const send=async action=>{ try{ await postJSON(`/api/center/promotions/${r.dataset.id}/partner`,{action}); toast(action==='accepted'?'Promoción aceptada: ya puedes canjear sus códigos.':'Invitación rechazada.'); refresh(); }catch(err){ toast(err.message); } };
      $('.pr-acc',r).onclick=()=>send('accepted'); $('.pr-dec',r).onclick=()=>send('declined'); });
    $$('.pr-card',mount).forEach(c=>{ const p=d.items.find(x=>x.id===+c.dataset.id);
      $('.pr-assign',c)?.addEventListener('click',()=>openPromoAssign(p,refresh));
      $('.pr-codes',c).onclick=()=>openPromoCodes(p,refresh);
      $('.pr-edit',c).onclick=()=>openPromoEditor(p,refresh);
      $('.pr-toggle',c).onclick=async()=>{ const st=p.status==='active'?'archived':'active'; if(st==='archived'&&!confirm('¿Finalizar la promoción? Sus códigos dejarán de ser válidos.')) return; try{ await postJSON(`/api/center/promotions/${p.id}/status`,{status:st}); toast(st==='archived'?'Promoción finalizada.':'Promoción reactivada.'); refresh(); }catch(err){ toast(err.message); } };
    });
  }
  function openPromoEditor(p,onDone){
    p=p||{title:'',value_text:'',description:'',conditions:'',valid_from:'',valid_until:'',uses_per_code:1,partners:[]};
    const partners=new Map((p.partners||[]).map(x=>[x.center_id,x.name])); const esc=escapeHtml;
    const in3m=new Date(Date.now()+90*864e5).toISOString().slice(0,10);
    const body=`<form id="pr-form" class="form-grid pr-form">
      <label class="field full"><span>Título</span><input id="pr-title" maxlength="120" required value="${esc(p.title)}" placeholder="Curso Open Water + 1 año de equipo gratis"></label>
      <label class="field full"><span>Lo que recibe el cliente <em>(se ve en grande)</em></span><input id="pr-value" maxlength="120" value="${esc(p.value_text||'')}" placeholder="Equipo completo gratis durante 12 meses"></label>
      <label class="field full"><span>Descripción</span><textarea id="pr-desc" rows="2" maxlength="1000">${esc(p.description||'')}</textarea></label>
      <label class="field"><span>Válida desde <em>(opcional)</em></span><input id="pr-from" type="date" value="${esc(p.valid_from||'')}"></label>
      <label class="field"><span>Caduca el</span><input id="pr-until" type="date" required value="${esc(p.valid_until||in3m)}"></label>
      <label class="field"><span>Usos por cliente</span><input id="pr-uses" type="number" min="1" max="50" value="${Number(p.uses_per_code||1)}"><small>1 = un solo canje. Más usos para bonos (p. ej. 10 alquileres).</small></label>
      <label class="field full"><span>Condiciones</span><textarea id="pr-cond" rows="2" maxlength="1000" placeholder="No acumulable. Presentar titulación. Sujeto a disponibilidad.">${esc(p.conditions||'')}</textarea></label>
      <div class="field full"><span>Válida también en otros centros <em>(opcional)</em></span><div class="pr-partner-pick"><input id="pr-psearch" type="search" placeholder="Busca un centro por nombre o ciudad" autocomplete="off"><div id="pr-presults" class="pr-presults" hidden></div></div><div id="pr-pchips" class="pr-pchips"></div><small>Cada centro recibe una invitación y debe aceptarla antes de poder canjear los códigos.</small></div>
    </form>`;
    const {el,close}=wdOpenModal({id:'promo-modal',size:'lg',title:p.id?'Editar promoción':'Nueva promoción',subtitle:'Cada cliente recibe un QR personal que caduca en la fecha indicada',body,footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="pr-form" class="btn btn-primary">Guardar promoción</button>'});
    const chips=()=>{ $('#pr-pchips',el).innerHTML=[...partners].map(([id,n])=>`<span class="pr-chip">${esc(n)}<button type="button" data-id="${id}" aria-label="Quitar ${esc(n)}">×</button></span>`).join(''); $$('#pr-pchips button',el).forEach(b=>b.onclick=()=>{ partners.delete(+b.dataset.id); chips(); }); }; chips();
    let t=0; $('#pr-psearch',el).oninput=e=>{ clearTimeout(t); const q=e.target.value.trim(); const box=$('#pr-presults',el); if(q.length<2){ box.hidden=true; return; }
      t=setTimeout(async()=>{ try{ const r=await api('/api/center/partner-search?q='+encodeURIComponent(q)); box.innerHTML=r.items.length?r.items.map(c=>`<button type="button" data-id="${c.id}" data-name="${esc(c.name)}">${esc(c.name)}<small>${esc([c.city,c.country].filter(Boolean).join(', '))}</small></button>`).join(''):'<p>Sin resultados</p>'; box.hidden=false;
        $$('button',box).forEach(b=>b.onclick=()=>{ partners.set(+b.dataset.id,b.dataset.name); chips(); box.hidden=true; $('#pr-psearch',el).value=''; }); }catch{} },250); };
    $('#pr-form',el).onsubmit=async e=>{ e.preventDefault();
      const data={id:p.id||0,title:$('#pr-title',el).value,value_text:$('#pr-value',el).value,description:$('#pr-desc',el).value,conditions:$('#pr-cond',el).value,valid_from:$('#pr-from',el).value,valid_until:$('#pr-until',el).value,uses_per_code:+$('#pr-uses',el).value||1,partner_ids:[...partners.keys()]};
      try{ const r=await postJSON('/api/center/promotions',data); close(); toast(p.id?'Promoción guardada.':'Promoción creada. Ahora elige a qué clientes dársela.'); onDone(); if(!p.id) openPromoAssign({...data,id:r.id,status:'active'},onDone); }catch(err){ toast(err.message); } };
  }
  async function openPromoAssign(p,onDone){
    let clients=[]; try{ clients=(await api('/api/center/clients')).items||[]; }catch(err){ toast(err.message); return; }
    const esc=escapeHtml, real=e=>e&&!String(e).endsWith('.local');
    const body=clients.length?`<div class="pr-assign-tools"><input id="pa-q" type="search" placeholder="Buscar cliente" aria-label="Buscar cliente"><label class="pr-all"><input type="checkbox" id="pa-all"> Seleccionar todos los visibles</label></div>
      <div class="pr-clients" id="pa-list">${clients.map(c=>`<label class="pr-client" data-s="${esc(`${c.fullname||''} ${c.email||''} ${c.phone||''}`.toLowerCase())}"><input type="checkbox" value="${c.id}"><span class="pl-avatar">${esc(initials(c.fullname||'?'))}</span><span><strong>${esc(c.fullname||'—')}</strong><small>${real(c.email)?esc(c.email):''}${c.bookings_count?` · ${c.bookings_count} reserva${c.bookings_count>1?'s':''}`:''}</small></span></label>`).join('')}</div>`
      :`<div class="empty"><h3>Todavía no tienes clientes</h3><p>Los clientes aparecen cuando reservan contigo o hacen check-in con tu QR.</p></div>`;
    const {el,close}=wdOpenModal({id:'promo-assign',size:'lg',title:`Dar «${p.title}»`,subtitle:'Cada cliente elegido recibe su QR personal y un aviso en su buzón',body,footer:`<span class="pa-count" id="pa-count">0 seleccionados</span><button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="pa-go" ${clients.length?'':'disabled'}>Enviar promoción</button>`});
    const count=()=>{ const n=$$('#pa-list input:checked',el).length; $('#pa-count',el).textContent=`${n} seleccionado${n===1?'':'s'}`; };
    el.addEventListener('change',count);
    $('#pa-q',el)?.addEventListener('input',e=>{ const v=e.target.value.trim().toLowerCase(); $$('.pr-client',el).forEach(r=>r.hidden=!!v&&!r.dataset.s.includes(v)); });
    $('#pa-all',el)?.addEventListener('change',e=>{ $$('.pr-client',el).forEach(r=>{ if(!r.hidden) r.querySelector('input').checked=e.target.checked; }); count(); });
    $('#pa-go',el).onclick=async()=>{ const ids=$$('#pa-list input:checked',el).map(i=>+i.value); if(!ids.length){ toast('Elige al menos un cliente.'); return; }
      try{ const r=await postJSON(`/api/center/promotions/${p.id}/assign`,{user_ids:ids}); close(); toast(r.created?`Promoción enviada a ${r.created} cliente${r.created>1?'s':''}.`+(r.skipped?` ${r.skipped} ya la tenían.`:''):'Esos clientes ya tenían esta promoción.'); onDone(); }catch(err){ toast(err.message); } };
  }
  async function openPromoCodes(p,onDone){
    let d; try{ d=await api(`/api/center/promotions/${p.id}/codes`); }catch(err){ toast(err.message); return; }
    const esc=escapeHtml;
    const body=d.items.length?`<div class="pr-codes">${d.items.map(c=>`<div class="pr-code-row" data-code="${esc(c.code)}"><span><strong>${esc(c.fullname||'—')}</strong><small>Entregado el ${esc(new Date(c.created_at).toLocaleDateString(wdLocale()))}${c.last_used?` · último uso ${esc(new Date(c.last_used).toLocaleDateString(wdLocale()))}`:''}</small></span><code>${esc(promoCode(c.code))}</code><span>${Number(c.uses)}/${p.uses_per_code}</span>${promoPill(c.state)}<span class="pr-code-act"><a class="btn" href="#/promo/${esc(c.code)}">Abrir</a>${c.state==='active'?'<button type="button" class="btn pr-revoke">Anular</button>':''}</span></div>`).join('')}</div>`:'<div class="empty"><h3>Nadie tiene esta promoción todavía</h3><p>Usa «Dar a clientes» para enviarla.</p></div>';
    const {el,close}=wdOpenModal({id:'promo-codes',size:'lg',title:`Códigos de «${p.title}»`,subtitle:`${d.items.length} cliente${d.items.length===1?'':'s'}`,body,footer:'<button type="button" class="btn btn-primary" data-modal-close>Cerrar</button>'});
    $$('.pr-code-row a',el).forEach(a=>a.addEventListener('click',()=>close()));
    $$('.pr-revoke',el).forEach(b=>b.onclick=async()=>{ const code=b.closest('.pr-code-row').dataset.code; if(!confirm('¿Anular este código? El cliente ya no podrá usarlo.')) return; try{ await postJSON(`/api/center/promo-codes/${code}/revoke`,{}); toast('Código anulado.'); close(); onDone(); openPromoCodes(p,onDone); }catch(err){ toast(err.message); } });
  }

  async function renderBookingDetail(params){
    const me=await api('/api/me');if(!me.authenticated){goLogin();return;}const id=Number(params?.get?.('id')||params||0);if(!id){location.hash='#/area';return;}
    const d=await api('/api/bookings/'+id);const b=d.booking;const own=b.user_id===me.user.id;const centerView=!own&&['center','freelance'].includes(me.user.role);const st=bookingStatus(b.status,b.status_label);const statusText=b.status_label||st[0];
    const canPay=own&&!!b.can_pay_online; const payRec=d.payment||null;const p=d.profile||{};const docs=d.documents||[];
    if(centerView){
      const docRows=docs.map(doc=>`<div class="doc-card"><div><strong>${escapeHtml(doc.title)}</strong><div style="font-size:12px;color:var(--muted)">${escapeHtml(doc.document_type)}${doc.expires_at?' · vence '+escapeHtml(doc.expires_at):''}</div></div><a class="btn" href="/api/documents/file/${doc.id}" target="_blank" rel="noopener">Abrir</a></div>`).join('');
      setApp(`<section class="page diver-sheet-page"><div class="breadcrumb"><a href="#/admin?tab=bookings">Reservas</a> / Ficha del buceador</div><p class="eyebrow">FICHA OPERATIVA · USO INTERNO</p><div class="diver-sheet-head"><div><h1>${escapeHtml(b.fullname)}</h1><p class="lead">Documentación y datos operativos del buceador.</p></div><div class="page-actions"><a class="btn" href="/api/bookings/${id}/receipt.pdf" target="_blank" rel="noopener">Justificante PDF + QR</a>${d.data_shared?`<a class="btn btn-primary" href="/api/bookings/${id}/diver-sheet.pdf" target="_blank" rel="noopener">Ficha operativa PDF</a>`:''}<button class="btn" type="button" id="center-notice">Enviar aviso al cliente</button>${Number(b.refundable||0)>0?'<button class="btn" type="button" id="center-refund">Devolver</button>':''}${['requested','confirmed','accepted_pending_payment'].includes(b.status)&&b.service_id?'<button class="btn" type="button" id="center-reschedule">Cambiar fecha u hora</button>':''}${['confirmed','accepted_pending_payment'].includes(b.status)?'<button class="btn danger" type="button" id="center-cancel">Cancelar reserva</button>':''}</div></div>
      ${bookingPaymentCard(b,d.payment||null,{own:false,canPay:false})}
      <div class="bk-state-bar">${wdStatus(b.status,b.status_label)}<span class="wd-mode">${escapeHtml(b.mode_label||'')}</span>${b.status==='requested'&&b.response_deadline?`<span class="acc-due">${wdIcon('clock',13)} Responde antes del ${escapeHtml(wdDeadline(b.response_deadline))}</span>`:''}${b.status==='accepted_pending_payment'&&b.payment_deadline?`<span class="acc-due">${wdIcon('clock',13)} El cliente paga antes del ${escapeHtml(wdDeadline(b.payment_deadline))}</span>`:''}
        ${b.status==='requested'?`<button class="btn btn-primary" type="button" id="center-confirm-booking">Aceptar</button><button class="btn danger" type="button" id="center-reject-booking">Rechazar</button>`:''}</div>
      ${d.data_shared?'':'<div class="notice warn"><strong>Ficha no compartida.</strong> Este cliente no ha reservado él mismo con tu centro ni ha compartido sus datos (por ejemplo, haciendo check-in con tu QR). Solo ves los datos de la reserva.</div>'}<div class="detail" style="margin-top:22px"><article class="detail-main"><section class="reservation-pass-section"><p class="eyebrow">DATOS DEL BUCEADOR</p><div class="data-grid"><div class="data-item"><span>Nombre</span><strong>${escapeHtml(b.fullname)}</strong></div><div class="data-item"><span>Teléfono</span><strong>${p.phone?`<a href="tel:${escapeHtml(p.phone)}">${escapeHtml(p.phone)}</a>`:'—'}</strong></div><div class="data-item"><span>Email</span><strong>${escapeHtml(b.email||'—')}</strong></div><div class="data-item"><span>Ciudad</span><strong>${escapeHtml(p.city||'—')}</strong></div><div class="data-item"><span>Titulación</span><strong>${escapeHtml(p.certification_name||'No indicada')}</strong></div><div class="data-item"><span>Contacto de emergencia</span><strong>${escapeHtml([p.emergency_contact_name,p.emergency_contact_phone].filter(Boolean).join(' · ')||'—')}</strong></div></div></section><section class="reservation-pass-section"><p class="eyebrow">EQUIPO Y PREFERENCIAS</p><div class="data-grid"><div class="data-item"><span>Necesita equipo</span><strong>${p.equipment_required?'Sí':'No'}</strong></div><div class="data-item"><span>Traje / talla</span><strong>${escapeHtml([p.suit_type,p.suit_size].filter(Boolean).join(' · ')||'—')}</strong></div><div class="data-item"><span>Botas</span><strong>${escapeHtml(p.boot_size||'—')}</strong></div><div class="data-item"><span>Chaleco</span><strong>${escapeHtml(p.bcd_size||'—')}</strong></div><div class="data-item"><span>Aletas</span><strong>${escapeHtml(p.fin_size||'—')}</strong></div><div class="data-item"><span>Máscara</span><strong>${escapeHtml(p.mask_size||'—')}</strong></div><div class="data-item"><span>Botella</span><strong>${escapeHtml(p.tank_preference||'—')}</strong></div><div class="data-item"><span>Ordenador</span><strong>${escapeHtml(p.computer_preference||'—')}</strong></div><div class="data-item"><span>Peso habitual</span><strong>${p.usual_weight_kg?escapeHtml(String(p.usual_weight_kg))+' kg':'—'}</strong></div></div>${p.equipment_notes?`<div class="notice" style="margin-top:14px"><strong>Notas de equipo</strong><br>${escapeHtml(p.equipment_notes)}</div>`:''}</section><section class="reservation-pass-section"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><div><p class="eyebrow">DOCUMENTACIÓN</p><h2>Documentación del buceador</h2></div><a class="btn" href="/api/bookings/${id}/diver-sheet.pdf" target="_blank" rel="noopener">PDF</a></div>${docRows||'<div class="empty" style="margin-top:12px">El buceador todavía no ha aportado documentación.</div>'}</section></article><aside class="detail-side"><div class="notice"><strong>Ficha interna del centro</strong><p style="margin:8px 0 0">Esta pantalla no modifica la reserva. La confirmación, pago y estado se gestionan desde la pantalla de reservas.</p></div><a class="btn" style="margin-top:12px;width:100%" href="#/admin?tab=bookings">← Volver a reservas</a></aside></div></section>`);
      bindCenterBookingActions(b,id,()=>renderBookingDetail(new URLSearchParams('id='+id))); return;
    }
    const payBox=bookingPaymentCard(b,payRec,{own,canPay,cancelled:params?.get?.('pago')==='cancelado'})+(own?bookingReviewPrompt(b)+bookingCancelCard(b):'');
    const customerPanel=centerView?`<section class="reservation-pass-section"><p class="eyebrow">FICHA OPERATIVA DEL BUCEADOR</p><h2>${escapeHtml(b.fullname)}</h2><div class="data-grid"><div class="data-item"><span>Email</span><strong>${escapeHtml(b.email||'—')}</strong></div><div class="data-item"><span>Teléfono</span><strong>${p.phone?`<a href="tel:${escapeHtml(p.phone)}">${escapeHtml(p.phone)}</a>`:'—'}</strong></div><div class="data-item"><span>Ciudad</span><strong>${escapeHtml(p.city||'—')}</strong></div><div class="data-item"><span>Titulación</span><strong>${escapeHtml(p.certification_name||'No indicada')}</strong></div><div class="data-item"><span>Seguro / documentación</span><strong>${docs.length?`${docs.length} documento(s) disponible(s)`:'No aportada'}</strong></div><div class="data-item"><span>Necesita equipo</span><strong>${p.equipment_required?'Sí':'No'}</strong></div><div class="data-item"><span>Traje / talla</span><strong>${escapeHtml([p.suit_type,p.suit_size].filter(Boolean).join(' · ')||'—')}</strong></div><div class="data-item"><span>Botas</span><strong>${escapeHtml(p.boot_size||'—')}</strong></div><div class="data-item"><span>Chaleco</span><strong>${escapeHtml(p.bcd_size||'—')}</strong></div><div class="data-item"><span>Aletas</span><strong>${escapeHtml(p.fin_size||'—')}</strong></div><div class="data-item"><span>Máscara</span><strong>${escapeHtml(p.mask_size||'—')}</strong></div><div class="data-item"><span>Botella</span><strong>${escapeHtml(p.tank_preference||'—')}</strong></div><div class="data-item"><span>Ordenador</span><strong>${escapeHtml(p.computer_preference||'—')}</strong></div><div class="data-item"><span>Peso habitual</span><strong>${p.usual_weight_kg?escapeHtml(String(p.usual_weight_kg))+' kg':'—'}</strong></div></div>${p.equipment_notes?`<div class="notice" style="margin-top:14px"><strong>Notas de equipo</strong><br>${escapeHtml(p.equipment_notes)}</div>`:''}<div style="margin-top:18px"><h3 style="margin-bottom:8px">Documentación disponible</h3>${docs.map(doc=>`<div class="doc-card"><div><strong>${escapeHtml(doc.title)}</strong><div style="font-size:12px;color:var(--muted)">${escapeHtml(doc.document_type)}${doc.expires_at?' · vence '+escapeHtml(doc.expires_at):''}</div></div><a class="btn" href="/api/documents/file/${doc.id}" target="_blank" rel="noopener">Abrir</a></div>`).join('')||'<div class="empty">El buceador todavía no ha aportado documentación.</div>'}</div></section>`:'';
    const customerNotes=centerView?`<div class="notice"><strong>Información proporcionada por el buceador</strong><br>${escapeHtml(b.notes||'Sin notas adicionales.')}</div>`:(b.notes?`<div class="notice"><strong>Tus notas para el centro</strong><br>${escapeHtml(b.notes)}</div>`:'');
    const passActions=centerView?`<div class="page-actions"><a class="btn" href="#/admin?tab=bookings">Volver a reservas</a><a class="btn" href="/api/bookings/${id}/receipt.pdf" target="_blank" rel="noopener">Recibo PDF + QR</a><a class="btn" href="/api/bookings/${id}/diver-sheet.pdf" target="_blank" rel="noopener">Ficha operativa PDF</a>${(b.status==='requested'||b.status==='pending')?`<button class="btn btn-primary" id="center-confirm-booking">Confirmar reserva</button><button class="btn danger" id="center-reject-booking">Rechazar</button>`:''}</div>`:`<aside class="reservation-qr"><img src="/api/bookings/${id}/qr.svg" alt="QR de la reserva"><strong>Presenta este QR</strong><small>El centro puede escanearlo para verificar la reserva.</small><a class="btn btn-primary" href="/api/bookings/${id}/receipt.pdf" target="_blank" rel="noopener">Descargar esta reserva en PDF</a></aside>`;
    setApp(`<section class="page"><div class="breadcrumb"><a href="${centerView?'#/admin?tab=bookings':'#/area'}">${centerView?'Reservas':'Mi área'}</a> / Reserva WOD-${String(id).padStart(6,'0')}</div><div class="reservation-pass"><div class="reservation-pass-head"><div><p class="eyebrow">WORLDIVES DISCOVERY · ${own?'MI RESERVA':'RESERVA DEL CENTRO'}</p><h1>${escapeHtml(b.center_name)}</h1><p class="lead">${escapeHtml(areaDate(b.booking_date,b.booking_time))}</p></div><span class="status ${st[1]}">${escapeHtml(statusText)}</span></div><div class="reservation-pass-grid"><div><p class="eyebrow">${centerView?'DATOS DE LA SALIDA':'TU INMERSIÓN'}</p><h2>${escapeHtml(b.point_name||'Punto a concretar con el centro')}</h2><div class="data-grid"><div class="data-item"><span>Fecha</span><strong>${escapeHtml(b.booking_date)}</strong></div><div class="data-item"><span>Hora</span><strong>${escapeHtml(b.booking_time||'Por confirmar')}</strong></div><div class="data-item"><span>Punto</span><strong>${escapeHtml(b.point_name||'A concretar con el centro')}</strong></div><div class="data-item"><span>Participantes</span><strong>${b.participants}</strong></div><div class="data-item"><span>Servicio</span><strong>${escapeHtml(b.service_title||'—')}</strong></div><div class="data-item"><span>Precio</span><strong>${Number(b.price||0).toFixed(2)} ${escapeHtml(b.currency||'EUR')}</strong>${(()=>{let ls=[];try{ls=JSON.parse(b.price_breakdown||'[]')||[];}catch{} return ls.length>1?`<small class="booking-price-lines">${ls.map(l=>`${escapeHtml(l.label)}: ${l.qty} × ${Number(l.unit||0).toFixed(2)} €`).join('<br>')}</small>`:'';})()}</div><div class="data-item"><span>Pago</span><strong>${Number(b.price||0)>0?wdPayment(b.payment_status):'Sin coste'}</strong></div><div class="data-item"><span>Modo de reserva</span><strong>${escapeHtml(b.mode_label||'')}</strong></div><div class="data-item"><span>Equipo solicitado</span><strong>${b.needs_equipment?'Sí':'No'}${b.equipment_items?' · '+escapeHtml(b.equipment_items):''}</strong></div><div class="data-item"><span>Guía</span><strong>${b.needs_guide?'Sí':'No'}${b.guide_notes?' · '+escapeHtml(b.guide_notes):''}</strong></div><div class="data-item"><span>Nitrox</span><strong>${b.nitrox?'Sí':'No'}</strong></div><div class="data-item"><span>Traslado</span><strong>${b.pickup?'Sí':'No'}</strong></div></div></div>${passActions}</div>${centerView?customerNotes:`<div class="reservation-pass-section"><p class="eyebrow">CENTRO DE BUCEO</p><h2><a href="#/centro?id=${b.center_id}">${escapeHtml(b.center_name)}</a></h2><div class="data-grid"><div class="data-item"><span>Ciudad</span><strong>${escapeHtml(b.center_city||'—')}</strong></div><div class="data-item"><span>Teléfono</span><strong>${b.center_phone?`<a href="tel:${escapeHtml(b.center_phone)}">${escapeHtml(b.center_phone)}</a>`:'—'}</strong></div><div class="data-item"><span>Email</span><strong>${b.center_email?`<a href="mailto:${escapeHtml(b.center_email)}">${escapeHtml(b.center_email)}</a>`:'—'}</strong></div><div class="data-item"><span>Dirección</span><strong>${escapeHtml(b.center_address||'—')}</strong></div></div></div>`}${customerPanel}${payBox}<div class="notice ${['confirmed','completed'].includes(b.status)?'success':['rejected','cancelled','expired'].includes(b.status)?'warning':''}"><strong>${escapeHtml(statusText)}.</strong> ${bookingStateHelp(b)}</div></div></section>`);
    if(canPay)$('#booking-pay-now').onclick=async e=>{const btn=e.currentTarget; btn.disabled=true; btn.textContent='Abriendo el pago seguro…'; try{const pay=await postJSON('/api/payments/checkout',{booking_id:id,service_id:Number(b.service_id||0),slot_id:Number(b.slot_id||0)||null});if(pay.checkout_url){location.href=pay.checkout_url;return;}}catch(err){toast(err.message)} btn.disabled=false; btn.textContent='Pagar ahora de forma segura';};
    if(own) bindBookingCancel(b,id);
    if(own&&params?.get?.('pago')==='cancelado'&&!renderBookingDetail.cancelled?.[id]){ (renderBookingDetail.cancelled??={})[id]=1; postJSON('/api/payments/cancel',{booking_id:id}).then(r=>{ if(r.paid){ toast('El pago ya se había completado.'); renderBookingDetail(new URLSearchParams('id='+id)); } else if(r.status&&r.status!==b.status){ toast(r.status==='expired'?'No se ha completado el pago: la reserva no se ha hecho y las plazas se han liberado.':'No se ha completado el pago.'); renderBookingDetail(new URLSearchParams('id='+id)); } }).catch(()=>{}); }
  }
  // What a booking's state means, in the diver's words.
  function bookingStateHelp(b){
    const dl=v=>escapeHtml(wdDeadline(v));
    switch(b.status){
      case 'requested': case 'pending': return `No se cobra nada hasta que el centro acepte.${b.response_deadline?` El centro responde como muy tarde el ${dl(b.response_deadline)}; si no, la solicitud caduca sola.`:''}`;
      case 'accepted_pending_payment': return `El centro ha aceptado y te guarda la plaza. Paga antes del ${dl(b.payment_deadline)} para confirmarla; si no, la reserva se cancela sola y no se te cobra nada.`;
      case 'payment_in_progress': return 'Estamos esperando la confirmación del pago. Si has cerrado la ventana de pago, puedes volver a intentarlo durante unos minutos.';
      case 'confirmed': return b.payment_status==='at_center'?'La reserva está confirmada. Pagas en el centro el día de la actividad.':'La reserva está confirmada.';
      case 'completed': return 'Esta inmersión está completada.';
      case 'rejected': return `El centro no ha podido aceptar la solicitud.${b.reject_reason?' Motivo: '+escapeHtml(b.reject_reason):''} No se te ha cobrado nada.`;
      case 'expired': return 'Esta reserva ha caducado y las plazas se han liberado. No se te ha cobrado nada.';
      case 'cancelled': return 'La reserva está cancelada.';
      default: return '';
    }
  }
  // Provider actions on one booking: accept, reject with an optional reason, and «Enviar aviso al cliente» (G11).
  function bindCenterBookingActions(b,id,after){
    $('#center-confirm-booking')?.addEventListener('click',async()=>{ try{ const r=await postJSON('/api/bookings/'+id+'/status',{status:'confirmed'}); toast(r.status==='accepted_pending_payment'?'Solicitud aceptada. El cliente tiene un plazo para pagar.':'Reserva confirmada.'); after&&after(); }catch(e){ toast(e.message); } });
    $('#center-reject-booking')?.addEventListener('click',()=>openRejectModal(id,after));
    $('#center-notice')?.addEventListener('click',()=>openNoticeModal(id,b,after));
    $('#center-refund')?.addEventListener('click',()=>openRefundModal(id,after));
    $('#center-cancel')?.addEventListener('click',()=>openProviderCancelModal(id,after));
    $('#center-reschedule')?.addEventListener('click',()=>openRescheduleModal(b,after));
  }
  function openRejectModal(id,after){
    const {el,close}=wdOpenModal({id:'reject-booking',title:'Rechazar la solicitud',subtitle:'El cliente recibirá un email. No se le cobra nada.',
      body:`<div class="field"><label for="rj-reason">Motivo (opcional)</label><input id="rj-reason" maxlength="300" placeholder="Ej. previsión de mal estado del mar"></div>`,
      footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn danger" id="rj-ok">Rechazar</button>'});
    $('#rj-ok',el).onclick=async()=>{ try{ await postJSON('/api/bookings/'+id+'/status',{status:'rejected',reason:$('#rj-reason',el).value}); close(); toast('Solicitud rechazada.'); after&&after(); }catch(e){ toast(e.message); } };
  }
  function openNoticeModal(id,b,after){
    const {el,close}=wdOpenModal({id:'booking-notice',title:'Enviar aviso al cliente',subtitle:'Solo sobre esta reserva. Le llega por email y a sus «Avisos», con el teléfono y el email de tu centro para que te conteste directamente.',
      body:`<div class="field"><label for="nt-subject">Asunto</label><input id="nt-subject" maxlength="180" value="Aviso sobre tu reserva del ${escapeHtml(wdDay(b.booking_date))}"></div><div class="field"><label for="nt-body">Aviso</label><textarea id="nt-body" rows="4" maxlength="3000" placeholder="Ej. La salida pasa a las 10:00 por el estado del mar."></textarea></div>`,
      footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="nt-ok">Enviar aviso</button>'});
    $('#nt-ok',el).onclick=async()=>{ try{ await postJSON('/api/messages',{booking_id:id,subject:$('#nt-subject',el).value,body:$('#nt-body',el).value}); close(); toast('Aviso enviado.'); after&&after(); }catch(e){ toast(e.message); } };
  }

  async function renderPublicBookingVerification(params){
    const id=Number(params?.get?.('id')||0); if(!id){setApp('<section class="page"><div class="empty"><h2>QR no válido</h2><p>No se ha encontrado una reserva asociada a este código.</p></div></section>');return;}
    try{
      const tk=params?.get?.('t')||''; const d=await api('/api/public/bookings/'+id+(tk?'?t='+encodeURIComponent(tk):'')); const b=d.booking; const confirmed=['confirmed','completed'].includes(b.status);
      const statusText=b.status==='confirmed'?'RESERVA CONFIRMADA':b.status==='completed'?'INMERSIÓN COMPLETADA':['requested','accepted_pending_payment','payment_in_progress','pending'].includes(b.status)?'RESERVA PENDIENTE':'RESERVA NO VÁLIDA';
      setApp(`<section class="page auth"><div class="auth-card" style="max-width:720px"><p class="eyebrow">WORLDIVES DISCOVERY · VERIFICACIÓN QR</p><div style="font-size:48px;margin-bottom:8px">${confirmed?'✓':'!'}</div><h1 style="font-size:38px">${escapeHtml(statusText)}</h1><p class="lead">Reserva ${escapeHtml(b.ref||'#'+id)}</p><div class="data-grid" style="text-align:left;margin-top:24px"><div class="data-item"><span>Buceador</span><strong>${escapeHtml(b.customer||'')}</strong></div><div class="data-item"><span>Centro</span><strong>${escapeHtml(b.center_name)}</strong></div><div class="data-item"><span>Fecha</span><strong>${escapeHtml(b.booking_date)}</strong></div><div class="data-item"><span>Hora</span><strong>${escapeHtml(b.booking_time||'Por confirmar')}</strong></div><div class="data-item"><span>Punto</span><strong>${escapeHtml(b.point_name||'A concretar')}</strong></div><div class="data-item"><span>Participantes</span><strong>${b.participants}</strong></div><div class="data-item"><span>Pago</span><strong>${b.payment_status==='paid'?'Pagado':b.payment_status==='not_required'?'No requerido':b.payment_status==='required'?'Pendiente de pago':'En proceso'}</strong></div></div><div class="notice ${confirmed?'success':'warning'}" style="margin-top:20px">${confirmed?(b.payment_status==='required'?'Reserva confirmada, pero el pago todavía está pendiente. Comprueba el pago antes de admitir al buceador.':'El código QR corresponde a una reserva válida de WORLDIVES DISCOVERY.'):'Este QR no acredita una reserva confirmada. Comprueba el estado antes de admitir al buceador.'}</div></div></section>`);
    }catch(e){setApp('<section class="page"><div class="empty"><h2>QR no válido</h2><p>La reserva no existe, ya no está disponible o el enlace está incompleto. Escanea de nuevo el QR de la reserva.</p></div></section>');}
  }

  async function renderLogbook(){
    if(!(await loadMe(),state.me)){goLogin();return;}
    const items=(await api('/api/logbook')).items||[]; const esc=escapeHtml;
    const chrono=[...items].sort((a,b)=>String(a.dive_date).localeCompare(String(b.dive_date))||a.id-b.id); const num=new Map(chrono.map((x,i)=>[x.id,i+1]));
    const maxDepth=Math.max(0,...items.map(x=>Number(x.depth)||0)); const minutes=items.reduce((n,x)=>n+(Number(x.duration)||0),0);
    const countries=new Set(items.map(x=>String(x.country||'').trim().toLowerCase()).filter(Boolean)).size;
    const hm=m=>m>=60?`${Math.floor(m/60)} h ${m%60?String(m%60).padStart(2,'0')+' min':''}`.trim():`${m} min`;
    const byYear={}; items.forEach(x=>(byYear[String(x.dive_date||'').slice(0,4)||'—']??=[]).push(x));
    const row=x=>`<article class="lb-row" data-id="${x.id}" data-s="${esc(`${x.site||''} ${x.country||''} ${x.dive_type||''} ${x.notes||''}`.toLowerCase())}"><span class="lb-num">#${num.get(x.id)}</span>${accDate(x.dive_date)}
      <div class="lb-main"><strong>${esc(x.site)}</strong><small>${esc([x.country,x.dive_type].filter(Boolean).join(' · '))}${x.booking_id?' · <span class="lb-tag">Reserva WORLDIVES</span>':''}</small>${x.notes?`<p>${esc(x.notes)}</p>`:''}</div>
      <div class="lb-figs"><span><b>${x.depth??'—'}</b> m</span><span><b>${x.duration??'—'}</b> min</span></div>
      <div class="lb-act"><button type="button" class="btn lb-edit">Editar</button>${x.booking_id?'':'<button type="button" class="btn lb-del" aria-label="Borrar inmersión">Borrar</button>'}</div></article>`;
    setApp(accountShell('logbook',{eyebrow:'MI ACTIVIDAD',title:'Log Book',lead:'Tu historial de inmersiones. Las reservas completadas se añaden solas; el resto, en un momento.',actions:`<button type="button" class="btn" id="lb-csv" ${items.length?'':'disabled'}>${wdIcon('download',15)} Exportar CSV</button><button type="button" class="btn btn-primary" id="lb-new">${wdIcon('plus',15)} Nueva inmersión</button>`},`
      <div class="acc-kpis">${accKpi('book',items.length,'inmersiones')}${accKpi('depth',maxDepth?maxDepth+' m':'—','profundidad máxima')}${accKpi('clock',minutes?hm(minutes):'—','bajo el agua')}${accKpi('globe',countries,countries===1?'país':'países')}</div>
      <section class="acc-card"><div class="acc-card-head"><h2>Mis inmersiones</h2>${items.length>4?`<label class="svc-search lb-search">${wdIcon('search',16)}<input id="lb-q" type="search" placeholder="Buscar punto, país o nota" aria-label="Buscar en el Log Book"></label>`:''}</div>
        ${items.length?Object.keys(byYear).sort().reverse().map(y=>`<div class="lb-year" data-year="${esc(y)}"><h3>${esc(y)} <small>${byYear[y].length} inmersion${byYear[y].length===1?'':'es'}</small></h3>${byYear[y].map(row).join('')}</div>`).join('')+(items.length>25?`<button type="button" class="btn acc-more" id="lb-more">Ver las ${items.length} inmersiones</button>`:'')
          :`<div class="acc-blank">${wdIcon('book',34)}<h3>Tu Log Book está vacío</h3><p>Apunta tu primera inmersión o reserva una: cuando el centro la marque como completada aparecerá aquí sola.</p><button type="button" class="btn btn-primary" id="lb-new-2">Añadir mi primera inmersión</button></div>`}</section>`));
    fillAccountLevel();
    const open=x=>{ x=x||{}; const body=`<form id="log-form" class="form-grid">
        <div class="field"><label for="l-date">Fecha</label><input id="l-date" type="date" required max="${wdToday()}" value="${esc(x.dive_date||wdToday())}"></div>
        <div class="field"><label for="l-site">Punto de buceo</label><input id="l-site" required maxlength="200" value="${esc(x.site||'')}" placeholder="El Bajo de la Morra"></div>
        <div class="field"><label for="l-country">País</label><input id="l-country" maxlength="100" value="${esc(x.country||'')}"></div>
        <div class="field"><label for="l-type">Tipo de inmersión</label><input id="l-type" maxlength="100" list="lb-types" value="${esc(x.dive_type||'')}"><datalist id="lb-types">${['Arrecife','Pared','Pecio','Cueva','Nocturna','Deriva','Profunda','Formación','Costa'].map(t=>`<option value="${t}">`).join('')}</datalist></div>
        <div class="field"><label for="l-depth">Profundidad máxima (m)</label><input id="l-depth" type="number" min="0" max="350" step="0.1" inputmode="decimal" value="${x.depth??''}"></div>
        <div class="field"><label for="l-duration">Duración (min)</label><input id="l-duration" type="number" min="0" max="600" inputmode="numeric" value="${x.duration??''}"></div>
        <div class="field full"><label for="l-notes">Notas</label><textarea id="l-notes" rows="3" maxlength="2000" placeholder="Visibilidad, fauna, compañeros, equipo…">${esc(x.notes||'')}</textarea></div></form>`;
      const {el,close}=wdOpenModal({id:'log-modal',title:x.id?'Editar inmersión':'Nueva inmersión',subtitle:x.id?`Inmersión #${num.get(x.id)}`:'Se añade a tu historial',body,footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="log-form" class="btn btn-primary">Guardar inmersión</button>'});
      $('#log-form',el).onsubmit=async e=>{ e.preventDefault(); const data={id:x.id,dive_date:$('#l-date',el).value,site:$('#l-site',el).value,country:$('#l-country',el).value,depth:$('#l-depth',el).value,duration:$('#l-duration',el).value,dive_type:$('#l-type',el).value,notes:$('#l-notes',el).value};
        try{ await postJSON(x.id?'/api/logbook/update':'/api/logbook',data); close(); toast('Inmersión guardada.'); renderLogbook(); }catch(err){ toast(err.message); } }; };
    $('#lb-new').onclick=()=>open(); $('#lb-new-2')?.addEventListener('click',()=>open());
    $$('.lb-row').forEach(r=>{ const x=items.find(i=>i.id===+r.dataset.id); $('.lb-edit',r).onclick=()=>open(x);
      $('.lb-del',r)?.addEventListener('click',async()=>{ if(!confirm(`¿Borrar la inmersión en ${x.site}?`)) return; try{ await postJSON('/api/logbook/delete',{id:x.id}); toast('Inmersión borrada.'); renderLogbook(); }catch(err){ toast(err.message); } }); });
    let showAll=items.length<=25; const paint=()=>{ const v=($('#lb-q')?.value||'').trim().toLowerCase(); let i=0; $$('.lb-row').forEach(r=>{ const hit=!v||r.dataset.s.includes(v); r.hidden=!hit||(!v&&!showAll&&i>=25); if(hit) i++; }); $$('.lb-year').forEach(y=>y.hidden=!$$('.lb-row',y).some(r=>!r.hidden)); const m=$('#lb-more'); if(m) m.hidden=showAll||!!v; };
    $('#lb-q')?.addEventListener('input',paint); $('#lb-more')?.addEventListener('click',()=>{ showAll=true; paint(); }); paint();
    $('#lb-csv').onclick=()=>{ const rows=[['#','Fecha','Punto','País','Tipo','Profundidad (m)','Duración (min)','Notas'],...chrono.map(x=>[num.get(x.id),x.dive_date,x.site,x.country,x.dive_type,x.depth,x.duration,x.notes])];
      const csv='﻿'+rows.map(r=>r.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(';')).join('\r\n'); const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})); a.download='logbook-worldives.csv'; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),2000); };
  }
  // ---------------------------------------------------------------- v50.35 · WORLDIVES points (Fase 3)
  // Points are earned (diving, logging dives, completed bookings) or granted by a centre, and are exchanged only
  // for advantages that each centre defines and pays for. They are not money: no top-ups, transfers or cash.
  const PTS_KIND={earned:'Conseguidos',granted:'Concedidos por un centro',redeemed:'Canje',reversal:'Devueltos',migrated:'Saldo del monedero convertido',adjust:'Ajuste'};
  const CODE_STATE={issued:['Para usar','good'],redeemed:['Usado','muted'],expired:['Caducado','muted'],cancelled:['Anulado','muted']};
  const REWARD_TYPES={discount:'Descuento del centro',activity:'Inmersión o actividad',course_discount:'Descuento en un curso',insurance:'Seguro de día pagado por el centro',gift:'Regalo o ventaja del centro'};
  const wdPts=n=>`${Number(n||0).toLocaleString(wdLocale())} ${Math.abs(Number(n||0))===1?'punto':'puntos'}`;
  async function renderMyPoints(){
    if(!state.me){goLogin();return;} const d=await api('/api/points'); const esc=escapeHtml;
    setApp(accountShell('mis-puntos',{eyebrow:'MI ACTIVIDAD',title:'Mis puntos',lead:'Ganas puntos al bucear, registrar inmersiones y completar reservas. Los canjeas por ventajas que ofrece cada centro.'},`
      <div class="acc-grid"><div class="acc-col">
        <section class="wl-balance"><div><span>Puntos disponibles</span><strong>${wdPts(d.balance)}</strong><small>Los puntos no son dinero: no se compran, no se transfieren y no se cambian por dinero.</small></div><a class="btn" href="#/recompensas">${wdIcon('gift',16)} Ver ventajas</a></section>
        <div class="acc-kpis is-3">${accKpi('arrow',wdPts(d.earned),'conseguidos en total')}${accKpi('tag',wdPts(d.spent),'canjeados')}${accKpi('receipt',(d.codes||[]).length,'códigos')}</div>
        <section class="acc-card"><div class="acc-card-head"><h2>Movimientos</h2></div>
          ${d.items.length?`<div class="wl-moves">${d.items.map(x=>{ const v=Number(x.points); return `<div class="wl-move"><span class="wl-ic ${v>=0?'is-in':'is-out'}">${wdIcon(v>=0?'plus':'tag',15)}</span><span><strong>${esc(x.description)}</strong><small>${esc(PTS_KIND[x.kind]||'')} · ${fmtDate(x.created_at)}</small></span><b class="${v>=0?'is-in':'is-out'}">${v>=0?'+':'−'}${Math.abs(v).toLocaleString(wdLocale())}</b></div>`; }).join('')}</div>`:'<p class="acc-empty">Todavía no hay movimientos. Tus primeros puntos llegan solos al completar tu perfil o registrar una inmersión.</p>'}</section>
        ${(d.legacy_wallet||[]).length?`<details class="acc-card"><summary><strong>Historial del antiguo monedero</strong> <small>(convertido a puntos: 1 € = 1 punto)</small></summary><div class="wl-moves">${d.legacy_wallet.map(x=>`<div class="wl-move"><span><strong>${esc(x.description)}</strong><small>${fmtDate(x.created_at)}</small></span><b>${Number(x.amount)>=0?'+':'−'}${wdMoney(Math.abs(Number(x.amount)),'EUR')}</b></div>`).join('')}</div></details>`:''}</div>
      <aside class="acc-col">
        <section class="acc-card"><div class="acc-card-head"><h2>Mis códigos</h2></div>${(d.codes||[]).length?d.codes.map(r=>{ const st=CODE_STATE[r.status]||[r.status,'muted']; return `<div class="wl-code"><div><strong>${esc(r.title)}</strong><small>${esc(r.center_name||'')} · ${wdPts(r.cost_points)} · <span class="status ${st[1]}">${esc(st[0])}</span>${r.status==='issued'&&r.expires_at?` · válido hasta el ${esc(fmtDate(r.expires_at))}`:''}${r.status==='redeemed'&&r.redeemed_at?` · ${esc(fmtDate(r.redeemed_at))}`:''}</small></div>
          ${r.status==='issued'?`<button type="button" class="wl-copy" data-qr="${r.id}" data-code="${esc(r.code)}" title="Ver el código para enseñarlo en el centro"><code>${esc(r.code)}</code>${wdIcon('qr',14)}</button><button type="button" class="btn btn-sm" data-cancel-code="${r.id}">Anular</button>`:`<code class="wl-code-used">${esc(r.code)}</code>`}</div>`; }).join(''):'<p class="acc-empty">Cuando canjees puntos por una ventaja, su código aparecerá aquí para enseñarlo en el centro.</p>'}</section>
        <section class="acc-card"><div class="acc-card-head"><h2>Cómo funcionan</h2></div><ol class="wl-steps"><li><b>Ganas puntos</b><span>Al completar tu perfil, registrar inmersiones, completar reservas y hacer check-in en centros. Algunos centros te regalan puntos.</span></li><li><b>Eliges una ventaja</b><span>Cada centro decide qué ofrece y lo paga él.</span></li><li><b>Enseñas el código</b><span>El centro lo valida en su panel. Si no lo usas, puedes anularlo y recuperas los puntos.</span></li></ol><a href="#/como-funcionan-los-puntos">Más información sobre los puntos</a></section>
      </aside></div>`));
    fillAccountLevel();
    $$('[data-qr]').forEach(b=>b.onclick=()=>{ wdOpenModal({id:'code-qr',size:'sm',title:b.dataset.code,subtitle:'Enséñalo en el centro para que lo valide.',body:`<div class="code-qr"><img src="/api/points/codes/${b.dataset.qr}/qr.svg" alt="QR del código ${escapeHtml(b.dataset.code)}" width="220" height="220"><code>${escapeHtml(b.dataset.code)}</code></div>`,footer:'<button type="button" class="btn" data-modal-close>Cerrar</button>'}); });
    $$('[data-cancel-code]').forEach(b=>b.onclick=async()=>{ if(!confirm('¿Anular este código? Recuperas los puntos y el código deja de valer.')) return; try{ await postJSON('/api/points/codes/cancel',{id:+b.dataset.cancelCode}); toast('Código anulado. Has recuperado los puntos.'); renderMyPoints(); }catch(e){ toast(e.message); } });
  }
  function renderPointsInfo(){
    setApp(`<section class="page legal-page"><article class="legal-doc"><p class="eyebrow">WORLDIVES DISCOVERY</p><h1>Cómo funcionan los puntos</h1>
      <p class="lead">Los puntos premian que buceas. No son dinero y no cuestan dinero.</p>
      <h2>Cómo se consiguen</h2><ul><li>Completar los datos esenciales de tu perfil de buceador.</li><li>Registrar inmersiones en tu Log Book (y al llegar a 1, 5, 10, 25, 50 y 100 inmersiones).</li><li>Completar una reserva con un centro.</li><li>Hacer check-in con el QR de un centro (una vez por centro).</li><li>Algunos centros te conceden puntos como agradecimiento, con un límite al mes.</li></ul>
      <h2>Para qué sirven</h2><p>Para canjearlos por <b>ventajas que ofrece y paga cada centro</b>: un descuento, una inmersión, un regalo… Cada ventaja dice lo que cuesta en puntos y sus condiciones. Al canjear recibes un código que enseñas en el centro; el centro lo valida en su panel.</p>
      <h2>Lo que no se puede hacer</h2><ul><li>Comprar o recargar puntos con dinero.</li><li>Pasar puntos a otra persona.</li><li>Cambiar puntos por dinero o usarlos para pagar una reserva online.</li></ul>
      <h2>Códigos</h2><p>Un código vale durante un tiempo limitado. Si no lo usas, puedes anularlo y recuperas los puntos; si caduca sin usar, también los recuperas.</p>
      <h2>Del monedero a los puntos</h2><p>Antes había un «monedero» con saldo en euros. Ese saldo se ha convertido en puntos a razón de 1 € = 1 punto, redondeando hacia arriba, y su historial se conserva en «Mis puntos».</p>
      <p><a class="btn btn-primary" href="#/mis-puntos">Ver mis puntos</a> <a class="btn" href="#/recompensas">Ver ventajas</a></p></article></section>`);
  }
  // Centre panel: its advantages, validating codes at the desk and granting points to its clients.
  async function renderRewardsManager(mountId,{isAdmin=false,centers=[],centerId=null}={}){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml; const refresh=()=>renderRewardsManager(mountId,{isAdmin,centers,centerId});
    const [offers,codes,clients]=await Promise.all([api('/api/provider/reward-offers').then(r=>r.items||[]).catch(()=>[]),isAdmin?[]:api('/api/center/redemptions').then(r=>r.items||[]).catch(()=>[]),isAdmin?[]:api('/api/center/clients').then(r=>r.items||[]).catch(()=>[])]);
    const cs=isAdmin?centers.filter(c=>c.active!==0):[];
    mount.innerHTML=`<section class="rw-manager">
      <div class="svc-head"><div><p class="eyebrow">PUNTOS WORLDIVES</p><h2>${isAdmin?'Ventajas de los centros':'Ventajas y puntos'}</h2><p>Los buceadores canjean sus puntos por las ventajas que tu centro define y paga. Los puntos no son dinero: WORLDIVES no los vende ni financia las ventajas.</p></div></div>
      ${isAdmin?'':`<div class="cb-grid-2"><section class="cb-panel"><div class="cb-panel-head"><div><h3>${wdIcon('qr',17)} Validar un código</h3><p>Escanea el QR del cliente o escribe el código.</p></div></div>
          <form id="rw-validate" class="rw-validate"><input id="rw-code" placeholder="WOD-XXXXXXXX" autocomplete="off" autocapitalize="characters"><button type="button" class="btn" id="rw-scan">${wdIcon('qr',15)} Escanear</button><button class="btn btn-primary">Comprobar</button></form>
          <video id="rw-video" playsinline muted hidden></video><div id="rw-result"></div></section>
        <section class="cb-panel"><div class="cb-panel-head"><div><h3>${wdIcon('gift',17)} Conceder puntos</h3><p>A clientes con una reserva o un check-in en tu centro. Hay un límite de puntos al mes por cliente.</p></div></div>
          <form id="rw-grant" class="form-grid"><div class="field full"><label for="rw-client">Cliente</label><select id="rw-client">${clients.filter(c=>c.user_id||c.id).map(c=>`<option value="${c.user_id||c.id}">${esc(c.fullname||c.name||'Cliente')}${c.email&&!String(c.email).endsWith('.local')?' · '+esc(c.email):''}</option>`).join('')||'<option value="">Todavía no tienes clientes</option>'}</select></div>
            <div class="field"><label for="rw-points">Puntos</label><input id="rw-points" type="number" min="1" step="1" value="20"></div><div class="field"><label for="rw-reason">Motivo</label><input id="rw-reason" maxlength="200" placeholder="Gracias por tu quinta inmersión"></div>
            <div class="form-actions full"><button class="btn btn-primary">Conceder</button></div></form></section></div>`}
      <section class="cb-panel"><div class="cb-panel-head"><div><h3>${isAdmin?'Ventajas configuradas':'Tus ventajas'}</h3></div><button type="button" class="btn btn-primary" id="rw-new">+ Nueva ventaja</button></div>
        <div class="table-wrap"><table><thead><tr><th>Ventaja</th>${isAdmin?'<th>Centro</th>':''}<th>Tipo</th><th>Coste</th><th>Stock</th><th>Estado</th><th></th></tr></thead><tbody>${offers.map(o=>`<tr><td><strong>${esc(o.title)}</strong><br><small>${esc(o.value_text||'')}</small></td>${isAdmin?`<td>${esc(o.center_name||'—')}</td>`:''}<td>${esc(REWARD_TYPES[o.reward_type]||REWARD_TYPES.gift)}</td><td>${wdPts(o.cost_points)}</td><td>${o.stock==null?'Sin límite':o.stock}</td><td>${o.active&&o.center_id?'Activa':'Pausada'}</td><td>${o.center_id?`<button type="button" class="btn" data-edit-offer="${o.id}">Editar</button>`:''}</td></tr>`).join('')||`<tr><td colspan="${isAdmin?7:6}">Todavía no hay ventajas.</td></tr>`}</tbody></table></div></section>
      ${isAdmin?'':`<section class="cb-panel"><div class="cb-panel-head"><div><h3>Códigos canjeados</h3></div></div>${codes.length?`<div class="table-wrap"><table><thead><tr><th>Código</th><th>Cliente</th><th>Ventaja</th><th>Estado</th><th>Fecha</th></tr></thead><tbody>${codes.map(r=>{ const st=CODE_STATE[r.status]||[r.status,'muted']; return `<tr><td><code>${esc(r.code)}</code></td><td>${esc(r.customer||'')}</td><td>${esc(r.title)}</td><td><span class="status ${st[1]}">${esc(st[0])}</span></td><td>${esc(fmtDate(r.redeemed_at||r.created_at))}</td></tr>`; }).join('')}</tbody></table></div>`:'<p class="acc-empty">Cuando un cliente canjee una ventaja de tu centro, su código aparecerá aquí.</p>'}</section>`}</section>`;
    translateTree(mount);
    const openOffer=o=>{ o=o||{}; const {el,close}=wdOpenModal({id:'reward-offer',title:o.id?'Editar ventaja':'Nueva ventaja',subtitle:'La ventaja la ofrece y la paga tu centro.',
      body:`<form id="ro-form" class="form-grid">${isAdmin?`<div class="field full"><label for="ro-center">Centro</label><select id="ro-center">${cs.map(c=>`<option value="${c.id}" ${String(c.id)===String(o.center_id)?'selected':''}>${esc(c.name)}</option>`).join('')}</select></div>`:''}
        <div class="field full"><label for="ro-title">Nombre</label><input id="ro-title" maxlength="180" required value="${esc(o.title||'')}" placeholder="10 % de descuento en tu próxima inmersión"></div>
        <div class="field"><label for="ro-type">Tipo</label><select id="ro-type">${Object.entries(REWARD_TYPES).map(([k,l])=>`<option value="${k}" ${o.reward_type===k?'selected':''}>${l}</option>`).join('')}</select></div>
        <div class="field"><label for="ro-cost">Coste en puntos</label><input id="ro-cost" type="number" min="1" step="1" required value="${o.cost_points||''}"></div>
        <div class="field"><label for="ro-value">Lo que recibe el cliente</label><input id="ro-value" maxlength="180" value="${esc(o.value_text||'')}" placeholder="10 % de descuento"></div>
        <div class="field"><label for="ro-stock">Unidades disponibles</label><input id="ro-stock" type="number" min="0" value="${o.stock??''}" placeholder="Sin límite"></div>
        <div class="field full"><label for="ro-description">Descripción</label><textarea id="ro-description" rows="2">${esc(o.description||'')}</textarea></div>
        <div class="field full"><label for="ro-conditions">Condiciones</label><textarea id="ro-conditions" rows="2" placeholder="Solo de lunes a viernes, sujeto a disponibilidad…">${esc(o.conditions||'')}</textarea></div>
        ${o.id?`<label class="svc-check full"><input type="checkbox" id="ro-active" ${o.active?'checked':''}><span><strong>Activa</strong><small>Los buceadores pueden canjearla.</small></span></label>`:''}</form>`,
      footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="ro-save">Guardar</button>'});
      $('#ro-save',el).onclick=async()=>{ try{ await postJSON('/api/provider/reward-offers',{id:o.id||0,center_id:isAdmin?+$('#ro-center',el).value:centerId,title:$('#ro-title',el).value,reward_type:$('#ro-type',el).value,cost_points:$('#ro-cost',el).value,value_text:$('#ro-value',el).value,stock:$('#ro-stock',el).value,description:$('#ro-description',el).value,conditions:$('#ro-conditions',el).value,active:o.id?$('#ro-active',el).checked:true}); close(); toast('Ventaja guardada.'); refresh(); }catch(err){ toast(err.message); } }; };
    $('#rw-new',mount).onclick=()=>openOffer();
    $$('[data-edit-offer]',mount).forEach(b=>b.onclick=()=>openOffer(offers.find(o=>String(o.id)===b.dataset.editOffer)));
    if(isAdmin) return;
    const show=async code=>{ const box=$('#rw-result',mount); code=String(code||'').trim().toUpperCase(); if(!code) return;
      try{ const r=(await api('/api/center/redemptions?code='+encodeURIComponent(code))).item; const st=CODE_STATE[r.status]||[r.status,'muted'];
        box.innerHTML=`<div class="rw-check ${r.status==='issued'?'is-ok':'is-bad'}"><strong>${esc(r.title)}</strong><small>${esc(r.customer||'')} · ${wdPts(r.cost_points)} · <span class="status ${st[1]}">${esc(st[0])}</span>${r.status==='issued'&&r.expires_at?` · válido hasta el ${esc(fmtDate(r.expires_at))}`:''}</small>${r.value_text?`<p>${esc(r.value_text)}</p>`:''}${r.conditions?`<small>${esc(r.conditions)}</small>`:''}${r.status==='issued'?`<button type="button" class="btn btn-primary" id="rw-ok">Validar y dar la ventaja</button>`:''}</div>`;
        translateTree(box);
        $('#rw-ok',box)?.addEventListener('click',async()=>{ try{ await postJSON('/api/center/redemptions/validate',{code}); toast('Código validado. Ya no se puede volver a usar.'); refresh(); }catch(e){ toast(e.message); } });
      }catch(e){ box.innerHTML=`<div class="rw-check is-bad"><strong>${esc(e.message)}</strong></div>`; } };
    $('#rw-validate',mount).onsubmit=e=>{ e.preventDefault(); show($('#rw-code',mount).value); };
    $('#rw-scan',mount).onclick=async()=>{ const v=$('#rw-video',mount);
      if(!('BarcodeDetector' in window)||!navigator.mediaDevices?.getUserMedia){ toast('Este navegador no puede escanear: escribe el código.'); $('#rw-code',mount).focus(); return; }
      try{ const det=new BarcodeDetector({formats:['qr_code']}); const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}}); v.srcObject=stream; v.hidden=false; await v.play();
        const stop=()=>{ stream.getTracks().forEach(t=>t.stop()); v.hidden=true; };
        const tick=async()=>{ if(v.hidden) return; try{ const f=await det.detect(v); if(f[0]){ stop(); $('#rw-code',mount).value=f[0].rawValue; show(f[0].rawValue); return; } }catch{} requestAnimationFrame(tick); }; tick();
        setTimeout(stop,30000);
      }catch(e){ toast('No se ha podido abrir la cámara: escribe el código.'); } };
    $('#rw-grant',mount).onsubmit=async e=>{ e.preventDefault(); const uid=+$('#rw-client',mount).value; if(!uid){ toast('Elige un cliente.'); return; }
      try{ const r=await postJSON('/api/provider/points-grant',{user_id:uid,points:$('#rw-points',mount).value,reason:$('#rw-reason',mount).value}); toast(`Puntos concedidos. Este mes puedes darle ${r.left_this_month} más.`); $('#rw-reason',mount).value=''; }catch(err){ toast(err.message); } };
  }
  // Repeated achievements («Inmersión registrada» ×40) are shown once with their count and total.
  function groupRewards(items){ const m=new Map(); items.forEach(x=>{ const g=m.get(x.title)||{title:x.title,description:x.description,n:0,points:0,wallet:0,last:''}; g.n++; g.points+=Number(x.points||0); g.wallet+=Number(x.wallet_amount||0); if(String(x.created_at||'')>g.last) g.last=x.created_at||''; m.set(x.title,g); }); return [...m.values()].sort((a,b)=>String(b.last).localeCompare(String(a.last))); }
  async function renderRewards(){
    if(!state.me){goLogin();return;} const esc=escapeHtml;
    const [d,promos]=await Promise.all([api('/api/rewards'),api('/api/my/promotions').catch(()=>({items:[]}))]);
    const lvl=d.level; const progress=lvl.next_threshold?Math.min(100,Math.round(((d.points-lvl.threshold)/(lvl.next_threshold-lvl.threshold))*100)):100;
    const order={active:0,upcoming:1,used:2,expired:3,ended:4,revoked:5}; const myPromos=(promos.items||[]).sort((a,b)=>(order[a.state]??9)-(order[b.state]??9));
    const livePromos=myPromos.filter(p=>p.state==='active').length;
    setApp(accountShell('recompensas',{eyebrow:'MI ACTIVIDAD',title:'Recompensas',lead:'Tu progreso crece solo mientras buceas y reservas. Aquí tienes también las promociones que te regalan los centros.'},`
      <section class="rw-level"><div class="rw-level-main"><span class="rw-badge">${wdIcon('star',26)}</span><div><span>Nivel actual</span><strong>${esc(lvl.name)}</strong><small>${Number(d.points).toLocaleString(wdLocale())} puntos conseguidos</small></div></div>
        <div class="rw-progress"><div class="rw-progress-top"><span>${lvl.next_name?`Siguiente: <b>${esc(lvl.next_name)}</b>`:'Has alcanzado el nivel máximo'}</span><span>${lvl.next_threshold?`${d.points} / ${lvl.next_threshold}`:''}</span></div><div class="acc-bar is-light"><i style="width:${progress}%"></i></div>${lvl.next_threshold?`<small>Te faltan ${lvl.next_threshold-d.points} puntos.</small>`:''}</div>
        <div class="rw-stats"><div><b>${d.stats.dives}</b><span>inmersiones</span></div><div><b>${Number(d.balance||0).toLocaleString(wdLocale())}</b><span>puntos disponibles</span></div><div><b>${livePromos}</b><span>promociones activas</span></div></div></section>
      <section class="acc-card" id="mis-promociones"><div class="acc-card-head"><h2>${wdIcon('qr',18)} Mis promociones</h2>${myPromos.length?`<small class="acc-help">Toca una para ver su QR en grande</small>`:''}</div>
        ${myPromos.length?`<div class="rw-promos">${myPromos.map(p=>promoTicket(p)).join('')}</div>`:'<p class="acc-empty">Cuando un centro te regale una promoción (por ejemplo, un curso con equipo incluido), aparecerá aquí con tu QR personal.</p>'}</section>
      <section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('gift',18)} Ventajas de los centros</h2><span class="acc-help">Tienes <b>${wdPts(d.balance)}</b> · <a href="#/como-funcionan-los-puntos">Cómo funcionan</a></span></div>
        ${d.offers.length?`<div class="rw-offers">${d.offers.map(o=>{ const cost=Number(o.cost_points), short=Math.max(0,cost-Number(d.balance||0)); return `<article class="rw-offer"><span class="rw-offer-from">${esc(o.center_name||'')}${o.center_city?' · '+esc(o.center_city):''}</span><h3>${esc(o.title)}</h3>${o.value_text?`<p class="pr-value">${esc(o.value_text)}</p>`:''}<p>${esc(o.description||'')}</p>${o.conditions?`<small>${esc(o.conditions)}</small>`:''}<div class="rw-offer-foot"><b>${wdPts(cost)}</b><button class="btn btn-primary redeem-reward" data-id="${o.id}" ${short>0?'disabled':''}>Canjear</button></div>${short>0?`<small class="rw-short">Te faltan ${wdPts(short)}</small>`:''}<small class="rw-paid">Ventaja ofrecida y pagada por el centro.</small></article>`; }).join('')}</div>`:'<p class="acc-empty">Todavía no hay ventajas disponibles.</p>'}</section>
      <section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('star',18)} Lo que ya has conseguido</h2></div>
        ${d.items.length?`<div class="rw-log">${groupRewards(d.items).map(x=>`<div class="rw-log-row"><span class="rw-dot">${wdIcon('check',13)}</span><span><strong>${esc(x.title)}${x.n>1?` <em class="rw-times">×${x.n}</em>`:''}</strong><small>${esc(x.description||'')}${x.last?` · ${x.n>1?'última vez ':''}${fmtDate(x.last)}`:''}</small></span><b>+${x.points} pts</b></div>`).join('')}</div>`:'<p class="acc-empty">Tu primer logro aparecerá automáticamente cuando completes una acción.</p>'}</section>`));
    fillAccountLevel(d); if(location.hash.includes('promociones')) setTimeout(()=>$('#mis-promociones')?.scrollIntoView({behavior:'smooth'}),200);
    $$('.redeem-reward').forEach(b=>b.onclick=async()=>{ if(!confirm('¿Canjear tus puntos por esta ventaja?')) return; try{const r=await postJSON('/api/rewards/redeem',{offer_id:+b.dataset.id});toast('Canje hecho. Tu código: '+r.code+' (lo tienes en «Mis puntos»).');renderRewards();}catch(e){toast(e.message)}});
  }
  async function renderFreelancePanel(d){
    const u=d.user||{}, esc=escapeHtml; state.me=d;
    const tabs=[['dashboard','⌂','Resumen'],['bookings','☰','Reservas'],['planning','▦','Planning / agenda'],['services','◈','Servicios y tarifas'],['experiences','✈','Experiencias y solicitudes'],['payments','€','Cobros y pagos'],['profile','✦','Perfil público'],
      ['requests','✉','Solicitudes de información'],['stats','◑','Estadísticas'],['tools','⇩','Herramientas'],['fiscal','§','Datos fiscales y seguro'],['plan','◆','Mi plan']];
    setApp(`<section class="center-backoffice fl-office">
      <div class="cb-header"><div class="cb-header-id">${u.avatar_url?`<img class="center-logo fl-avatar" src="${esc(u.avatar_url)}" alt="">`:`<span class="acc-avatar fl-avatar-txt">${esc(initials(u.fullname||''))}</span>`}<div><p class="eyebrow">Panel del profesional</p><h1>${esc(u.fullname||'Profesional')}</h1><p>Instructor / guía freelance · tus salidas, experiencias y ficha pública en un solo panel.</p></div></div>
        <div class="cb-header-actions"><a class="btn" href="#/profesional?id=${u.id}">${wdIcon('eye',15)} Ver mi ficha pública</a><a class="btn" href="#/cuenta">${wdIcon('user',15)} Mi cuenta</a></div></div>
      <div class="cb-layout"><aside class="cb-sidebar"><div class="cb-section-title">MI ACTIVIDAD</div>${tabs.map(([k,ic,l])=>`<button class="cb-nav" data-cbtab="${k}">${ic} <span>${l}</span>${k==='experiences'?'<b id="fl-req-badge" hidden></b>':k==='bookings'?'<b id="fl-bk-badge" hidden></b>':''}</button>`).join('')}
        <div class="cb-section-title">CUENTA</div><a class="cb-nav" href="#/logbook">${wdIcon('book',15)} <span>Log Book</span></a><a class="cb-nav" href="#/cuenta">${wdIcon('user',15)} <span>Mi cuenta</span></a></aside>
      <main class="cb-main"><div id="cb-content"></div></main></div></section>`); proTermsBanner(d.user);
    const content=$('#cb-content'), nav=$$('.cb-nav[data-cbtab]');
    const goServices=()=>load('services');
    api('/api/center/requests').then(r=>{ const bd=$('#fl-bk-badge'); const n=(r.count||0)+(r.pending_refunds||0); if(bd&&n){ bd.hidden=false; bd.textContent=n; } }).catch(()=>{});
    let expData=null; const loadExp=async()=>{ try{ expData=await api('/api/provider/experiences'); }catch{ expData={items:[],requests:[]}; } const n=(expData.requests||[]).filter(r=>r.status==='requested').length; const b=$('#fl-req-badge'); if(b){ b.hidden=!n; b.textContent=n; } return expData; };
    async function load(tab){
      nav.forEach(n=>n.classList.toggle('active',n.dataset.cbtab===tab));
      try{ history.replaceState(null,'','#/admin?tab='+tab); }catch{}
      if(tab==='planning'){ content.innerHTML='<div id="fl-planning"></div>'; await renderCenterPlanning('fl-planning',{center:{name:u.fullname,city:'',cover_url:''},canBook:false,onManage:goServices}); }
      else if(tab==='services'){ content.innerHTML='<div id="freelance-services-manager"></div>'; await renderProviderServicesManager(u.id,'freelance','freelance-services-manager'); }
      else if(tab==='experiences'){ content.innerHTML='<div id="freelance-experiences"></div>'; await renderProviderExperiences('freelance-experiences','freelance',{goServices}); loadExp(); }
      else if(tab==='bookings'){ content.innerHTML='<div id="fl-bookings"></div>'; await renderCenterBookings('fl-bookings',{freelance:true}); }
      else if(tab==='payments'){ content.innerHTML='<div id="fl-payments"></div>'; await renderProviderPayments('fl-payments'); }
      else if(tab==='requests'){ content.innerHTML='<div id="fl-requests"></div>'; await renderInfoRequests('fl-requests'); }
      else if(tab==='stats'){ content.innerHTML='<div id="fl-stats"></div>'; await renderProviderStats('fl-stats'); }
      else if(tab==='tools'){ content.innerHTML='<div id="fl-tools"></div>'; await renderProviderTools('fl-tools',false); }
      else if(tab==='fiscal'){ content.innerHTML='<div id="fl-fiscal"></div>'; await renderFiscalCard('fl-fiscal'); }
      else if(tab==='plan'){ content.innerHTML='<div id="fl-plan"></div>'; await renderMyPlan('fl-plan'); }
      else if(tab==='profile') renderFreelanceProfile();
      else await renderFreelanceDashboard();
    }
    async function renderFreelanceDashboard(){
      content.innerHTML='<p class="wd-loading">Cargando…</p>';
      const month=wdToday().slice(0,7);
      const [svc,plan,exp]=await Promise.all([api('/api/provider-services?provider_id='+u.id).catch(()=>({items:[]})),api('/api/center/planning?month='+month).catch(()=>({slots:[]})),loadExp()]);
      const services=(svc.items||[]).filter(s=>s.active!==0&&s.active!==false), today=wdToday();
      const slots=(plan.slots||[]).filter(s=>s.slot_date>=today).sort((a,b)=>(a.slot_date+a.slot_time).localeCompare(b.slot_date+b.slot_time));
      const reqs=(exp.requests||[]).filter(r=>r.status==='requested'), exps=exp.items||[];
      const checks=[['Presentación',(u.provider_bio||'').length>=60],['Foto profesional',!!u.avatar_url],['Redes sociales',!!(u.instagram_url||u.facebook_url||u.youtube_url||u.tiktok_url||u.twitter_url)],['Un servicio activo',services.length>0],['Salidas programadas',slots.length>0]];
      const pct=Math.round(checks.filter(c=>c[1]).length*100/checks.length);
      content.innerHTML=`<div class="cb-welcome"><div><p class="eyebrow">${esc(wdLongDay(today))}</p><h2>Hola, <span translate="no">${esc((u.fullname||'').split(' ')[0])}</span></h2><p>${reqs.length?`Tienes <b>${reqs.length}</b> solicitud${reqs.length>1?'es':''} esperando respuesta.`:slots.length?`Tu próxima salida es el ${esc(wdLongDay(slots[0].slot_date))} a las ${esc(slots[0].slot_time)}.`:'Programa tus próximas salidas para que los buceadores puedan encontrarte.'}</p></div>
          <div class="cb-quick"><button type="button" class="btn btn-primary" data-go="services">${wdIcon('plus',15)} Nuevo servicio</button><button type="button" class="btn" data-go="planning">Ver planning</button></div></div>
        <div class="acc-kpis">${accKpi('salida',services.length,'servicios activos')}${accKpi('calendar',slots.length,'salidas este mes')}${accKpi('inbox',reqs.length,'solicitudes pendientes',null,reqs.length>0)}${accKpi('viaje',exps.length,'experiencias')}</div>
        <div class="acc-grid"><div class="acc-col">
          <section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('calendar',18)} Próximas salidas</h2><button type="button" class="cb-link" data-go="planning">Planning completo</button></div>
            ${slots.length?`<div class="acc-list">${slots.slice(0,6).map(s=>`<div class="acc-row">${accDate(s.slot_date)}<span class="acc-row-main"><strong>${esc(s.service_title)}</strong><small>${esc(s.slot_time)} · ${s.taken||0}/${s.spots_total} plazas ocupadas</small></span><span class="acc-row-tags"><span class="status ${s.status==='full'?'warn':'good'}">${s.status==='full'?'Completa':'Abierta'}</span></span></div>`).join('')}</div>`:`<p class="acc-empty">No tienes salidas este mes.</p><button type="button" class="btn" data-go="services">Programar salidas</button>`}</section>
          <section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('inbox',18)} Solicitudes de experiencias</h2><button type="button" class="cb-link" data-go="experiences">Gestionar</button></div>
            ${reqs.length?`<div class="acc-list">${reqs.slice(0,6).map(r=>`<div class="acc-row">${accDate(r.departure_date||r.start_date||r.created_at?.slice(0,10))}<span class="acc-row-main"><strong>${esc(r.fullname||r.customer_name||'Buceador')}</strong><small>${esc(r.title||r.experience_title||'Experiencia')} · ${r.participants||1} pers.</small></span><span class="acc-row-tags"><span class="status warn">Pendiente</span></span></div>`).join('')}</div>`:'<p class="acc-empty">No hay solicitudes pendientes.</p>'}</section></div>
        <aside class="acc-col"><section class="acc-card acc-profile"><div class="acc-card-head"><h2>Tu ficha pública</h2><b>${pct}%</b></div><div class="acc-bar"><i style="width:${pct}%"></i></div>
            <ul class="fl-checks">${checks.map(c=>`<li class="${c[1]?'is-ok':''}">${wdIcon(c[1]?'check':'plus',14)} ${esc(c[0])}</li>`).join('')}</ul><button type="button" class="btn ${pct<100?'btn-primary':''}" data-go="profile">${pct<100?'Completar mi ficha':'Editar mi ficha'}</button></section>
          <section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('megaphone',18)} Consejo</h2></div><p class="acc-help">Las fichas con foto, presentación y salidas programadas reciben muchas más solicitudes. Comparte el enlace de tu ficha en tus redes.</p>
            <button type="button" class="btn" id="fl-share">${wdIcon('receipt',15)} Copiar enlace de mi ficha</button></section></aside></div>`;
      $$('[data-go]',content).forEach(b=>b.onclick=()=>load(b.dataset.go));
      $('#fl-share').onclick=()=>navigator.clipboard?.writeText(`${location.origin}/#/profesional?id=${u.id}`).then(()=>toast('Enlace copiado.')).catch(()=>{});
    }
    function renderFreelanceProfile(){
      const socials=[['instagram_url','Instagram','https://instagram.com/…'],['facebook_url','Facebook','https://facebook.com/…'],['youtube_url','YouTube','https://youtube.com/…'],['tiktok_url','TikTok','https://tiktok.com/@…'],['twitter_url','X / Twitter','https://x.com/…']];
      content.innerHTML=`<div class="cb-module"><div class="cb-module-head"><div><p class="eyebrow">PERFIL PÚBLICO</p><h2>Tu ficha de profesional</h2><p>Es lo que ve un buceador al pulsar tu nombre en una experiencia o servicio.</p></div><a class="btn" href="#/profesional?id=${u.id}">${wdIcon('eye',15)} Ver cómo queda</a></div>
        <form id="freelance-profile-form" class="fl-profile"><div class="fl-photo">${u.avatar_url?`<img src="${esc(u.avatar_url)}" alt="" id="fp-preview">`:`<span class="fl-photo-empty" id="fp-preview">${esc(initials(u.fullname||''))}</span>`}<label class="btn">${wdIcon('image',15)} ${u.avatar_url?'Cambiar foto':'Subir foto'}<input id="fp-photo" type="file" accept=".jpg,.jpeg,.png,.webp" hidden></label><small>Foto de cara, con buena luz. JPG, PNG o WEBP.</small></div>
          <div class="form-grid"><div class="field full"><label for="fp-bio">Presentación profesional</label><textarea id="fp-bio" rows="7" maxlength="3000" placeholder="Quién eres, tus titulaciones, idiomas, zonas donde guías y qué tipo de buceo te apasiona…">${esc(u.provider_bio||'')}</textarea><small id="fp-count"></small></div>
            ${socials.map(([k,l,ph])=>`<div class="field"><label for="fp-${k}">${l}</label><input id="fp-${k}" type="url" value="${esc(u[k]||'')}" placeholder="${ph}"></div>`).join('')}</div>
          <div class="form-actions"><button class="btn btn-primary" type="submit">Guardar mi ficha pública</button></div></form></div>`;
      const bio=$('#fp-bio'), cnt=()=>{ $('#fp-count').textContent=`${bio.value.length} / 3000 caracteres${bio.value.length<60?' · escribe al menos 60 para una buena presentación':''}`; }; bio.oninput=cnt; cnt();
      $('#fp-photo').onchange=e=>{ const f=e.target.files[0]; if(!f) return; const url=URL.createObjectURL(f); $('#fp-preview').outerHTML=`<img src="${url}" alt="" id="fp-preview">`; };
      $('#freelance-profile-form').onsubmit=async e=>{ e.preventDefault(); const btn=e.target.querySelector('[type=submit]'); btn.disabled=true;
        try{ await postJSON('/api/provider/profile',Object.fromEntries([['provider_bio',bio.value],...socials.map(([k])=>[k,$('#fp-'+k).value])]));
          if($('#fp-photo').files[0]){ const fd=new FormData(); fd.append('file',$('#fp-photo').files[0]); await api('/api/provider/avatar',{method:'POST',body:fd}); }
          toast('Ficha pública guardada.'); const fresh=await api('/api/me'); Object.assign(u,fresh.user); state.me=fresh; renderFreelanceProfile(); }catch(err){ toast(err.message); btn.disabled=false; } };
    }
    nav.forEach(n=>n.onclick=()=>load(n.dataset.cbtab));
    const req=new URLSearchParams(location.hash.split('?')[1]||'').get('tab');
    loadExp(); load(tabs.some(t=>t[0]===req)?req:'dashboard');
  }

  // «Cobros y pagos» of a provider: a centre, or a freelance professional without a centre (v50.34, Fase 2).
  // Direct charges: the money goes from the diver to the provider's own Stripe account. WORLDIVES takes no commission.
  const PAY_ORDER_STATE={paid:['Cobrado','good'],pending:['En curso','warn'],review:['En revisión','bad'],refund_due:['Devolución pendiente','bad'],partially_refunded:['Devolución parcial','warn'],refunded:['Devuelto','muted'],expired:['Caducado','muted'],cancelled:['Cancelado','muted'],failed:['Fallido','bad']};
  function wdPolicyText(h,p){ h=Number(h||0); p=Number(p||0); const when=h>=48&&h%24===0?`${h/24} días`:`${h} horas`;
    if(!h&&!p) return 'Sin cancelación gratuita: no hay reembolso al cancelar.'; if(!h) return `Al cancelar se devuelve el ${p} % de lo pagado.`;
    return `Cancelación gratuita hasta ${when} antes de la actividad; ${p===0?'después no hay reembolso.':p<100?`después se devuelve el ${p} % de lo pagado.`:'después también se devuelve todo.'}`; }
  async function renderCenterPayments(centerId,mountId){ return renderProviderPayments(mountId,centerId); }
  async function renderProviderPayments(mountId,centerId){
    const mount=document.getElementById(mountId); if(!mount)return; const esc=escapeHtml; const q=centerId&&state.me?.user?.role==='admin'?`?center_id=${centerId}`:'';
    const body=q?{center_id:centerId}:{};
    try{
      const qs=new URLSearchParams(location.hash.split('?')[1]||'');
      if(qs.get('stripe')==='return'||qs.get('stripe')==='refresh'){ try{ await postJSON('/api/payments/connect/sync',body); }catch(e){} }
      const [st,d]=await Promise.all([api('/api/payments/connect-status'+q),api('/api/provider/payments'+q)]);
      const pf=d.profile||{}; const freelance=pf.type==='freelance';
      const status=st.ready?'<span class="status good">● Cobros activos</span>':st.configured?'<span class="status warn">● Configuración pendiente</span>':'<span class="status warn">● Cobros sin configurar</span>';
      const income=(d.income||[]);
      mount.innerHTML=`<section class="pay-module">
        <div class="svc-head"><div><p class="eyebrow">COBROS Y PAGOS</p><h2>${freelance?'Tus cobros':'Cobros del centro'}</h2>
          <p>El cliente paga en una página segura de Stripe y el dinero va <strong>directamente a tu cuenta de Stripe</strong>. WORLDIVES no cobra comisión por las reservas ni guarda datos de tarjetas. Las comisiones de Stripe por cada cobro las paga tu cuenta.</p></div>${status}</div>
        ${st.platform_ready===false?'<div class="notice warn"><strong>Cobros online pendientes en WORLDIVES</strong><p>El administrador todavía no ha configurado la conexión con Stripe en el servidor.</p></div>':''}
        <div class="acc-kpis">${income.length?income.map(x=>accKpi('chart',wdMoney(x.net,x.currency),`Ingresos (${x.currency}) · ${x.n} ${x.n===1?'pago':'pagos'}${x.refunded?` · ${wdMoney(x.refunded,x.currency)} devueltos`:''}`)).join(''):accKpi('chart',wdMoney(0,'EUR'),'Ingresos online')}${accKpi('alert',(d.pending_refunds||[]).length,'devoluciones pendientes',null,(d.pending_refunds||[]).length>0)}</div>
        <div class="form-actions">
          ${st.ready?`<button class="btn btn-primary" id="stripe-dashboard">${wdIcon('chart',15)} Abrir mi panel de Stripe</button>`:`<button class="btn btn-primary" id="stripe-onboard">${st.configured?'Continuar la configuración en Stripe':'Activar los cobros online'}</button>`}
          ${st.configured?'<button class="btn" id="stripe-sync">Actualizar estado</button>':''}
        </div>
        <div class="notice"><strong>Cómo funciona</strong><p>Tu cuenta de Stripe es tuya: tienes su panel completo, recibes los pagos en tu banco según su calendario y gestionas desde allí las disputas. Las devoluciones puedes hacerlas desde cada reserva (botón «Devolver») o desde Stripe; las dos quedan registradas aquí.</p></div>
        ${(d.pending_refunds||[]).length?`<section class="cb-panel"><div class="cb-panel-head"><div><h3>${wdIcon('alert',17)} Devoluciones pendientes</h3><p>Clientes que cancelaron una reserva pagada. Según tu política les corresponde este importe.</p></div></div>
          <div class="acc-list">${d.pending_refunds.map(r=>`<div class="acc-row">${accDate(r.booking_date)}<span class="acc-row-main"><strong>${esc(r.customer_name||'Cliente')} · ${wdMoney(r.refund_proposed,r.currency)}</strong><small>${esc(r.service_title||'Reserva')} · ${r.refund_status==='failed'?'la devolución automática falló':'propuesta '+esc(fmtDate(r.refund_proposed_at))}</small></span><a class="btn btn-primary" href="#/reserva?id=${r.id}">Devolver</a></div>`).join('')}</div></section>`:''}
        <section class="cb-panel"><div class="cb-panel-head"><div><h3>Datos del prestador del servicio</h3><p>Aparecen en el justificante de cada reserva como «Prestador del servicio». El justificante no es una factura: si tu actividad lo exige, la factura la emites tú.</p></div></div>
          <form id="pay-profile" class="form-grid"><div class="field"><label for="pp-legal">Razón social o nombre completo</label><input id="pp-legal" maxlength="160" value="${esc(pf.legal_name)}" placeholder="${esc(pf.name||'')}"></div>
            <div class="field"><label for="pp-tax">NIF / número fiscal</label><input id="pp-tax" maxlength="40" value="${esc(pf.tax_id)}" placeholder="B12345678"></div>
            <div class="field full"><label for="pp-addr">Dirección fiscal</label><input id="pp-addr" maxlength="300" value="${esc(pf.fiscal_address)}" placeholder="Calle, número, código postal, ciudad, país"></div>
            <div class="form-actions full"><button class="btn btn-primary" type="submit">Guardar datos</button></div></form></section>
        <div id="cancel-policy-card"></div>
        <section class="cb-panel"><div class="cb-panel-head"><div><h3>Últimas operaciones</h3></div></div>
        <div class="table-wrap"><table class="data-table"><thead><tr><th>Reserva</th><th>Cliente</th><th>Importe</th><th>Tipo</th><th>Estado</th><th>Fecha</th></tr></thead><tbody>
        ${(d.items||[]).length?d.items.map(r=>{ const s=PAY_ORDER_STATE[r.status]||[r.status,'muted']; return `<tr><td>${r.booking_id?`<a href="#/reserva?id=${r.booking_id}">WOD-${String(r.booking_id).padStart(6,'0')}</a>`:'#'+(r.experience_booking_id||r.id)}</td><td>${esc(r.customer_name||'')}</td><td>${wdMoney(r.amount_received??r.amount,r.currency)}${r.refunded_total>0?`<small> · ${wdMoney(r.refunded_total,r.currency)} devueltos</small>`:''}</td><td>${r.payment_kind==='deposit'?'Señal':'Total'}</td><td><span class="status ${s[1]}">${s[0]}</span>${r.incident?' <span class="status bad">Incidencia</span>':''}</td><td>${esc(fmtDate(r.created_at))}</td></tr>`; }).join(''):'<tr><td colspan="6">Todavía no hay operaciones de pago.</td></tr>'}
        </tbody></table></div></section></section>`;
      renderCancelPolicyCard(pf,$('#cancel-policy-card',mount));
      translateTree(mount);
      $('#pay-profile',mount).onsubmit=async e=>{ e.preventDefault(); try{ await postJSON('/api/provider/payment-profile',{legal_name:$('#pp-legal',mount).value,tax_id:$('#pp-tax',mount).value,fiscal_address:$('#pp-addr',mount).value}); toast('Datos guardados. Saldrán en los justificantes.'); }catch(err){ toast(err.message); } };
      $('#stripe-onboard',mount)?.addEventListener('click',async()=>{try{const r=await postJSON('/api/payments/connect/onboard',body);location.href=r.url;}catch(e){toast(e.message)}});
      $('#stripe-sync',mount)?.addEventListener('click',async()=>{try{await postJSON('/api/payments/connect/sync',body);toast('Estado actualizado.');renderProviderPayments(mountId,centerId);}catch(e){toast(e.message)}});
      $('#stripe-dashboard',mount)?.addEventListener('click',async()=>{try{const r=await postJSON('/api/payments/connect/login',body);window.open(r.url,'_blank','noopener');}catch(e){toast(e.message)}});
    }catch(err){mount.innerHTML=`<div class="empty"><h3>No se pudo cargar la sección de cobros</h3><p>${escapeHtml(err.message)}</p></div>`;}
  }
  // Cancellation policy (Fase 2.6): free until X hours before, then Y % refunded. Presets are shortcuts.
  async function renderCancelPolicyCard(pf,mount){
    if(!mount) return; const esc=escapeHtml;
    const presets=[[24,0,'Flexible','Gratis hasta 24 h antes'],[48,0,'Moderada','Gratis hasta 48 h antes'],[168,0,'Estricta','Gratis hasta 7 días antes']];
    mount.innerHTML=`<section class="cb-panel cxp-card"><div class="cb-panel-head"><div><h3>Política de cancelación</h3><p>Se muestra antes de reservar y se guarda con cada reserva. Si el cliente cancela una reserva pagada, te proponemos la devolución que le corresponde y la haces tú. Si cancelas tú, devuelves todo. Puedes fijar otra política en cada servicio.</p></div></div>
      <div class="cxp-opts">${presets.map(([h,p,l,s])=>`<button type="button" class="cxp-opt" data-h="${h}" data-p="${p}"><span><b>${l}</b><small>${s}</small></span></button>`).join('')}</div>
      <div class="form-grid"><div class="field"><label for="cxp-h">Cancelación gratuita hasta (horas antes)</label><input id="cxp-h" type="number" min="0" max="720" value="${Number(pf.cancel_free_hours??48)}"></div>
        <div class="field"><label for="cxp-p">Después se devuelve (%)</label><input id="cxp-p" type="number" min="0" max="100" value="${Number(pf.cancel_refund_pct??0)}"></div>
        <div class="field full"><label for="cxp-note">Nota para el cliente (opcional)</label><input id="cxp-note" maxlength="500" value="${esc(pf.cancellation_note||'')}" placeholder="Ej.: Si el mar no permite salir, te ofrecemos otra fecha o la devolución."></div></div>
      <p class="cxp-preview" id="cxp-preview"></p>
      <div class="form-actions"><button type="button" class="btn btn-primary" id="cxp-save">Guardar política</button><a class="btn" href="#/legal/condiciones-centros" target="_blank" rel="noopener">Condiciones para centros</a></div></section>`;
    const prev=()=>{ $('#cxp-preview',mount).textContent=wdPolicyText($('#cxp-h',mount).value,$('#cxp-p',mount).value); translateTree($('#cxp-preview',mount)); };
    $$('.cxp-opt',mount).forEach(b=>b.onclick=()=>{ $('#cxp-h',mount).value=b.dataset.h; $('#cxp-p',mount).value=b.dataset.p; prev(); });
    ['#cxp-h','#cxp-p'].forEach(s=>$(s,mount).oninput=prev); prev(); translateTree(mount);
    $('#cxp-save',mount).onclick=async()=>{ try{ await postJSON('/api/provider/cancellation-policy',{cancel_free_hours:$('#cxp-h',mount).value,cancel_refund_pct:$('#cxp-p',mount).value,note:$('#cxp-note',mount).value}); toast('Política de cancelación guardada. Se aplica a las reservas nuevas.'); }catch(err){ toast(err.message); } };
  }

  const SERVICE_COLOR_PALETTE = [
    {key:'ocean', label:'Azul océano', value:'#2563eb'},
    {key:'violet', label:'Violeta', value:'#7c3aed'},
    {key:'amber', label:'Ámbar', value:'#d97706'},
    {key:'emerald', label:'Esmeralda', value:'#059669'},
    {key:'rose', label:'Coral', value:'#e11d48'},
    {key:'cyan', label:'Turquesa', value:'#0891b2'},
    {key:'slate', label:'Pizarra', value:'#475569'},
    {key:'orange', label:'Naranja', value:'#ea580c'}
  ];
  const serviceColorOptions=(selected)=>SERVICE_COLOR_PALETTE.map(c=>`<option value="${c.value}" ${String(selected||'')===c.value?'selected':''}>${c.label}</option>`).join('');
  // Line icons (inline SVG) so the catalogue looks the same on every device, unlike emoji.
  const WD_ICON_PATHS={
    star:'<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    eye:'<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    plus:'<path d="M12 5v14M5 12h14"/>',
    shield:'<path d="M12 3 4 6v6c0 4.6 3.4 8.3 8 9 4.6-.7 8-4.4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    lock:'<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    check:'<path d="m5 12 5 5 9-10"/>',
    qr:'<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><path d="M14 14h2v2h-2zM18 18h2v2h-2zM14 18h2M18 14h2"/>',
    gift:'<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v8h14v-8M12 8v12M12 8S10.5 4 8 4a2 2 0 0 0 0 4M12 8s1.5-4 4-4a2 2 0 0 1 0 4"/>',
    wallet:'<path d="M4 7a2 2 0 0 1 2-2h12v4"/><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M16 13.5h2"/>',
    book:'<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h11"/>',
    user:'<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    receipt:'<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
    tag:'<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.5"/>',
    chart:'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    home:'<path d="m3 11 9-7 9 7"/><path d="M5 10v10h14V10"/>',
    message:'<path d="M4 5h16v11H8l-4 4z"/>',
    arrow:'<path d="M5 12h14M13 6l6 6-6 6"/>',
    alert:'<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17v.5"/>',
    info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    image:'<rect x="3" y="4" width="18" height="16" rx="2.5"/><circle cx="9" cy="10" r="1.8"/><path d="m21 16-5-5-8 9"/>',
    download:'<path d="M12 4v11"/><path d="m7 10 5 5 5-5"/><path d="M5 20h14"/>',
    megaphone:'<path d="M4 10v4a1 1 0 0 0 1 1h3l6 4V5L8 9H5a1 1 0 0 0-1 1Z"/><path d="M18 9a4 4 0 0 1 0 6"/>',
    inmersion:'<path d="M3 9.5A3.5 3.5 0 0 1 6.5 6h11A3.5 3.5 0 0 1 21 9.5V12a3 3 0 0 1-3 3h-2.6l-1.6-2.2h-3.6L8.6 15H6a3 3 0 0 1-3-3z"/><path d="M12 6V4"/>',
    curso:'<path d="M2.5 9 12 4.5 21.5 9 12 13.5z"/><path d="M6.5 11v4.6c3.2 2.2 7.8 2.2 11 0V11"/><path d="M21.5 9v5"/>',
    experiencia:'<circle cx="8.5" cy="15" r="4.5"/><circle cx="16.5" cy="7.5" r="3"/><circle cx="17.5" cy="16.5" r="2"/>',
    salida:'<path d="M3 15.5 5 20h14l2-4.5z"/><path d="M12 15.5V3l7 9.5h-7"/>',
    vida_a_bordo:'<path d="M2 17l2.2 3.5h15.6L22 17z"/><path d="M5 17v-4.5h14V17M8 12.5V9h8v3.5M11 9V5.5h2V9"/>',
    viaje:'<path d="M3 13.5 21 6l-5.5 14.5-3.2-5.6z"/><path d="m12.3 14.9-3.8 3.6"/>',
    alquiler_equipo:'<rect x="8" y="7" width="8" height="14" rx="4"/><path d="M10 7V4h4v3M14 4h3.5M12 11v3"/>',
    extra:'<circle cx="12" cy="12" r="8.5"/><path d="M12 8v8M8 12h8"/>',
    calendar:'<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    users:'<circle cx="9" cy="8.5" r="3.5"/><path d="M2.5 20c.8-3.6 3.4-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/><path d="M16 5.5a3.3 3.3 0 0 1 0 6.3M18.5 14.8c1.6.8 2.6 2.5 3 5.2"/>',
    clock:'<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    globe:'<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.6 2.6 3.6 5.4 3.6 8.5s-1 5.9-3.6 8.5c-2.6-2.6-3.6-5.4-3.6-8.5s1-5.9 3.6-8.5z"/>',
    bolt:'<path d="M13 2.5 5 13.5h6l-1 8 8-11h-6z"/>',
    inbox:'<path d="M3.5 13.5 6 5h12l2.5 8.5V19a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 19z"/><path d="M3.5 13.5h5l1.2 2.5h4.6l1.2-2.5h5"/>',
    depth:'<path d="M12 3v14"/><path d="m7 12 5 5 5-5"/><path d="M5 21h14"/>',
    level:'<path d="M4 20h4v-6H4z"/><path d="M10 20h4V9h-4z"/><path d="M16 20h4V4h-4z"/>',
    pin:'<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.4"/>',
    search:'<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
    map:'<path d="M9 4.5 3.5 6.5v13l5.5-2 6 2 5.5-2v-13l-5.5 2z"/><path d="M9 4.5v13M15 6.5v13"/>',
    mail:'<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    file:'<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    target:'<circle cx="12" cy="12" r="7.5"/><circle cx="12" cy="12" r="2.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    card:'<rect x="2.5" y="5.5" width="19" height="13" rx="2"/><path d="M2.5 10h19M6.5 15h4"/>'
  };
  const wdIcon=(name,size=20)=>`<svg class="wd-icon" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${WD_ICON_PATHS[name]||WD_ICON_PATHS.extra}</svg>`;
  const SERVICE_TYPES=[
    {value:'inmersion',label:'Inmersión',hint:'Simple, doble, nocturna'},
    {value:'curso',label:'Curso',hint:'Open Water, Advanced, Rescue'},
    {value:'experiencia',label:'Bautizo / experiencia',hint:'Try dive, snorkel'},
    {value:'salida',label:'Salida en barco',hint:'Excursión de un día'},
    {value:'vida_a_bordo',label:'Vida a bordo',hint:'Varios días embarcado'},
    {value:'viaje',label:'Viaje',hint:'Paquetes y destinos'},
    {value:'alquiler_equipo',label:'Alquiler de equipo',hint:'Sin agenda ni salidas'}
  ];
  // Two booking modes only (v50.32). Labels shared with the server (wod/bookings.py) and every screen.
  const BOOKING_MODES=[
    {value:'payment',label:'Pago al reservar',icon:'card',hint:'El cliente paga online al reservar y la reserva se confirma sola, sin que tengas que aceptarla.',example:'El cliente verá «Pago al reservar · confirmación inmediata» y el botón «Reservar y pagar».'},
    {value:'request',label:'Bajo petición',icon:'inbox',hint:'El cliente envía una solicitud sin pagar nada; tú la aceptas o la rechazas dentro del plazo.',example:'El cliente verá «Bajo petición · el centro responde en 24 h» y el botón «Enviar solicitud».'}
  ];
  const wdModeLabel=(mode,hours)=>mode==='payment'?'Pago al reservar · confirmación inmediata':`Bajo petición · el centro responde en ${Number(hours)||24} h`;
  const wdModeTag=s=>{ if(!s) return ''; const pay=s.booking_mode==='payment'; const off=s.bookable===false; return `<span class="wd-mode ${pay?'is-pay':'is-req'} ${off?'is-off':''}" title="${escapeHtml(off?(s.unavailable_reason||'No se puede reservar ahora mismo'):'')}">${wdIcon(pay?'card':'inbox',13)}${escapeHtml(s.mode_label||wdModeLabel(s.booking_mode,s.response_hours))}${off?' · no disponible':''}</span>`; };
  const TRIP_TYPES=new Set(['viaje','vida_a_bordo']);
  // Default templates: «Pago al reservar» where it makes sense and the provider has online payments, otherwise «Bajo petición»
  // (booking_mode 'auto' is resolved when the template is used).
  const SERVICE_TEMPLATES=[
    {name:'Buceo simple',title:'Buceo simple',service_type:'inmersion',duration_minutes:120,max_participants:12,booking_mode:'auto',color:'#0891b2'},
    {name:'Buceo doble',title:'Buceo doble',service_type:'inmersion',duration_minutes:240,max_participants:12,booking_mode:'auto',color:'#2563eb'},
    {name:'Bautizo de buceo',title:'Bautizo de buceo',service_type:'experiencia',duration_minutes:150,max_participants:4,booking_mode:'request',color:'#059669'},
    {name:'Curso Open Water',title:'Curso Open Water',service_type:'curso',duration_minutes:0,max_participants:4,booking_mode:'auto',color:'#d97706'},
    {name:'Curso Advanced',title:'Curso Advanced',service_type:'curso',duration_minutes:0,max_participants:4,booking_mode:'auto',color:'#ea580c'},
    {name:'Viaje de buceo',title:'Viaje de buceo',service_type:'viaje',duration_minutes:0,max_participants:10,booking_mode:'request',color:'#7c3aed'},
    {name:'Alquiler de equipo',title:'Alquiler de equipo',service_type:'alquiler_equipo',duration_minutes:0,max_participants:0,booking_mode:'request',color:'#475569'}
  ];
  const svcUi={tab:'services',q:'',type:'all'};

  // Shared formatting for the professional panel.
  const wdMoney=(n,cur)=>{const v=Number(n||0);try{return new Intl.NumberFormat(wdLocale(),{style:'currency',currency:cur||'EUR',minimumFractionDigits:Number.isInteger(v)?0:2,maximumFractionDigits:2}).format(v);}catch{return v.toFixed(2)+' €';}};
  const wdParseDate=s=>{const [y,m,dd]=String(s||'').split('-').map(Number); return new Date(y,(m||1)-1,dd||1);};
  const wdToday=()=>{const t=new Date(); return `${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')}`;};
  const wdAddDays=(iso,n)=>{const d=wdParseDate(iso); d.setDate(d.getDate()+n); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
  // Spanish dates in sentence case: «Lun, 12 oct», «Lunes, 12 de octubre».
  const wdCap=s=>s?s.charAt(0).toUpperCase()+s.slice(1):'';
  const wdDay=s=>s?wdCap(wdParseDate(s).toLocaleDateString(wdLocale(),{weekday:'short',day:'numeric',month:'short'}).replace(/\./g,'')):'';
  const wdLongDay=s=>s?wdCap(wdParseDate(s).toLocaleDateString(wdLocale(),{weekday:'long',day:'numeric',month:'long'})):'';
  const wdFullDate=s=>s?wdParseDate(s).toLocaleDateString(wdLocale(),{day:'numeric',month:'long',year:'numeric'}):'';
  const wdDuration=m=>{m=Number(m||0); if(!m)return ''; if(m%1440===0)return (m/1440)+(m===1440?' día':' días'); if(m<60)return m+' min'; const h=Math.floor(m/60),r=m%60; return r?`${h} h ${r} min`:`${h} h`;};
  const BOOKING_STATUS=Object.fromEntries(Object.entries(WD_STATES).map(([k,v])=>[k,[v[0],k==='completed'?'done':v[1]]]));
  const PAYMENT_STATUS={paid:['Pagado','good'],deposit_paid:['Señal pagada','good'],required:['Pendiente de pago','warn'],pending:['Pago en curso','warn'],at_center:['Pago en el centro','muted'],not_required:['Sin cobro','muted'],refunded:['Devuelto','muted'],review:['Pago en revisión','warn'],not_paid:['No pagada','muted'],partially_refunded:['Devuelto en parte','muted']};
  const wdStatus=(s,label)=>{const x=BOOKING_STATUS[s]||[s||'—','muted']; return `<span class="wd-pill wd-pill-${x[1]}">${escapeHtml(label||x[0])}</span>`;};
  const wdPayment=s=>{const x=PAYMENT_STATUS[s]||[s||'—','muted']; return `<span class="wd-pay wd-pay-${x[1]}">${escapeHtml(x[0])}</span>`;};

  // Generic modal: fixed overlay, centered card. Esc, × and Cancel close it; a click outside closes it only while the form is untouched.
  function wdOpenModal({id,size='md',title='',subtitle='',body='',footer=''}){
    document.getElementById(id)?.remove();
    document.body.insertAdjacentHTML('beforeend',`<div class="modal-backdrop wd-modal" id="${id}" role="dialog" aria-modal="true" aria-labelledby="${id}-title"><div class="modal-card wd-modal-card wd-modal-${size}"><header class="wd-modal-head"><h2 id="${id}-title">${title}</h2>${subtitle?`<p class="modal-help">${subtitle}</p>`:''}<button type="button" class="modal-close" data-modal-close aria-label="Cerrar">×</button></header><div class="wd-modal-body">${body}</div>${footer?`<footer class="wd-modal-foot">${footer}</footer>`:''}</div></div>`);
    const el=document.getElementById(id); let downOnBackdrop=false;
    const close=()=>{if(!el.isConnected)return; el.classList.add('is-closing'); setTimeout(()=>el.remove(),120);};
    el.addEventListener('mousedown',e=>{downOnBackdrop=e.target===el;});
    el.addEventListener('click',e=>{ if(e.target.closest('[data-modal-close]')){e.preventDefault();close();return;} if(e.target===el&&downOnBackdrop&&!el.dataset.dirty)close(); });
    el.addEventListener('input',()=>{el.dataset.dirty='1';});
    setTimeout(()=>{const f=el.querySelector('[autofocus]')||el.querySelector('.wd-modal-body input:not([type=hidden]):not([type=radio]):not([type=checkbox]):not([readonly]),.wd-modal-body textarea'); if(f)f.focus({preventScroll:true});},50);
    return {el,close};
  }
  if(!window.__wdModalKeys){
    window.__wdModalKeys=true;
    document.addEventListener('keydown',e=>{ if(e.key!=='Escape')return; const all=$$('.modal-backdrop'); const top=all[all.length-1]; if(!top)return; const btn=top.querySelector('[data-modal-close],.modal-close'); if(btn){e.preventDefault();btn.click();} });
    document.addEventListener('click',e=>{ $$('details.svc-more[open]').forEach(d=>{ if(!d.contains(e.target)) d.removeAttribute('open'); }); });
  }

  async function renderProviderServicesManager(providerId, role, mountId, opts={}){
    const mount=document.getElementById(mountId); if(!mount)return;
    const refresh=(o={})=>renderProviderServicesManager(providerId,role,mountId,o);
    if(!mount.querySelector('.svc-module')) mount.innerHTML='<p class="wd-loading">Cargando catálogo…</p>';
    try{
      const isCenter=role==='center';
      const centerId=isCenter?(state.me?.user?.center_id||0):0;
      const [d, assignedResult, tariffResult, extrasResult, equipmentResult, ownTplResult, expResult, payResult]=await Promise.all([
        api('/api/provider-services?provider_id='+providerId+'&include_inactive=1'),
        isCenter?api('/api/center-points?center_id='+centerId):{items:[]},
        isCenter?api('/api/center/tariffs'):{items:[]},
        isCenter?api('/api/center/extras'):{items:[]},
        isCenter?api('/api/center-equipment?center_id='+centerId):{items:[]},
        api('/api/service-templates').catch(()=>({items:[]})),
        api('/api/provider/experiences').catch(()=>({destinations:[]})),
        api('/api/payments/connect-status').catch(()=>({ready:false}))
      ]);
      const payReady=!!payResult.ready;
      const resolveMode=m=>m==='auto'||m==='instant'?(payReady?'payment':'request'):(m==='payment'&&!payReady?'request':m);
      const items=(d.items||[]).slice().sort((a,b)=>(Number(b.active)-Number(a.active))||String(a.title).localeCompare(String(b.title),'es'));
      const assigned=assignedResult.items||[], tariffs=tariffResult.items||[], extras=extrasResult.items||[], equipment=equipmentResult.items||[];
      const destinations=expResult.destinations||[];
      let ownTemplates=ownTplResult.items||[];
      const esc=escapeHtml;
      if(!isCenter) svcUi.tab='services';
      const todayIso=wdToday();
      const typeOf=v=>SERVICE_TYPES.find(t=>t.value===v)||{value:v,label:v||'Servicio',hint:''};
      const modeOf=v=>BOOKING_MODES.find(m=>m.value===v)||BOOKING_MODES[1];
      const offline=items.filter(s=>s.active&&s.booking_mode==='payment'&&s.bookable===false);
      const tariffFor=id=>tariffs.find(t=>Number(t.service?.id)===Number(id));
      const nextTariff=id=>{const h=(tariffFor(id)?.history||[]).filter(x=>String(x.effective_from)>todayIso).sort((a,b)=>String(a.effective_from).localeCompare(String(b.effective_from))); return h[0]||null;};
      const pointText=sl=>sl.point_mode==='weather'?'Según el estado del mar':((sl.points||[]).map(p=>p.name).join(', ')||'Punto sin asignar');
      const capClass=sl=>{const a=Number(sl.spots_available||0); return a<=0?'bad':a<=2?'warn':'good';};
      const booked=sl=>Number(sl.spots_total||0)-Number(sl.spots_available||0);
      const capPct=sl=>{const t=Number(sl.spots_total||0); return t?Math.round((booked(sl)/t)*100):0;};
      const findService=id=>items.find(x=>Number(x.id)===Number(id));
      const findSlot=(s,id)=>(s?.slots||[]).find(x=>Number(x.id)===Number(id));
      const destName=id=>destinations.find(x=>Number(x.id)===Number(id))?.title||'';

      // ---------- Overview ----------
      const activeItems=items.filter(s=>s.active);
      const allSlots=activeItems.filter(s=>s.service_type!=='alquiler_equipo').flatMap(s=>s.slots||[]);
      const freeSpots=allSlots.reduce((n,sl)=>n+Number(sl.spots_available||0),0);
      const totalSpots=allSlots.reduce((n,sl)=>n+Number(sl.spots_total||0),0);
      const occupancy=totalSpots?Math.round(((totalSpots-freeSpots)/totalSpots)*100):0;
      const pricedEquipment=equipment.filter(x=>x.price!==null&&x.price!==undefined&&x.price!=='').length;
      const kpis=`<div class="svc-kpis">
        <div><span>A la venta</span><strong>${activeItems.length}</strong><small>${items.length>activeItems.length?`${items.length-activeItems.length} en pausa`:'servicios'}</small></div>
        <div><span>Próximas salidas</span><strong>${allSlots.length}</strong><small>programadas</small></div>
        <div><span>Plazas libres</span><strong>${freeSpots}</strong><small>de ${totalSpots}</small></div>
        <div><span>Ocupación</span><strong>${occupancy}%</strong><div class="svc-kpi-bar"><i style="width:${occupancy}%"></i></div></div>
      </div>`;
      const tabs=isCenter?`<div class="svc-tabs" role="tablist">
        <button type="button" role="tab" aria-selected="${svcUi.tab==='services'}" class="svc-tab ${svcUi.tab==='services'?'active':''}" data-svc-tab="services">Servicios <b>${items.length}</b></button>
        <button type="button" role="tab" aria-selected="${svcUi.tab==='extras'}" class="svc-tab ${svcUi.tab==='extras'?'active':''}" data-svc-tab="extras">Extras <b>${extras.length}</b></button>
        <button type="button" role="tab" aria-selected="${svcUi.tab==='equipment'}" class="svc-tab ${svcUi.tab==='equipment'?'active':''}" data-svc-tab="equipment"><span class="svc-tab-long">Alquiler de equipo</span><span class="svc-tab-short">Equipo</span> <b>${pricedEquipment}/${equipment.length}</b></button>
      </div>`:'';

      // ---------- Services ----------
      const slotMini=(s,sl)=>`<button type="button" class="svc-slot slot-edit" data-id="${sl.id}" data-service="${s.id}" title="Editar salida"><span class="svc-slot-date">${esc(wdDay(sl.slot_date))}</span><span class="svc-slot-time">${esc(sl.slot_time)}</span><span class="svc-slot-bar"><i class="${capClass(sl)}" style="width:${capPct(sl)}%"></i></span><span class="svc-slot-cap ${capClass(sl)}">${Number(sl.spots_available||0)<=0?'Completa':Number(sl.spots_available)+' libres'}</span></button>`;
      const serviceCard=s=>{
        const t=typeOf(s.service_type), m=modeOf(s.booking_mode), slots=s.slots||[], isRental=s.service_type==='alquiler_equipo';
        const color=esc(s.color||'#2563eb'), dur=wdDuration(s.duration_minutes), nt=isCenter?nextTariff(s.id):null;
        const exp=s.experience&&s.experience.active?s.experience:null;
        return `<article class="svc-card ${s.active?'':'is-paused'}" style="--svc:${color}" data-service="${s.id}">
          <div class="svc-card-top">
            <span class="svc-icon">${wdIcon(s.service_type,22)}</span>
            <div class="svc-card-title"><h3>${esc(s.title)}</h3><p>${esc(t.label)}${dur?` · ${esc(dur)}`:''}</p></div>
            <span class="svc-state ${s.active?'on':'off'}">${s.active?'A la venta':'En pausa'}</span>
          </div>
          <div class="svc-price-row">
            <div><strong class="svc-price">${wdMoney(s.price,s.currency)}</strong><small>${isRental?'tarifa base':'por persona'}${nt?` · desde el ${esc(wdDay(nt.effective_from))}: ${wdMoney(nt.price,nt.currency)}`:''}</small></div>
            ${isCenter?`<button type="button" class="svc-link service-price" data-id="${s.id}">Cambiar tarifa</button>`:''}
          </div>
          <div class="svc-meta">
            ${wdModeTag(s)}
            ${s.max_participants&&!isRental?`<span>${wdIcon('users',15)}Hasta ${esc(String(s.max_participants))}</span>`:''}
            ${exp?`<span class="svc-meta-exp" title="Visible en Experiencias">${wdIcon('globe',15)}${exp.status==='published'?'En Experiencias':'Experiencia en revisión'}${destName(exp.travel_offer_id)?` · ${esc(destName(exp.travel_offer_id))}`:''}</span>`:''}
          </div>
          ${isRental
            ?`<div class="svc-rental-note">Sin agenda ni salidas.${isCenter?' Los precios por artículo están en <button type="button" class="svc-link" data-svc-tab="equipment">Alquiler de equipo</button>.':''}</div>`
            :`<div class="svc-next"><div class="svc-next-head"><span>Próximas salidas</span>${slots.length?`<button type="button" class="svc-link svc-open-agenda" data-id="${s.id}">Ver ${slots.length===1?'la salida':'las '+slots.length}</button>`:''}</div>
               ${slots.slice(0,3).map(sl=>slotMini(s,sl)).join('')||`<button type="button" class="svc-next-empty new-slot" data-service="${s.id}">Sin salidas programadas · <u>crear la primera</u></button>`}</div>`}
          <footer class="svc-card-actions">
            ${isRental?'':`<button type="button" class="svc-btn svc-btn-primary new-slot" data-service="${s.id}">+ Salida</button><button type="button" class="svc-btn svc-open-agenda" data-id="${s.id}">Agenda</button>`}
            <button type="button" class="svc-btn service-edit" data-id="${s.id}">Editar</button>
            <details class="svc-more"><summary class="svc-iconbtn" aria-label="Más acciones">···</summary><div class="svc-menu">
              <button type="button" class="service-duplicate" data-id="${s.id}">Duplicar</button>
              <button type="button" class="service-save-template" data-id="${s.id}">Guardar como plantilla</button>
              <button type="button" class="service-toggle" data-id="${s.id}">${s.active?'Poner en pausa':'Volver a poner a la venta'}</button>
              <button type="button" class="service-delete danger" data-id="${s.id}">Eliminar</button>
            </div></details>
          </footer>
        </article>`;
      };
      const allTemplates=()=>[...ownTemplates.map(t=>({...t,own:true})),...SERVICE_TEMPLATES];
      const emptyServices=()=>`<div class="svc-empty"><span class="svc-empty-icon">${wdIcon('inmersion',30)}</span><h3>Crea tu primer servicio</h3><p>Un servicio es lo que vendes: un buceo, un bautizo, un curso, un viaje o el alquiler de equipo. Después le añades salidas con fecha, hora y plazas.</p><button type="button" class="btn btn-primary new-center-service">+ Crear servicio</button><div class="svc-empty-templates"><small>O empieza con una plantilla</small><div>${allTemplates().map((t,i)=>`<button type="button" class="svc-template" data-template="${i}">${wdIcon(t.service_type,16)}${esc(t.name)}</button>`).join('')}</div></div></div>`;
      const filtered=()=>{const q=svcUi.q.trim().toLowerCase(); return items.filter(s=>(svcUi.type==='all'||s.service_type===svcUi.type)&&(!q||`${s.title} ${s.description||''} ${typeOf(s.service_type).label}`.toLowerCase().includes(q)));};
      const presentTypes=[...new Set(items.map(s=>s.service_type))];
      if(svcUi.type!=='all'&&!presentTypes.includes(svcUi.type)) svcUi.type='all';
      const servicesPane=()=>!items.length?emptyServices():`<div class="svc-toolbar">
          <label class="svc-search"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/></svg><input id="svc-search" type="search" placeholder="Buscar servicio" value="${esc(svcUi.q)}" aria-label="Buscar servicio"></label>
          <div class="svc-chips">${presentTypes.length>1?[`<button type="button" class="svc-chip ${svcUi.type==='all'?'active':''}" data-type="all">Todos</button>`,...presentTypes.map(v=>`<button type="button" class="svc-chip ${svcUi.type===v?'active':''}" data-type="${esc(v)}">${wdIcon(v,15)}${esc(typeOf(v).label)}</button>`)].join(''):''}</div>
        </div>
        <div class="svc-grid" id="svc-grid"></div>`;
      const renderGrid=()=>{const g=mount.querySelector('#svc-grid'); if(!g)return; const list=filtered(); g.innerHTML=list.map(serviceCard).join('')+(list.length?`<button type="button" class="svc-card svc-card-add new-center-service"><span>+</span><strong>Nuevo servicio</strong><small>Inmersión, curso, bautizo, viaje…</small></button>`:`<div class="svc-empty svc-empty-small"><p>Ningún servicio coincide con la búsqueda.</p></div>`);};

      // ---------- Extras ----------
      const extrasPane=()=>`<div class="svc-pane-head"><div><h3>Extras que el cliente puede añadir</h3><p>Nitrox, fotografía, guía privado… Se ofrecen al reservar y se cobran por persona.</p></div><button type="button" class="btn btn-primary" id="new-center-extra">+ Nuevo extra</button></div>
        ${extras.length?`<div class="svc-extra-grid">${extras.map(x=>`<article class="svc-extra ${x.active?'':'is-paused'}"><div class="svc-extra-main"><h4>${esc(x.name)}</h4>${x.description?`<p>${esc(x.description)}</p>`:''}</div><div class="svc-extra-side"><strong>${wdMoney(x.price)}</strong><span class="svc-state ${x.active?'on':'off'}">${x.active?'Disponible':'En pausa'}</span></div><div class="svc-extra-actions"><button type="button" class="svc-btn edit-extra" data-id="${x.id}">Editar</button><button type="button" class="svc-btn svc-btn-danger delete-extra" data-id="${x.id}">Eliminar</button></div></article>`).join('')}</div>`
        :`<div class="svc-empty svc-empty-small"><span class="svc-empty-icon">${wdIcon('extra',26)}</span><p>Todavía no hay extras. Prueba con <strong>Nitrox</strong>, <strong>Fotografía submarina</strong> o <strong>Guía privado</strong>.</p></div>`}`;

      // ---------- Equipment ----------
      const equipmentPane=()=>`<div class="svc-pane-head"><div><h3>Precios de alquiler</h3><p>Precio por persona y artículo. Solo se ofrece al cliente el equipo con precio; deja vacío lo que no alquilas.</p></div><button type="button" class="btn btn-primary" id="svc-equipment-save-all" disabled>Guardar cambios</button></div>
        <div class="svc-equipment">${equipment.map(x=>{const has=x.price!==null&&x.price!==undefined&&x.price!=='';return `<div class="svc-equipment-row" data-code="${esc(x.code)}"><strong>${esc(x.label)}</strong><span class="svc-state ${has?'on':'off'}">${has?'Se alquila':'No se alquila'}</span><label class="svc-money"><input class="center-equipment-price" data-code="${esc(x.code)}" data-initial="${has?esc(String(x.price)):''}" type="number" min="0" step="0.01" inputmode="decimal" value="${has?esc(String(x.price)):''}" placeholder="—" aria-label="Precio de ${esc(x.label)}"><span>€</span></label><button type="button" class="svc-btn save-equipment-price" data-code="${esc(x.code)}">Guardar</button></div>`;}).join('')}</div>`;

      const render=()=>{mount.innerHTML=`<section class="svc-module services-operations-module">
        <div class="svc-head"><div><p class="eyebrow">Catálogo y precios</p><h2>Servicios y tarifas</h2><p>Lo que vende tu centro, su precio y sus salidas.</p></div><button type="button" class="btn btn-primary new-center-service" id="new-center-service">+ Nuevo servicio</button></div>
        ${offline.length?`<div class="notice warn" role="alert"><strong>${offline.length===1?'Un servicio no se puede reservar':offline.length+' servicios no se pueden reservar'}.</strong> Usan «Pago al reservar» y los cobros online no están activos: ${offline.map(s=>esc(s.title)).join(', ')}. Actívalos en <a href="#/admin?tab=payments">Cobros y pagos</a> o cambia esos servicios a «Bajo petición».</div>`:''}
        ${items.length?kpis:''}${tabs}
        <div class="svc-pane">${svcUi.tab==='extras'?extrasPane():svcUi.tab==='equipment'?equipmentPane():servicesPane()}</div>
      </section>`; if(svcUi.tab==='services')renderGrid(); bindPane();};
      const bindPane=()=>{
        const search=mount.querySelector('#svc-search'); if(search) search.oninput=()=>{svcUi.q=search.value;renderGrid();};
        const saveAll=mount.querySelector('#svc-equipment-save-all');
        if(saveAll){
          const changed=()=>$$('.center-equipment-price',mount).filter(i=>i.value!==i.dataset.initial);
          mount.querySelector('.svc-equipment').oninput=()=>{const n=changed().length;saveAll.disabled=!n;saveAll.textContent=n?`Guardar cambios (${n})`:'Guardar cambios';};
          saveAll.onclick=async()=>{const rows=changed(); if(!rows.length)return; saveAll.disabled=true; try{for(const i of rows) await postJSON('/api/center-equipment',{code:i.dataset.code,price:i.value});toast(rows.length===1?'Precio guardado.':'Precios guardados.');await refresh();}catch(err){toast(err.message);saveAll.disabled=false;}};
          $$('.center-equipment-price',mount).forEach(i=>i.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();mount.querySelector(`.save-equipment-price[data-code="${i.dataset.code}"]`)?.click();}});
        }
      };

      // ---------- Templates ----------
      const saveTemplate=async(data,name)=>{const fields=['title','service_type','description','duration_minutes','max_participants','booking_mode','response_hours','payment_hours','color','price']; const payload={name}; fields.forEach(f=>{payload[f]=data[f]??'';}); const existing=ownTemplates.find(x=>x.name.toLowerCase()===name.toLowerCase()); if(existing)payload.id=existing.id; const r=await postJSON('/api/service-templates/save',payload); ownTemplates=(await api('/api/service-templates')).items||[]; return r;};

      // ---------- Service form ----------
      const openServiceForm=(existing,template)=>{
        const id=existing?.id||0; const src=existing||template||{};
        const curType=src.service_type||'inmersion', curMode=existing?(existing.booking_mode==='payment'?'payment':'request'):resolveMode(src.booking_mode||'auto'), curColor=src.color||SERVICE_COLOR_PALETTE[0].value;
        const curResp=Number(src.response_hours)||24, curPay=Number(src.payment_hours)||24;
        const exp=existing?.experience&&existing.experience.active?existing.experience:null;
        const publishDefault=exp?true:(!id&&TRIP_TYPES.has(curType));
        const tplChips=()=>`<span class="svc-tpl-label">Plantillas</span>${allTemplates().map((t,i)=>`<span class="svc-tpl ${t.own?'is-own':''}"><button type="button" class="svc-tpl-use" data-template="${i}" title="${t.own?'Tu plantilla':'Plantilla predefinida'}">${wdIcon(t.service_type,15)}${esc(t.name)}</button>${t.own?`<button type="button" class="svc-tpl-del" data-id="${t.id}" aria-label="Eliminar la plantilla ${esc(t.name)}">×</button>`:''}</span>`).join('')}`;
        const body=`<form id="svc-form" class="svc-form" novalidate>
          ${!id?`<div class="svc-form-templates" id="svc-tpl-bar">${tplChips()}</div>`:''}
          <div class="svc-field"><label for="svc-title">Nombre del servicio</label><input id="svc-title" required maxlength="180" value="${esc(src.title||'')}" placeholder="Ej. Buceo doble en barco" autofocus></div>
          <fieldset class="svc-fieldset"><legend>Tipo</legend><div class="svc-type-grid">${SERVICE_TYPES.map(t=>`<label class="svc-type-option"><input type="radio" name="svc-type" value="${t.value}" ${t.value===curType?'checked':''}><span><b>${wdIcon(t.value,22)}</b><strong>${esc(t.label)}</strong><small>${esc(t.hint)}</small></span></label>`).join('')}</div></fieldset>
          <div class="svc-form-row">
            <div class="svc-field"><label for="svc-price">${id?'Tarifa vigente':'Precio por persona'}</label>${id
              ?`<div class="svc-price-locked"><strong id="svc-price-display">${wdMoney(existing.price,existing.currency)}</strong>${isCenter?'<button type="button" class="svc-link" id="svc-open-tariff">Cambiar tarifa</button>':''}</div><input id="svc-price" type="hidden" value="${Number(existing.price||0)}">`
              :`<label class="svc-money"><input id="svc-price" type="number" min="0" step="0.01" inputmode="decimal" required value="${src.price!=null&&src.price!==''?esc(String(src.price)):''}" placeholder="0"><span>€</span></label><small>Será la tarifa vigente desde hoy.</small>`}</div>
            <div class="svc-field svc-hide-rental"><label for="svc-duration">Duración</label><label class="svc-money"><input id="svc-duration" type="number" min="0" step="5" value="${src.duration_minutes||''}" placeholder="120"><span>min</span></label><small id="svc-duration-hint">${esc(wdDuration(src.duration_minutes))||'Opcional'}</small></div>
            <div class="svc-field svc-hide-rental"><label for="svc-max">Plazas por salida</label><label class="svc-money"><input id="svc-max" type="number" min="1" value="${src.max_participants||''}" placeholder="12"><span>pax</span></label><small>Valor inicial de cada salida.</small></div>
          </div>
          <fieldset class="svc-fieldset"><legend>Cómo se reserva</legend><div class="svc-mode-grid">${BOOKING_MODES.map(m=>{ const locked=m.value==='payment'&&!payReady&&curMode!=='payment'; return `<label class="svc-mode-option ${locked?'is-locked':''}"><input type="radio" name="svc-mode" value="${m.value}" ${m.value===curMode?'checked':''} ${locked?'disabled':''}><span><b>${wdIcon(m.icon,20)}</b><strong>${esc(m.label)}</strong><small>${esc(m.hint)}</small><em class="svc-mode-example">${esc(m.example)}</em>${locked?`<em class="svc-mode-lock">Activa los cobros online para usar esta opción. <a href="#/admin?tab=payments">Cobros y pagos</a></em>`:''}</span></label>`; }).join('')}</div>
            <div class="svc-form-row svc-mode-times" id="svc-mode-times">
              <div class="svc-field"><label for="svc-resp-hours">Plazo para responder</label><label class="svc-money"><input id="svc-resp-hours" type="number" min="1" max="168" step="1" value="${curResp}"><span>h</span></label><small>Si no respondes a tiempo, la solicitud caduca sola y avisamos al cliente. Nunca después del inicio de la salida.</small></div>
              <div class="svc-field" ${payReady?'':'hidden'}><label for="svc-pay-hours">Plazo para pagar tras aceptar</label><label class="svc-money"><input id="svc-pay-hours" type="number" min="1" max="168" step="1" value="${curPay}"><span>h</span></label><small>Si el cliente no paga a tiempo, la reserva se cancela sola y las plazas se liberan.</small></div>
            </div>
            ${id?'<small class="svc-mode-note">Si cambias el modo, las reservas que ya están en curso conservan el modo con el que se hicieron.</small>':''}</fieldset>
          <fieldset class="svc-fieldset"><legend>Señal y cancelación</legend>
            <div class="svc-form-row" ${payReady?'':'hidden'}><div class="svc-field"><label for="svc-dep-type">Pago online</label><select id="svc-dep-type"><option value="none" ${(src.deposit_type||'none')==='none'?'selected':''}>Cobrar el total</option><option value="percent" ${src.deposit_type==='percent'?'selected':''}>Cobrar una señal (% del total)</option><option value="fixed" ${src.deposit_type==='fixed'?'selected':''}>Cobrar una señal (importe por persona)</option></select><small>Con señal, el cliente paga esa parte online y el resto en el centro.</small></div>
              <div class="svc-field" id="svc-dep-wrap"><label for="svc-dep-value">Señal</label><label class="svc-money"><input id="svc-dep-value" type="number" min="0" step="0.01" value="${src.deposit_value??''}"><span id="svc-dep-unit">%</span></label></div></div>
            <label class="svc-check"><input type="checkbox" id="svc-pol-own" ${src.cancel_free_hours!=null?'checked':''}><span><strong>Política de cancelación propia para este servicio</strong><small>Si no la marcas, se aplica la política general de «Cobros y pagos».</small></span></label>
            <div class="svc-form-row" id="svc-pol-wrap"><div class="svc-field"><label for="svc-pol-h">Gratis hasta (horas antes)</label><label class="svc-money"><input id="svc-pol-h" type="number" min="0" max="720" value="${src.cancel_free_hours??48}"><span>h</span></label></div>
              <div class="svc-field"><label for="svc-pol-p">Después se devuelve</label><label class="svc-money"><input id="svc-pol-p" type="number" min="0" max="100" value="${src.cancel_refund_pct??0}"><span>%</span></label></div></div>
            <small class="svc-mode-note" id="svc-pol-text"></small></fieldset>
          <fieldset class="svc-fieldset"><legend>Color en el planning <em id="svc-color-name">${esc((SERVICE_COLOR_PALETTE.find(c=>c.value===curColor)||SERVICE_COLOR_PALETTE[0]).label)}</em></legend><div class="svc-swatches">${SERVICE_COLOR_PALETTE.map(c=>`<label class="svc-swatch" title="${esc(c.label)}"><input type="radio" name="svc-color" value="${c.value}" ${c.value===curColor?'checked':''} aria-label="${esc(c.label)}"><span style="background:${c.value}"></span></label>`).join('')}</div></fieldset>
          <div class="svc-field"><label for="svc-description">Descripción para el cliente</label><textarea id="svc-description" rows="3" maxlength="5000" placeholder="Qué incluye, nivel necesario, punto de encuentro…">${esc(src.description||'')}</textarea></div>
          <div class="svc-publish ${publishDefault?'is-on':''}" id="svc-publish">
            <label class="svc-check"><input type="checkbox" id="svc-publish-exp" ${publishDefault?'checked':''}><span><strong>Publicar también en Experiencias</strong><small>Aparecerá en el destino que elijas con su precio y sus fechas, siempre actualizados desde aquí. Ideal para viajes y vida a bordo.</small></span></label>
            <div class="svc-publish-fields">
              <div class="svc-field"><label for="svc-dest">Destino</label><select id="svc-dest"><option value="">Elige un destino…</option>${destinations.map(x=>`<option value="${x.id}" ${exp&&Number(exp.travel_offer_id)===Number(x.id)?'selected':''}>${esc(x.title)}</option>`).join('')}<option value="new">+ Otro destino…</option></select></div>
              <div class="svc-field" id="svc-dest-new" hidden><label for="svc-dest-name">Nombre del destino</label><input id="svc-dest-name" maxlength="180" placeholder="Ej. Islas Medas · Costa Brava"></div>
            </div>
          </div>
          ${id?`<label class="svc-switch"><input type="checkbox" id="svc-active" ${existing.active?'checked':''}><span></span><div><strong>A la venta</strong><small>Si lo pones en pausa deja de aparecer en el motor de reservas. Las reservas ya hechas no cambian.</small></div></label>`:''}
          <div class="svc-tpl-save" id="svc-tpl-save" hidden><label for="svc-tpl-name">Nombre de la plantilla</label><div><input id="svc-tpl-name" maxlength="80" placeholder="Ej. Salida en barco a la Granadella"><button type="button" class="btn" id="svc-tpl-confirm">Guardar plantilla</button><button type="button" class="svc-link" id="svc-tpl-cancel">Cancelar</button></div><small>Guarda tipo, precio, duración, plazas, forma de reserva, color y descripción para reutilizarlos.</small></div>
        </form>`;
        const {el,close}=wdOpenModal({id:'center-service-modal',size:'lg',title:id?'Editar servicio':'Nuevo servicio',subtitle:id?esc(existing.title):'Define lo que vendes. Las fechas y plazas se añaden después como salidas.',body,
          footer:`<button type="button" class="svc-link svc-foot-left" id="svc-tpl-open">+ Guardar como plantilla</button><button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="svc-form" class="btn btn-primary">${id?'Guardar cambios':'Crear servicio'}</button>`});
        const form=el.querySelector('#svc-form'), durInput=el.querySelector('#svc-duration');
        const pubBox=el.querySelector('#svc-publish'), pubChk=el.querySelector('#svc-publish-exp'), destSel=el.querySelector('#svc-dest'), destNew=el.querySelector('#svc-dest-new');
        const syncType=()=>{const v=form.querySelector('input[name="svc-type"]:checked')?.value; form.classList.toggle('is-rental',v==='alquiler_equipo'); pubBox.hidden=v==='alquiler_equipo';};
        const syncPublish=()=>{pubBox.classList.toggle('is-on',pubChk.checked); destNew.hidden=destSel.value!=='new';};
        const syncMode=()=>{ const m=form.querySelector('input[name="svc-mode"]:checked')?.value; el.querySelector('#svc-mode-times').hidden=m!=='request'; };
        const syncDeposit=()=>{ const t=el.querySelector('#svc-dep-type').value; el.querySelector('#svc-dep-wrap').hidden=t==='none'; el.querySelector('#svc-dep-unit').textContent=t==='percent'?'%':'€/pax';
          const own=el.querySelector('#svc-pol-own').checked; el.querySelector('#svc-pol-wrap').hidden=!own; el.querySelector('#svc-pol-text').textContent=own?wdPolicyText(el.querySelector('#svc-pol-h').value,el.querySelector('#svc-pol-p').value):''; };
        ['#svc-dep-type','#svc-pol-own','#svc-pol-h','#svc-pol-p'].forEach(q=>{ const x=el.querySelector(q); x.addEventListener('input',syncDeposit); x.addEventListener('change',syncDeposit); }); syncDeposit();
        form.addEventListener('change',e=>{
          if(e.target.name==='svc-type'){ syncType(); if(!id&&!el.dataset.pubTouched){pubChk.checked=TRIP_TYPES.has(e.target.value); syncPublish();} }
          if(e.target.name==='svc-color') el.querySelector('#svc-color-name').textContent=SERVICE_COLOR_PALETTE.find(c=>c.value===e.target.value)?.label||'';
          if(e.target===pubChk){el.dataset.pubTouched='1'; syncPublish();}
          if(e.target===destSel) syncPublish();
          if(e.target.name==='svc-mode') syncMode();
        }); syncType(); syncPublish(); syncMode();
        durInput.oninput=()=>{el.querySelector('#svc-duration-hint').textContent=wdDuration(durInput.value)||'Opcional';};
        const formData=()=>({title:el.querySelector('#svc-title').value.trim(),service_type:form.querySelector('input[name="svc-type"]:checked')?.value||'inmersion',color:form.querySelector('input[name="svc-color"]:checked')?.value||SERVICE_COLOR_PALETTE[0].value,price:el.querySelector('#svc-price').value,duration_minutes:durInput.value,max_participants:el.querySelector('#svc-max').value,booking_mode:form.querySelector('input[name="svc-mode"]:checked')?.value||'request',response_hours:el.querySelector('#svc-resp-hours').value,payment_hours:el.querySelector('#svc-pay-hours').value,description:el.querySelector('#svc-description').value,
          deposit_type:el.querySelector('#svc-dep-type').value,deposit_value:el.querySelector('#svc-dep-value').value,
          cancel_free_hours:el.querySelector('#svc-pol-own').checked?el.querySelector('#svc-pol-h').value:'',cancel_refund_pct:el.querySelector('#svc-pol-own').checked?el.querySelector('#svc-pol-p').value:''});
        const applyTemplate=t=>{ if(!t)return; if(t.title)el.querySelector('#svc-title').value=t.title; const ty=form.querySelector(`input[name="svc-type"][value="${t.service_type}"]`); if(ty)ty.checked=true; const mo=form.querySelector(`input[name="svc-mode"][value="${resolveMode(t.booking_mode)}"]`); if(mo&&!mo.disabled)mo.checked=true; if(t.response_hours)el.querySelector('#svc-resp-hours').value=t.response_hours; if(t.payment_hours)el.querySelector('#svc-pay-hours').value=t.payment_hours; syncMode(); const c=form.querySelector(`input[name="svc-color"][value="${t.color}"]`); if(c){c.checked=true; el.querySelector('#svc-color-name').textContent=SERVICE_COLOR_PALETTE.find(x=>x.value===t.color)?.label||'';} durInput.value=t.duration_minutes||''; durInput.oninput(); el.querySelector('#svc-max').value=t.max_participants||''; const pr=el.querySelector('#svc-price'); if(pr.type!=='hidden'&&t.price!=null&&t.price!=='')pr.value=t.price; if(t.description!=null)el.querySelector('#svc-description').value=t.description||''; syncType(); if(!el.dataset.pubTouched){pubChk.checked=TRIP_TYPES.has(t.service_type); syncPublish();} el.dataset.dirty='1'; };
        const tplBar=el.querySelector('#svc-tpl-bar');
        const bindTplBar=()=>{ if(!tplBar)return; tplBar.innerHTML=tplChips();
          $$('.svc-tpl-use',tplBar).forEach(b=>b.onclick=()=>{ $$('.svc-tpl',tplBar).forEach(x=>x.classList.remove('is-active')); b.parentElement.classList.add('is-active'); applyTemplate(allTemplates()[+b.dataset.template]); el.querySelector('#svc-price')?.focus(); });
          $$('.svc-tpl-del',tplBar).forEach(b=>b.onclick=async()=>{ const t=ownTemplates.find(x=>Number(x.id)===Number(b.dataset.id)); if(!t||!confirm(`¿Eliminar la plantilla «${t.name}»?`))return; try{await postJSON('/api/service-templates/delete',{id:t.id}); ownTemplates=ownTemplates.filter(x=>x.id!==t.id); bindTplBar(); toast('Plantilla eliminada.');}catch(err){toast(err.message)} }); };
        bindTplBar();
        // «Guardar como plantilla»: discreet link in the footer that opens a small inline step.
        const tplBox=el.querySelector('#svc-tpl-save'), tplName=el.querySelector('#svc-tpl-name');
        el.querySelector('#svc-tpl-open').onclick=()=>{tplBox.hidden=false; tplName.value=tplName.value||el.querySelector('#svc-title').value.trim(); tplBox.scrollIntoView({block:'nearest',behavior:'smooth'}); tplName.focus(); tplName.select();};
        el.querySelector('#svc-tpl-cancel').onclick=()=>{tplBox.hidden=true;};
        tplName.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();el.querySelector('#svc-tpl-confirm').click();}};
        el.querySelector('#svc-tpl-confirm').onclick=async()=>{const name=tplName.value.trim(); if(!name){tplName.focus();toast('Ponle un nombre a la plantilla.');return;} const btn=el.querySelector('#svc-tpl-confirm'); btn.disabled=true;
          try{if(ownTemplates.some(t=>t.name.toLowerCase()===name.toLowerCase())&&!confirm(`Ya tienes una plantilla llamada «${name}». ¿Quieres sustituirla?`)){btn.disabled=false;return;}
            await saveTemplate(formData(),name); tplBox.hidden=true; bindTplBar(); toast(`Plantilla «${name}» guardada.`);}catch(err){toast(err.message)} btn.disabled=false;};
        el.querySelector('#svc-open-tariff')?.addEventListener('click',()=>openTariffForm(existing));
        form.onsubmit=async e=>{e.preventDefault();
          const data=formData(); if(!data.title){el.querySelector('#svc-title').focus();toast('Escribe el nombre del servicio.');return;}
          if(!id&&(data.price===''||Number(data.price)<0)){el.querySelector('#svc-price').focus();toast('Indica el precio. Puede ser 0.');return;}
          const publish=pubChk.checked&&data.service_type!=='alquiler_equipo';
          if(publish&&!destSel.value){destSel.focus();toast('Elige el destino donde aparecerá en Experiencias.');return;}
          if(publish&&destSel.value==='new'&&!el.querySelector('#svc-dest-name').value.trim()){el.querySelector('#svc-dest-name').focus();toast('Escribe el nombre del nuevo destino.');return;}
          const payload={id,...data,price:+data.price,active:id?el.querySelector('#svc-active').checked:true,publish_experience:publish,travel_offer_id:destSel.value&&destSel.value!=='new'?+destSel.value:0,new_destination:destSel.value==='new'?el.querySelector('#svc-dest-name').value.trim():''};
          const submit=el.querySelector('button[type="submit"]'); submit.disabled=true;
          try{await postJSON(id?'/api/provider-services/update':'/api/provider-services',payload);close();toast(id?'Cambios guardados.':(publish?'Servicio creado y publicado en Experiencias.':'Servicio creado.'));svcUi.tab='services';await refresh();}catch(err){toast(err.message);submit.disabled=false;}
        };
      };
      const openSaveTemplate=service=>{
        const {el,close}=wdOpenModal({id:'tpl-modal',size:'sm',title:'Guardar como plantilla',subtitle:'La tendrás en «Plantillas» al crear un servicio nuevo.',
          body:`<form id="tpl-form" class="svc-form"><div class="svc-field"><label for="tpl-name">Nombre de la plantilla</label><input id="tpl-name" required maxlength="80" value="${esc(service.title)}" autofocus></div></form>`,
          footer:`<button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="tpl-form" class="btn btn-primary">Guardar plantilla</button>`});
        setTimeout(()=>el.querySelector('#tpl-name').select(),60);
        el.querySelector('#tpl-form').onsubmit=async e=>{e.preventDefault(); const name=el.querySelector('#tpl-name').value.trim(); if(!name)return;
          if(ownTemplates.some(t=>t.name.toLowerCase()===name.toLowerCase())&&!confirm(`Ya tienes una plantilla llamada «${name}». ¿Quieres sustituirla?`))return;
          try{await saveTemplate(service,name);close();toast(`Plantilla «${name}» guardada.`);}catch(err){toast(err.message)}};
      };

      // ---------- Agenda (all departures of one service) ----------
      const openAgenda=service=>{
        const slots=service.slots||[]; let lastMonth='';
        const rows=slots.map(sl=>{const mo=wdCap(wdParseDate(sl.slot_date).toLocaleDateString(wdLocale(),{month:'long',year:'numeric'})); const head=mo!==lastMonth?`<div class="svc-agenda-month">${esc(mo)}</div>`:''; lastMonth=mo;
          return head+`<div class="svc-agenda-row"><div class="svc-agenda-date"><strong>${esc(wdLongDay(sl.slot_date))}</strong><span>${esc(sl.slot_time)} · ${esc(pointText(sl))}</span></div><div class="svc-agenda-cap"><span class="svc-slot-bar"><i class="${capClass(sl)}" style="width:${capPct(sl)}%"></i></span><small class="${capClass(sl)}">${booked(sl)} de ${Number(sl.spots_total||0)} plazas ocupadas</small></div><div class="svc-agenda-actions"><button type="button" class="svc-btn agenda-slot-edit" data-id="${sl.id}">Editar</button><button type="button" class="svc-btn svc-btn-danger agenda-slot-delete" data-id="${sl.id}">Eliminar</button></div></div>`;}).join('');
        const {el}=wdOpenModal({id:'svc-agenda-modal',size:'lg',title:`Salidas de ${esc(service.title)}`,subtitle:slots.length?`${slots.length} ${slots.length===1?'salida programada':'salidas programadas'}. Cada salida cobra la tarifa vigente en su fecha.`:'',
          body:`<div class="svc-agenda">${rows||`<div class="svc-empty svc-empty-small"><span class="svc-empty-icon">${wdIcon('calendar',26)}</span><p>Todavía no hay salidas. Crea la primera con fecha, hora y plazas.</p></div>`}</div>`,
          footer:`<button type="button" class="btn" data-modal-close>Cerrar</button><button type="button" class="btn btn-primary" id="agenda-new-slot">+ Nueva salida</button>`});
        el.querySelector('#agenda-new-slot').onclick=()=>openSlotForm(service,null,true);
        $$('.agenda-slot-edit',el).forEach(b=>b.onclick=()=>{const sl=findSlot(service,b.dataset.id); if(sl)openSlotForm(service,sl,true);});
        $$('.agenda-slot-delete',el).forEach(b=>b.onclick=()=>deleteSlot(+b.dataset.id,service.id,true));
      };
      const deleteSlot=async(slotId,serviceId,fromAgenda)=>{if(!confirm('¿Eliminar esta salida?'))return;try{await postJSON('/api/provider-services/slot-delete',{id:slotId});toast('Salida eliminada.');await refresh(fromAgenda?{reopenAgenda:serviceId}:{});}catch(err){toast(err.message)}};

      // ---------- Slot form ----------
      const openSlotForm=(service,slot,fromAgenda=false)=>{
        const sid=service.id,id=slot?.id||0; const mode=slot?.point_mode||'fixed'; const used=slot?booked(slot):0;
        const pointChips=assigned.length?assigned.map(p=>`<label class="svc-point"><input type="checkbox" value="${p.id}" ${(slot?.points||[]).some(x=>Number(x.id||x)===Number(p.id))?'checked':''}><span>${esc(p.name)}</span></label>`).join(''):'<small>Tu centro aún no tiene puntos asociados. Añádelos en «Puntos de buceo» y asígnalos más tarde.</small>';
        const body=`<form id="slot-form" class="svc-form">
          <div class="svc-form-row">
            <div class="svc-field"><label for="slot-date">Fecha</label><input id="slot-date" type="date" required min="${id?'':todayIso}" value="${esc(slot?.slot_date||'')}"></div>
            <div class="svc-field"><label for="slot-time">Hora de salida</label><input id="slot-time" type="time" required value="${esc(slot?.slot_time||'')}"></div>
            <div class="svc-field"><label for="slot-total">Plazas</label><label class="svc-money"><input id="slot-total" type="number" min="${Math.max(1,used)}" required value="${Number(slot?.spots_total||service.max_participants||12)}"><span>pax</span></label>${used?`<small>${used} ya reservadas.</small>`:''}</div>
          </div>
          <fieldset class="svc-fieldset"><legend>Punto de buceo</legend><div class="svc-mode-grid svc-mode-grid-2">
            <label class="svc-mode-option"><input type="radio" name="slot-point-mode" value="fixed" ${mode!=='weather'?'checked':''}><span><b>${wdIcon('globe',20)}</b><strong>Lo decido ahora</strong><small>Marca el punto o puntos previstos.</small></span></label>
            <label class="svc-mode-option"><input type="radio" name="slot-point-mode" value="weather" ${mode==='weather'?'checked':''}><span><b>${wdIcon('salida',20)}</b><strong>Según el estado del mar</strong><small>Se decide el mismo día.</small></span></label>
          </div></fieldset>
          <div class="svc-field"><span class="svc-label" id="slot-points-label">${mode==='weather'?'Puntos habituales (orientativo)':'Puntos previstos'}</span><div class="svc-points" id="slot-points" role="group" aria-labelledby="slot-points-label">${pointChips}</div></div>
          <p class="svc-note">Precio de esta salida: la tarifa vigente en su fecha (hoy, ${wdMoney(service.price,service.currency)} por persona).</p>
        </form>`;
        const {el,close}=wdOpenModal({id:'slot-modal',size:'md',title:id?'Editar salida':'Nueva salida',subtitle:esc(service.title),body,
          footer:`<button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="slot-form" class="btn btn-primary">${id?'Guardar salida':'Crear salida'}</button>`});
        el.querySelector('#slot-form').addEventListener('change',e=>{if(e.target.name==='slot-point-mode')el.querySelector('#slot-points-label').textContent=e.target.value==='weather'?'Puntos habituales (orientativo)':'Puntos previstos';});
        el.querySelector('#slot-form').onsubmit=async e=>{e.preventDefault(); if(!e.target.reportValidity())return;
          const data={service_id:sid,slot_date:el.querySelector('#slot-date').value,slot_time:el.querySelector('#slot-time').value,spots_total:+el.querySelector('#slot-total').value,dive_point_ids:$$('#slot-points input:checked',el).map(x=>Number(x.value)),point_mode:el.querySelector('input[name="slot-point-mode"]:checked')?.value||'fixed'};
          const submit=el.querySelector('button[type="submit"]'); submit.disabled=true;
          try{await postJSON(id?'/api/provider-services/slot-update':'/api/provider-services/slot',id?{...data,id}:{...data});close();toast(id?'Salida guardada.':'Salida creada.');await refresh(fromAgenda?{reopenAgenda:sid}:{});}catch(err){toast(err.message);submit.disabled=false;}};
      };

      // ---------- Tariff form ----------
      const openTariffForm=service=>{
        const entry=tariffFor(service.id); const hist=(entry?.history||[]).slice().sort((a,b)=>String(b.effective_from).localeCompare(String(a.effective_from))||Number(b.id)-Number(a.id));
        const future=hist.filter(h=>String(h.effective_from)>todayIso).reverse(); const past=hist.filter(h=>String(h.effective_from)<=todayIso);
        const body=`<form id="tariff-form" class="svc-form">
          <div class="svc-tariff-current"><span>Precio vigente hoy</span><strong>${wdMoney(service.price,service.currency)}</strong></div>
          <div class="svc-form-row svc-form-row-2">
            <div class="svc-field"><label for="tariff-price">Nuevo precio</label><label class="svc-money"><input id="tariff-price" type="number" min="0" step="0.01" inputmode="decimal" required value="${Number(service.price||0)}"><span>€</span></label></div>
            <div class="svc-field"><label for="tariff-date">A partir del</label><input id="tariff-date" type="date" required value="${todayIso}"><small>Pon una fecha futura para programar la temporada alta.</small></div>
          </div>
          <p class="svc-note">Las reservas ya hechas mantienen su precio. Las nuevas pagan la tarifa vigente en el día de la actividad.</p>
          ${future.length?`<div class="svc-history"><h4>Cambios programados</h4>${future.map(h=>`<div class="svc-history-row"><span>Desde el ${esc(wdFullDate(h.effective_from))}</span><strong>${wdMoney(h.price,h.currency)}</strong><button type="button" class="svc-btn svc-btn-danger tariff-history-delete" data-id="${h.id}">Anular</button></div>`).join('')}</div>`:''}
          ${past.length>1?`<div class="svc-history"><h4>Historial</h4>${past.slice(0,6).map((h,i)=>`<div class="svc-history-row ${i===0?'is-current':''}"><span>Desde el ${esc(wdFullDate(h.effective_from))}</span><strong>${wdMoney(h.price,h.currency)}</strong><em>${i===0?'Vigente':''}</em></div>`).join('')}</div>`:''}
        </form>`;
        const {el,close}=wdOpenModal({id:'tariff-modal',size:'md',title:'Tarifa',subtitle:esc(service.title),body,
          footer:`<button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="tariff-form" class="btn btn-primary">Guardar tarifa</button>`});
        el.querySelector('#tariff-form').onsubmit=async e=>{e.preventDefault(); if(!e.target.reportValidity())return; const submit=el.querySelector('button[type="submit"]'); submit.disabled=true;
          const price=+el.querySelector('#tariff-price').value, from=el.querySelector('#tariff-date').value;
          try{await postJSON('/api/center/tariffs/save',{service_id:service.id,price,effective_from:from});close();
            const disp=document.getElementById('svc-price-display'); if(disp&&from<=todayIso)disp.textContent=wdMoney(price,service.currency);
            toast(from>todayIso?`Nueva tarifa programada para el ${wdFullDate(from)}.`:'Tarifa guardada.');await refresh();}catch(err){toast(err.message);submit.disabled=false;}};
        $$('.tariff-history-delete',el).forEach(b=>b.onclick=async()=>{if(!confirm('¿Anular este cambio de tarifa?'))return;try{await postJSON('/api/center/tariffs/history-delete',{id:+b.dataset.id});toast('Cambio de tarifa anulado.');await refresh({reopenTariff:service.id});}catch(err){toast(err.message)}});
      };

      // ---------- Extra form ----------
      const openExtraForm=id=>{const existing=extras.find(x=>Number(x.id)===Number(id));
        const body=`<form id="extra-form" class="svc-form">
          <div class="svc-form-row svc-form-row-2"><div class="svc-field"><label for="extra-name">Nombre</label><input id="extra-name" required maxlength="120" value="${esc(existing?.name||'')}" placeholder="Nitrox" autofocus></div>
          <div class="svc-field"><label for="extra-price">Precio por persona</label><label class="svc-money"><input id="extra-price" type="number" min="0" step="0.01" inputmode="decimal" required value="${existing?.price??''}" placeholder="0"><span>€</span></label></div></div>
          <div class="svc-field"><label for="extra-desc">Descripción (opcional)</label><textarea id="extra-desc" rows="2" maxlength="500" placeholder="Por botella, incluye análisis de mezcla">${esc(existing?.description||'')}</textarea></div>
          ${existing?`<label class="svc-switch"><input type="checkbox" id="extra-active" ${existing.active?'checked':''}><span></span><div><strong>Disponible</strong><small>Desactívalo para dejar de ofrecerlo en reservas nuevas.</small></div></label>`:''}
        </form>`;
        const {el,close}=wdOpenModal({id:'extra-modal',size:'sm',title:existing?'Editar extra':'Nuevo extra',body,footer:`<button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="extra-form" class="btn btn-primary">Guardar extra</button>`});
        el.querySelector('#extra-form').onsubmit=async e=>{e.preventDefault(); if(!e.target.reportValidity())return; const submit=el.querySelector('button[type="submit"]'); submit.disabled=true;
          try{await postJSON('/api/center/extras/save',{id:id||0,name:el.querySelector('#extra-name').value.trim(),description:el.querySelector('#extra-desc').value,price:+el.querySelector('#extra-price').value,active:existing?(el.querySelector('#extra-active').checked?1:0):1});close();toast('Extra guardado.');svcUi.tab='extras';await refresh();}catch(err){toast(err.message);submit.disabled=false;}};
      };

      render();
      if(opts.reopenAgenda){const s=findService(opts.reopenAgenda); if(s)openAgenda(s);}
      if(opts.reopenTariff){const s=findService(opts.reopenTariff); if(s)openTariffForm(s);}
      if(opts.openNew) openServiceForm();

      mount.onclick=async e=>{
        const tpl=e.target.closest('.svc-template'); if(tpl){openServiceForm(null,allTemplates()[+tpl.dataset.template]);return;}
        const tabBtn=e.target.closest('[data-svc-tab]'); if(tabBtn){svcUi.tab=tabBtn.dataset.svcTab;render();return;}
        const chip=e.target.closest('.svc-chip'); if(chip){svcUi.type=chip.dataset.type;$$('.svc-chip',mount).forEach(c=>c.classList.toggle('active',c===chip));renderGrid();return;}
        const btn=e.target.closest('button'); if(!btn)return;
        btn.closest('details')?.removeAttribute('open');
        const s=findService(btn.dataset.id||btn.dataset.service);
        if(btn.classList.contains('new-center-service')){e.preventDefault();openServiceForm();return;}
        if(btn.classList.contains('service-edit')){if(s)openServiceForm(s);return;}
        if(btn.classList.contains('service-price')){if(s)openTariffForm(s);return;}
        if(btn.classList.contains('svc-open-agenda')){if(s)openAgenda(s);return;}
        if(btn.classList.contains('new-slot')){if(s)openSlotForm(s);return;}
        if(btn.classList.contains('slot-edit')){const sl=findSlot(s,btn.dataset.id);if(s&&sl)openSlotForm(s,sl);return;}
        if(btn.classList.contains('service-duplicate')){if(s){const {id,experience,...copy}=s; openServiceForm(null,{...copy,title:s.title+' (copia)'});}return;}
        if(btn.classList.contains('service-save-template')){if(s)openSaveTemplate(s);return;}
        if(btn.classList.contains('service-toggle')){if(!s)return;try{await postJSON('/api/provider-services/update',{id:s.id,title:s.title,service_type:s.service_type,color:s.color,duration_minutes:s.duration_minutes||'',max_participants:s.max_participants||'',booking_mode:s.booking_mode,description:s.description||'',active:!s.active});toast(s.active?'Servicio en pausa. Ya no aparece en el motor de reservas.':'Servicio a la venta de nuevo.');await refresh();}catch(err){toast(err.message)}return;}
        if(btn.classList.contains('service-delete')){if(!confirm(`¿Eliminar «${s?.title||'este servicio'}»? No se puede deshacer.`))return;try{await postJSON('/api/provider-services/delete',{id:+btn.dataset.id});toast('Servicio eliminado.');await refresh();}catch(err){toast(err.message)}return;}
        if(btn.classList.contains('edit-extra')){openExtraForm(Number(btn.dataset.id));return;}
        if(btn.classList.contains('delete-extra')){if(!confirm('¿Eliminar este extra?'))return;try{await postJSON('/api/center/extras/delete',{id:+btn.dataset.id});toast('Extra eliminado.');await refresh();}catch(err){toast(err.message)}return;}
        if(btn.id==='new-center-extra'){openExtraForm();return;}
        if(btn.classList.contains('save-equipment-price')){try{const input=mount.querySelector('.center-equipment-price[data-code="'+btn.dataset.code+'"]');await postJSON('/api/center-equipment',{code:btn.dataset.code,price:input?.value??''});toast('Precio guardado.');await refresh();}catch(err){toast(err.message)}return;}
      };
    }catch(err){mount.innerHTML=`<div class="empty"><h3>No se ha podido cargar el catálogo</h3><p>${escapeHtml(err.message)}</p><button type="button" class="btn" id="retry-services">Reintentar</button></div>`;$('#retry-services').onclick=()=>renderProviderServicesManager(providerId,role,mountId);}
  }

  // =====================================================================
  //  Center operations: bookings inbox, manual booking, experiences, showcase
  // =====================================================================
  const BK_VIEWS=[
    {key:'today',label:'Hoy'},
    {key:'week',label:'Próximos 7 días'},
    {key:'pending',label:'Solicitudes pendientes'},
    {key:'unpaid',label:'Por cobrar'},
    {key:'upcoming',label:'Todas las próximas'},
    {key:'history',label:'Historial'}
  ];
  const BK_SOURCE={online:'WORLDIVES',manual:'Manual',web:'Tu web'};
  const PAYMENT_METHODS=['Efectivo','Tarjeta (TPV)','Transferencia','Bizum','Bono / regalo','Otro'];
  const bkUi={view:'week',q:'',service:'',from:'',to:''};

  const wdLeft=m=>{ m=Number(m)||0; if(m<60) return `${m} min`; const h=Math.floor(m/60); return h<48?`${h} h`:`${Math.floor(h/24)} días`; };
  function bkQuery(){
    const t=wdToday(), p=new URLSearchParams();
    if(bkUi.view==='today'){p.set('from',t);p.set('to',t);p.set('order','asc');}
    if(bkUi.view==='week'){p.set('from',t);p.set('to',wdAddDays(t,7));p.set('order','asc');}
    if(bkUi.view==='pending'){p.set('status','requested');p.set('order','asc');}
    if(bkUi.view==='unpaid'){p.set('payment','required');p.set('order','asc');}
    if(bkUi.view==='upcoming'){p.set('from',t);p.set('order','asc');}
    if(bkUi.view==='history'){p.set('to',wdAddDays(t,-1));p.set('limit','400');}
    if(bkUi.from)p.set('from',bkUi.from); if(bkUi.to)p.set('to',bkUi.to);
    if(bkUi.q)p.set('q',bkUi.q); if(bkUi.service)p.set('service_id',bkUi.service);
    return p.toString();
  }

  async function renderCenterBookings(mountId, ctx={}){
    const mount=document.getElementById(mountId); if(!mount)return;
    const refresh=()=>renderCenterBookings(mountId,ctx);
    if(!mount.querySelector('.bk-module')) mount.innerHTML='<p class="wd-loading">Cargando reservas…</p>';
    try{
      const [list,pend,unpaid,svc]=await Promise.all([api('/api/bookings?'+bkQuery()),api('/api/center/requests'),api('/api/bookings?payment=required&limit=500'),api('/api/provider-services?provider_id='+(state.me?.user?.id||0)+'&include_inactive=1')]);
      const items=list.items||[], services=svc.items||[]; const esc=escapeHtml; const t=wdToday();
      const reqById=Object.fromEntries((pend.items||[]).map(x=>[x.id,x]));
      const pendingCount=pend.count||0, unpaidCount=(unpaid.items||[]).filter(b=>!['cancelled','rejected','expired'].includes(b.status)).length;
      const counts={pending:pendingCount,unpaid:unpaidCount};
      const actions=b=>{
        const out=[];
        const req=b.status==='requested'||(b.status==='requested'||b.status==='pending');
        if(req) out.push(`<button type="button" class="bk-act bk-primary" data-act="confirmed" data-id="${b.id}">Aceptar</button><button type="button" class="bk-act" data-act="rejected" data-id="${b.id}">Rechazar</button>`);
        if((b.payment_status==='required'||b.payment_status==='at_center'||b.payment_status==='deposit_paid')&&['confirmed','accepted_pending_payment'].includes(b.status)&&Number(b.price)>0) out.push(`<button type="button" class="bk-act" data-act="pay" data-id="${b.id}">${b.payment_status==='deposit_paid'?'Cobrar el resto':'Registrar cobro'}</button>`);
        if(['proposed','failed'].includes(b.refund_status)) out.push(`<button type="button" class="bk-act bk-primary" data-act="refund" data-id="${b.id}">Devolver</button>`);
        if(b.status==='confirmed'&&b.booking_date<=t) out.push(`<button type="button" class="bk-act" data-act="completed" data-id="${b.id}">Completar</button>`);
        const menu=[`<a href="#/reserva?id=${b.id}">Ver ficha completa</a>`,`<button type="button" data-act="notice" data-id="${b.id}">Enviar aviso al cliente</button>`];
        if(['accepted_pending_payment','confirmed'].includes(b.status)) menu.push(`<button type="button" class="danger" data-act="cancelled" data-id="${b.id}">Cancelar reserva</button>`);
        if(['paid','deposit_paid','partially_refunded'].includes(b.payment_status)&&Number(b.amount_paid||0)>0&&!['proposed','failed'].includes(b.refund_status)) menu.push(`<button type="button" data-act="refund" data-id="${b.id}">Devolver dinero</button>`);
        if(b.payment_status==='paid') menu.push(`<button type="button" data-act="unpay" data-id="${b.id}">Marcar como no pagado</button>`);
        return out.join('')+`<details class="svc-more"><summary class="svc-iconbtn" aria-label="Más acciones">···</summary><div class="svc-menu">${menu.join('')}</div></details>`;
      };
      const row=b=>`<div class="bk-row bk-st-${esc(b.status)}" style="--svc:${esc(b.service_color||'#94a3b8')}">
          <div class="bk-time"><strong>${esc(b.booking_time||'—')}</strong><span>#${b.id}</span></div>
          <div class="bk-client"><strong>${esc(b.fullname||'Cliente')}</strong><span>${esc(b.contact_phone||'')}${b.contact_phone&&b.email&&!String(b.email).endsWith('.worldives.local')?' · ':''}${b.email&&!String(b.email).endsWith('.worldives.local')?esc(b.email):''}</span></div>
          <div class="bk-activity"><strong><i></i>${esc(b.service_title||'Reserva')}</strong><span>${esc(b.point_name||'Punto sin asignar')}${b.equipment_items?' · Equipo: '+esc(b.equipment_items):''}</span></div>
          <div class="bk-pax"><strong>${Number(b.participants||1)}</strong><span>${Number(b.participants||1)===1?'persona':'personas'}</span></div>
          <div class="bk-amount"><strong>${wdMoney(b.price,b.currency)}</strong>${wdPayment(b.payment_status)}</div>
          <div class="bk-state">${wdStatus(b.status,b.status_label)}${(b.status==='requested'||(b.status==='requested'||b.status==='pending'))&&reqById[b.id]?.minutes_left!=null?`<span class="acc-due">${wdIcon('clock',12)} ${esc(wdLeft(reqById[b.id].minutes_left))} para responder</span>`:''}${b.status==='accepted_pending_payment'&&b.payment_deadline?`<span class="acc-due">Paga antes del ${esc(wdDeadline(b.payment_deadline))}</span>`:''}<span class="bk-source">${esc(BK_SOURCE[b.source]||(b.external_ref?'Tu web':'WORLDIVES'))}</span></div>
          <div class="bk-actions">${actions(b)}</div>
        </div>`;
      const grouped=()=>{ if(!items.length) return `<div class="bk-empty"><span>${wdIcon('calendar',26)}</span><h3>${bkUi.view==='today'?'Hoy no hay reservas':bkUi.view==='pending'?'No hay nada por confirmar':bkUi.view==='unpaid'?'No hay cobros pendientes':'No hay reservas'}</h3><p>${bkUi.q||bkUi.service||bkUi.from||bkUi.to?'Prueba a quitar algún filtro.':'Cuando entre una reserva, o la crees tú, aparecerá aquí.'}</p><button type="button" class="btn btn-primary bk-new">+ Nueva reserva</button></div>`;
        const days={}; items.forEach(b=>{(days[b.booking_date]=days[b.booking_date]||[]).push(b);});
        return Object.entries(days).map(([day,list])=>{const pax=list.filter(b=>!['cancelled','rejected'].includes(b.status)).reduce((n,b)=>n+Number(b.participants||1),0);
          return `<section class="bk-day"><header><h3>${day===t?'Hoy · ':day===wdAddDays(t,1)?'Mañana · ':''}${esc(wdLongDay(day))}</h3><span>${list.length} ${list.length===1?'reserva':'reservas'} · ${pax} ${pax===1?'persona':'personas'}</span></header>${list.map(row).join('')}</section>`;}).join(''); };
      mount.innerHTML=`<section class="bk-module">
        <div class="svc-head"><div><p class="eyebrow">Gestión de reservas</p><h2>Reservas</h2><p>${ctx.freelance?'Las reservas y solicitudes de tus servicios.':'Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apuntas tú.'}</p></div>${ctx.freelance?'':'<button type="button" class="btn btn-primary bk-new">+ Nueva reserva</button>'}</div>
        <div class="bk-views" role="tablist">${BK_VIEWS.map(v=>`<button type="button" role="tab" aria-selected="${bkUi.view===v.key}" class="bk-view ${bkUi.view===v.key?'active':''}" data-view="${v.key}">${v.label}${counts[v.key]?`<b>${counts[v.key]}</b>`:''}</button>`).join('')}</div>
        <div class="bk-filters">
          <label class="svc-search"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/></svg><input id="bk-q" type="search" placeholder="Cliente, teléfono, email o nº de reserva" value="${esc(bkUi.q)}"></label>
          <select id="bk-service" aria-label="Actividad"><option value="">Todas las actividades</option>${services.map(s=>`<option value="${s.id}" ${String(bkUi.service)===String(s.id)?'selected':''}>${esc(s.title)}</option>`).join('')}</select>
          <label class="bk-date"><span>Desde</span><input id="bk-from" type="date" value="${esc(bkUi.from)}"></label>
          <label class="bk-date"><span>Hasta</span><input id="bk-to" type="date" value="${esc(bkUi.to)}"></label>
          ${bkUi.q||bkUi.service||bkUi.from||bkUi.to?'<button type="button" class="svc-link" id="bk-clear">Quitar filtros</button>':''}
        </div>
        <div class="bk-list">${grouped()}</div>
        ${items.length>=400?'<p class="wd-muted-note">Se muestran las 400 reservas más recientes. Usa las fechas para buscar más atrás.</p>':''}
      </section>`;
      let timer=0;
      mount.querySelector('#bk-q').oninput=e=>{clearTimeout(timer);timer=setTimeout(()=>{bkUi.q=e.target.value.trim();refresh().then(()=>{const q=mount.querySelector('#bk-q');if(q){q.focus();q.setSelectionRange(q.value.length,q.value.length);}});},300);};
      mount.querySelector('#bk-service').onchange=e=>{bkUi.service=e.target.value;refresh();};
      mount.querySelector('#bk-from').onchange=e=>{bkUi.from=e.target.value;refresh();};
      mount.querySelector('#bk-to').onchange=e=>{bkUi.to=e.target.value;refresh();};
      mount.querySelector('#bk-clear')?.addEventListener('click',()=>{Object.assign(bkUi,{q:'',service:'',from:'',to:''});refresh();});
      const byId=id=>items.find(x=>Number(x.id)===Number(id));
      mount.onclick=async e=>{
        const v=e.target.closest('.bk-view'); if(v){bkUi.view=v.dataset.view;refresh();return;}
        if(e.target.closest('.bk-new')){openManualBooking({onSaved:()=>{bkUi.view='upcoming';refresh();ctx.onChange?.();}});return;}
        const a=e.target.closest('[data-act]'); if(!a)return; a.closest('details')?.removeAttribute('open');
        const b=byId(a.dataset.id); if(!b)return; const act=a.dataset.act;
        if(act==='pay'){openPaymentModal(b,()=>{refresh();ctx.onChange?.();});return;}
        if(act==='unpay'){if(!confirm('¿Marcar esta reserva como no pagada?'))return; try{await postJSON(`/api/bookings/${b.id}/payment`,{payment_status:'required'});toast('Pago desmarcado.');refresh();}catch(err){toast(err.message)} return;}
        if(act==='rejected'){ openRejectModal(b.id,()=>{refresh();ctx.onChange?.();}); return; }
        if(act==='notice'){ openNoticeModal(b.id,b,refresh); return; }
        const labels={confirmed:'aceptada',cancelled:'cancelada',completed:'completada'};
        if(act==='cancelled'){ openProviderCancelModal(b.id,()=>{refresh();ctx.onChange?.();}); return; }
        if(act==='refund'){ openRefundModal(b.id,()=>{refresh();ctx.onChange?.();}); return; }
        try{const r=await postJSON(`/api/bookings/${b.id}/status`,{status:act});toast(r.status==='accepted_pending_payment'?'Solicitud aceptada: el cliente tiene un plazo para pagar.':`Reserva ${labels[act]}.`);refresh();ctx.onChange?.();}catch(err){toast(err.message)}
      };
    }catch(err){mount.innerHTML=`<div class="empty"><h3>No se han podido cargar las reservas</h3><p>${escapeHtml(err.message)}</p><button type="button" class="btn" id="bk-retry">Reintentar</button></div>`;$('#bk-retry').onclick=refresh;}
  }

  function openPaymentModal(b,onDone){
    const {el,close}=wdOpenModal({id:'pay-modal',size:'sm',title:'Registrar pago',subtitle:`Reserva #${b.id} · ${escapeHtml(b.fullname||'')}`,
      body:`<form id="pay-form" class="svc-form"><p class="svc-tariff-now">${b.payment_status==='deposit_paid'?`Resto a cobrar <strong>${wdMoney(Math.max(0,Number(b.price||0)-Number(b.amount_paid||0)),b.currency)}</strong> <small>(señal de ${wdMoney(b.amount_paid,b.currency)} ya pagada online)</small>`:`Importe <strong>${wdMoney(b.price,b.currency)}</strong>`}</p><div class="svc-field"><label for="pay-method">Forma de pago</label><select id="pay-method">${PAYMENT_METHODS.map(m=>`<option>${m}</option>`).join('')}</select></div>${(b.status==='requested'||b.status==='pending')?'<p class="svc-note">Al registrar el pago la reserva queda confirmada y se reservan sus plazas.</p>':''}</form>`,
      footer:`<button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="pay-form" class="btn btn-primary">Marcar como pagada</button>`});
    el.querySelector('#pay-form').onsubmit=async e=>{e.preventDefault(); try{await postJSON(`/api/bookings/${b.id}/payment`,{payment_status:'paid',payment_method:el.querySelector('#pay-method').value});close();toast('Pago registrado.');onDone?.();}catch(err){toast(err.message)}};
  }

  // ---------- Manual booking ----------
  async function openManualBooking(opts={}){
    let services=[], extras=[], equipment=[];
    try{
      const cid=state.me?.user?.center_id||0;
      const [s,x,eq]=await Promise.all([api('/api/provider-services?provider_id='+(state.me?.user?.id||0)+'&include_inactive=1'),api('/api/center/extras'),api('/api/center-equipment?center_id='+cid)]);
      services=(s.items||[]).filter(v=>v.active).sort((a,b)=>((b.slots||[]).length>0)-((a.slots||[]).length>0)||(a.service_type==='alquiler_equipo')-(b.service_type==='alquiler_equipo')||String(a.title).localeCompare(String(b.title),'es')); extras=(x.items||[]).filter(v=>v.active); equipment=(eq.items||[]).filter(v=>v.price!=null&&v.price!=='');
    }catch(err){toast(err.message);return;}
    if(!services.length){toast('Primero crea un servicio en «Servicios y tarifas».');return;}
    const esc=escapeHtml;
    const body=`<form id="mb-form" class="svc-form mb-form" novalidate>
      <section class="mb-section"><h3>Cliente</h3>
        <div class="svc-form-row">
          <div class="svc-field"><label for="mb-name">Nombre y apellidos</label><input id="mb-name" required maxlength="180" autofocus placeholder="María López"></div>
          <div class="svc-field"><label for="mb-phone">Teléfono</label><input id="mb-phone" type="tel" maxlength="60" placeholder="+34 600 000 000"></div>
          <div class="svc-field"><label for="mb-email">Email (opcional)</label><input id="mb-email" type="email" maxlength="160" placeholder="cliente@email.com"></div>
        </div>
        <small class="mb-hint">Si el cliente ya tiene cuenta con ese email, la reserva aparecerá también en su área.</small>
      </section>
      <section class="mb-section"><h3>Actividad</h3>
        <div class="svc-form-row svc-form-row-2">
          <div class="svc-field"><label for="mb-service">Servicio</label><select id="mb-service">${services.map(s=>`<option value="${s.id}" ${Number(opts.serviceId)===Number(s.id)?'selected':''}>${esc(s.title)} · ${wdMoney(s.price,s.currency)}</option>`).join('')}</select></div>
          <div class="svc-field"><label for="mb-pax">Personas</label><input id="mb-pax" type="number" min="1" max="200" value="1"><small id="mb-pax-hint"></small></div>
        </div>
        <div class="svc-field"><span class="svc-label">Salida</span><div class="mb-slots" id="mb-slots"></div></div>
        <div class="svc-form-row svc-form-row-2 mb-custom-date" id="mb-custom" hidden>
          <div class="svc-field"><label for="mb-date">Fecha</label><input id="mb-date" type="date"></div>
          <div class="svc-field"><label for="mb-time">Hora</label><input id="mb-time" type="time"></div>
        </div>
      </section>
      ${equipment.length||extras.length?`<section class="mb-section"><h3>Equipo y extras <small>(por persona)</small></h3><div class="mb-checks">
        ${equipment.map(e=>`<label class="svc-point"><input type="checkbox" class="mb-eq" value="${esc(e.code)}"><span>${esc(e.label)} · ${wdMoney(e.price)}</span></label>`).join('')}
        ${extras.map(x=>`<label class="svc-point"><input type="checkbox" class="mb-extra" value="${x.id}"><span>${esc(x.name)} · ${wdMoney(x.price)}</span></label>`).join('')}
      </div></section>`:''}
      <section class="mb-section"><h3>Estado y pago</h3>
        <div class="svc-form-row svc-form-row-2">
          <fieldset class="svc-fieldset"><legend>Reserva</legend><div class="mb-seg"><label><input type="radio" name="mb-status" value="confirmed" checked><span>Confirmada</span></label><label><input type="radio" name="mb-status" value="pending"><span>Pendiente</span></label></div></fieldset>
          <fieldset class="svc-fieldset"><legend>Pago</legend><div class="mb-seg"><label><input type="radio" name="mb-pay" value="required" checked><span>Por cobrar</span></label><label><input type="radio" name="mb-pay" value="paid"><span>Pagado</span></label></div></fieldset>
        </div>
        <div class="svc-field" id="mb-method-field" hidden><label for="mb-method">Forma de pago</label><select id="mb-method">${PAYMENT_METHODS.map(m=>`<option>${m}</option>`).join('')}</select></div>
      </section>
      <section class="mb-section mb-quote-box"><div id="mb-quote" class="mb-quote" aria-live="polite"></div>
        <div class="svc-field mb-override"><label for="mb-override">Precio final (opcional)</label><label class="svc-money"><input id="mb-override" type="number" min="0" step="0.01" placeholder="Igual que el calculado"><span>€</span></label><small>Para descuentos o precios pactados.</small></div>
      </section>
      <section class="mb-section"><div class="svc-form-row svc-form-row-2">
        <div class="svc-field"><label for="mb-notes">Nota visible para el cliente</label><textarea id="mb-notes" rows="2" maxlength="2000" placeholder="Punto de encuentro, qué traer…"></textarea></div>
        <div class="svc-field"><label for="mb-internal">Nota interna</label><textarea id="mb-internal" rows="2" maxlength="2000" placeholder="Solo la ve tu equipo"></textarea></div>
      </div></section>
    </form>`;
    const {el,close}=wdOpenModal({id:'manual-booking-modal',size:'lg',title:'Nueva reserva',subtitle:'Para reservas por teléfono, en el mostrador, por email o de una agencia.',body,
      footer:`<button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="mb-form" class="btn btn-primary">Guardar reserva</button>`});
    let slotId=0; let quoteSeq=0, qTimer=0;
    const svc=()=>services.find(s=>String(s.id)===el.querySelector('#mb-service').value);
    const slotObj=()=>(svc()?.slots||[]).find(x=>Number(x.id)===slotId);
    const renderSlots=()=>{const s=svc(); const slots=(s?.slots||[]).slice(0,24); const wrap=el.querySelector('#mb-slots');
      if(opts.slotId&&slots.some(x=>Number(x.id)===Number(opts.slotId))){slotId=Number(opts.slotId);opts.slotId=0;}
      if(slotId&&!slots.some(x=>Number(x.id)===slotId))slotId=0;
      wrap.innerHTML=slots.map(sl=>`<button type="button" class="mb-slot ${Number(sl.id)===slotId?'active':''} ${Number(sl.spots_available)<=0?'is-full':''}" data-slot="${sl.id}"><strong>${esc(wdDay(sl.slot_date))}</strong><span>${esc(sl.slot_time)}</span><small>${Number(sl.spots_available)<=0?'Completa':sl.spots_available+' libres'}</small></button>`).join('')+`<button type="button" class="mb-slot mb-slot-other ${slotId===0?'active':''}" data-slot="0"><strong>Otra fecha</strong><span>sin salida</span><small>${s&&s.service_type==='alquiler_equipo'?'alquiler':'fecha libre'}</small></button>`;
      el.querySelector('#mb-custom').hidden=slotId!==0; syncPax(); quote(); };
    const syncPax=()=>{const sl=slotObj(); const hint=el.querySelector('#mb-pax-hint'); hint.textContent=sl?`${sl.spots_available} plazas libres en esta salida.`:''; hint.className=sl&&Number(el.querySelector('#mb-pax').value)>Number(sl.spots_available)?'mb-warn':'';};
    const quote=()=>{clearTimeout(qTimer); qTimer=setTimeout(async()=>{const seq=++quoteSeq; const p=new URLSearchParams({center_id:String(state.me?.user?.center_id||0),service_id:el.querySelector('#mb-service').value,slot_id:String(slotId||0),participants:String(Math.max(1,+el.querySelector('#mb-pax').value||1)),extras:$$('.mb-extra:checked',el).map(x=>x.value).join(','),equipment:$$('.mb-eq:checked',el).map(x=>x.value).join(',')});
      try{const r=await api('/api/booking-quote?'+p.toString()); if(seq!==quoteSeq)return; el.dataset.quote=String(r.total);
        el.querySelector('#mb-quote').innerHTML=`<table>${r.lines.map(l=>`<tr><td>${esc(l.label)}</td><td>${l.qty} × ${wdMoney(l.unit,r.currency)}</td><td>${wdMoney(l.total,r.currency)}</td></tr>`).join('')}<tr class="mb-total"><td>Total</td><td></td><td>${wdMoney(r.total,r.currency)}</td></tr></table>`;}catch(err){el.querySelector('#mb-quote').innerHTML='';}},200);};
    el.querySelector('#mb-slots').onclick=e=>{const b=e.target.closest('.mb-slot'); if(!b)return; slotId=Number(b.dataset.slot); renderSlots();};
    el.querySelector('#mb-service').onchange=()=>{slotId=0; const s=svc(); renderSlots(); if(s&&!slotId&&s.slots?.length){slotId=Number(s.slots.find(x=>Number(x.spots_available)>0)?.id||0); renderSlots();}};
    el.querySelector('#mb-pax').oninput=()=>{syncPax();quote();};
    el.querySelector('#mb-form').addEventListener('change',e=>{ if(e.target.matches('.mb-eq,.mb-extra'))quote(); if(e.target.name==='mb-pay')el.querySelector('#mb-method-field').hidden=e.target.value!=='paid'; });
    if(opts.date){el.querySelector('#mb-date').value=opts.date;}
    { const s=svc(); if(!opts.slotId&&!opts.date&&s?.slots?.length) slotId=Number(s.slots.find(x=>Number(x.spots_available)>0)?.id||0); renderSlots(); }
    el.querySelector('#mb-form').onsubmit=async e=>{e.preventDefault();
      const name=el.querySelector('#mb-name').value.trim(); if(!name){el.querySelector('#mb-name').focus();toast('Escribe el nombre del cliente.');return;}
      if(!slotId&&!el.querySelector('#mb-date').value){el.querySelector('#mb-date').focus();toast('Elige una salida o indica la fecha.');return;}
      const email=el.querySelector('#mb-email').value.trim(); if(email&&!el.querySelector('#mb-email').checkValidity()){el.querySelector('#mb-email').focus();toast('Revisa el email.');return;}
      const pay=el.querySelector('input[name="mb-pay"]:checked').value;
      const payload={fullname:name,phone:el.querySelector('#mb-phone').value.trim(),email,service_id:+el.querySelector('#mb-service').value,slot_id:slotId||null,booking_date:el.querySelector('#mb-date').value,booking_time:el.querySelector('#mb-time').value,participants:Math.max(1,+el.querySelector('#mb-pax').value||1),equipment_codes:$$('.mb-eq:checked',el).map(x=>x.value),extra_ids:$$('.mb-extra:checked',el).map(x=>+x.value),status:el.querySelector('input[name="mb-status"]:checked').value,payment_status:pay,payment_method:pay==='paid'?el.querySelector('#mb-method').value:'',price_override:el.querySelector('#mb-override').value,notes:el.querySelector('#mb-notes').value,internal_notes:el.querySelector('#mb-internal').value};
      const submit=el.querySelector('button[type="submit"]'); submit.disabled=true;
      try{const r=await postJSON('/api/center/bookings/manual',payload);close();toast(`Reserva #${r.id} guardada · ${wdMoney(r.total)}`);opts.onSaved?.(r);}catch(err){toast(err.message);submit.disabled=false;}
    };
  }

  // ---------- Experiences (center and freelance) ----------
  // ---------------------------------------------------------------------------
  // Imágenes editables (v50.25)
  // ---------------------------------------------------------------------------
  async function uploadForm(url, fields, file){
    const fd=new FormData(); Object.entries(fields||{}).forEach(([k,v])=>fd.append(k,v)); if(file) fd.append('file',file);
    return api(url,{method:'POST',body:fd});
  }
  const IMG_HINT='Fotos reales en JPG, PNG o WEBP, máximo 6 MB. Si la foto no es tuya, usa una con licencia libre e indica el autor en «Crédito».';

  // ---------------------------------------------------------------------------
  // Colaboradores y ofertas destacadas de la portada (v50.26)
  // ---------------------------------------------------------------------------
  function promoHref(u){ u=String(u||''); return /^(https?:\/\/|#\/)/i.test(u)?u:''; }
  function promoLinkAttrs(u){ const h=promoHref(u); if(!h) return ''; return h.startsWith('#/')?`href="${escapeHtml(h)}"`:`href="${escapeHtml(h)}" target="_blank" rel="noopener sponsored"`; }
  function marqueeTrack(items,secsPerItem=3.2){
    if(!items.length) return '';
    let row=items.join(''); const reps=Math.max(1,Math.ceil(10/items.length)); row=Array.from({length:reps},()=>row).join('');
    const dur=Math.max(30,items.length*reps*secsPerItem);
    return `<div class="hm-marquee-track" style="--dur:${dur}s"><div class="hm-marquee-row">${row}</div><div class="hm-marquee-row" aria-hidden="true">${row.replace(/<a /g,'<a tabindex="-1" ')}</div></div>`;
  }
  function partnerMarquee(list){
    const item=p=>{ const inner=p.image_path?`<img src="${escapeHtml(p.image_path)}" alt="${escapeHtml(p.title)}" loading="lazy">`:`<span class="hm-logo-text">${escapeHtml(p.title)}</span>`; const attrs=promoLinkAttrs(p.url); return attrs?`<a class="hm-logo" ${attrs} title="${escapeHtml(p.title)}">${inner}</a>`:`<span class="hm-logo" title="${escapeHtml(p.title)}">${inner}</span>`; };
    // Repeat the row so the band always fills the screen and loops seamlessly.
    let row=list.map(item).join(''); let reps=Math.max(1,Math.ceil(12/Math.max(list.length,1)));
    row=Array.from({length:reps},()=>row).join('');
    const dur=Math.max(24,list.length*reps*3.2);
    return `<div class="hm-marquee-track" style="--dur:${dur}s"><div class="hm-marquee-row">${row}</div><div class="hm-marquee-row" aria-hidden="true">${row.replace(/<a /g,'<a tabindex="-1" ')}</div></div>`;
  }
  function offerCard(o){ const attrs=promoLinkAttrs(o.url); const tag=attrs?'a':'div';
    return `<${tag} class="hm-offer" ${attrs}><div class="hm-offer-media"><img src="${escapeHtml(o.image_path)}" alt="" loading="lazy"><span class="hm-offer-label">Patrocinado</span></div><div class="hm-offer-body"><h3>${escapeHtml(o.title)}</h3>${o.subtitle?`<p>${escapeHtml(o.subtitle)}</p>`:''}${attrs?'<span class="hm-offer-go">Ver oferta →</span>':''}</div></${tag}>`; }

  async function renderPromosManager(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml; const refresh=()=>renderPromosManager(mountId);
    let d; try{ d=await api('/api/admin/site-promos'); }catch(err){ mount.innerHTML=`<div class="empty"><h3>No se ha podido cargar</h3><p>${esc(err.message)}</p></div>`; return; }
    const st=d.settings||{}; const today=new Date().toISOString().slice(0,10);
    const state_=p=>!p.active?['Pausado','warn']:(p.starts_on&&p.starts_on>today)?['Programado','warn']:(p.ends_on&&p.ends_on<today)?['Caducado','bad']:(p.kind==='offer'&&!p.image_path)?['Falta la foto','bad']:['Visible','good'];
    const row=p=>{ const s=state_(p); return `<article class="pr-row" data-id="${p.id}"><div class="pr-thumb ${p.kind==='partner'?'is-logo':''}">${p.image_path?`<img src="${esc(p.image_path)}" alt="">`:`<span>${esc(initials(p.title))}</span>`}</div>
      <div class="pr-main"><strong>${esc(p.title)}</strong><small>${esc([p.subtitle,promoHref(p.url)?p.url.replace(/^https?:\/\//,''):'Sin enlace'].filter(Boolean).join(' · '))}</small><small>${p.starts_on||p.ends_on?`${p.starts_on?'Desde '+esc(wdDay(p.starts_on)):''}${p.ends_on?' hasta '+esc(wdDay(p.ends_on)):''}`:'Sin fechas'} · Orden ${Number(p.sort_order||0)}</small></div>
      <span class="status ${s[1]}">${s[0]}</span><div class="pr-actions"><button type="button" class="btn pr-edit">Editar</button><button type="button" class="btn pr-del">Eliminar</button></div></article>`; };
    const partners=d.items.filter(p=>p.kind==='partner'), offers=d.items.filter(p=>p.kind==='offer');
    mount.innerHTML=`<section class="pr-module"><div class="svc-head"><div><p class="eyebrow">Portada</p><h2>Patrocinio y colaboradores</h2><p>Lo que pongas aquí aparece en la parte baja de la portada: la banda de logos que se desplaza y las ofertas destacadas.</p></div></div>
      <section class="cb-panel pr-panel"><div class="cb-panel-head"><div><h3>Banda de colaboradores</h3><p>Logos de patrocinadores, marcas y partners. Mejor en PNG con fondo transparente, horizontal (por ejemplo 400 × 160 px).</p></div><button type="button" class="btn btn-primary pr-new" data-kind="partner">+ Añadir colaborador</button></div>
        <div class="pr-list">${partners.map(row).join('')||'<div class="pr-empty">Todavía no hay colaboradores. Mientras no haya ninguno, la banda no se muestra.</div>'}</div></section>
      <section class="cb-panel pr-panel"><div class="cb-panel-head"><div><h3>Ofertas destacadas</h3><p>Viajes, promociones o anuncios con foto. Se muestran hasta tres a la vez, por orden, y desaparecen solas al pasar la fecha de fin.</p></div><button type="button" class="btn btn-primary pr-new" data-kind="offer">+ Añadir oferta</button></div>
        <div class="pr-list">${offers.map(row).join('')||'<div class="pr-empty">Todavía no hay ofertas. Mientras no haya ninguna, la sección no se muestra.</div>'}</div></section>
      <section class="cb-panel pr-panel"><div class="cb-panel-head"><div><h3>Contacto para marcas</h3><p>Si indicas un email, la portada muestra el bloque «Colabora con WORLDIVES» con un botón que abre un correo a esa dirección.</p></div></div>
        <form id="pr-settings" class="pr-settings"><label class="field"><span>Email de contacto</span><input id="pr-email" type="email" maxlength="160" value="${esc(st.partners_email||'')}" placeholder="partners@tudominio.com"></label><label class="field"><span>Texto (opcional)</span><input id="pr-text" maxlength="200" value="${esc(st.partners_text||'')}" placeholder="Llega a buceadores de todo el mundo que están eligiendo su próxima inmersión."></label><label class="field"><span>Mínimo de centros para mostrar «Centros asociados»</span><input id="pr-minc" type="number" min="1" max="100" value="${esc(st.partners_min_centers||'6')}"></label><button class="btn btn-primary" type="submit">Guardar</button></form></section></section>`;
    mount.querySelector('.pr-module').insertAdjacentHTML('beforeend',`<section class="cb-panel pr-panel"><div class="cb-panel-head"><div><h3>Registro de patrocinios</h3><p>Quién ha patrocinado cada logo u oferta, con fechas e importe. Se conserva aunque borres la publicación.</p></div></div>
      ${(d.sponsorships||[]).length?`<div class="table-wrap"><table class="data-table"><thead><tr><th>Patrocinador</th><th>Dónde</th><th>Fechas</th><th>Importe</th><th>Estado</th></tr></thead><tbody>${d.sponsorships.map(x=>`<tr><td>${esc(x.sponsor_name)}<small>${esc(x.sponsor_contact||'')}</small></td><td>${x.placement==='band'?'Banda de colaboradores':'Oferta destacada'} #${x.ref_id}</td><td>${esc([x.starts_on,x.ends_on].filter(Boolean).map(wdDay).join(' – ')||'Sin fechas')}</td><td>${x.amount!=null?wdMoney(x.amount,x.currency):'—'}</td><td>${x.ended_at?'Terminado '+esc(fmtDate(x.ended_at)):'Activo'}</td></tr>`).join('')}</tbody></table></div>`:'<p class="acc-empty">Todavía no hay patrocinios registrados.</p>'}</section>`);
    translateTree(mount);
    $$('.pr-new',mount).forEach(b=>b.onclick=()=>openPromoForm({kind:b.dataset.kind},refresh));
    $$('.pr-row',mount).forEach(r=>{ const p=d.items.find(x=>String(x.id)===r.dataset.id);
      $('.pr-edit',r).onclick=()=>openPromoForm(p,refresh);
      $('.pr-del',r).onclick=async()=>{ if(!confirm(`¿Eliminar «${p.title}»?`)) return; try{ await postJSON('/api/admin/site-promos/delete',{id:p.id}); toast('Eliminado.'); refresh(); }catch(err){ toast(err.message); } }; });
    $('#pr-settings',mount).onsubmit=async e=>{ e.preventDefault(); try{ await postJSON('/api/admin/site-promos/settings',{partners_email:$('#pr-email',mount).value.trim(),partners_text:$('#pr-text',mount).value.trim(),partners_min_centers:$('#pr-minc',mount).value}); toast('Contacto guardado.'); }catch(err){ toast(err.message); } };
  }
  function openPromoForm(p,onDone){
    const esc=escapeHtml; const isOffer=p.kind==='offer'; const editing=!!p.id;
    const body=`<form id="pr-form" class="svc-form" novalidate>
      <div class="pr-form-media"><div class="pr-preview ${isOffer?'':'is-logo'}">${p.image_path?`<img src="${esc(p.image_path)}" alt="">`:`<span>${isOffer?'Sin foto':'Sin logo'}</span>`}</div>
        <div><label class="btn pr-pick">${p.image_path?'Cambiar':'Subir'} ${isOffer?'foto':'logo'}<input type="file" id="pr-file" accept="image/jpeg,image/png,image/webp" hidden></label>${p.image_path?'<label class="pr-remove"><input type="checkbox" id="pr-remove"> Quitar imagen</label>':''}<small>${isOffer?'Foto horizontal, 1200 × 800 px o más. Obligatoria para que la oferta se vea.':'PNG transparente o JPG, horizontal. Si no subes logo se muestra el nombre.'} Máximo 6 MB.</small></div></div>
      <div class="svc-field"><label for="pr-title">${isOffer?'Título':'Nombre'}</label><input id="pr-title" required maxlength="120" value="${esc(p.title||'')}" placeholder="${isOffer?'Mar Rojo en vida a bordo · 7 noches':'Nombre de la marca'}"></div>
      ${isOffer?`<div class="svc-field"><label for="pr-sub">Descripción corta</label><input id="pr-sub" maxlength="240" value="${esc(p.subtitle||'')}" placeholder="Salidas en marzo y abril desde 1.290 €"></div>`:''}
      <p class="svc-note">${wdIcon('tag',14)} Se muestra siempre con la etiqueta <b>«Patrocinado»</b>. No se puede cambiar.</p>
      <fieldset class="svc-fieldset"><legend>Registro del patrocinio</legend>
        <div class="svc-field"><label for="pr-sponsor">Quién patrocina (empresa o persona que paga)</label><input id="pr-sponsor" maxlength="160" required value="${esc(p.sponsor?.sponsor_name||(!isOffer?p.title||'':''))}"></div>
        <div class="svc-form-row"><div class="svc-field"><label for="pr-contact">Contacto</label><input id="pr-contact" maxlength="200" value="${esc(p.sponsor?.sponsor_contact||'')}" placeholder="email o teléfono"></div>
          <div class="svc-field"><label for="pr-amount">Importe acordado (€)</label><input id="pr-amount" type="number" min="0" step="0.01" value="${p.sponsor?.amount??''}"></div></div>
        <div class="svc-field"><label for="pr-notes">Notas internas</label><input id="pr-notes" maxlength="500" value="${esc(p.sponsor?.notes||'')}"></div></fieldset>
      <div class="svc-field"><label for="pr-url">Enlace</label><input id="pr-url" maxlength="500" value="${esc(p.url||'')}" placeholder="https://… o #/experiencias"></div>
      <div class="svc-form-row svc-form-row-3"><div class="svc-field"><label for="pr-from">Desde</label><input id="pr-from" type="date" value="${esc(p.starts_on||'')}"></div><div class="svc-field"><label for="pr-to">Hasta</label><input id="pr-to" type="date" value="${esc(p.ends_on||'')}"></div><div class="svc-field"><label for="pr-order">Orden</label><input id="pr-order" type="number" min="0" max="999" value="${Number(p.sort_order||0)}"></div></div>
      <label class="pr-active"><input type="checkbox" id="pr-active" ${p.active===0?'':'checked'}> Visible en la portada</label>
    </form>`;
    const {el,close}=wdOpenModal({id:'promo-form',title:`${editing?'Editar':'Nuevo'} ${isOffer?'oferta destacada':'colaborador'}`,body,footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="pr-save">Guardar</button>'});
    let file=null;
    el.querySelector('#pr-file').onchange=e=>{ file=e.target.files[0]||null; if(file){ const u=URL.createObjectURL(file); el.querySelector('.pr-preview').innerHTML=`<img src="${u}" alt="">`; const r=el.querySelector('#pr-remove'); if(r) r.checked=false; } };
    el.querySelector('#pr-save').onclick=async()=>{ const title=el.querySelector('#pr-title').value.trim(); if(!title){ el.querySelector('#pr-title').focus(); toast('Escribe el nombre.'); return; }
      const fields={id:String(p.id||0),kind:p.kind,title,url:el.querySelector('#pr-url').value.trim(),starts_on:el.querySelector('#pr-from').value,ends_on:el.querySelector('#pr-to').value,sort_order:el.querySelector('#pr-order').value||'0',active:el.querySelector('#pr-active').checked?'1':'0'};
      if(isOffer){ fields.subtitle=el.querySelector('#pr-sub').value.trim(); }
      Object.assign(fields,{sponsor_name:el.querySelector('#pr-sponsor').value.trim(),sponsor_contact:el.querySelector('#pr-contact').value.trim(),sponsor_amount:el.querySelector('#pr-amount').value,sponsor_notes:el.querySelector('#pr-notes').value.trim()});
      if(!fields.sponsor_name){ el.querySelector('#pr-sponsor').focus(); toast('Indica quién patrocina.'); return; }
      if(el.querySelector('#pr-remove')?.checked) fields.remove_image='1';
      const btn=el.querySelector('#pr-save'); btn.disabled=true;
      try{ await uploadForm('/api/admin/site-promos',fields,file); toast('Guardado.'); close(); onDone?.(); }catch(err){ toast(err.message); btn.disabled=false; } };
  }

  // Pestaña «Pagos» (administrador). Since v50.34 the money goes straight to each provider (direct charges):
  // the administrator sees payments and refunds, the providers' income by currency, and marks incidents.
  const PO_INCIDENT={refund_pending:'Devolución pendiente del prestador',dispute:'Disputa abierta',dispute_closed:'Disputa cerrada',customer_complaint:'Queja del cliente',resolved:'Resuelta'};
  async function renderAdminPayments(mountId,filter=''){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/admin/payments'+(filter?'?status='+filter:'')); }catch(err){ mount.innerHTML=`<div class="empty"><h3>No se han podido cargar los pagos</h3><p>${esc(err.message)}</p></div>`; return; }
    const sm=k=>d.summary[k]||{n:0,amount:0};
    const incidents=d.items.filter(o=>o.incident&&o.incident!=='resolved').length;
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Seguridad de cobros</p><h2>Pagos online</h2><p>Cada cobro va directamente a la cuenta de Stripe del centro o profesional (cargo directo). WORLDIVES no cobra comisión ni mueve dinero: aquí ves los pagos y las devoluciones y marcas incidencias.</p></div></div>
      <div class="ap-checks"><span class="${d.stripe_ready?'is-ok':'is-bad'}">${wdIcon(d.stripe_ready?'check':'alert',15)} Clave de Stripe ${d.stripe_ready?'configurada':'sin configurar'}</span><span class="${d.webhook_ready?'is-ok':'is-bad'}">${wdIcon(d.webhook_ready?'check':'alert',15)} Webhook de la plataforma ${d.webhook_ready?'firmado':'sin configurar'}</span><span class="${d.connect_webhook_ready?'is-ok':'is-bad'}">${wdIcon(d.connect_webhook_ready?'check':'alert',15)} Webhook de Connect ${d.connect_webhook_ready?'firmado':'sin configurar'}</span><span class="is-ok">${wdIcon('shield',15)} Importe y moneda comprobados con Stripe</span></div>
      <div class="acc-kpis">${(d.income||[]).length?d.income.map(x=>accKpi('chart',wdMoney(x.net,x.currency),`Ingresos de los prestadores (${x.currency}) · ${x.n} ${x.n===1?'cobro':'cobros'}`)).join(''):accKpi('chart',wdMoney(0,'EUR'),'Ingresos de los prestadores')}${accKpi('clock',sm('pending').n,'en curso')}${accKpi('alert',sm('review').n+incidents,'en revisión / incidencias',null,(sm('review').n+incidents)>0)}${accKpi('receipt',(d.pending_refunds||[]).length,'devoluciones pendientes',null,(d.pending_refunds||[]).length>0)}</div>
      <div class="ap-filter">${[['','Todos'],['incident','Incidencias'],['review','En revisión'],['pending','En curso'],['paid','Cobrados'],['partially_refunded','Devolución parcial'],['refunded','Devueltos'],['expired','Caducados']].map(([k,l])=>`<button type="button" class="cd-chip" data-f="${k}" aria-pressed="${k===filter}">${l}</button>`).join('')}</div>
      ${d.items.length?`<div class="table-wrap"><table class="ap-table"><thead><tr><th>Ref.</th><th>Fecha</th><th>Cliente</th><th>Prestador</th><th>Importe</th><th>Tipo</th><th>Estado</th><th></th></tr></thead><tbody>${d.items.map(o=>{ const st=PAY_ORDER_STATE[o.status]||[o.status,'muted']; const diff=o.amount_received!=null&&Math.abs(o.amount_received-o.amount)>0.009;
        return `<tr data-id="${o.id}"><td>PAY-${String(o.id).padStart(5,'0')}${o.booking_id?`<small><a href="#/reserva?id=${o.booking_id}">WOD-${String(o.booking_id).padStart(6,'0')}</a></small>`:''}</td><td>${esc(fmtDate(o.created_at))}</td><td>${esc(o.fullname||'')}<small>${esc(o.email||'')}</small></td><td>${esc(o.center_name||'—')}</td>
          <td><b>${wdMoney(o.amount,o.currency)}</b>${diff?`<small class="ap-diff">Recibido ${wdMoney(o.amount_received,o.currency)}</small>`:''}${o.refunded_total>0?`<small>Devuelto ${wdMoney(o.refunded_total,o.currency)}</small>`:''}</td><td>${o.payment_kind==='deposit'?'Señal':'Total'}<small>${o.charge_type==='direct'?'Cargo directo':'Cargo antiguo (con comisión)'}</small></td>
          <td><span class="pr-pill is-${st[1]}">${esc(st[0])}</span>${o.incident?`<small class="ap-diff">${esc(PO_INCIDENT[o.incident]||o.incident)}${o.incident_note?' · '+esc(o.incident_note):''}</small>`:''}</td>
          <td class="ap-act">${o.status==='review'?'<button type="button" class="btn btn-primary ap-accept">Aceptar</button><button type="button" class="btn ap-refund">Pedir devolución</button>':''}<button type="button" class="btn ap-incident">Incidencia</button>${o.receipt_url?`<a class="btn" href="${esc(o.receipt_url)}" target="_blank" rel="noopener">Recibo</a>`:''}</td></tr>`; }).join('')}</tbody></table></div>`:'<div class="empty"><h3>No hay pagos con este filtro</h3></div>'}
      <section class="cb-panel"><div class="cb-panel-head"><div><h3>Devoluciones pendientes de los prestadores</h3><p>Cancelaciones con devolución según la política del prestador que todavía no se han hecho (se recuerda al prestador a las 72 h).</p></div></div>
        ${(d.pending_refunds||[]).length?`<div class="acc-list">${d.pending_refunds.map(r=>`<div class="acc-row"><span class="acc-row-main"><strong><a href="#/reserva?id=${r.booking_id}">WOD-${String(r.booking_id).padStart(6,'0')}</a> · ${esc(r.center_name||'')}</strong><small>${wdMoney(r.refund_proposed,r.currency)} · ${r.refund_status==='failed'?'falló':'propuesta'} ${esc(fmtDate(r.refund_proposed_at))}</small></span></div>`).join('')}</div>`:'<p class="acc-empty">No hay devoluciones pendientes.</p>'}</section>
      <section class="cb-panel"><div class="cb-panel-head"><div><h3>Últimas devoluciones</h3></div></div>
        ${(d.refunds||[]).length?`<div class="table-wrap"><table class="data-table"><thead><tr><th>Fecha</th><th>Reserva</th><th>Prestador</th><th>Importe</th><th>Origen</th><th>Estado</th></tr></thead><tbody>${d.refunds.map(r=>`<tr><td>${esc(fmtDate(r.created_at))}</td><td>${r.booking_id?`<a href="#/reserva?id=${r.booking_id}">WOD-${String(r.booking_id).padStart(6,'0')}</a>`:'—'}</td><td>${esc(r.center_name||'—')}</td><td>${wdMoney(r.amount,r.currency)}</td><td>${esc({panel:'Panel del prestador',stripe:'Panel de Stripe',center_cancel:'Cancelación del prestador',reject:'Solicitud rechazada',system:'Automática',migration:'Histórico'}[r.source]||r.source)}</td><td>${esc({succeeded:'Hecha',pending:'En curso',failed:'Fallida'}[r.status]||r.status)}</td></tr>`).join('')}</tbody></table></div>`:'<p class="acc-empty">Todavía no hay devoluciones.</p>'}</section></section>`;
    translateTree(mount);
    $$('.ap-filter .cd-chip',mount).forEach(b=>b.onclick=()=>renderAdminPayments(mountId,b.dataset.f));
    $$('.ap-table tr[data-id]',mount).forEach(tr=>{ const id=+tr.dataset.id;
      const send=async action=>{ if(!confirm(action==='accept'?'¿Aceptar el pago y confirmar la reserva?':'¿Pedir al prestador que devuelva este pago? Se le avisa por email y al cliente en sus avisos.')) return; try{ await postJSON('/api/admin/payments/resolve',{id,action}); toast(action==='accept'?'Pago aceptado y reserva confirmada.':'Devolución pedida al prestador.'); renderAdminPayments(mountId,filter); }catch(err){ toast(err.message); } };
      $('.ap-accept',tr)?.addEventListener('click',()=>send('accept')); $('.ap-refund',tr)?.addEventListener('click',()=>send('refund'));
      $('.ap-incident',tr)?.addEventListener('click',()=>{ const o=d.items.find(x=>x.id===id)||{};
        const {el,close}=wdOpenModal({id:'po-incident',size:'sm',title:'Marcar incidencia',subtitle:`PAY-${String(id).padStart(5,'0')}`,
          body:`<div class="field"><label for="pi-kind">Incidencia</label><select id="pi-kind"><option value="">Ninguna</option>${Object.entries(PO_INCIDENT).map(([k,l])=>`<option value="${k}" ${o.incident===k?'selected':''}>${l}</option>`).join('')}</select></div><div class="field"><label for="pi-note">Nota interna</label><input id="pi-note" maxlength="500" value="${esc(o.incident_note||'')}"></div>`,
          footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="pi-ok">Guardar</button>'});
        $('#pi-ok',el).onclick=async()=>{ try{ await postJSON('/api/admin/payments/incident',{order_id:id,incident:$('#pi-kind',el).value||null,note:$('#pi-note',el).value}); close(); toast('Incidencia guardada.'); renderAdminPayments(mountId,filter); }catch(err){ toast(err.message); } }; }); });
  }

  // Pestaña «Imágenes de la web» (administrador)
  async function renderSiteMediaManager(mountId){
    const mount=document.getElementById(mountId); if(!mount) return;
    const refresh=()=>renderSiteMediaManager(mountId);
    let d; try{ d=await api('/api/admin/site-media'); }catch(err){ mount.innerHTML=`<div class="empty"><h3>No se han podido cargar las imágenes</h3><p>${escapeHtml(err.message)}</p></div>`; return; }
    const groups={}; (d.slots||[]).forEach(s=>(groups[s.group]??=[]).push(s));
    const card=s=>{ const it=d.items[s.key]||{}; return `<article class="mm-card" data-key="${escapeHtml(s.key)}">
      <div class="mm-preview"><img src="${escapeHtml(it.url||s.default)}" alt="" loading="lazy"><span class="mm-badge ${it.custom?'is-custom':''}">${it.custom?'Personalizada':'Original'}</span></div>
      <div class="mm-body"><strong>${escapeHtml(s.label)}</strong><small>${escapeHtml(s.where)} · ${escapeHtml(s.size)} px</small>
        <label class="mm-credit"><span>Crédito</span><input type="text" maxlength="200" value="${escapeHtml(it.credit||'')}" placeholder="Foto: autor / licencia"></label>
        <div class="mm-actions"><label class="btn btn-primary mm-file">Cambiar foto<input type="file" accept="image/jpeg,image/png,image/webp" hidden></label><button type="button" class="btn mm-save-credit">Guardar crédito</button>${it.custom?'<button type="button" class="btn mm-reset">Restaurar original</button>':''}</div>
      </div></article>`; };
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Escaparate</p><h2>Imágenes de la web</h2><p>Portadas de cada sección y foto de cada tipo de buceo. Los cambios se ven al momento.</p></div></div>
      <div class="ex-tip">${wdIcon('bolt',18)}<p>${IMG_HINT} Recomendado: fotos horizontales, nítidas, sin texto ni marcas de agua, y con luz natural.</p></div>
      ${Object.entries(groups).map(([g,list])=>`<h3 class="mm-group">${escapeHtml(g)}</h3><div class="mm-grid">${list.map(card).join('')}</div>`).join('')}</section>`;
    const send=async(key,fields,file,msg)=>{ try{ await uploadForm('/api/admin/site-media',{key,...fields},file); await loadSiteMedia(); toast(msg); refresh(); }catch(err){ toast(err.message); } };
    $$('.mm-card',mount).forEach(c=>{ const key=c.dataset.key, credit=()=>$('.mm-credit input',c).value;
      $('.mm-file input',c).onchange=e=>{ const f=e.target.files[0]; if(f) send(key,{credit:credit()},f,'Foto actualizada.'); };
      $('.mm-save-credit',c).onclick=()=>send(key,{credit:credit()},null,'Crédito guardado.');
      $('.mm-reset',c)?.addEventListener('click',()=>{ if(confirm('¿Volver a la foto original?')) send(key,{reset:'1'},null,'Foto original restaurada.'); });
    });
  }

  // ---------------------------------------------------------------------------
  // Temas de temporada (v50.29): fotos y color de la web según la época del año y el hemisferio.
  // ---------------------------------------------------------------------------
  const TH_MONTHS=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
  const thDate=md=>{ if(!md) return '—'; const [m,d]=md.split('-').map(Number); return new Date(2024,m-1,d).toLocaleDateString(wdLocale(),{day:'numeric',month:'long'}); };
  const TH_SCOPES={all:'Todo el mundo',north:'Hemisferio norte',south:'Hemisferio sur'};
  function themeWhen(t){ return t.mode==='always'?'Activado a mano, sin fechas':t.mode==='off'?'Desactivado':`Cada año del ${thDate(t.starts_on)} al ${thDate(t.ends_on)}`; }
  async function renderThemeManager(mountId){
    const mount=document.getElementById(mountId); if(!mount) return;
    const refresh=()=>renderThemeManager(mountId);
    let d; try{ d=await api('/api/admin/site-themes'); }catch(err){ mount.innerHTML=`<div class="empty"><h3>No se han podido cargar los temas</h3><p>${escapeHtml(err.message)}</p></div>`; return; }
    const byId=Object.fromEntries(d.themes.map(t=>[t.id,t]));
    const nowName=h=>d.current[h]?escapeHtml(byId[d.current[h]]?.name||''):'Aspecto original';
    const swatch=a=>{ const x=THEME_ACCENTS[a]||THEME_ACCENTS.oceano; return `<span class="th-swatch" style="--a:${x.v[0]};--b:${x.v[1]};--c:${x.v[2]}" aria-hidden="true"></span>`; };
    const status=t=>{ const live=t.id===d.current.north||t.id===d.current.south; return t.mode==='off'?'<span class="status">Desactivado</span>':live?`<span class="status good">En la web ahora${d.current.north!==d.current.south?` · ${t.id===d.current.north?'norte':'sur'}`:''}</span>`:(t.live_north||t.live_south)?'<span class="status warn">En fechas · otro tema tiene prioridad</span>':'<span class="status">Programado</span>'; };
    const card=t=>{ const n=Object.keys(t.media||{}).length, cover=t.media?.['hero:home']?.url||d.slots.find(s=>s.key==='hero:home')?.default;
      return `<article class="th-card" data-id="${t.id}"><div class="th-cover"><img src="${escapeHtml(cover||'')}" alt="" loading="lazy">${swatch(t.accent)}</div>
      <div class="th-body"><div class="th-title"><strong>${escapeHtml(t.name)}</strong>${status(t)}</div>
        <small>${escapeHtml(themeWhen(t))} · ${escapeHtml(TH_SCOPES[t.scope]||TH_SCOPES.all)}</small>
        ${t.ribbon?`<small class="th-ribbon-txt">«${escapeHtml(t.ribbon)}»</small>`:''}
        <small>${n?`${n} foto${n>1?'s':''} propia${n>1?'s':''}`:'Usa las fotos normales de la web'} · color ${escapeHtml(THEME_ACCENTS[t.accent]?.label||'Océano')}</small>
        <div class="th-actions"><button type="button" class="btn btn-primary th-edit">Editar</button><button type="button" class="btn th-photos">Fotos</button><button type="button" class="btn th-preview">Vista previa</button><button type="button" class="btn th-del" aria-label="Eliminar tema ${escapeHtml(t.name)}">Eliminar</button></div>
      </div></article>`; };
    mount.innerHTML=`<section class="mm-module th-module"><div class="svc-head"><div><p class="eyebrow">Apariencia</p><h2>Temas de temporada</h2><p>Cambia las fotos y el color de la web según la época del año o la zona del visitante. Fuera de las fechas de cualquier tema se ve el aspecto original.</p></div><button type="button" class="btn btn-primary" id="th-new">${wdIcon('plus',16)} Nuevo tema</button></div>
      <div class="th-now"><div><span>Ahora en el hemisferio norte</span><strong>${nowName('north')}</strong></div><div><span>Ahora en el hemisferio sur</span><strong>${nowName('south')}</strong></div></div>
      ${d.themes.length?`<div class="th-grid">${d.themes.map(card).join('')}</div>`:`<div class="empty th-empty"><h3>Todavía no hay temas</h3><p>Ejemplos: «Verano en el Mediterráneo» (1 jun – 31 ago), «Temporada de mantas» o «Navidad» con su color y sus portadas.</p></div>`}</section>`;
    $('#th-new',mount).onclick=()=>openThemeEditor(null,d,refresh);
    $$('.th-card',mount).forEach(c=>{ const t=byId[c.dataset.id];
      $('.th-edit',c).onclick=()=>openThemeEditor(t,d,refresh);
      $('.th-photos',c).onclick=()=>openThemePhotos(t,d,refresh);
      $('.th-preview',c).onclick=async()=>{ try{ sessionStorage.setItem('wd_theme_preview',String(t.id)); }catch{} await loadSiteMedia(); location.hash='#/'; };
      $('.th-del',c).onclick=async()=>{ if(!confirm(`¿Eliminar el tema «${t.name}» y sus fotos?`)) return; try{ await postJSON('/api/admin/site-themes/delete',{id:t.id}); await loadSiteMedia(); toast('Tema eliminado.'); refresh(); }catch(err){ toast(err.message); } };
    });
  }
  function openThemeEditor(t,d,onDone){
    t=t||{name:'',accent:'oceano',ribbon:'',mode:'schedule',scope:'all',starts_on:'06-01',ends_on:'08-31'};
    const [sm,sd]=(t.starts_on||'06-01').split('-').map(Number), [em,ed]=(t.ends_on||'08-31').split('-').map(Number);
    const monthSel=(id,v)=>`<select id="${id}">${TH_MONTHS.map((m,i)=>`<option value="${i+1}" ${i+1===v?'selected':''}>${new Date(2024,i,1).toLocaleDateString(wdLocale(),{month:'long'})}</option>`).join('')}</select>`;
    const body=`<form id="th-form" class="th-form">
      <label class="field"><span>Nombre del tema</span><input id="th-name" maxlength="80" required value="${escapeHtml(t.name)}" placeholder="Verano en el Mediterráneo"></label>
      <label class="field"><span>Frase en la portada <em>(opcional)</em></span><input id="th-ribbon" maxlength="90" value="${escapeHtml(t.ribbon||'')}" placeholder="Temporada de mantas en Maldivas · reserva ya"></label>
      <fieldset class="field th-accents"><legend>Color principal</legend>${Object.entries(THEME_ACCENTS).map(([k,x])=>`<label class="th-accent"><input type="radio" name="th-accent" value="${k}" ${k===t.accent?'checked':''}><span class="th-swatch" style="--a:${x.v[0]};--b:${x.v[1]};--c:${x.v[2]}"></span><b>${x.label}</b></label>`).join('')}</fieldset>
      <div class="form-grid th-grid2"><label class="field"><span>Cuándo se muestra</span><select id="th-mode"><option value="schedule" ${t.mode==='schedule'?'selected':''}>Por fechas, cada año</option><option value="always" ${t.mode==='always'?'selected':''}>Ahora, hasta que lo cambie</option><option value="off" ${t.mode==='off'?'selected':''}>Desactivado (borrador)</option></select></label>
      <label class="field"><span>Para quién</span><select id="th-scope">${Object.entries(TH_SCOPES).map(([k,v])=>`<option value="${k}" ${k===t.scope?'selected':''}>${v}</option>`).join('')}</select><small>El hemisferio se deduce de la zona horaria del visitante.</small></label></div>
      <div class="th-dates" id="th-dates"><div class="field"><span>Desde</span><div class="th-date"><input id="th-sd" type="number" min="1" max="31" value="${sd}" aria-label="Día de inicio">${monthSel('th-sm',sm)}</div></div>
        <div class="field"><span>Hasta</span><div class="th-date"><input id="th-ed" type="number" min="1" max="31" value="${ed}" aria-label="Día de fin">${monthSel('th-em',em)}</div></div></div>
      <p class="th-help">Si dos temas coinciden, gana el que se ha activado a mano y, si no, el de fechas más cortas (una campaña de dos semanas se impone a toda la temporada).</p>
    </form>`;
    const {el,close}=wdOpenModal({id:'theme-modal',title:t.id?'Editar tema':'Nuevo tema',subtitle:'Fotos y color de la web para una época del año',body,footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="th-form" class="btn btn-primary">Guardar tema</button>'});
    const sync=()=>{ $('#th-dates',el).hidden=$('#th-mode',el).value!=='schedule'; }; $('#th-mode',el).onchange=sync; sync();
    const md=(m,dd)=>`${String(m).padStart(2,'0')}-${String(Math.max(1,Math.min(31,+dd||1))).padStart(2,'0')}`;
    $('#th-form',el).onsubmit=async e=>{ e.preventDefault();
      const data={id:t.id||0,name:$('#th-name',el).value,ribbon:$('#th-ribbon',el).value,accent:($('input[name="th-accent"]:checked',el)||{}).value||'oceano',mode:$('#th-mode',el).value,scope:$('#th-scope',el).value,starts_on:md($('#th-sm',el).value,$('#th-sd',el).value),ends_on:md($('#th-em',el).value,$('#th-ed',el).value)};
      try{ const r=await postJSON('/api/admin/site-themes',data); await loadSiteMedia(); close(); toast(t.id?'Tema guardado.':'Tema creado. Ahora puedes añadirle fotos.'); onDone(); if(!t.id) openThemePhotos({...data,id:r.id,media:{}},d,onDone); }catch(err){ toast(err.message); } };
  }
  function openThemePhotos(t,d,onDone){
    const body=`<p class="pm-hint">${IMG_HINT} Las portadas sin foto propia muestran la foto normal de la web.</p><div class="mm-grid th-photo-grid">${d.slots.map(s=>{ const own=t.media?.[s.key]; return `<article class="mm-card" data-key="${escapeHtml(s.key)}">
      <div class="mm-preview"><img src="${escapeHtml(own?.url||s.default)}" alt="" loading="lazy"><span class="mm-badge ${own?'is-custom':''}">${own?'Del tema':'Normal'}</span></div>
      <div class="mm-body"><strong>${escapeHtml(s.label)}</strong><small>${escapeHtml(s.where)} · ${escapeHtml(s.size)} px</small>
        <div class="mm-actions"><label class="btn btn-primary mm-file">${own?'Cambiar':'Subir foto'}<input type="file" accept="image/jpeg,image/png,image/webp" hidden></label>${own?'<button type="button" class="btn mm-reset">Quitar</button>':''}</div></div></article>`; }).join('')}</div>`;
    const {el,close}=wdOpenModal({id:'theme-photos',size:'lg',title:`Fotos de «${t.name}»`,subtitle:'Portadas que cambian mientras el tema está activo',body,footer:'<button type="button" class="btn btn-primary" data-modal-close>Hecho</button>'});
    const send=async(key,fields,file,msg)=>{ try{ const r=await uploadForm('/api/admin/site-theme-media',{theme_id:t.id,key,...fields},file); t.media=t.media||{}; if(fields.reset) delete t.media[key]; else t.media[key]={url:r.url}; await loadSiteMedia(); toast(msg); close(); onDone(); openThemePhotos(t,d,onDone); }catch(err){ toast(err.message); } };
    $$('.mm-card',el).forEach(c=>{ const key=c.dataset.key;
      $('.mm-file input',c).onchange=e=>{ const f=e.target.files[0]; if(f) send(key,{},f,'Foto del tema guardada.'); };
      $('.mm-reset',c)?.addEventListener('click',()=>send(key,{reset:'1'},null,'Foto quitada del tema.'));
    });
  }

  // Ventana para gestionar una sola foto (destino o experiencia)
  function openPhotoModal({title,subtitle,current,upload,remove,onDone}){
    const body=`<div class="pm-wrap"><div class="pm-preview">${current?`<img src="${escapeHtml(current)}" alt="">`:'<div class="pm-empty">Sin foto propia: se muestra la del destino.</div>'}</div><p class="pm-hint">${IMG_HINT}</p></div>`;
    const {el,close}=wdOpenModal({id:'photo-modal',title,subtitle,body,footer:`${current&&remove?'<button type="button" class="btn pm-remove">Quitar foto</button>':''}<label class="btn btn-primary pm-pick">${current?'Cambiar foto':'Subir foto'}<input type="file" accept="image/jpeg,image/png,image/webp" hidden></label>`});
    el.querySelector('.pm-pick input').onchange=async e=>{ const f=e.target.files[0]; if(!f) return; try{ await upload(f); toast('Foto guardada.'); close(); onDone?.(); }catch(err){ toast(err.message); } };
    el.querySelector('.pm-remove')?.addEventListener('click',async()=>{ try{ await remove(); toast('Foto quitada.'); close(); onDone?.(); }catch(err){ toast(err.message); } });
  }

  // Fotos de un punto (centro que bucea en él, o administrador)
  async function openPointPhotos(point){
    let d; try{ d=await api('/api/dive-points/'+point.id); }catch(err){ toast(err.message); return; }
    const mine=state.me?.user?.id, admin=state.me?.user?.role==='admin';
    const photos=(d.photos||[]).filter(ph=>!/\/assets\/images\//.test(ph.image_path||''));
    const body=`<p class="pm-hint">Sube fotos reales de este punto: aparecen en su ficha pública y en el catálogo. ${IMG_HINT}</p>
      <div class="pp-photos">${photos.map(ph=>`<figure><img src="${escapeHtml(ph.image_path)}" alt=""><figcaption>${escapeHtml(ph.caption||'')}</figcaption>${(admin||ph.uploaded_by===mine)?`<button type="button" class="btn pp-photo-del" data-id="${ph.id}">Quitar</button>`:''}</figure>`).join('')||'<div class="pm-empty">Este punto todavía no tiene fotos propias.</div>'}</div>
      <label class="field"><span>Pie de foto (opcional)</span><input id="pp-caption" maxlength="300" placeholder="Ej. Gorgonias en la pared norte, 25 m"></label>`;
    const {el,close}=wdOpenModal({id:'point-photos',size:'lg',title:`Fotos · ${point.name}`,subtitle:'Máximo 24 fotos por punto',body,footer:'<button type="button" class="btn" data-modal-close>Cerrar</button><label class="btn btn-primary pm-pick">Añadir foto<input type="file" accept="image/jpeg,image/png,image/webp" hidden></label>'});
    el.querySelector('.pm-pick input').onchange=async e=>{ const f=e.target.files[0]; if(!f) return; try{ await uploadForm(`/api/dive-points/${point.id}/photos`,{caption:el.querySelector('#pp-caption').value},f); toast('Foto añadida.'); close(); openPointPhotos(point); }catch(err){ toast(err.message); } };
    $$('.pp-photo-del',el).forEach(b=>b.onclick=async()=>{ if(!confirm('¿Quitar esta foto?')) return; try{ await postJSON(`/api/dive-points/${point.id}/photos/delete`,{photo_id:+b.dataset.id}); toast('Foto quitada.'); close(); openPointPhotos(point); }catch(err){ toast(err.message); } });
  }

  async function renderProviderExperiences(mountId, role, ctx={}){
    const mount=document.getElementById(mountId); if(!mount)return;
    const refresh=()=>renderProviderExperiences(mountId,role,ctx);
    if(!mount.querySelector('.ex-module')) mount.innerHTML='<p class="wd-loading">Cargando experiencias…</p>';
    try{
      const d=await api('/api/provider/experiences'); const items=d.items||[], reqs=d.requests||[], dests=d.destinations||[]; const esc=escapeHtml;
      const stLabel=e=>!e.active?['Oculta','muted']:e.status==='published'?['Publicada','good']:e.status==='rejected'?['No aprobada','bad']:['En revisión','warn'];
      const card=e=>{const st=stLabel(e); const deps=(e.departures||[]);
        return `<article class="ex-card ${e.active?'':'is-hidden'}">
          <div class="ex-card-photo">${e.image_url?`<img src="${esc(e.image_url)}" alt="">`:`<span>${wdIcon('viaje',22)}Sin foto propia</span>`}<button type="button" class="ex-photo" data-id="${e.id}">${e.image_url?'Cambiar foto':'Añadir foto'}</button></div>
          <div class="ex-card-top"><span class="wd-pill wd-pill-${st[1]}">${st[0]}</span>${e.pending_requests?`<span class="ex-req-badge">${e.pending_requests} ${e.pending_requests===1?'solicitud':'solicitudes'}</span>`:''}</div>
          <h3>${esc(e.title)}</h3>
          <p class="ex-dest">${wdIcon('globe',15)}${esc(e.destination_title||'')}</p>
          <dl class="ex-data"><div><dt>Precio</dt><dd>${e.price!=null?wdMoney(e.price,e.currency):'Consultar'}</dd></div>
            <div><dt>${e.service_id?'Próxima salida':'Fechas'}</dt><dd>${e.service_id?(deps[0]?esc(wdDay(deps[0].slot_date)):'Sin salidas'):(e.start_date?esc(wdDay(e.start_date))+(e.end_date?' – '+esc(wdDay(e.end_date)):''):'Por confirmar')}</dd></div>
            <div><dt>Plazas</dt><dd>${e.spots_available!=null?esc(String(e.spots_available)):'—'}</dd></div></dl>
          <p class="ex-source">${e.service_id?`Sincronizada con el servicio <strong>${esc(e.service_title||'')}</strong>: precio y fechas se actualizan solos.`:'Experiencia independiente.'}</p>
          <footer>${e.active&&e.status==='published'?`<a class="svc-btn" href="#/experiencia?id=${e.travel_offer_id}">Ver en la web</a>`:''}${e.service_id?`<button type="button" class="svc-btn ex-go-services">Editar en Servicios</button>`:`<button type="button" class="svc-btn ex-edit" data-id="${e.id}">Editar</button>`}${e.active?`<button type="button" class="svc-btn svc-btn-danger ex-hide" data-id="${e.id}">Ocultar</button>`:''}</footer>
        </article>`;};
      const reqRow=r=>`<div class="ex-req-row"><div><strong>${esc(r.fullname||'')}</strong><span>${esc(r.email||'')}${r.phone?' · '+esc(r.phone):''}</span></div><div><strong>${esc(r.experience_title)}</strong><span>${Number(r.participants||1)} ${Number(r.participants)===1?'persona':'personas'} · ${esc(wdDay(String(r.created_at).slice(0,10)))}</span>${r.notes?`<em>«${esc(r.notes)}»</em>`:''}</div><div>${wdStatus(r.status)}</div><div class="ex-req-actions">${r.status==='requested'?`<button type="button" class="bk-act bk-primary ex-req" data-id="${r.id}" data-status="confirmed">Aceptar</button><button type="button" class="bk-act ex-req" data-id="${r.id}" data-status="rejected">Rechazar</button>`:r.status==='confirmed'?`<button type="button" class="bk-act ex-req" data-id="${r.id}" data-status="cancelled">Cancelar</button>`:''}</div></div>`;
      const pendingReqs=reqs.filter(r=>r.status==='requested');
      { const nav=document.querySelector('.cb-nav[data-cbtab="experiences"]'); if(nav){ let b=nav.querySelector('b'); if(pendingReqs.length){ if(!b){b=document.createElement('b');nav.appendChild(b);} b.textContent=pendingReqs.length; } else b?.remove(); } }
      mount.innerHTML=`<section class="ex-module">
        <div class="svc-head"><div><p class="eyebrow">Escaparate de viajes</p><h2>Experiencias</h2><p>Viajes, vida a bordo y salidas especiales que se muestran en la sección Experiencias de WORLDIVES.</p></div><button type="button" class="btn btn-primary ex-new">+ Nueva experiencia</button></div>
        <div class="ex-tip">${wdIcon('bolt',18)}<p><strong>Sin trabajo doble.</strong> Al crear o editar un viaje en «Servicios y tarifas», marca «Publicar también en Experiencias» y aparecerá aquí con su precio y sus salidas siempre al día.${role==='center'?'':' Tus propuestas se revisan antes de publicarse.'}</p></div>
        ${reqs.length?`<section class="ex-requests"><h3>Solicitudes ${pendingReqs.length?`<b>${pendingReqs.length} por responder</b>`:''}</h3>${reqs.slice(0,30).map(reqRow).join('')}</section>`:''}
        ${items.length?`<div class="ex-grid">${items.map(card).join('')}</div>`:`<div class="svc-empty"><span class="svc-empty-icon">${wdIcon('viaje',30)}</span><h3>Aún no tienes experiencias</h3><p>Publica un viaje desde «Servicios y tarifas» o crea aquí una experiencia independiente con sus fechas y precio.</p><button type="button" class="btn btn-primary ex-new">+ Nueva experiencia</button></div>`}
      </section>`;
      const openForm=e=>{
        const body=`<form id="ex-form" class="svc-form">
          <div class="svc-form-row svc-form-row-2"><div class="svc-field"><label for="ex-dest">Destino</label><select id="ex-dest"><option value="">Elige un destino…</option>${dests.map(x=>`<option value="${x.id}" ${e&&Number(e.travel_offer_id)===Number(x.id)?'selected':''}>${esc(x.title)}</option>`).join('')}<option value="new">+ Otro destino…</option></select></div>
          <div class="svc-field" id="ex-dest-new" hidden><label for="ex-dest-name">Nombre del destino</label><input id="ex-dest-name" maxlength="180" placeholder="Ej. Raja Ampat · Indonesia"></div></div>
          <div class="svc-field"><label for="ex-title">Título</label><input id="ex-title" required maxlength="180" value="${esc(e?.title||'')}" placeholder="Ej. Semana de vida a bordo en el Mar Rojo" autofocus></div>
          <div class="svc-field"><label for="ex-summary">Resumen</label><input id="ex-summary" maxlength="500" value="${esc(e?.summary||'')}" placeholder="Una frase que lo explique todo"></div>
          <div class="svc-field"><label for="ex-desc">Descripción</label><textarea id="ex-desc" rows="4" maxlength="5000">${esc(e?.description||'')}</textarea></div>
          <div class="svc-form-row"><div class="svc-field"><label for="ex-start">Inicio</label><input id="ex-start" type="date" value="${esc(e?.start_date||'')}"></div><div class="svc-field"><label for="ex-end">Fin</label><input id="ex-end" type="date" value="${esc(e?.end_date||'')}"></div><div class="svc-field"><label for="ex-price">Precio por persona</label><label class="svc-money"><input id="ex-price" type="number" min="0" step="0.01" value="${e?.price??''}"><span>€</span></label></div></div>
          <div class="svc-form-row svc-form-row-2"><div class="svc-field"><label for="ex-spots">Plazas</label><input id="ex-spots" type="number" min="1" value="${e?.spots_total??''}"></div><div></div></div>
          <div class="svc-form-row svc-form-row-2"><div class="svc-field"><label for="ex-includes">Incluye</label><textarea id="ex-includes" rows="3">${esc(e?.includes||'')}</textarea></div><div class="svc-field"><label for="ex-conditions">Requisitos y condiciones</label><textarea id="ex-conditions" rows="3">${esc(e?.conditions||'')}</textarea></div></div>
        </form>`;
        const {el,close}=wdOpenModal({id:'ex-modal',size:'lg',title:e?'Editar experiencia':'Nueva experiencia',subtitle:role==='center'?'Se publica al guardar.':'Se publicará cuando WORLDIVES la revise.',body,footer:`<button type="button" class="btn" data-modal-close>Cancelar</button><button type="submit" form="ex-form" class="btn btn-primary">${e?'Guardar cambios':(role==='center'?'Publicar':'Enviar a revisión')}</button>`});
        const sel=el.querySelector('#ex-dest'); sel.onchange=()=>{el.querySelector('#ex-dest-new').hidden=sel.value!=='new';};
        el.querySelector('#ex-form').onsubmit=async ev=>{ev.preventDefault(); if(!el.querySelector('#ex-title').value.trim()){toast('Ponle un título.');return;} if(!sel.value){sel.focus();toast('Elige un destino.');return;}
          if(el.querySelector('#ex-end').value&&el.querySelector('#ex-start').value&&el.querySelector('#ex-end').value<el.querySelector('#ex-start').value){toast('La fecha de fin no puede ser anterior al inicio.');return;}
          const spots=el.querySelector('#ex-spots').value;
          const payload={id:e?.id||0,travel_offer_id:sel.value!=='new'?+sel.value:0,new_destination:sel.value==='new'?el.querySelector('#ex-dest-name').value.trim():'',title:el.querySelector('#ex-title').value.trim(),summary:el.querySelector('#ex-summary').value,description:el.querySelector('#ex-desc').value,start_date:el.querySelector('#ex-start').value,end_date:el.querySelector('#ex-end').value,price:el.querySelector('#ex-price').value,spots_total:spots,spots_available:(()=>{if(spots==='')return '';if(!e||e.spots_total==null||e.spots_available==null)return spots;const used=Number(e.spots_total)-Number(e.spots_available);return Math.max(0,Number(spots)-used);})(),includes:el.querySelector('#ex-includes').value,conditions:el.querySelector('#ex-conditions').value};
          try{await postJSON(e?'/api/travel-experiences/update':'/api/travel-experiences',payload);close();toast(e?'Experiencia guardada.':(role==='center'?'Experiencia publicada.':'Experiencia enviada a revisión.'));refresh();}catch(err){toast(err.message)}};
      };
      mount.onclick=async ev=>{
        if(ev.target.closest('.ex-new')){openForm(null);return;}
        const ph=ev.target.closest('.ex-photo'); if(ph){ const e=items.find(x=>Number(x.id)===Number(ph.dataset.id)); if(e) openPhotoModal({title:'Foto de la experiencia',subtitle:e.title,current:e.image_url,upload:f=>uploadForm('/api/provider/experience-image',{id:e.id},f),remove:()=>uploadForm('/api/provider/experience-image',{id:e.id,remove:'1'}),onDone:()=>{ __travel=null; refresh(); }}); return; }
        if(ev.target.closest('.ex-go-services')){ctx.goServices?.();return;}
        const ed=ev.target.closest('.ex-edit'); if(ed){openForm(items.find(x=>Number(x.id)===Number(ed.dataset.id)));return;}
        const hd=ev.target.closest('.ex-hide'); if(hd){if(!confirm('¿Ocultar esta experiencia de la web?'))return; try{await postJSON('/api/travel-experiences/update',{id:+hd.dataset.id,delete:true});toast('Experiencia oculta.');refresh();}catch(err){toast(err.message)} return;}
        const rq=ev.target.closest('.ex-req'); if(rq){try{await postJSON('/api/provider/experience-bookings/status',{id:+rq.dataset.id,status:rq.dataset.status});toast('Solicitud actualizada. El cliente recibirá un aviso.');refresh();}catch(err){toast(err.message)} return;}
      };
    }catch(err){mount.innerHTML=`<div class="empty"><h3>No se han podido cargar las experiencias</h3><p>${escapeHtml(err.message)}</p></div>`;}
  }

  // ---------- Showcase editor (public page of the center) ----------
  async function renderCenterShowcaseEditor(mountId, centerId){
    const mount=document.getElementById(mountId); if(!mount)return;
    const refresh=()=>renderCenterShowcaseEditor(mountId,centerId);
    let c;
    try{ c=(await api('/api/centers/'+centerId)).item; }catch(err){mount.innerHTML=`<div class="empty"><h3>No se ha podido cargar tu centro</h3><p>${escapeHtml(err.message)}</p></div>`;return;}
    const esc=escapeHtml; const gallery=c.gallery||[];
    const upload=async(url,file)=>{const fd=new FormData();fd.append('file',file);return api(url,{method:'POST',body:fd});};
    mount.innerHTML=`<section class="sc-module">
      <div class="svc-head"><div><p class="eyebrow">Tu página pública</p><h2>Escaparate</h2><p>Así ven tu centro los buceadores. Cambia la portada, las fotos y los textos cuando quieras.</p></div><a class="btn" href="#/centro?id=${c.id}">Ver mi página</a></div>
      <div class="sc-hero" style="${c.cover_url?`background-image:url('${esc(c.cover_url)}')`:''}">
        <div class="sc-hero-shade"></div>
        <div class="sc-hero-content">${centerLogoMarkup(c,'72px')}<div><strong>${esc(c.name)}</strong><span id="sc-tagline-preview">${esc(c.tagline||'Añade una frase que presente tu centro')}</span></div></div>
        <div class="sc-hero-actions"><label class="btn sc-file">Cambiar portada<input type="file" id="sc-cover" accept="image/jpeg,image/png,image/webp" hidden></label>${c.cover_url?'<button type="button" class="btn" id="sc-cover-remove">Quitar</button>':''}<label class="btn sc-file">Cambiar logo<input type="file" id="sc-logo" accept="image/jpeg,image/png,image/webp" hidden></label></div>
      </div>
      <p class="sc-hint">Portada recomendada: foto horizontal de al menos 1600 × 700 px (JPG, PNG o WEBP, máximo 6 MB). La misma portada aparece en la cabecera de tu panel.</p>
      <label class="lg-check sc-consent"><input type="checkbox" id="sc-logo-consent" ${c.logo_consent?'checked':''}> <span>Autorizo a WORLDIVES DISCOVERY a mostrar el nombre y el logo de mi centro en la banda «Centros asociados» de la portada. Puedo retirar la autorización cuando quiera desmarcando esta casilla.</span></label>
      <form id="sc-form" class="svc-form sc-form">
        <section class="sc-card"><h3>Presentación</h3>
          <div class="svc-field"><label for="sc-tagline">Frase de presentación</label><input id="sc-tagline" maxlength="160" value="${esc(c.tagline||'')}" placeholder="Buceo en barco en la reserva marina de Tabarca desde 1998"></div>
          <div class="svc-field"><label for="mc-desc">Sobre el centro</label><textarea id="mc-desc" rows="5" maxlength="5000" placeholder="Quiénes sois, cómo trabajáis, qué hace especial bucear con vosotros…">${esc(c.description||'')}</textarea></div>
          <div class="svc-form-row"><div class="svc-field"><label for="mc-spec">Especialidades</label><input id="mc-spec" value="${esc(c.specialties||'')}" placeholder="Nitrox, cursos PADI, fotografía"></div><div class="svc-field"><label for="sc-languages">Idiomas</label><input id="sc-languages" maxlength="160" value="${esc(c.languages||'')}" placeholder="Español, inglés, francés"></div><div class="svc-field"><label for="sc-hours">Horario</label><input id="sc-hours" maxlength="300" value="${esc(c.opening_hours||'')}" placeholder="Todos los días de 8:00 a 19:00"></div></div>
        </section>
        <section class="sc-card"><h3>Galería <small>${gallery.length} de 12 fotos</small></h3>
          <div class="sc-gallery" id="sc-gallery">${gallery.map(u=>`<figure data-url="${esc(u)}"><img src="${esc(u)}" alt="" loading="lazy"><button type="button" class="sc-del" aria-label="Quitar foto">×</button></figure>`).join('')}${gallery.length<12?`<label class="sc-add">${wdIcon('extra',22)}<span>Añadir fotos</span><input type="file" id="sc-gallery-add" accept="image/jpeg,image/png,image/webp" multiple hidden></label>`:''}</div>
        </section>
        <section class="sc-card"><h3>Contacto y ubicación</h3>
          <div class="svc-form-row"><div class="svc-field"><label for="mc-name">Nombre del centro</label><input id="mc-name" required value="${esc(c.name||'')}"></div><div class="svc-field"><label for="mc-phone">Teléfono</label><input id="mc-phone" value="${esc(c.phone||'')}"></div><div class="svc-field"><label for="mc-email">Email</label><input id="mc-email" type="email" value="${esc(c.email||'')}"></div></div>
          <div class="svc-form-row"><div class="svc-field"><label for="mc-web">Web</label><input id="mc-web" value="${esc(c.website||'')}" placeholder="https://"></div><div class="svc-field"><label for="mc-city">Ciudad</label><input id="mc-city" value="${esc(c.city||'')}"></div><div class="svc-field"><label for="mc-region">Región / provincia</label><input id="mc-region" value="${esc(c.region||'')}"></div></div>
          <div class="svc-form-row"><div class="svc-field"><label for="mc-country">País</label><input id="mc-country" value="${esc(c.country||'')}"></div><div class="svc-field"><label for="mc-lat">Latitud</label><input id="mc-lat" type="number" step="any" value="${c.latitude??''}" placeholder="38.5"></div><div class="svc-field"><label for="mc-lng">Longitud</label><input id="mc-lng" type="number" step="any" value="${c.longitude??''}" placeholder="-0.2"></div></div>
          <div class="svc-field"><label for="mc-address">Dirección</label><input id="mc-address" value="${esc(c.address||'')}"></div>
        </section>
        <section class="sc-card"><h3>Redes sociales</h3>
          <div class="svc-form-row">${[['instagram_url','Instagram','https://instagram.com/…'],['facebook_url','Facebook','https://facebook.com/…'],['youtube_url','YouTube','https://youtube.com/…'],['tiktok_url','TikTok','https://tiktok.com/@…'],['twitter_url','X / Twitter','https://x.com/…']].map(([k,l,p])=>`<div class="svc-field"><label for="mc-${k}">${l}</label><input id="mc-${k}" value="${esc(c[k]||'')}" placeholder="${p}"></div>`).join('')}</div>
        </section>
        <div class="sc-save"><button type="submit" class="btn btn-primary">Guardar escaparate</button></div>
      </form>
    </section>`;
    mount.querySelector('#sc-tagline').oninput=e=>{mount.querySelector('#sc-tagline-preview').textContent=e.target.value||'Añade una frase que presente tu centro';};
    mount.querySelector('#sc-cover').onchange=async e=>{const f=e.target.files[0]; if(!f)return; try{toast('Subiendo portada…');await upload('/api/provider/center-cover',f);toast('Portada actualizada.');refresh();}catch(err){toast(err.message)}};
    mount.querySelector('#sc-logo').onchange=async e=>{const f=e.target.files[0]; if(!f)return; try{await upload('/api/provider/avatar',f);toast('Logo actualizado.');refresh();}catch(err){toast(err.message)}};
    mount.querySelector('#sc-cover-remove')?.addEventListener('click',async()=>{if(!confirm('¿Quitar la portada?'))return; try{await postJSON('/api/provider/center-showcase',{tagline:c.tagline||'',languages:c.languages||'',opening_hours:c.opening_hours||'',remove_cover:true});toast('Portada quitada.');refresh();}catch(err){toast(err.message)}});
    mount.querySelector('#sc-gallery-add')?.addEventListener('change',async e=>{const files=[...e.target.files].slice(0,12-gallery.length); if(!files.length)return; let ok=0; for(const f of files){try{await upload('/api/provider/center-gallery',f);ok++;}catch(err){toast(err.message);break;}} if(ok)toast(ok===1?'Foto añadida.':`${ok} fotos añadidas.`); refresh();});
    mount.querySelector('#sc-gallery').onclick=async e=>{const del=e.target.closest('.sc-del'); if(!del)return; const url=del.closest('figure').dataset.url; if(!confirm('¿Quitar esta foto de la galería?'))return; try{await postJSON('/api/provider/center-showcase',{tagline:c.tagline||'',languages:c.languages||'',opening_hours:c.opening_hours||'',gallery:gallery.filter(x=>x!==url)});toast('Foto quitada.');refresh();}catch(err){toast(err.message)}};
    mount.querySelector('#sc-form').onsubmit=async e=>{e.preventDefault(); const v=id=>mount.querySelector('#'+id).value;
      if(!v('mc-name').trim()){toast('El nombre del centro es obligatorio.');return;}
      const btn=e.target.querySelector('button[type=submit]'); btn.disabled=true;
      try{
        await postJSON('/api/provider/center-update',{logo_consent:!!mount.querySelector('#sc-logo-consent')?.checked,name:v('mc-name'),country:v('mc-country'),region:v('mc-region'),city:v('mc-city'),phone:v('mc-phone'),website:v('mc-web'),email:v('mc-email'),address:v('mc-address'),specialties:v('mc-spec'),description:v('mc-desc'),latitude:v('mc-lat'),longitude:v('mc-lng'),instagram_url:v('mc-instagram_url'),facebook_url:v('mc-facebook_url'),twitter_url:v('mc-twitter_url'),youtube_url:v('mc-youtube_url'),tiktok_url:v('mc-tiktok_url')});
        await postJSON('/api/provider/center-showcase',{tagline:v('sc-tagline'),languages:v('sc-languages'),opening_hours:v('sc-hours')});
        toast('Escaparate guardado.'); refresh();
      }catch(err){toast(err.message);btn.disabled=false;}
    };
  }

  function centerClientsView(items){
    const esc=escapeHtml; const real=e=>e&&!String(e).endsWith('.worldives.local');
    return `<section class="cl-module"><div class="svc-head"><div><p class="eyebrow">Base de clientes</p><h2>Clientes</h2><p>Todas las personas que han reservado con tu centro o han hecho check-in con tu QR.</p></div></div>
      <div class="svc-toolbar"><label class="svc-search"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/></svg><input id="cl-q" type="search" placeholder="Buscar por nombre, email o teléfono"></label><span class="cl-count">${items.length} ${items.length===1?'cliente':'clientes'}</span></div>
      ${items.length?`<div class="cl-table"><div class="cl-row cl-head"><span>Cliente</span><span>Contacto</span><span>Reservas</span><span>Última</span><span>Pagado</span></div>${items.map(x=>`<div class="cl-row" data-search="${esc(`${x.fullname||''} ${real(x.email)?x.email:''} ${x.phone||''}`.toLowerCase())}"><span><strong>${esc(x.fullname||'—')}</strong>${x.first_checkin?'<small>Check-in con QR</small>':''}</span><span>${real(x.email)?`<a href="mailto:${esc(x.email)}">${esc(x.email)}</a>`:''}${x.phone?`<small>${esc(x.phone)}</small>`:''}</span><span>${Number(x.bookings_count||0)}</span><span>${x.last_booking?esc(wdDay(x.last_booking)):'—'}</span><span>${wdMoney(x.total_paid)}</span></div>`).join('')}</div>`:`<div class="svc-empty"><span class="svc-empty-icon">${wdIcon('users',28)}</span><h3>Aún no hay clientes</h3><p>Aparecerán aquí en cuanto alguien reserve o haga check-in con tu QR.</p></div>`}
    </section>`;
  }

  function loadTabFromCenterWorkspace(tab){const nav=document.querySelector(`.cb-nav[data-cbtab="${tab}"]`);if(nav)nav.click();}

  async function renderCenterPointManager(centerId,mountId){
    const mount=document.getElementById(mountId);if(!mount)return;const mine=(await api('/api/center-points?center_id='+centerId)).items;const all=(await api('/api/dive-points')).items;const assigned=new Set(mine.map(p=>Number(p.id)));const available=all.filter(p=>!assigned.has(Number(p.id)));
    mount.innerHTML=`<section class="notice"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap"><div><p class="eyebrow">CENTRO · PUNTOS</p><h3 style="margin:0">Mis puntos de buceo</h3><p style="margin:5px 0;color:var(--muted)">Asocia aquí los lugares a los que suele ir tu centro. No necesitas crear el punto de nuevo si ya existe en WORLDIVES DISCOVERY.</p></div><div class="page-actions"><button class="btn btn-primary" id="new-center-point" type="button">Nuevo punto</button></div></div><div class="checklist" style="margin-top:16px">${mine.map(p=>`<div class="check-row"><div><strong>${escapeHtml(p.name)}</strong><div><small>${escapeHtml(p.region||p.country||'')} · ${escapeHtml(p.dive_type||'')}</small></div></div><div class="page-actions" style="margin:0"><button class="btn point-photos" data-id="${p.id}" type="button">Fotos</button><button class="btn danger unassign-point" data-id="${p.id}">Quitar</button></div></div>`).join('')||'<div class="empty">Todavía no tienes puntos asociados.</div>'}</div><div class="field full" style="margin-top:18px"><label>Añadir un punto existente</label><input id="center-point-search" placeholder="Busca Xàbia, Granadella, Portitxol…"><div id="center-point-results" class="checklist" style="margin-top:10px"></div></div></section>`;
    const render=()=>{const q=($('#center-point-search').value||'').toLowerCase();const res=available.filter(p=>(`${p.name} ${p.region||''} ${p.country||''}`).toLowerCase().includes(q)).slice(0,20);$('#center-point-results').innerHTML=res.map(p=>`<div class="check-row"><div><strong>${escapeHtml(p.name)}</strong><div><small>${escapeHtml(p.region||p.country||'')}</small></div></div><button class="btn add-point" data-id="${p.id}">Añadir</button></div>`).join('')||'<div class="empty">No hay más puntos que coincidan.</div>';$('[data-id]');$$('.add-point').forEach(b=>b.onclick=async()=>{try{await postJSON('/api/center-points/assign',{dive_point_id:+b.dataset.id});toast('Punto asociado al centro.');renderCenterPointManager(centerId,mountId);}catch(e){toast(e.message)}});};
    $('#center-point-search').oninput=render;render();$$('.point-photos').forEach(b=>b.onclick=()=>{ const p=mine.find(x=>Number(x.id)===Number(b.dataset.id)); if(p) openPointPhotos(p); });$('#new-center-point').onclick=()=>editPointForm();$$('.unassign-point').forEach(b=>b.onclick=async()=>{if(!confirm('¿Quitar este punto de los puntos habituales del centro?'))return;try{await postJSON('/api/center-points/unassign',{dive_point_id:+b.dataset.id});toast('Punto desasociado.');renderCenterPointManager(centerId,mountId);}catch(e){toast(e.message)}});
  }

  function centerDashboard(bookings, points, clients, rewardOffers){
    points=points.filter(p=>p.active===undefined||Number(p.active)!==0);
    const now=new Date();
    const isoNow=now.toISOString().slice(0,10);
    const week=new Date(now); week.setDate(week.getDate()+7); const isoWeek=week.toISOString().slice(0,10);
    const active=b=>!['cancelled','rejected','completed'].includes(b.status);
    const pending=bookings.filter(b=>(b.status==='requested'||b.status==='pending'));
    const confirmed=bookings.filter(b=>b.status==='confirmed');
    const paid=bookings.filter(b=>b.payment_status==='paid');
    const unpaid=bookings.filter(b=>b.payment_status && b.payment_status!=='paid' && !['cancelled','rejected'].includes(b.status));
    const today=bookings.filter(b=>b.booking_date===isoNow && active(b)).sort((a,b)=>String(a.booking_time||'').localeCompare(String(b.booking_time||'')));
    const upcoming=bookings.filter(b=>b.booking_date>=isoNow && b.booking_date<=isoWeek && active(b)).sort((a,b)=>`${a.booking_date} ${a.booking_time||''}`.localeCompare(`${b.booking_date} ${b.booking_time||''}`));
    const future=bookings.filter(b=>b.booking_date>isoWeek && active(b)).sort((a,b)=>`${a.booking_date} ${a.booking_time||''}`.localeCompare(`${b.booking_date} ${b.booking_time||''}`));
    const todayParticipants=today.reduce((n,b)=>n+Number(b.participants||1),0);
    const bookingRow=b=>`<div class="ops-row"><div class="ops-date"><strong>${escapeHtml(b.booking_date||'')}</strong><span>${escapeHtml(b.booking_time||'Por confirmar')}</span></div><div class="ops-main"><strong>${escapeHtml(b.fullname||'Cliente')}</strong><span>${escapeHtml(b.service_title||'Inmersión')} · ${escapeHtml(b.point_name||'Punto por concretar')}</span></div><span class="status ${b.status==='confirmed'?'good':b.status==='rejected'||b.status==='cancelled'?'bad':'warn'}">${escapeHtml((b.status==='requested'||b.status==='pending')?'Pendiente':b.status==='confirmed'?'Confirmada':b.status==='completed'?'Completada':b.status==='cancelled'?'Cancelada':b.status)}</span><a class="btn booking-detail" href="#/reserva?id=${b.id}">Ver reserva</a></div>`;
    return `<div class="center-dashboard">
      <div class="dashboard-hero center-hero"><div><p class="eyebrow">CENTRO DE OPERACIONES</p><h2>Buenos días. Este es el estado de tu centro.</h2><p>Una vista rápida para saber qué requiere atención, qué tienes hoy y qué viene después.</p></div><div class="hero-actions"><a class="btn btn-primary" href="#/admin?tab=bookings">Gestionar reservas</a><a class="btn" href="#/admin?tab=services">Gestionar servicios</a></div></div>
      <div class="ops-kpis center-kpis">
        <div class="ops-kpi urgent"><span>⚠ Reservas por confirmar</span><strong>${pending.length}</strong><a href="#/admin?tab=bookings&status=pending">Revisar pendientes →</a></div>
        <div class="ops-kpi"><span>✓ Reservas confirmadas</span><strong>${confirmed.length}</strong><small>Activas ahora</small></div>
        <div class="ops-kpi"><span>💳 Reservas pagadas</span><strong>${paid.length}</strong><small>${Object.entries(paid.reduce((m,b)=>{ const c=(b.currency||'EUR').toUpperCase(); m[c]=(m[c]||0)+Number(b.price||0); return m; },{})).map(([c,v])=>wdMoney(v,c)).join(' · ')||wdMoney(0,'EUR')} cobrados</small></div>
        <div class="ops-kpi"><span>⏳ Pagos pendientes</span><strong>${unpaid.length}</strong><small>Revisar antes de la salida</small></div>
        <div class="ops-kpi"><span>📅 Salidas hoy</span><strong>${today.length}</strong><small>${todayParticipants} participante${todayParticipants===1?'':'s'}</small></div>
        <div class="ops-kpi"><span>📍 Puntos activos</span><strong>${points.length}</strong><small>Gestionados por tu centro</small></div>
      </div>
      <div class="dashboard-grid">
        <section class="ops-panel attention-panel"><div class="ops-panel-head"><div><p class="eyebrow">REQUIERE ATENCIÓN</p><h3>Lo que tienes que revisar</h3></div><a href="#/admin?tab=bookings">Abrir reservas</a></div>
          ${pending.slice(0,6).map(bookingRow).join('')||unpaid.slice(0,6).map(bookingRow).join('')||'<div class="empty"><h3>Todo al día</h3><p>No hay reservas pendientes de confirmación ni pagos pendientes.</p></div>'}
        </section>
        <section class="ops-panel"><div class="ops-panel-head"><div><p class="eyebrow">HOY</p><h3>Agenda de hoy</h3></div><a href="#/admin?tab=bookings">Ver agenda completa</a></div>
          ${today.slice(0,8).map(bookingRow).join('')||'<div class="empty"><h3>No hay salidas hoy</h3><p>Cuando entre una reserva para hoy aparecerá aquí automáticamente.</p></div>'}
        </section>
      </div>
      <div class="dashboard-grid dashboard-grid-lower">
        <section class="ops-panel"><div class="ops-panel-head"><div><p class="eyebrow">PRÓXIMOS 7 DÍAS</p><h3>Próximas salidas</h3></div><a href="#/admin?tab=bookings">Gestionar</a></div>${upcoming.slice(0,10).map(bookingRow).join('')||'<div class="empty">No hay salidas programadas en los próximos 7 días.</div>'}</section>
        <section class="ops-panel"><div class="ops-panel-head"><div><p class="eyebrow">RESUMEN</p><h3>Tu centro</h3></div><a href="#/admin?tab=center">Editar ficha</a></div><div class="center-summary-grid"><a class="summary-card" href="#/admin?tab=clients"><strong>${clients.length}</strong><span>Clientes</span></a><a class="summary-card" href="#/admin?tab=rewards"><strong>${rewardOffers.length}</strong><span>Recompensas activas</span></a><a class="summary-card" href="#/admin?tab=services"><strong>${future.length+upcoming.length}</strong><span>Reservas futuras</span></a><a class="summary-card" href="#/admin?tab=points"><strong>${points.length}</strong><span>Puntos publicados</span></a></div></section>
      </div>
      <section class="quick-actions center-quick-actions"><a class="quick-action" href="#/admin?tab=bookings"><strong>📥 Reservas</strong><span>Pendientes, confirmadas, pagadas y completadas</span></a><a class="quick-action" href="#/admin?tab=services"><strong>🤿 Servicios y salidas</strong><span>Precios, horarios, plazas y disponibilidad</span></a><a class="quick-action" href="#/admin?tab=clients"><strong>👥 Clientes</strong><span>Consulta tus buceadores</span></a><a class="quick-action" href="#/admin?tab=points"><strong>📍 Puntos de buceo</strong><span>Gestiona los puntos asociados</span></a><a class="quick-action" href="#/admin?tab=qr"><strong>▣ QR / Check-in</strong><span>Verifica reservas y asocia clientes</span></a><a class="quick-action" href="#/admin?tab=center"><strong>🏪 Mi centro</strong><span>Foto, datos, redes y ficha pública</span></a></section>
    </div>`;
  }

  function centerProfileEditor(c){
    return `<section class="provider-profile-panel"><div class="profile-panel-head"><div><p class="eyebrow">MI CENTRO</p><h2>${escapeHtml(c.name||'Mi centro')}</h2><p>Esta información es la que verá el cliente en la ficha pública del centro.</p></div><a class="btn" href="#/centros">Ver ficha pública</a></div><form id="my-center-form"><div class="form-grid"><div class="field"><label>Nombre</label><input id="mc-name" value="${escapeHtml(c.name||'')}" required></div><div class="field"><label>Teléfono</label><input id="mc-phone" value="${escapeHtml(c.phone||'')}"></div><div class="field"><label>País</label><input id="mc-country" value="${escapeHtml(c.country||'')}"></div><div class="field"><label>Región / provincia</label><input id="mc-region" value="${escapeHtml(c.region||'')}"></div><div class="field"><label>Ciudad</label><input id="mc-city" value="${escapeHtml(c.city||'')}"></div><div class="field"><label>Web</label><input id="mc-web" value="${escapeHtml(c.website||'')}"></div><div class="field"><label>Email</label><input id="mc-email" value="${escapeHtml(c.email||'')}"></div><div class="field"><label>Logo URL</label><input id="mc-logo" value="${escapeHtml(c.logo_url||'')}"></div><div class="field full"><label>Dirección</label><input id="mc-address" value="${escapeHtml(c.address||'')}"></div><div class="field full"><label>Especialidades</label><input id="mc-spec" value="${escapeHtml(c.specialties||'')}"></div><div class="field full"><label>Descripción</label><textarea id="mc-desc">${escapeHtml(c.description||'')}</textarea></div><div class="field full"><label>Foto / logo del centro</label><input id="mc-photo" type="file" accept=".jpg,.jpeg,.png,.webp"><small>La nueva imagen sustituirá la imagen pública actual.</small></div><div class="field"><label>Instagram</label><input id="mc-instagram" value="${escapeHtml(c.instagram_url||'')}" placeholder="https://instagram.com/…"></div><div class="field"><label>Facebook</label><input id="mc-facebook" value="${escapeHtml(c.facebook_url||'')}" placeholder="https://facebook.com/…"></div><div class="field"><label>X / Twitter</label><input id="mc-twitter" value="${escapeHtml(c.twitter_url||'')}" placeholder="https://x.com/…"></div><div class="field"><label>YouTube</label><input id="mc-youtube" value="${escapeHtml(c.youtube_url||'')}" placeholder="https://youtube.com/…"></div><div class="field"><label>TikTok</label><input id="mc-tiktok" value="${escapeHtml(c.tiktok_url||'')}" placeholder="https://tiktok.com/@…"></div></div><div class="form-actions"><button class="btn btn-primary">Guardar cambios</button></div></form><section class="notice" style="margin-top:22px"><p class="eyebrow">ALQUILER DE EQUIPO</p><h3>Precios que verá el buceador al reservar</h3><p>Configura el precio de cada elemento. Si lo dejas vacío, aparecerá como «Precio a consultar».</p><div id="center-equipment-editor" class="equipment-admin-grid"><div class="empty">Cargando catálogo…</div></div></section></section>`;
  }

  function centerWorkspaceShell(c,metrics){
    const m=metrics||{};
    return `<section class="center-backoffice">
      <div class="cb-header ${c?.cover_url?'has-cover':''}" style="${c?.cover_url?`--cover:url('${escapeHtml(c.cover_url)}')`:''}"><div class="cb-header-id">${centerLogoMarkup(c||{},'58px')}<div><p class="eyebrow">Panel del centro</p><h1>${escapeHtml(c?.name||'Mi centro')}</h1>${c?.tagline?`<p>${escapeHtml(c.tagline)}</p>`:''}</div></div><div class="cb-header-actions"><a class="btn" href="#/centro?id=${c?.id||''}">Ver mi página</a><button class="btn btn-primary" id="cb-refresh">Actualizar</button></div></div>
      <div class="cb-layout"><aside class="cb-sidebar">
        <div class="cb-section-title">OPERACIONES</div>
        <button class="cb-nav active" data-cbtab="dashboard">⌂ <span>Resumen</span></button>
        <button class="cb-nav" data-cbtab="planning">▦ <span>Planning / agenda</span></button>
        <button class="cb-nav" data-cbtab="bookings">▣ <span>Reservas</span><b>${m.pending||0}</b></button>
        <button class="cb-nav" data-cbtab="clients">♙ <span>Clientes</span></button>
        <div class="cb-section-title">VENTAS</div>
        <button class="cb-nav" data-cbtab="services">◈ <span>Servicios y tarifas</span></button>
        <button class="cb-nav" data-cbtab="experiences">✈ <span>Experiencias</span>${m.experience_requests?`<b>${m.experience_requests}</b>`:''}</button>
        <button class="cb-nav" data-cbtab="payments">▤ <span>Cobros y pagos</span></button>
        <div class="cb-section-title">CONTROL</div>
        <button class="cb-nav" data-cbtab="analytics">◔ <span>Analítica e informes</span></button>
        <button class="cb-nav" data-cbtab="integration">↔ <span>Web e integraciones</span></button>
        <button class="cb-nav" data-cbtab="points">⌖ <span>Puntos de buceo</span></button>
        <button class="cb-nav" data-cbtab="qr">▣ <span>Check-in / QR y promociones</span></button>
        <div class="cb-section-title">CONFIGURACIÓN</div>
        <button class="cb-nav" data-cbtab="center">✦ <span>Escaparate y datos</span></button>
        <button class="cb-nav" data-cbtab="rewards">★ <span>Recompensas</span></button>
        <div class="cb-section-title">MI CUENTA PROFESIONAL</div>
        <button class="cb-nav" data-cbtab="requests">✉ <span>Solicitudes de información</span></button>
        <button class="cb-nav" data-cbtab="stats">◑ <span>Estadísticas</span></button>
        <button class="cb-nav" data-cbtab="tools">⇩ <span>Herramientas</span></button>
        <button class="cb-nav" data-cbtab="team" data-owner>☺ <span>Equipo</span></button>
        <button class="cb-nav" data-cbtab="activity" data-owner>☷ <span>Registro de actividad</span></button>
        <button class="cb-nav" data-cbtab="fiscal" data-owner>§ <span>Datos fiscales y seguro</span></button>
        <button class="cb-nav" data-cbtab="plan" data-owner>◆ <span>Mi plan</span></button>
      </aside><main class="cb-main"><div id="cb-content"></div></main></div>
    </section>`;
  }

  function centerDashboardPro(c, a, bookings, services){
    const esc=escapeHtml, t=wdToday(), tomorrow=wdAddDays(t,1), week=wdAddDays(t,7);
    const live=b=>!['cancelled','rejected','expired','payment_in_progress'].includes(b.status);
    const todayB=bookings.filter(b=>b.booking_date===t&&live(b));
    const nextB=bookings.filter(b=>b.booking_date>=t&&b.booking_date<=tomorrow&&live(b)).sort((x,y)=>`${x.booking_date} ${x.booking_time||''}`.localeCompare(`${y.booking_date} ${y.booking_time||''}`));
    const pending=bookings.filter(b=>(b.status==='requested'||b.status==='pending'));
    const unpaid=bookings.filter(b=>b.payment_status==='required'&&live(b));
    const unpaidAmount=unpaid.reduce((n,b)=>n+Number(b.price||0),0);
    const weekB=bookings.filter(b=>b.booking_date>=t&&b.booking_date<=week&&live(b));
    const paid=bookings.filter(b=>b.payment_status==='paid').reduce((n,b)=>n+Number(b.price||0),0);
    const hour=new Date().getHours(); const hello=hour<13?'Buenos días':hour<20?'Buenas tardes':'Buenas noches';
    const row=b=>`<a class="db-row" href="#/reserva?id=${b.id}" style="--svc:${esc(b.service_color||'#94a3b8')}"><span class="db-when"><strong>${esc(b.booking_time||'—')}</strong><small>${b.booking_date===t?'Hoy':b.booking_date===tomorrow?'Mañana':esc(wdDay(b.booking_date))}</small></span><span class="db-who"><strong>${esc(b.fullname||'Cliente')}</strong><small>${esc(b.service_title||'Reserva')} · ${Number(b.participants||1)} ${Number(b.participants||1)===1?'persona':'personas'}</small></span>${wdStatus(b.status)}</a>`;
    const attention=[...pending.map(b=>({b,why:'Solicitud: acéptala o recházala'})),...unpaid.filter(b=>!['requested','pending'].includes(b.status)).map(b=>({b,why:'Por cobrar · '+wdMoney(b.price,b.currency)}))].slice(0,7);
    const channels=a.channels||{}; const chTotal=Object.values(channels).reduce((n,v)=>n+v,0)||1;
    return `<div class="cb-dashboard db">
      <div class="db-hello"><div><p class="eyebrow">${esc(wdLongDay(t))}</p><h2>${hello}. ${todayB.length?`Hoy tienes ${todayB.length} ${todayB.length===1?'reserva':'reservas'} con ${todayB.reduce((n,b)=>n+Number(b.participants||1),0)} buceadores.`:'Hoy no hay reservas en agenda.'}</h2></div><div class="db-actions"><button type="button" class="btn btn-primary db-new-booking">+ Nueva reserva</button><button type="button" class="btn cb-go" data-tab="planning">Abrir planning</button></div></div>
      <div class="db-kpis">
        <button type="button" class="cb-go" data-tab="bookings" data-view="today"><span>Hoy</span><strong>${todayB.length}</strong><small>${todayB.reduce((n,b)=>n+Number(b.participants||1),0)} personas</small></button>
        <button type="button" class="cb-go ${pending.length?'is-alert':''}" data-tab="bookings" data-view="pending"><span>Solicitudes pendientes</span><strong>${pending.length}</strong><small>${pending.length?'Necesitan respuesta':'Todo al día'}</small></button>
        <button type="button" class="cb-go ${unpaid.length?'is-warn':''}" data-tab="bookings" data-view="unpaid"><span>Por cobrar</span><strong>${wdMoney(unpaidAmount)}</strong><small>${unpaid.length} ${unpaid.length===1?'reserva':'reservas'}</small></button>
        <button type="button" class="cb-go" data-tab="bookings" data-view="week"><span>Próximos 7 días</span><strong>${weekB.length}</strong><small>reservas</small></button>
        <button type="button" class="cb-go" data-tab="analytics"><span>Cobrado</span><strong>${wdMoney(paid)}</strong><small>total registrado</small></button>
      </div>
      <div class="cb-grid-2">
        <section class="cb-panel"><div class="cb-panel-head"><div><h3>Hoy y mañana</h3></div><button type="button" class="cb-link cb-go" data-tab="bookings" data-view="week">Ver la semana</button></div><div class="db-list">${nextB.slice(0,8).map(row).join('')||`<div class="db-empty">Sin reservas para hoy ni mañana. <button type="button" class="svc-link db-new-booking">Apuntar una reserva</button></div>`}</div></section>
        <section class="cb-panel"><div class="cb-panel-head"><div><h3>Requiere atención</h3></div><button type="button" class="cb-link cb-go" data-tab="bookings" data-view="pending">Ir a reservas</button></div><div class="db-list">${attention.map(x=>`<a class="db-row" href="#/reserva?id=${x.b.id}" style="--svc:${esc(x.b.service_color||'#94a3b8')}"><span class="db-when"><strong>${esc(wdDay(x.b.booking_date))}</strong><small>${esc(x.b.booking_time||'')}</small></span><span class="db-who"><strong>${esc(x.b.fullname||'Cliente')}</strong><small>${esc(x.b.service_title||'Reserva')}</small></span><span class="db-why">${esc(x.why)}</span></a>`).join('')||'<div class="db-empty">Todo al día: nada pendiente de confirmar ni de cobrar.</div>'}</div></section>
      </div>
      <div class="cb-grid-3">
        <section class="cb-panel"><h3>De dónde llegan tus reservas</h3><div class="cb-bars">${Object.entries(channels).map(([name,n])=>`<div><span>${esc(name)}</span><b>${n}</b><i style="width:${Math.round((n/chTotal)*100)}%"></i></div>`).join('')}</div></section>
        <section class="cb-panel"><h3>Lo más vendido</h3>${(a.by_service||[]).slice(0,5).map(x=>`<div class="cb-rank"><span>${esc(x.name)}</span><strong>${x.participants} personas</strong></div>`).join('')||'<p class="db-muted">Aún sin ventas.</p>'}</section>
        <section class="cb-panel"><h3>Accesos rápidos</h3><div class="cb-action-grid"><button type="button" class="cb-action cb-go" data-tab="services">${wdIcon('calendar',18)}Programar salidas</button><button type="button" class="cb-action cb-go" data-tab="experiences">${wdIcon('viaje',18)}Publicar un viaje</button><button type="button" class="cb-action cb-go" data-tab="center">${wdIcon('globe',18)}Editar escaparate</button><button type="button" class="cb-action cb-go" data-tab="clients">${wdIcon('users',18)}Ver clientes</button></div></section>
      </div>
    </div>`;
  }

  function centerBookingsPro(bookings){
    return `<div class="cb-module"><div class="cb-module-head"><div><p class="eyebrow">GESTIÓN DE RESERVAS</p><h2>Reservas</h2><p>Una única bandeja para reservas online, WORLDIVES y reservas introducidas por el equipo.</p></div><div class="cb-filters"><input id="cb-booking-search" placeholder="Buscar cliente, servicio o referencia…"><select id="cb-booking-status"><option value="">Todos los estados</option>${Object.entries(WD_STATES).filter(([k])=>!['pending','payment_in_progress'].includes(k)).map(([k,v])=>`<option value="${k}">${v[0]}</option>`).join('')}</select></div></div><div id="cb-booking-table" class="table-wrap"></div></div>`;
  }

  function renderCenterBookingTable(bookings){
    const q=(document.getElementById('cb-booking-search')?.value||'').toLowerCase(); const st=document.getElementById('cb-booking-status')?.value||'';
    const rows=bookings.filter(b=>(!st||b.status===st)&&(!q||`${b.fullname||''} ${b.email||''} ${b.service_title||''} ${b.external_ref||''} ${b.id}`.toLowerCase().includes(q))).sort((a,b)=>`${a.booking_date} ${a.booking_time||''}`.localeCompare(`${b.booking_date} ${b.booking_time||''}`));
    document.getElementById('cb-booking-table').innerHTML=`<table><thead><tr><th>Fecha / hora</th><th>Cliente</th><th>Servicio</th><th>Canal</th><th>Plazas</th><th>Importe</th><th>Estado</th><th>Acción</th></tr></thead><tbody>${rows.map(b=>`<tr><td><strong>${escapeHtml(b.booking_date)}</strong><br><small>${escapeHtml(b.booking_time||'Por confirmar')}</small></td><td><strong>${escapeHtml(b.fullname||'')}</strong><br><small>${escapeHtml(b.email||'')}</small></td><td>${escapeHtml(b.service_title||'Reserva manual')}<br><small>${escapeHtml(b.point_name||'Punto por concretar')}</small></td><td><span class="cb-channel ${b.external_ref?'web':'wod'}">${b.external_ref?'WEB':'WORLDIVES'}</span></td><td>${Number(b.participants||1)}</td><td>${Number(b.price||0).toFixed(2)} €<br><small>${escapeHtml(b.payment_status||'')}</small></td><td><span class="status ${b.status==='confirmed'||b.status==='completed'?'good':b.status==='cancelled'||b.status==='rejected'?'bad':'warn'}">${escapeHtml(b.status)}</span></td><td><button class="btn cb-status" data-id="${b.id}" data-status="confirmed">Confirmar</button> <button class="btn cb-status" data-id="${b.id}" data-status="completed">Completar</button></td></tr>`).join('')||'<tr><td colspan="8">No hay reservas que coincidan.</td></tr>'}</tbody></table>`;
  }

  async function centerAnalyticsView(){
    const a=await api('/api/center/analytics'); const k=a.metrics||{}; const max=Math.max(1,...(a.by_day||[]).map(x=>x.participants));
    return `<div class="cb-module"><div class="cb-module-head"><div><p class="eyebrow">ANALÍTICA</p><h2>Informes y rendimiento</h2><p>Datos operativos del centro, calculados a partir de las reservas reales.</p></div><button class="btn" id="cb-export-report">Exportar CSV</button></div><div class="cb-report-kpis"><div><span>Ingresos cobrados</span><strong>${(k.income||[]).length?k.income.map(x=>wdMoney(x.amount,x.currency)).join(' · '):wdMoney(0,'EUR')}</strong></div><div><span>Participantes</span><strong>${k.participants||0}</strong></div><div><span>Conversión operativa</span><strong>${k.total?Math.round(((k.confirmed+k.completed)/k.total)*100):0}%</strong></div><div><span>Cancelación</span><strong>${k.total?Math.round((k.cancelled/k.total)*100):0}%</strong></div></div><div class="cb-grid-2"><section class="cb-panel"><p class="eyebrow">DEMANDA</p><h3>Participantes por día</h3><div class="cb-chart">${(a.by_day||[]).map(x=>`<div class="cb-chart-bar" title="${x.date}: ${x.participants}"><i style="height:${Math.max(5,(x.participants/max)*100)}%"></i><small>${escapeHtml(x.date.slice(5))}</small></div>`).join('')||'<div class="empty">Sin datos.</div>'}</div></section><section class="cb-panel"><p class="eyebrow">PRODUCTO</p><h3>Servicios más demandados</h3>${(a.by_service||[]).map((x,i)=>`<div class="cb-rank"><span>${i+1}. ${escapeHtml(x.name)}</span><strong>${x.participants} pax</strong></div>`).join('')||'<div class="empty">Sin datos.</div>'}</section></div></div>`;
  }

  async function centerIntegrationView(){
    const d=await api('/api/center/integration'); const i=d.integration; const base=`${location.origin}/api/integrations/bookings`;
    return `<div class="cb-module"><div class="cb-module-head"><div><p class="eyebrow">CONECTIVIDAD</p><h2>Web, API y sincronización</h2><p>Conecta el motor de reservas de la web del centro para que las reservas entren directamente en este planning.</p></div><span class="status ${i?.enabled?'good':'warn'}">${i?.enabled?'● Integración activa':'● Sin configurar'}</span></div><div class="cb-integration-grid"><section class="cb-panel"><h3>Motor de reservas de tu web</h3><p>La web puede enviar cada reserva a WORLDIVES con una referencia externa. Se evita la duplicación y la salida mantiene las plazas centralizadas.</p><div class="cb-code"><strong>POST</strong> ${escapeHtml(base)}<br><small>Header: X-WORLDIVES-API-Key</small></div><div class="cb-api-fields"><div><span>Endpoint</span><code>${escapeHtml(base)}</code></div><div><span>Identificador</span><code>external_ref</code></div><div><span>Sincronización</span><code>Reserva → Planning → plazas</code></div></div><button class="btn btn-primary" id="cb-new-api-key">${i?'Regenerar API Key':'Generar API Key'}</button><div id="cb-api-result"></div></section><section class="cb-panel"><h3>Calendarios</h3><p>Las salidas gestionadas en WORLDIVES pueden consultarse desde el calendario operativo del centro. La conexión con calendarios externos se mantiene separada del motor de reservas.</p><div class="cb-checklist"><div>✓ Disponibilidad por salida</div><div>✓ Plazas actualizadas</div><div>✓ Referencia externa de reserva</div><div>✓ Estado centralizado</div></div></section></div></div>`;
  }

  // ---------------------------------------------------------------------------
  // Planning del centro (v50.26): cualquier mes, pasado o futuro, con resumen por día
  // ---------------------------------------------------------------------------
  const PL_WEEK=['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'];
  const plMonthLabel=m=>wdCap(new Date(+m.slice(0,4),+m.slice(5,7)-1,1).toLocaleDateString(wdLocale(),{month:'long',year:'numeric'}));
  const plShortMonth=m=>new Date(+m.slice(0,4),+m.slice(5,7)-1,1).toLocaleDateString(wdLocale(),{month:'short'}).replace('.','');
  const plIso=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const plEndTime=(t,min)=>{ if(!min||!/^\d{1,2}:\d{2}/.test(t||'')) return ''; const [h,m]=t.split(':').map(Number); const x=h*60+m+Number(min); if(x>=24*60) return ''; return `${String(Math.floor(x/60)).padStart(2,'0')}:${String(x%60).padStart(2,'0')}`; };
  const plFree=sl=>Math.max(Number(sl.spots_total||0)-Number(sl.taken||0),0);
  const plActive=b=>!['cancelled','rejected','expired'].includes(b.status);
  const PL_STATUS={pending:['Pendiente','warn'],confirmed:['Confirmada','good'],completed:['Completada','good'],cancelled:['Cancelada','bad'],rejected:['Rechazada','bad']};
  const PL_PAY={paid:['Pagado','good'],required:['Pago pendiente','warn'],pending:['Pago en curso','warn'],at_center:['Paga en el centro','muted'],not_required:['Sin cobro','muted'],refunded:['Devuelto','muted'],review:['Pago en revisión','warn']};

  async function renderCenterPlanning(mountId,{center,onManage,canBook=true}={}){
    const mount=document.getElementById(mountId); if(!mount) return;
    const ui=renderCenterPlanning.ui||(renderCenterPlanning.ui={month:'',view:(window.innerWidth<720?'list':'month')});
    if(!ui.month) ui.month=plIso(new Date()).slice(0,7);
    const esc=escapeHtml;
    mount.innerHTML=`<div class="pl-wrap"><div class="pl-loading">${wdIcon('calendar',22)} Cargando el planning…</div></div>`;
    let d; try{ d=await api('/api/center/planning?month='+encodeURIComponent(ui.month)); }catch(err){ mount.innerHTML=`<div class="svc-empty"><h3>No se ha podido cargar el planning</h3><p>${esc(err.message)}</p><button type="button" class="btn" id="pl-retry">Reintentar</button></div>`; $('#pl-retry',mount).onclick=()=>renderCenterPlanning(mountId,{center,onManage,canBook}); return; }
    if(!mount.isConnected) return;
    ui.month=d.month;
    const today=d.today, cur=today.slice(0,7);
    const phase=d.month<cur?['Historial','past']:d.month>cur?['Previsión','future']:['Mes en curso','now'];
    const byDay={}; d.slots.forEach(sl=>(byDay[sl.slot_date]??={slots:[],other:[]}).slots.push(sl)); (d.other||[]).forEach(b=>(byDay[b.booking_date]??={slots:[],other:[]}).other.push(b));
    const dayFig=day=>{ const x=byDay[day]||{slots:[],other:[]}; const offered=x.slots.reduce((n,s)=>n+Number(s.spots_total||0),0), taken=x.slots.reduce((n,s)=>n+Number(s.taken||0),0);
      const bks=[...x.slots.flatMap(s=>s.bookings),...x.other].filter(plActive); return {slots:x.slots,other:x.other,offered,taken,free:Math.max(offered-taken,0),divers:bks.reduce((n,b)=>n+Number(b.participants||1),0),revenue:bks.reduce((n,b)=>n+Number(b.price||0),0),bookings:bks.length}; };
    const st=d.stats, pv=d.prev_stats;
    const delta=(a,b,money)=>{ if(!b&&!a) return ''; if(!b) return '<span class="pl-delta up">nuevo</span>'; const p=Math.round((a-b)/b*100); if(!p) return '<span class="pl-delta">= que el mes anterior</span>'; return `<span class="pl-delta ${p>0?'up':'down'}">${p>0?'▲':'▼'} ${Math.abs(p)}% vs ${esc(plShortMonth(d.prev))}</span>`; };
    const kpi=(label,value,sub,extra='')=>`<div class="pl-kpi"><span>${label}</span><strong>${value}</strong>${sub?`<small>${sub}</small>`:''}${extra}</div>`;
    const occBar=(taken,offered)=>{ const p=offered?Math.min(100,Math.round(taken/offered*100)):0; return `<span class="pl-occ ${p>=100?'is-full':p>=70?'is-high':p>=35?'is-mid':''}"><i style="width:${p}%"></i></span>`; };
    const maxTrend=Math.max(1,...d.trend.map(t=>Math.max(t.offered,t.divers)));
    const trend=d.trend.map(t=>{ const off=Math.round(t.offered/maxTrend*100), tk=Math.round(Math.max(t.taken,t.divers)/maxTrend*100);
      return `<button type="button" class="pl-tbar ${t.month===d.month?'is-current':''} ${t.month>cur?'is-future':''} ${t.month===cur?'is-now':''}" data-month="${t.month}" title="${esc(plMonthLabel(t.month))}: ${t.slots} salidas · ${t.taken} de ${t.offered} plazas ocupadas · ${t.bookings} reservas · ${wdMoney(t.revenue)}"><span class="pl-tbar-col"><i class="off" style="height:${off}%"></i><i class="tk" style="height:${tk}%"></i></span><small>${esc(plShortMonth(t.month))}</small><b>${t.divers||''}</b></button>`; }).join('');
    // Calendar grid
    const [Y,M]=[+d.month.slice(0,4),+d.month.slice(5,7)-1]; const first=new Date(Y,M,1), days=new Date(Y,M+1,0).getDate(), lead=(first.getDay()+6)%7;
    let cells=''; for(let i=0;i<lead;i++) cells+='<div class="pl-cell is-blank" aria-hidden="true"></div>';
    for(let day=1;day<=days;day++){ const iso=plIso(new Date(Y,M,day)); const f=dayFig(iso); const n=f.slots.length+f.other.length;
      const chips=f.slots.slice(0,3).map(sl=>`<span class="pl-chip ${sl.status==='closed'?'is-closed':''}" style="--c:${esc(sl.service_color||'#2563eb')}"><b>${esc(sl.slot_time)}</b><em>${esc(sl.service_title)}</em><small>${sl.taken}/${sl.spots_total}</small></span>`).join('')+(f.other.length&&f.slots.length<3?`<span class="pl-chip is-loose" style="--c:#64748b"><em>${f.other.length} ${f.other.length===1?'reserva':'reservas'} sin salida</em></span>`:'');
      const more=n>3?`<span class="pl-more">+${n-3} más</span>`:'';
      cells+=`<button type="button" class="pl-cell ${iso===today?'is-today':''} ${iso<today?'is-past':''} ${n?'has-events':''}" data-day="${iso}" aria-label="${esc(wdLongDay(iso))}${n?`: ${f.slots.length} salidas, ${f.divers} buceadores`:''}">
        <span class="pl-cell-top"><span class="pl-num">${day}</span>${f.divers?`<span class="pl-divers" title="Buceadores">${wdIcon('users',12)}${f.divers}</span>`:''}</span>
        <span class="pl-chips">${chips}${more}</span>
        ${f.offered?`<span class="pl-cell-foot">${occBar(f.taken,f.offered)}<small>${f.free?`${f.free} libres`:'Completo'}</small></span>`:''}
        ${n?`<span class="pl-dots">${f.slots.slice(0,5).map(s=>`<i style="background:${esc(s.service_color||'#2563eb')}"></i>`).join('')}</span>`:''}
      </button>`; }
    // List view
    const listDays=Object.keys(byDay).sort();
    const list=listDays.map(day=>{ const f=dayFig(day); return `<section class="pl-lday ${day<today?'is-past':''} ${day===today?'is-today':''}"><button type="button" class="pl-lday-head" data-day="${day}"><span class="pl-ldate"><b>${new Date(+day.slice(0,4),+day.slice(5,7)-1,+day.slice(8,10)).getDate()}</b><small>${esc(wdDay(day).split(' ')[0].replace(',',''))}</small></span><span class="pl-lsum"><strong>${esc(wdLongDay(day))}</strong><small>${f.slots.length} ${f.slots.length===1?'salida':'salidas'} · ${f.divers} buceadores${f.offered?` · ${f.free} plazas libres`:''}</small></span>${f.offered?occBar(f.taken,f.offered):''}<span class="pl-lgo">›</span></button></section>`; }).join('');
    const legend=[...new Map(d.slots.map(s=>[s.service_title,s.service_color||'#2563eb'])).entries()].slice(0,10);
    const monthOpts=[]; for(let i=-24;i<=18;i++){ const x=new Date(+cur.slice(0,4),+cur.slice(5,7)-1+i,1); const m=plIso(x).slice(0,7); monthOpts.push(`<option value="${m}" ${m===d.month?'selected':''}>${esc(plMonthLabel(m))}</option>`); }
    mount.innerHTML=`<div class="pl-wrap pl-phase-${phase[1]}">
      <header class="pl-head">
        <div class="pl-title"><p class="eyebrow">Agenda operativa</p><h2>Planning</h2></div>
        <div class="pl-nav" role="group" aria-label="Mes">
          <button type="button" class="pl-arrow" data-go="${d.prev}" aria-label="Mes anterior">‹</button>
          <label class="pl-month"><span class="sr-only">Elegir mes</span><select id="pl-month">${monthOpts.join('')}</select><strong>${esc(plMonthLabel(d.month))}</strong></label>
          <button type="button" class="pl-arrow" data-go="${d.next}" aria-label="Mes siguiente">›</button>
          ${d.month!==cur?`<button type="button" class="btn pl-today" data-go="${cur}">Hoy</button>`:''}
        </div>
        <div class="pl-actions"><div class="pl-views" role="tablist"><button type="button" data-view="month" aria-pressed="${ui.view==='month'}">Mes</button><button type="button" data-view="list" aria-pressed="${ui.view==='list'}">Lista</button></div>${canBook?'<button type="button" class="btn btn-primary pl-new">+ Reserva</button>':''}</div>
      </header>
      <section class="pl-summary">
        <div class="pl-phase"><span class="pl-badge ${phase[1]}">${phase[0]}</span><p>${phase[1]==='past'?'Así fue este mes.':phase[1]==='future'?'Lo que ya está reservado para este mes.':'Cómo va el mes hasta ahora, incluidas las salidas que quedan.'}</p></div>
        <div class="pl-kpis">
          ${kpi('Salidas',st.slots,`${st.offered} plazas ofrecidas`,delta(st.slots,pv.slots))}
          ${kpi('Ocupación',st.offered?st.occupancy+'%':'—',`${st.taken} de ${st.offered} plazas`,occBar(st.taken,st.offered))}
          ${kpi('Reservas',st.bookings,`${st.divers} buceadores${st.pending?` · ${st.pending} por confirmar`:''}`,delta(st.bookings,pv.bookings))}
          ${kpi(phase[1]==='past'?'Ingresos':'Ingresos previstos',wdMoney(st.revenue),`${wdMoney(st.paid)} cobrado${st.cancelled?` · ${st.cancelled} canceladas`:''}`,delta(st.revenue,pv.revenue))}
          ${kpi('Plazas libres',st.free,phase[1]==='past'?'sin vender':'para vender',phase[1]!=='past'&&st.free?'<button type="button" class="pl-kpi-link pl-month-poster">Crear cartel</button>':'')}
        </div>
        <div class="pl-trend" aria-label="Últimos y próximos meses"><div class="pl-trend-head"><span>Tendencia</span><small><i class="off"></i>Plazas ofrecidas <i class="tk"></i>Ocupadas · cifra: buceadores</small></div><div class="pl-trend-bars">${trend}</div></div>
      </section>
      <div class="pl-body" data-view="${ui.view}">
        <div class="pl-cal"><div class="pl-week">${PL_WEEK.map(w=>`<span>${w}</span>`).join('')}</div><div class="pl-grid">${cells}</div></div>
        <div class="pl-list">${list||`<div class="svc-empty svc-empty-small"><span class="svc-empty-icon">${wdIcon('calendar',26)}</span><p>No hay salidas ni reservas en ${esc(plMonthLabel(d.month).toLowerCase())}.</p></div>`}</div>
      </div>
      ${legend.length?`<div class="pl-legend">${legend.map(([t,c])=>`<span><i style="background:${esc(c)}"></i>${esc(t)}</span>`).join('')}</div>`:''}
    </div>`;
    const go=m=>{ ui.month=m; closePop(); renderCenterPlanning(mountId,{center,onManage,canBook}); };
    $$('[data-go]',mount).forEach(b=>b.onclick=()=>go(b.dataset.go));
    $('#pl-month',mount).onchange=e=>go(e.target.value);
    $$('.pl-tbar',mount).forEach(b=>b.onclick=()=>go(b.dataset.month));
    $$('.pl-views button',mount).forEach(b=>b.onclick=()=>{ ui.view=b.dataset.view; $('.pl-body',mount).dataset.view=ui.view; $$('.pl-views button',mount).forEach(x=>x.setAttribute('aria-pressed',String(x===b))); closePop(); });
    const reload=()=>renderCenterPlanning(mountId,{center,onManage,canBook});
    $('.pl-new',mount)&&($('.pl-new',mount).onclick=()=>openManualBooking({date:d.month===cur?today:`${d.month}-01`,onSaved:reload}));
    $('.pl-month-poster',mount)?.addEventListener('click',()=>{ const up=d.slots.filter(s=>s.slot_date>=today&&s.status!=='closed'&&plFree(s)>0); if(!up.length){toast('No quedan salidas con plazas libres este mes.');return;} openPosterStudio({center,slots:up.slice(0,6)}); });
    $$('.pl-cell.has-events,.pl-cell[data-day],.pl-lday-head',mount).forEach(c=>c.onclick=()=>openDay(c.dataset.day,c));
    // ---- Bocadillo del día
    function closePop(){ document.getElementById('pl-pop')?.remove(); document.removeEventListener('keydown',onKey); $$('.pl-cell.is-open',mount).forEach(x=>x.classList.remove('is-open')); }
    function onKey(e){ if(e.key==='Escape') closePop(); }
    function openDay(day,anchor){
      closePop(); const f=dayFig(day); const past=day<today;
      anchor.classList.add('is-open');
      const slotCard=sl=>{ const free=plFree(sl), end=plEndTime(sl.slot_time,sl.duration_minutes), act=sl.bookings.filter(plActive), gone=sl.bookings.length-act.length;
        const stTag=sl.status==='closed'?'<span class="pl-tag bad">Cerrada</span>':free<=0?'<span class="pl-tag good">Completa</span>':`<span class="pl-tag ${free<=2?'warn':''}">${free} ${free===1?'plaza libre':'plazas libres'}</span>`;
        return `<article class="pl-slot" style="--c:${esc(sl.service_color||'#2563eb')}">
          <div class="pl-slot-head"><span class="pl-time">${esc(sl.slot_time)}${end?`<small>– ${end}</small>`:''}</span><div class="pl-slot-title"><strong>${esc(sl.service_title)}</strong><small>${esc(sl.points.map(p=>p.name).join(' · ')||'Punto a elegir')}</small></div>${stTag}</div>
          <div class="pl-slot-occ">${occBar(sl.taken,sl.spots_total)}<small>${sl.taken} de ${sl.spots_total} plazas ocupadas</small></div>
          ${act.length?`<ul class="pl-people">${act.map(b=>b.placeholder?`<li><span class="pl-person is-placeholder" title="Un buceador está pagando estas plazas. Si no completa el pago en unos minutos, se liberan solas."><span class="pl-avatar">…</span><span class="pl-pname">Pago en curso${Number(b.participants)>1?` <em>×${b.participants}</em>`:''}</span></span></li>`:`<li><button type="button" class="pl-person" data-booking="${b.id}"><span class="pl-avatar">${esc(initials(b.fullname||'?'))}</span><span class="pl-pname">${esc(b.fullname||'Cliente')}${Number(b.participants)>1?` <em>×${b.participants}</em>`:''}</span>${PL_PAY[b.payment_status]?`<span class="pl-tag ${PL_PAY[b.payment_status][1]}">${PL_PAY[b.payment_status][0]}</span>`:''}${(b.status==='requested'||b.status==='pending')?'<span class="pl-tag warn">Solicitud</span>':b.status==='accepted_pending_payment'?'<span class="pl-tag warn">Aceptada · pendiente de pago</span>':''}</button></li>`).join('')}</ul>`:'<p class="pl-nobody">Todavía sin reservas.</p>'}
          ${gone?`<p class="pl-gone">${gone} ${gone===1?'reserva cancelada':'reservas canceladas'}</p>`:''}
          <div class="pl-slot-actions">${!past&&sl.status!=='closed'&&free>0?`${canBook?`<button type="button" class="btn pl-add" data-slot="${sl.id}" data-service="${sl.service_id}">+ Reserva</button>`:''}<button type="button" class="btn pl-poster" data-slot="${sl.id}">${wdIcon('image',15)} Crear cartel</button>`:''}<button type="button" class="btn pl-manage">Gestionar</button></div>
        </article>`; };
      const loose=f.other.filter(plActive);
      const html=`<div class="pl-pop" id="pl-pop" role="dialog" aria-label="${esc(wdLongDay(day))}">
        <header class="pl-pop-head"><div><p class="eyebrow">${past?'Historial':day===today?'Hoy':'Agenda'}</p><h3>${esc(wdLongDay(day))}</h3></div><button type="button" class="pl-pop-x" aria-label="Cerrar">×</button></header>
        <div class="pl-pop-sum"><span><b>${f.slots.length}</b> ${f.slots.length===1?'salida':'salidas'}</span><span><b>${f.divers}</b> buceadores</span>${f.offered?`<span><b>${f.free}</b> plazas libres</span>`:''}<span><b>${wdMoney(f.revenue)}</b></span></div>
        <div class="pl-pop-body">${f.slots.map(slotCard).join('')}
          ${loose.length?`<article class="pl-slot" style="--c:#64748b"><div class="pl-slot-head"><span class="pl-time">—</span><div class="pl-slot-title"><strong>Reservas sin salida programada</strong><small>Alquileres o reservas con hora libre</small></div></div><ul class="pl-people">${loose.map(b=>`<li><button type="button" class="pl-person" data-booking="${b.id}"><span class="pl-avatar">${esc(initials(b.fullname||'?'))}</span><span class="pl-pname">${esc(b.fullname||'Cliente')}${Number(b.participants)>1?` <em>×${b.participants}</em>`:''}<small>${esc([b.booking_time,b.service_title].filter(Boolean).join(' · '))}</small></span>${PL_PAY[b.payment_status]?`<span class="pl-tag ${PL_PAY[b.payment_status][1]}">${PL_PAY[b.payment_status][0]}</span>`:''}</button></li>`).join('')}</ul></article>`:''}
          ${!f.slots.length&&!loose.length?`<div class="pl-pop-empty">${past?'Este día no hubo actividad.':'No hay salidas este día.'}</div>`:''}
        </div>
        <footer class="pl-pop-foot">${!past&&canBook?`<button type="button" class="btn pl-day-add">+ Reserva este día</button>`:''}${!past&&f.slots.some(s=>s.status!=='closed'&&plFree(s)>0)?`<button type="button" class="btn btn-primary pl-day-poster">${wdIcon('image',15)} Cartel del día</button>`:''}</footer>
      </div>`;
      document.body.insertAdjacentHTML('beforeend',html);
      const pop=document.getElementById('pl-pop');
      // Position: next to the day on wide screens, as a bottom sheet on phones.
      if(window.innerWidth>=760){ const r=anchor.getBoundingClientRect(), w=Math.min(420,window.innerWidth-32); pop.style.width=w+'px';
        let left=r.right+12; if(left+w>window.innerWidth-16) left=r.left-w-12; if(left<16) left=Math.max(16,Math.min(window.innerWidth-w-16,r.left+r.width/2-w/2));
        const h=Math.min(pop.offsetHeight,window.innerHeight-32); let top=r.top+r.height/2-h/2; top=Math.max(16,Math.min(window.innerHeight-h-16,top));
        pop.style.left=left+'px'; pop.style.top=top+'px'; pop.classList.add('is-float'); }
      else pop.classList.add('is-sheet');
      document.addEventListener('keydown',onKey);
      const outside=e=>{ if(!document.getElementById('pl-pop')){document.removeEventListener('mousedown',outside,true);return;} if(!pop.contains(e.target)&&!e.target.closest('.pl-cell,.pl-lday-head')){ closePop(); document.removeEventListener('mousedown',outside,true);} };
      document.addEventListener('mousedown',outside,true);
      window.addEventListener('hashchange',closePop,{once:true});
      pop.querySelector('.pl-pop-x').onclick=closePop;
      pop.querySelector('.pl-pop-x').focus({preventScroll:true});
      $$('.pl-person',pop).forEach(b=>b.onclick=()=>{ closePop(); location.hash='#/reserva?id='+b.dataset.booking; });
      $$('.pl-add',pop).forEach(b=>b.onclick=()=>{ closePop(); openManualBooking({serviceId:+b.dataset.service,slotId:+b.dataset.slot,onSaved:reload}); });
      $$('.pl-poster',pop).forEach(b=>b.onclick=()=>{ const sl=f.slots.find(x=>String(x.id)===b.dataset.slot); closePop(); if(sl) openPosterStudio({center,slots:[sl]}); });
      $$('.pl-manage',pop).forEach(b=>b.onclick=()=>{ closePop(); onManage?.(); });
      pop.querySelector('.pl-day-add')?.addEventListener('click',()=>{ closePop(); openManualBooking({date:day,onSaved:reload}); });
      pop.querySelector('.pl-day-poster')?.addEventListener('click',()=>{ closePop(); openPosterStudio({center,slots:f.slots.filter(s=>s.status!=='closed'&&plFree(s)>0)}); });
    }
  }

  // ---------------------------------------------------------------------------
  // Generador de carteles para redes sociales (v50.27): 6 plantillas
  // ---------------------------------------------------------------------------
  const POSTER_FORMATS={post:{w:1080,h:1350,label:'Publicación',hint:'4:5 · Instagram y Facebook'},story:{w:1080,h:1920,label:'Historia',hint:'9:16 · Stories, Reels y WhatsApp'},square:{w:1080,h:1080,label:'Cuadrado',hint:'1:1'}};
  const posterLoadImg=src=>new Promise(res=>{ if(!src) return res(null); const im=new Image(); if(/^https?:/i.test(src)&&!src.startsWith(location.origin)) im.crossOrigin='anonymous'; im.onload=()=>res(im); im.onerror=()=>res(null); im.src=src; });
  let posterFontsReady=null;
  function loadPosterFonts(){
    if(posterFontsReady) return posterFontsReady;
    const list=[['WDPDisplay','InterDisplay-Black',{weight:'900'}],['WDPDisplay','InterDisplay-BlackItalic',{weight:'900',style:'italic'}],['WDPSans','Inter-ExtraBold',{weight:'800'}],['WDPSans','Inter-SemiBold',{weight:'600'}],['WDPSans','Inter-Regular',{weight:'400'}]];
    // v50.33: Polish and Russian letters come from the latin-ext and cyrillic subsets of the same font (OFL).
    const EXT={'latin-ext':'U+0100-02AF,U+0304,U+0308,U+0329,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF','cyrillic':'U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116'};
    const WEIGHT={'InterDisplay-Black':'900','InterDisplay-BlackItalic':'900-italic','Inter-ExtraBold':'800','Inter-SemiBold':'600','Inter-Regular':'400'};
    list.slice().forEach(([fam,file,d])=>Object.keys(EXT).forEach(sub=>list.push([fam,`Inter-${sub}-${WEIGHT[file]}`,{...d,unicodeRange:EXT[sub]},'woff2'])));
    posterFontsReady=Promise.all(list.map(([fam,file,d,fmt='woff'])=>{ try{ const f=new FontFace(fam,`url(/assets/fonts/${file}.${fmt}) format("${fmt}")`,d); return f.load().then(x=>document.fonts.add(x)).catch(()=>null); }catch{ return null; } }));
    return posterFontsReady;
  }
  // Drawing kit shared by every template
  const PK={
    disp:(s,it)=>`${it?'italic ':''}900 ${Math.round(s)}px WDPDisplay, "Arial Black", Impact, sans-serif`,
    sans:(s,w=600)=>`${w} ${Math.round(s)}px WDPSans, "Segoe UI", Roboto, system-ui, sans-serif`,
    serif:(s,w=400,it)=>`${it?'italic ':''}${w} ${Math.round(s)}px Georgia, "Times New Roman", serif`,
    rr(ctx,x,y,w,h,r){ r=Math.min(r,w/2,h/2); ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath(); },
    cover(ctx,img,x,y,w,h,fy=.5){ const s=Math.max(w/img.width,h/img.height), iw=img.width*s, ih=img.height*s; ctx.drawImage(img,x+(w-iw)/2,y+(h-ih)*fy,iw,ih); },
    wrap(ctx,text,maxW){ const words=String(text||'').split(/\s+/).filter(Boolean); const lines=[]; let line=''; words.forEach(w=>{ const t=line?line+' '+w:w; if(ctx.measureText(t).width>maxW&&line){ lines.push(line); line=w; } else line=t; }); if(line) lines.push(line); return lines; },
    fit(ctx,text,fontFn,start,maxW,min=14){ let s=start; ctx.font=fontFn(s); while(ctx.measureText(text).width>maxW&&s>min){ s-=2; ctx.font=fontFn(s); } return s; },
    block(ctx,text,fontFn,start,maxW,maxLines,min=24){ let s=start, lines; for(;;){ ctx.font=fontFn(s); lines=PK.wrap(ctx,text,maxW); if((lines.length<=maxLines&&lines.every(l=>ctx.measureText(l).width<=maxW))||s<=min) break; s-=4; } return {size:s,lines:lines.slice(0,maxLines)}; },
    ellipsis(ctx,text,maxW){ let t=String(text||''); if(ctx.measureText(t).width<=maxW) return t; while(t.length>1&&ctx.measureText(t+'…').width>maxW) t=t.slice(0,-1); return t.trim()+'…'; },
    spaced(ctx,text,x,y,sp,align='left'){ const chars=[...String(text)]; const w=chars.reduce((n,c)=>n+ctx.measureText(c).width,0)+sp*(chars.length-1); let cx=align==='center'?x-w/2:align==='right'?x-w:x; const a=ctx.textAlign; ctx.textAlign='left'; chars.forEach(c=>{ ctx.fillText(c,cx,y); cx+=ctx.measureText(c).width+sp; }); ctx.textAlign=a; return w; },
    qr(ctx,m,x,y,size,fg='#0b2f3f',bg='#fff',pad=14,r=18){ if(!m) return; ctx.fillStyle=bg; PK.rr(ctx,x-pad,y-pad,size+pad*2,size+pad*2,r); ctx.fill(); const n=m.length,c=size/n; ctx.fillStyle=fg; m.forEach((row,ri)=>{ for(let k=0;k<n;k++) if(row[k]==='1') ctx.fillRect(x+k*c,y+ri*c,Math.ceil(c),Math.ceil(c)); }); },
    logo(ctx,o,x,y,s,ring='#fff',monoBg='#0b6f8a',monoInk='#fff'){ ctx.save(); ctx.beginPath(); ctx.arc(x+s/2,y+s/2,s/2,0,Math.PI*2); ctx.fillStyle=ring; ctx.fill(); ctx.clip();
      if(o.logo){ const k=Math.min((s*.78)/o.logo.width,(s*.78)/o.logo.height); ctx.drawImage(o.logo,x+(s-o.logo.width*k)/2,y+(s-o.logo.height*k)/2,o.logo.width*k,o.logo.height*k); }
      else { ctx.fillStyle=monoBg; ctx.fillRect(x,y,s,s); ctx.fillStyle=monoInk; ctx.font=PK.sans(s*.38,800); ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(initials(o.centerName||'WD'),x+s/2,y+s/2+1); ctx.textBaseline='alphabetic'; ctx.textAlign='left'; }
      ctx.restore(); },
    money:(o,v)=>v?wdMoney(v,o.currency):'',
    free:n=>t(`${n} ${n===1?'plaza':'plazas'}`),
    darken(ctx,W,H,stops){ const g=ctx.createLinearGradient(0,0,0,H); stops.forEach(([p,c])=>g.addColorStop(p,c)); ctx.fillStyle=g; ctx.fillRect(0,0,W,H); },
    noPhoto(ctx,W,H,a,b){ const g=ctx.createLinearGradient(0,0,W,H); g.addColorStop(0,a); g.addColorStop(1,b); ctx.fillStyle=g; ctx.fillRect(0,0,W,H); ctx.save(); ctx.globalAlpha=.10; ctx.strokeStyle='#fff'; ctx.lineWidth=3; for(let i=0;i<14;i++){ ctx.beginPath(); for(let x=0;x<=W;x+=20){ const y=H*.25+i*H*.06+Math.sin(x/90+i)*18; x?ctx.lineTo(x,y):ctx.moveTo(x,y); } ctx.stroke(); } ctx.restore(); }
  };

  // Each template draws into a 1080-wide canvas. k (1 → 0.7) shrinks type until everything fits; it returns true when it overflowed.
  const POSTER_TEMPLATES={
    // 1 · Urgency, full-bleed photo, huge condensed headline, round sticker
    ultima:{name:'Última llamada',hint:'Urgente y directo',accents:['#ffd23f','#ff5a36','#3ee6c5','#ffffff'],draw(ctx,W,H,o,k){
      const A=o.accent, P=72;
      if(o.photo){ PK.cover(ctx,o.photo,0,0,W,H,.4); PK.darken(ctx,W,H,[[0,'rgba(2,20,30,.55)'],[.35,'rgba(2,20,30,.15)'],[.6,'rgba(2,20,30,.7)'],[1,'rgba(2,20,30,.96)']]); } else PK.noPhoto(ctx,W,H,'#062a3b','#0b5d73');
      // header
      PK.logo(ctx,o,P,P,84); ctx.fillStyle='#fff'; PK.fit(ctx,o.centerName,s=>PK.sans(s,800),34,W-P*2-84-300); ctx.fillText(o.centerName,P+104,P+40); ctx.font=PK.sans(24,600); ctx.fillStyle='rgba(255,255,255,.75)'; ctx.fillText(PK.ellipsis(ctx,o.place,W-P*2-104-300),P+104,P+74);
      // sticker
      if(o.showSpots&&o.totalFree){ const r=118*Math.min(1,k+.1), cx=W-P-r+10, cy=P+r-6; ctx.save(); ctx.translate(cx,cy); ctx.rotate(.14); ctx.fillStyle=A; ctx.beginPath(); for(let i=0;i<40;i++){ const ang=i/40*Math.PI*2, rr=i%2?r:r*.9; ctx.lineTo(Math.cos(ang)*rr,Math.sin(ang)*rr); } ctx.closePath(); ctx.fill();
        ctx.fillStyle='#0b1d26'; ctx.textAlign='center'; ctx.font=PK.sans(r*.2,800); ctx.fillText(t('QUEDAN'),0,-r*.36); ctx.font=PK.disp(r*.86); ctx.fillText(String(o.totalFree),0,r*.34); ctx.font=PK.sans(r*.2,800); ctx.fillText(t(o.totalFree===1?'PLAZA':'PLAZAS'),0,r*.62); ctx.restore(); ctx.textAlign='left'; }
      // bottom-up layout
      const qrS=o.qr?150:0, barH=112*k;
      let y=H-barH; ctx.fillStyle=A; ctx.fillRect(0,y,W,barH); ctx.fillStyle='#0b1d26'; PK.fit(ctx,o.cta.toUpperCase()+'  →',s=>PK.disp(s),46*k,W-P*2-(o.qr?qrS+40:0)); ctx.fillText(o.cta.toUpperCase()+'  →',P,y+barH/2+16*k);
      if(o.qr) PK.qr(ctx,o.qr,W-P-qrS,y-qrS/2-20,qrS,'#0b1d26','#fff',12,16);
      y-=40*k+(o.qr?qrS/2:0);
      const rows=o.slots.slice(0,o.rowsMax); const rh=78*k;
      for(let i=rows.length-1;i>=0;i--){ const s=rows[i]; y-=rh; ctx.strokeStyle='rgba(255,255,255,.22)'; ctx.lineWidth=2; ctx.beginPath(); ctx.moveTo(P,y+rh); ctx.lineTo(W-P,y+rh); ctx.stroke();
        ctx.fillStyle=A; ctx.font=PK.disp(40*k); ctx.fillText(s.time.split('–')[0],P,y+rh*.66); const tw=ctx.measureText('00:00').width+28;
        const right=[o.showPrice&&s.price?PK.money(o,s.price):'',o.showSpots?PK.free(s.free):''].filter(Boolean).join('  ·  '); ctx.font=PK.sans(28*k,800); const rw=ctx.measureText(right).width; ctx.fillStyle='#fff'; ctx.textAlign='right'; ctx.fillText(right,W-P,y+rh*.64); ctx.textAlign='left';
        ctx.font=PK.sans(30*k,600); ctx.fillStyle='#fff'; ctx.fillText(PK.ellipsis(ctx,s.title+(s.sub?' · '+s.sub:''),W-P*2-tw-rw-24),P+tw,y+rh*.64); }
      if(o.slots.length>rows.length){ y-=44*k; ctx.font=PK.sans(26*k,600); ctx.fillStyle='rgba(255,255,255,.75)'; ctx.fillText(t(`+ ${o.slots.length-rows.length} salidas más`),P,y+30*k); }
      y-=36*k;
      // date chip
      ctx.font=PK.sans(34*k,800); const dt=o.dateText.toUpperCase(); const dw=ctx.measureText(dt).width+56; y-=74*k; ctx.fillStyle='#fff'; PK.rr(ctx,P,y,dw,64*k,32*k); ctx.fill(); ctx.fillStyle='#0b1d26'; ctx.fillText(dt,P+28,y+44*k);
      // headline (condensed)
      if(o.message){ ctx.font=PK.sans(30*k,600); const ml=PK.wrap(ctx,o.message,W-P*2).slice(0,2); y-=18*k+ml.length*40*k; ml.forEach((l,i)=>{ ctx.fillStyle='rgba(255,255,255,.9)'; ctx.fillText(l,P,y+30*k+i*40*k); }); }
      const hl=o.headline.toUpperCase(); const b=PK.block(ctx,hl,s=>PK.disp(s),(o.format==='story'?190:o.format==='square'?118:150)*k,(W-P*2)/0.84,3,60);
      const lh=b.size*.94; y-=14*k+b.lines.length*lh;
      ctx.save(); ctx.translate(P,0); ctx.scale(.84,1); ctx.fillStyle='#fff'; ctx.font=PK.disp(b.size); b.lines.forEach((l,i)=>ctx.fillText(l,0,y+lh*(i+.88))); ctx.restore();
      // kicker
      if(o.badge){ y-=58*k; ctx.font=PK.sans(26*k,800); ctx.fillStyle=A; PK.spaced(ctx,o.badge.toUpperCase(),P,y+34*k,4); }
      return y<P+84+40;
    }},
    // 2 · Magazine cover
    revista:{name:'Portada de revista',hint:'Editorial y elegante',accents:['#ff5a36','#ffd23f','#58d6ff','#ffffff'],draw(ctx,W,H,o,k){
      const A=o.accent, P=64;
      if(o.photo){ PK.cover(ctx,o.photo,0,0,W,H); PK.darken(ctx,W,H,[[0,'rgba(0,0,0,.62)'],[.22,'rgba(0,0,0,.05)'],[.55,'rgba(0,0,0,.05)'],[1,'rgba(0,0,0,.82)']]); } else PK.noPhoto(ctx,W,H,'#0f3446','#2e7c8e');
      // masthead
      ctx.fillStyle='#fff'; ctx.textAlign='center'; const mh=o.centerName.toUpperCase(); const ms=PK.fit(ctx,mh,s=>PK.serif(s,700),o.format==='square'?120:150,W-P*2,48); ctx.fillText(mh,W/2,P+ms*.82);
      let y=P+ms*.82+24; ctx.fillStyle='rgba(255,255,255,.9)'; ctx.fillRect(P,y,W-P*2,3); y+=36; ctx.font=PK.sans(22,600); PK.spaced(ctx,[o.dp?`Nº ${o.dp.day}`:t('EDICIÓN'),o.dp?(o.dp.month+' '+o.dp.year).toUpperCase():'',o.place.toUpperCase()].filter(Boolean).join('  ·  '),W/2,y,3,'center'); ctx.textAlign='left';
      const top=y+20;
      // price sticker
      if(o.showPrice&&o.minPrice){ const r=96, cx=W-P-r, cy=top+r+40; ctx.fillStyle=A; ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2); ctx.fill(); ctx.fillStyle='#fff'; ctx.textAlign='center'; ctx.font=PK.serif(26,400,true); ctx.fillText(t('desde'),cx,cy-28); PK.fit(ctx,PK.money(o,o.minPrice),s=>PK.disp(s),62,r*1.7); ctx.fillText(PK.money(o,o.minPrice),cx,cy+26); ctx.font=PK.sans(18,600); ctx.fillText(t('por persona'),cx,cy+56); ctx.textAlign='left'; }
      // bottom: date + QR
      let b=H-P; const qrS=o.qr?130:0;
      if(o.qr){ PK.qr(ctx,o.qr,W-P-qrS,b-qrS,qrS,'#111','#fff',12,6); ctx.fillStyle='#fff'; ctx.font=PK.sans(18,600); ctx.textAlign='right'; ctx.fillText(t('ESCANEA Y RESERVA'),W-P,b-qrS-24); ctx.textAlign='left'; }
      ctx.fillStyle='#fff'; ctx.font=PK.serif(30*k,400,true); ctx.fillText(o.cta,P,b-8); ctx.font=PK.sans(22*k,600); ctx.fillStyle='rgba(255,255,255,.8)'; if(o.phone) ctx.fillText(o.phone,P,b-48*k);
      b-=Math.max(qrS+60,110*k);
      // cover lines (slots)
      const rows=o.slots.slice(0,o.rowsMax);
      for(let i=rows.length-1;i>=0;i--){ const s=rows[i]; b-=88*k; ctx.fillStyle=A; ctx.fillRect(P,b+10*k,7,64*k); ctx.fillStyle='#fff'; ctx.font=PK.disp(38*k); ctx.fillText(s.time.split('–')[0],P+24,b+44*k); ctx.font=PK.sans(25*k,600); ctx.fillStyle='rgba(255,255,255,.92)'; const extra=[s.title,o.showSpots?`${s.free} ${t(s.free===1?'plaza libre':'plazas libres')}`:''].filter(Boolean).join(' — '); ctx.fillText(PK.ellipsis(ctx,extra,W-P*2-26),P+24,b+76*k); }
      b-=58*k; ctx.font=PK.sans(30*k,800); ctx.fillStyle='#fff'; PK.spaced(ctx,o.dateText.toUpperCase(),P,b+40*k,2);
      b-=30*k;
      // headline in italic serif + kicker
      const hb=PK.block(ctx,o.headline,s=>PK.serif(s,700,true),(o.format==='story'?132:o.format==='square'?84:104)*k,W-P*2-(o.showPrice&&o.minPrice?60:0),3,44);
      const lh=hb.size*1.02; b-=hb.lines.length*lh; ctx.fillStyle='#fff'; ctx.font=PK.serif(hb.size,700,true); hb.lines.forEach((l,i)=>ctx.fillText(l,P,b+lh*(i+.82)));
      if(o.badge){ b-=56*k; ctx.font=PK.sans(24*k,800); const bw=ctx.measureText(o.badge.toUpperCase()).width+40; ctx.fillStyle=A; ctx.fillRect(P,b,bw,46*k); ctx.fillStyle='#fff'; ctx.fillText(o.badge.toUpperCase(),P+20,b+32*k); }
      if(o.message&&o.format!=='square'){ const ml=(()=>{ ctx.font=PK.sans(28*k,400); return PK.wrap(ctx,o.message,W*0.62).slice(0,2); })(); const yy=top+40; ml.forEach((l,i)=>{ ctx.fillStyle='rgba(255,255,255,.92)'; ctx.fillText(l,P,yy+i*38*k); }); }
      return b<top+(o.format==='square'?20:120);
    }},
    // 3 · Electric neon night
    neon:{name:'Noche eléctrica',hint:'Neón, para destacar',accents:['#2ef2ff','#ff3ea5','#b6ff3b','#ffb13b'],draw(ctx,W,H,o,k){
      const A=o.accent, B=A==='#ff3ea5'?'#2ef2ff':'#ff3ea5', P=70;
      const g=ctx.createLinearGradient(0,0,W,H); g.addColorStop(0,'#090322'); g.addColorStop(.55,'#1c0b4b'); g.addColorStop(1,'#03344a'); ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
      if(o.photo){ ctx.save(); ctx.globalAlpha=.55; ctx.globalCompositeOperation='luminosity'; PK.cover(ctx,o.photo,0,0,W,H); ctx.restore(); PK.darken(ctx,W,H,[[0,'rgba(9,3,34,.35)'],[.5,'rgba(9,3,34,.25)'],[1,'rgba(9,3,34,.92)']]); }
      const glow=(c,b)=>{ ctx.shadowColor=c; ctx.shadowBlur=b; };
      // giant outlined day number
      if(o.dp){ ctx.save(); ctx.font=PK.disp(o.format==='square'?520:640); ctx.lineWidth=5; ctx.strokeStyle=A; ctx.globalAlpha=.35; glow(A,24); ctx.textAlign='right'; ctx.strokeText(o.dp.day,W+30,o.format==='square'?560:H*.5); ctx.restore(); }
      PK.logo(ctx,o,P,P,76,'#fff'); ctx.fillStyle='#fff'; ctx.font=PK.sans(30,800); ctx.fillText(PK.ellipsis(ctx,o.centerName,W-P*2-100),P+96,P+36); ctx.font=PK.sans(22,600); ctx.fillStyle='rgba(255,255,255,.7)'; ctx.fillText(PK.ellipsis(ctx,o.place,W-P*2-100),P+96,P+66);
      let y=o.format==='story'?H*.33:o.format==='square'?P+150:H*.24;
      if(o.badge){ ctx.font=PK.sans(26*k,800); glow(B,18); ctx.fillStyle=B; PK.spaced(ctx,o.badge.toUpperCase(),P,y,6); ctx.shadowBlur=0; y+=26*k; }
      const hb=PK.block(ctx,o.headline.toUpperCase(),s=>PK.disp(s,true),(o.format==='story'?150:o.format==='square'?96:122)*k,W-P*2,3,48); const lh=hb.size*.98;
      ctx.font=PK.disp(hb.size,true); glow(A,34); ctx.fillStyle='#fff'; hb.lines.forEach((l,i)=>ctx.fillText(l,P,y+lh*(i+.9))); ctx.shadowBlur=0; y+=hb.lines.length*lh+24*k;
      if(o.dp){ ctx.font=PK.sans(40*k,800); ctx.fillStyle=A; glow(A,16); ctx.fillText(`${o.dp.wd.toUpperCase()} ${o.dp.day} ${o.dp.mon}`,P,y+40*k); ctx.shadowBlur=0; y+=66*k; } else { ctx.font=PK.sans(34*k,800); ctx.fillStyle=A; ctx.fillText(o.dateText,P,y+36*k); y+=60*k; }
      if(o.message&&o.format!=='square'){ ctx.font=PK.sans(28*k,400); ctx.fillStyle='rgba(255,255,255,.85)'; PK.wrap(ctx,o.message,W-P*2).slice(0,2).forEach((l,i)=>ctx.fillText(l,P,y+30*k+i*38*k)); y+=90*k; }
      y+=12*k;
      const rows=o.slots.slice(0,o.rowsMax), rh=92*k;
      rows.forEach((s,i)=>{ const ry=y+i*(rh+14*k); ctx.lineWidth=3; ctx.strokeStyle=i%2?B:A; glow(i%2?B:A,18); PK.rr(ctx,P,ry,W-P*2,rh,rh/2); ctx.stroke(); ctx.shadowBlur=0; ctx.fillStyle='rgba(255,255,255,.05)'; ctx.fill();
        ctx.fillStyle='#fff'; ctx.font=PK.disp(40*k); ctx.fillText(s.time.split('–')[0],P+36,ry+rh*.64); ctx.font=PK.sans(30*k,600); const right=[o.showPrice&&s.price?PK.money(o,s.price):'',o.showSpots?PK.free(s.free):''].filter(Boolean).join(' · '); ctx.textAlign='right'; ctx.fillStyle=i%2?B:A; ctx.font=PK.sans(28*k,800); ctx.fillText(right,W-P-36,ry+rh*.62); const rw=ctx.measureText(right).width; ctx.textAlign='left'; ctx.fillStyle='#fff'; ctx.font=PK.sans(28*k,600); ctx.fillText(PK.ellipsis(ctx,s.title,W-P*2-210-rw),P+180,ry+rh*.62); });
      y+=rows.length*(rh+14*k);
      const qrS=o.qr?140:0; const by=H-P-(o.qr?qrS:70);
      if(o.qr) PK.qr(ctx,o.qr,W-P-qrS,H-P-qrS,qrS,'#0b0322','#fff',12,18);
      const cw=Math.min(W-P*2-(o.qr?qrS+50:0),640); const ch=86*k; const cy=H-P-ch-(o.qr?(qrS-ch)/2:0);
      const cg=ctx.createLinearGradient(P,0,P+cw,0); cg.addColorStop(0,B); cg.addColorStop(1,A); ctx.fillStyle=cg; glow(B,22); PK.rr(ctx,P,cy,cw,ch,ch/2); ctx.fill(); ctx.shadowBlur=0; ctx.fillStyle='#0b0322'; PK.fit(ctx,o.cta.toUpperCase(),s=>PK.sans(s,800),32*k,cw-60); ctx.textAlign='center'; ctx.fillText(o.cta.toUpperCase(),P+cw/2,cy+ch/2+11*k); ctx.textAlign='left';
      return y>Math.min(cy,by)-20;
    }},
    // 4 · Travel postcard
    postal:{name:'Postal de viaje',hint:'Cálida y cercana',accents:['#e4572e','#0b7a89','#2a9d5c','#7a3fbf'],draw(ctx,W,H,o,k){
      const A=o.accent, P=64, ink='#173c47';
      ctx.fillStyle='#f4ead7'; ctx.fillRect(0,0,W,H); ctx.save(); ctx.globalAlpha=.07; ctx.strokeStyle=ink; ctx.lineWidth=2; for(let i=-H;i<W;i+=26){ ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i+H,H); ctx.stroke(); } ctx.restore();
      // polaroid
      const pw=o.format==='square'?560:W*.74, ph=o.format==='story'?pw*1.05:o.format==='square'?400:pw*.78; const px=o.format==='square'?P:(W-pw)/2-20, py=o.format==='square'?P+40:P+70;
      ctx.save(); ctx.translate(px+pw/2,py+ph/2); ctx.rotate(-.045); ctx.shadowColor='rgba(40,25,10,.28)'; ctx.shadowBlur=36; ctx.shadowOffsetY=14; ctx.fillStyle='#fffdf8'; ctx.fillRect(-pw/2-22,-ph/2-22,pw+44,ph+110); ctx.shadowColor='transparent';
      if(o.photo) PK.cover(ctx,o.photo,-pw/2,-ph/2,pw,ph); else { const gg=ctx.createLinearGradient(0,-ph/2,0,ph/2); gg.addColorStop(0,'#5cc3cf'); gg.addColorStop(1,'#0b5d73'); ctx.fillStyle=gg; ctx.fillRect(-pw/2,-ph/2,pw,ph); }
      ctx.fillStyle=ink; ctx.font=PK.serif(34,400,true); ctx.textAlign='center'; ctx.fillText(PK.ellipsis(ctx,o.message||(t('Saludos desde')+' '+(o.place||'el mar')),pw-40),0,ph/2+62); ctx.textAlign='left';
      ctx.fillStyle='rgba(240,214,150,.75)'; ctx.save(); ctx.rotate(-.3); ctx.fillRect(-pw/2-40,-ph/2-10,150,44); ctx.restore(); ctx.save(); ctx.translate(pw/2,-ph/2); ctx.rotate(.4); ctx.fillRect(-60,-10,150,44); ctx.restore();
      ctx.restore();
      // stamp
      const sw=o.format==='square'?300:200, sh=sw*1.2, sx=W-P-sw, sy=o.format==='square'?P+30:P;
      ctx.save(); ctx.translate(sx+sw/2,sy+sh/2); ctx.rotate(.06); ctx.fillStyle='#fffdf8'; ctx.beginPath(); const n=10, step=sw/n; for(let i=0;i<=n;i++){ ctx.arc(-sw/2+i*step,-sh/2,step*.28,Math.PI,0,false);} ctx.lineTo(sw/2,sh/2); ctx.lineTo(-sw/2,sh/2); ctx.closePath(); ctx.fill();
      ctx.fillStyle=A; ctx.fillRect(-sw/2+16,-sh/2+16,sw-32,sh-32); ctx.fillStyle='#fff'; ctx.textAlign='center'; if(o.dp){ ctx.font=PK.disp(sw*.42); ctx.fillText(o.dp.day,0,sh*.06); ctx.font=PK.sans(sw*.13,800); ctx.fillText(o.dp.mon,0,sh*.22); ctx.font=PK.sans(sw*.09,600); ctx.fillText(o.dp.wd.toUpperCase(),0,-sh*.25); } else { ctx.font=PK.sans(sw*.12,800); ctx.fillText(t('SALIDAS'),0,0); } ctx.restore(); ctx.textAlign='left';
      ctx.save(); ctx.strokeStyle='rgba(23,60,71,.45)'; ctx.lineWidth=3; ctx.beginPath(); ctx.arc(sx-10,sy+sh*.75,74,0,Math.PI*2); ctx.stroke(); for(let i=0;i<4;i++){ ctx.beginPath(); for(let x=0;x<220;x+=10){ const yy=sy+sh*.6+i*16+Math.sin(x/18)*5; x?ctx.lineTo(sx-120+x,yy):ctx.moveTo(sx-120+x,yy);} ctx.stroke(); } ctx.font=PK.sans(15,800); ctx.fillStyle='rgba(23,60,71,.6)'; ctx.textAlign='center'; ctx.fillText(o.centerName.toUpperCase().slice(0,18),sx-10,sy+sh*.75+6); ctx.restore(); ctx.textAlign='left';
      // text block
      let y=o.format==='square'?py+ph+150:py+ph+170;
      const tx=P, tw=W-P*2;
      const hb=PK.block(ctx,o.headline,s=>PK.serif(s,700,true),(o.format==='story'?104:o.format==='square'?64:82)*k,tw,2,38); ctx.fillStyle=A; ctx.font=PK.serif(hb.size,700,true); hb.lines.forEach((l,i)=>ctx.fillText(l,tx,y+hb.size*(i+.8))); y+=hb.lines.length*hb.size*1.02+18*k;
      const rows=o.slots.slice(0,o.rowsMax), rh=58*k;
      rows.forEach((s,i)=>{ const ry=y+i*rh; ctx.fillStyle=ink; ctx.font=PK.sans(32*k,800); ctx.fillText(s.time.split('–')[0],tx,ry+40*k); const right=[o.showSpots?PK.free(s.free):'',o.showPrice&&s.price?PK.money(o,s.price):''].filter(Boolean).join(' · '); ctx.font=PK.sans(28*k,800); ctx.textAlign='right'; ctx.fillStyle=A; ctx.fillText(right,W-P,ry+40*k); const rw=ctx.measureText(right).width; ctx.textAlign='left'; ctx.font=PK.serif(30*k,400,true); ctx.fillStyle=ink; const t=PK.ellipsis(ctx,s.title,W-P*2-130-rw-40); ctx.fillText(t,tx+120,ry+40*k); const endT=tx+120+ctx.measureText(t).width+14; ctx.fillStyle='rgba(23,60,71,.35)'; for(let x=endT;x<W-P-rw-14;x+=12) ctx.fillRect(x,ry+38*k,4,4); });
      y+=rows.length*rh;
      const qrS=o.qr?130:0; if(o.qr) PK.qr(ctx,o.qr,W-P-qrS,H-P-qrS,qrS,ink,'#fffdf8',12,10);
      ctx.fillStyle=ink; PK.fit(ctx,o.cta,s=>PK.sans(s,800),36*k,W-P*2-qrS-40); ctx.fillText(o.cta,P,H-P-(o.qr?62:30)); ctx.font=PK.sans(24*k,600); ctx.fillStyle='rgba(23,60,71,.75)'; ctx.fillText(PK.ellipsis(ctx,[o.centerName,o.phone].filter(Boolean).join(' · '),W-P*2-qrS-40),P,H-P-(o.qr?22:-4));
      return y>H-P-(o.qr?qrS:90)-20;
    }},
    // 5 · Boarding pass
    embarque:{name:'Tarjeta de embarque',hint:'Divertida y original',accents:['#0b7a89','#1d4ed8','#e4572e','#111827'],draw(ctx,W,H,o,k){
      const A=o.accent, P=56, ink='#0f2733';
      const g=ctx.createLinearGradient(0,0,0,H); g.addColorStop(0,A); g.addColorStop(1,'#04222f'); ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
      ctx.save(); ctx.globalAlpha=.12; ctx.strokeStyle='#fff'; ctx.lineWidth=2; for(let i=0;i<9;i++){ ctx.beginPath(); for(let x=0;x<=W;x+=24){ const y=60+i*34+Math.sin(x/70+i)*10; x?ctx.lineTo(x,y):ctx.moveTo(x,y);} ctx.stroke(); } ctx.restore();
      // headline above the ticket
      let y=P+20; ctx.fillStyle='#fff'; const hb=PK.block(ctx,o.headline,s=>PK.disp(s),(o.format==='story'?110:o.format==='square'?66:84)*k,W-P*2,2,40); ctx.font=PK.disp(hb.size); hb.lines.forEach((l,i)=>ctx.fillText(l,P,y+hb.size*(i+.85))); y+=hb.lines.length*hb.size*1.0+24*k;
      if(o.message&&o.format!=='square'){ ctx.font=PK.sans(28*k,600); ctx.fillStyle='rgba(255,255,255,.85)'; ctx.fillText(PK.ellipsis(ctx,o.message,W-P*2),P,y+20*k); y+=50*k; }
      // ticket
      const tx=P, tw=W-P*2, ty=y+10, th=H-ty-P; const stub=o.format==='square'?0:Math.min(300,th*.3); const tear=ty+th-stub;
      ctx.save(); ctx.shadowColor='rgba(0,0,0,.35)'; ctx.shadowBlur=40; ctx.shadowOffsetY=16; ctx.fillStyle='#fff'; PK.rr(ctx,tx,ty,tw,th,36); ctx.fill(); ctx.restore();
      if(stub){ ctx.save(); ctx.globalCompositeOperation='destination-out'; ctx.beginPath(); ctx.arc(tx,tear,30,0,Math.PI*2); ctx.arc(tx+tw,tear,30,0,Math.PI*2); ctx.fill(); ctx.restore(); ctx.strokeStyle='#c9d4d8'; ctx.setLineDash([14,12]); ctx.lineWidth=3; ctx.beginPath(); ctx.moveTo(tx+44,tear); ctx.lineTo(tx+tw-44,tear); ctx.stroke(); ctx.setLineDash([]); }
      // photo strip
      const sh=o.format==='square'?0:(o.format==='story'?300:200);
      if(sh){ ctx.save(); PK.rr(ctx,tx,ty,tw,sh,36); ctx.clip(); if(o.photo) PK.cover(ctx,o.photo,tx,ty,tw,sh); else PK.noPhoto(ctx,W,ty+sh,'#0b5d73','#5cc3cf'); ctx.fillStyle='rgba(0,0,0,.25)'; ctx.fillRect(tx,ty,tw,sh); ctx.restore(); ctx.fillStyle='#fff'; ctx.font=PK.sans(22,800); PK.spaced(ctx,t('TARJETA DE EMBARQUE · DIVE PASS'),tx+36,ty+52,3); }
      let iy=ty+(sh||0)+40; const ix=tx+40, iw=tw-80;
      if(!sh){ ctx.fillStyle=A; ctx.font=PK.sans(22,800); PK.spaced(ctx,t('TARJETA DE EMBARQUE · DIVE PASS'),ix,iy+6,3); iy+=30; }
      // route
      const code=t=>wdFold(t||'').replace(/[^a-z]/g,'').slice(0,3).toUpperCase()||'SEA';
      const dest=(o.slots[0]?.sub||o.place||o.centerName).split(' · ').pop();
      ctx.fillStyle='#7b8f97'; ctx.font=PK.sans(20,600); ctx.fillText(t('ORIGEN'),ix,iy+20); ctx.textAlign='right'; ctx.fillText(t('DESTINO'),ix+iw,iy+20); ctx.textAlign='left';
      ctx.fillStyle=ink; ctx.font=PK.disp(96*k); ctx.fillText(t('TÚ'),ix,iy+112*k); ctx.textAlign='right'; ctx.fillText(code(dest),ix+iw,iy+112*k); ctx.textAlign='left';
      ctx.font=PK.sans(22,600); ctx.fillStyle='#7b8f97'; ctx.fillText(t('Tu sofá'),ix,iy+146*k); ctx.textAlign='right'; ctx.fillText(PK.ellipsis(ctx,dest,iw/2-40),ix+iw,iy+146*k); ctx.textAlign='left';
      ctx.strokeStyle=A; ctx.lineWidth=3; ctx.setLineDash([6,10]); ctx.beginPath(); ctx.moveTo(ix+170,iy+80*k); ctx.lineTo(ix+iw-230,iy+80*k); ctx.stroke(); ctx.setLineDash([]); ctx.fillStyle=A; ctx.font=PK.sans(44,800); ctx.textAlign='center'; ctx.fillText('➜',ix+iw/2-30,iy+96*k); ctx.textAlign='left';
      iy+=180*k;
      // fields
      const fields=[[t('FECHA'),o.dp?`${o.dp.wdShort} ${o.dp.day} ${o.dp.mon}`:o.dateText],[t('EMBARQUE'),o.slots[0]?.time.split('–')[0]||'—'],[t('PLAZAS'),o.showSpots?String(o.totalFree):'—'],[t('DESDE'),o.showPrice&&o.minPrice?PK.money(o,o.minPrice):'—']];
      const fw=iw/4; fields.forEach(([l,v],i)=>{ ctx.fillStyle='#7b8f97'; ctx.font=PK.sans(19,600); ctx.fillText(l,ix+i*fw,iy+10); ctx.fillStyle=i===2?A:ink; PK.fit(ctx,v,s=>PK.sans(s,800),40*k,fw-16); ctx.fillText(v,ix+i*fw,iy+56*k); });
      iy+=90*k;
      const limit=stub?tear-24:ty+th-(o.qr?170:40);
      const rows=o.slots.slice(o.slots.length>1?0:1,o.rowsMax);
      if(rows.length){ ctx.fillStyle='#eef3f4'; ctx.fillRect(ix,iy,iw,2); iy+=14; rows.forEach((s,i)=>{ const ry=iy+i*54*k; if(ry+40>limit) return; ctx.fillStyle=ink; ctx.font=PK.sans(28*k,800); ctx.fillText(s.time.split('–')[0],ix,ry+38*k); ctx.font=PK.sans(26*k,600); ctx.fillStyle='#38535e'; const right=o.showSpots?PK.free(s.free):''; ctx.textAlign='right'; ctx.fillStyle=A; ctx.fillText(right,ix+iw,ry+38*k); ctx.textAlign='left'; ctx.fillStyle='#38535e'; ctx.fillText(PK.ellipsis(ctx,s.title,iw-260),ix+110,ry+38*k); }); iy+=rows.length*54*k; }
      // stub
      const qrS=o.qr?(stub?Math.min(stub-80,190):130):0;
      if(stub){ if(o.qr) PK.qr(ctx,o.qr,tx+tw-40-qrS,tear+(stub-qrS)/2,qrS,ink,'#fff',0,0); ctx.fillStyle=ink; PK.fit(ctx,o.cta,s=>PK.sans(s,800),40*k,tw-80-qrS-40); ctx.fillText(o.cta,tx+40,tear+stub/2-6); ctx.font=PK.sans(24,600); ctx.fillStyle='#7b8f97'; ctx.fillText(PK.ellipsis(ctx,[o.centerName,o.phone].filter(Boolean).join(' · '),tw-80-qrS-40),tx+40,tear+stub/2+34); if(o.badge){ ctx.font=PK.sans(22,800); ctx.fillStyle=A; PK.spaced(ctx,o.badge.toUpperCase(),tx+40,tear+stub/2-64,3); } }
      else { if(o.qr) PK.qr(ctx,o.qr,tx+tw-40-qrS,ty+th-40-qrS,qrS,ink,'#fff',0,0); ctx.fillStyle=ink; PK.fit(ctx,o.cta,s=>PK.sans(s,800),34,tw-80-qrS-40); ctx.fillText(o.cta,tx+40,ty+th-70); ctx.font=PK.sans(22,600); ctx.fillStyle='#7b8f97'; ctx.fillText(PK.ellipsis(ctx,o.centerName,tw-80-qrS-40),tx+40,ty+th-36); }
      return iy>limit+4;
    }},
    // 6 · Clean Swiss layout
    minimal:{name:'Minimal',hint:'Limpio y profesional',accents:['#0b7a89','#e4572e','#111827','#1d4ed8'],draw(ctx,W,H,o,k){
      const A=o.accent, P=72, ink='#101820';
      ctx.fillStyle='#ffffff'; ctx.fillRect(0,0,W,H);
      // photo block
      const ph=o.format==='story'?H*.40:o.format==='square'?H*.42:H*.40; const pw=o.format==='square'?W*.46:W-P*2; const px=o.format==='square'?W-P-pw:P, py=P+110;
      ctx.save(); PK.rr(ctx,px,py,pw,ph,8); ctx.clip(); if(o.photo) PK.cover(ctx,o.photo,px,py,pw,ph); else { ctx.fillStyle='#e9f1f2'; ctx.fillRect(px,py,pw,ph); } ctx.restore();
      // header row
      PK.logo(ctx,o,P,P,64,'#f1f5f6',A,'#fff'); ctx.fillStyle=ink; ctx.font=PK.sans(28,800); ctx.fillText(PK.ellipsis(ctx,o.centerName,W-P*2-80-260),P+84,P+30); ctx.font=PK.sans(21,400); ctx.fillStyle='#6b7b83'; ctx.fillText(PK.ellipsis(ctx,o.place,W-P*2-84-260),P+84,P+58);
      if(o.badge){ ctx.font=PK.sans(20,800); const bw=ctx.measureText(o.badge.toUpperCase()).width+36; ctx.strokeStyle=A; ctx.lineWidth=2.5; PK.rr(ctx,W-P-bw,P+10,bw,44,22); ctx.stroke(); ctx.fillStyle=A; ctx.fillText(o.badge.toUpperCase(),W-P-bw+18,P+40); }
      // big date
      let y=o.format==='square'?py:py+ph+40; const dx=P;
      if(o.dp){ ctx.fillStyle=A; ctx.font=PK.disp(o.format==='square'?250:(o.format==='story'?300:230)*k); const dw=ctx.measureText(o.dp.day).width; const dh=(o.format==='square'?250:(o.format==='story'?300:230)*k)*.74; ctx.fillText(o.dp.day,dx-8,y+dh); ctx.fillStyle=ink; ctx.font=PK.sans(40*k,800); ctx.fillText(o.dp.month.toUpperCase(),dx+dw+16,y+dh*.48); ctx.font=PK.sans(30*k,400); ctx.fillStyle='#6b7b83'; ctx.fillText(wdCap(o.dp.wd),dx+dw+16,y+dh*.48+42*k); y+=dh+36*k; }
      else { ctx.fillStyle=A; ctx.font=PK.disp(64*k); ctx.fillText(o.dateText,dx,y+60*k); y+=90*k; }
      const colW=o.format==='square'?W-P*2-pw-30:W-P*2;
      const hb=PK.block(ctx,o.headline,s=>PK.sans(s,800),(o.format==='story'?74:o.format==='square'?46:58)*k,colW,2,30); ctx.fillStyle=ink; ctx.font=PK.sans(hb.size,800); hb.lines.forEach((l,i)=>ctx.fillText(l,dx,y+hb.size*(i+.85))); y+=hb.lines.length*hb.size*1.1+16*k;
      if(o.format==='square') y=Math.max(y,py+ph+30);
      const rows=o.slots.slice(0,o.rowsMax), rh=66*k, tw=W-P*2;
      ctx.fillStyle=ink; ctx.fillRect(P,y,tw,3);
      rows.forEach((s,i)=>{ const ry=y+i*rh; ctx.fillStyle='#e3e9eb'; if(i) ctx.fillRect(P,ry,tw,1.5); ctx.fillStyle=ink; ctx.font=PK.sans(32*k,800); ctx.fillText(s.time,P,ry+44*k); const right=[o.showPrice&&s.price?PK.money(o,s.price):'',o.showSpots?PK.free(s.free):''].filter(Boolean).join('   '); ctx.font=PK.sans(28*k,800); ctx.textAlign='right'; ctx.fillStyle=A; ctx.fillText(right,W-P,ry+44*k); const rw=ctx.measureText(right).width; ctx.textAlign='left'; ctx.fillStyle='#38474f'; ctx.font=PK.sans(28*k,400); ctx.fillText(PK.ellipsis(ctx,s.title+(s.sub?' · '+s.sub:''),tw-240-rw-30),P+240,ry+44*k); });
      y+=rows.length*rh; ctx.fillStyle=ink; ctx.fillRect(P,y,tw,3); y+=20;
      const qrS=o.qr?120:0; if(o.qr) PK.qr(ctx,o.qr,W-P-qrS,H-P-qrS,qrS,ink,'#fff',0,0);
      ctx.fillStyle=ink; PK.fit(ctx,o.cta+' →',s=>PK.sans(s,800),36*k,W-P*2-qrS-40); ctx.fillText(o.cta+' →',P,H-P-(o.qr?54:20)); ctx.font=PK.sans(22,400); ctx.fillStyle='#6b7b83'; if(o.phone) ctx.fillText(o.phone,P,H-P-(o.qr?16:-10));
      return y>H-P-Math.max(qrS,70)-10;
    }}
  };

  async function drawPoster(canvas,o){
    const F=POSTER_FORMATS[o.format]; const T=POSTER_TEMPLATES[o.template]||POSTER_TEMPLATES.ultima;
    canvas.width=F.w; canvas.height=F.h; const ctx=canvas.getContext('2d');
    const rowsMax=o.format==='square'?3:o.format==='story'?5:4;
    for(const k of [1,.92,.85,.78,.72,.66]){
      for(const rm of [rowsMax,Math.max(1,rowsMax-1),Math.max(1,rowsMax-2)]){
        ctx.save(); ctx.clearRect(0,0,F.w,F.h); ctx.textBaseline='alphabetic'; ctx.textAlign='left'; ctx.shadowBlur=0; ctx.setLineDash([]); ctx.globalAlpha=1; ctx.globalCompositeOperation='source-over';
        let over=false; try{ over=T.draw(ctx,F.w,F.h,{...o,rowsMax:rm},k); }catch(err){ console.error('cartel',err); over=false; }
        ctx.restore();
        if(!over) return;
        if(rm===1) break;
      }
    }
  }

  async function openPosterStudio({center,slots}){
    if(!slots?.length){ toast('No hay salidas con plazas libres para anunciar.'); return; }
    const esc=escapeHtml; center=center||{};
    const day=slots[0].slot_date; const sameDay=slots.every(s=>s.slot_date===day);
    const dLong=x=>wdCap(wdParseDate(x).toLocaleDateString(wdLocale(),{weekday:'long',day:'numeric',month:'long'}));
    const totalFree=slots.reduce((n,s)=>n+plFree(s),0);
    const rel=(()=>{ const t=new Date(); t.setHours(0,0,0,0); const diff=Math.round((wdParseDate(day)-t)/864e5); return diff===0?'hoy':diff===1?'mañana':diff<7?'este '+wdParseDate(day).toLocaleDateString(wdLocale(),{weekday:'long'}):''; })();
    const firstPts=(slots[0].points||[]).map(p=>p.name).slice(0,2).join(' y ');
    const es=currentLanguage()==='es';
    const defaults={headline:sameDay?(totalFree<=3?(es?`¡Últimas plazas${rel?' '+rel:''}!`:t('¡Últimas plazas!')):(es?`¿Te vienes a bucear${rel?' '+rel:''}?`:t('¿Te vienes a bucear?'))):t('Próximas salidas con plazas libres'),
      message:slots.length===1?`${slots[0].service_title}${firstPts?(es?' en ':' · ')+firstPts:''}. ${t('¡Reserva la tuya!')}`:t('Elige tu hora y ven a bucear con nosotros.'),
      badge:t(totalFree<=3?'Últimas plazas':'Plazas libres'), cta:t('Reserva ya en WORLDIVES')};
    const cover=center.cover_url||'', siteHero=media('hero:centros')||'';
    const photoChoices=[cover&&['cover','Portada del centro',cover],siteHero&&['site','Foto de la web',siteHero],['none','Sin foto',''],['upload','Subir una foto…','']].filter(Boolean);
    const o={format:'post',template:'ultima',accent:POSTER_TEMPLATES.ultima.accents[0],photoKey:photoChoices[0][0],showPrice:true,showSpots:true,showQr:true,...defaults};
    const body=`<div class="ps-wrap">
      <div class="ps-stage"><canvas id="ps-canvas" aria-label="Vista previa del cartel"></canvas></div>
      <form class="ps-side" id="ps-form" data-nosubmit>
        <div class="ps-group"><span class="ps-label">Plantilla</span><div class="ps-templates" id="ps-templates">${Object.entries(POSTER_TEMPLATES).map(([k2,t])=>`<button type="button" class="ps-tpl" data-template="${k2}" aria-pressed="${k2===o.template}"><canvas width="216" height="270" aria-hidden="true"></canvas><strong>${esc(t.name)}</strong><small>${esc(t.hint)}</small></button>`).join('')}</div></div>
        <div class="ps-group"><span class="ps-label">Color</span><div class="ps-accents" id="ps-accents"></div></div>
        <div class="ps-group"><span class="ps-label">Formato</span><div class="ps-seg">${Object.entries(POSTER_FORMATS).map(([k2,f])=>`<button type="button" data-format="${k2}" aria-pressed="${k2===o.format}"><strong>${f.label}</strong><small>${f.hint}</small></button>`).join('')}</div></div>
        <label class="ps-group"><span class="ps-label">Foto de fondo</span><select id="ps-photo">${photoChoices.map(([k2,l])=>`<option value="${k2}">${esc(l)}</option>`).join('')}</select><input type="file" id="ps-file" accept="image/jpeg,image/png,image/webp" hidden></label>
        <label class="ps-group"><span class="ps-label">Titular</span><input id="ps-headline" maxlength="60" value="${esc(o.headline)}"></label>
        <label class="ps-group"><span class="ps-label">Texto</span><textarea id="ps-message" rows="2" maxlength="120">${esc(o.message)}</textarea></label>
        <div class="ps-row"><label class="ps-group"><span class="ps-label">Etiqueta</span><input id="ps-badge" maxlength="22" value="${esc(o.badge)}"></label><label class="ps-group"><span class="ps-label">Llamada a la acción</span><input id="ps-cta" maxlength="34" value="${esc(o.cta)}"></label></div>
        <div class="ps-checks"><label><input type="checkbox" id="ps-price" checked> Precio</label><label><input type="checkbox" id="ps-spots" checked> Plazas libres</label><label><input type="checkbox" id="ps-qr" checked> Código QR para reservar</label></div>
        <label class="ps-group"><span class="ps-label">Texto para la publicación <button type="button" class="svc-link" id="ps-copy">Copiar</button></span><textarea id="ps-caption" rows="4"></textarea></label>
      </form></div>`;
    const {el}=wdOpenModal({id:'poster-studio',size:'xl',title:'Crear cartel para redes',subtitle:`${esc(sameDay?dLong(day):'Varias fechas')} · ${slots.length} ${slots.length===1?'salida':'salidas'} con ${totalFree} ${totalFree===1?'plaza libre':'plazas libres'}`,
      body,footer:`<button type="button" class="btn" data-modal-close>Cerrar</button><button type="button" class="btn" id="ps-share" hidden>Compartir</button><button type="button" class="btn btn-primary" id="ps-download">${wdIcon('download',16)} Descargar imagen</button>`});
    const canvas=el.querySelector('#ps-canvas');
    const [logo,qrData]=await Promise.all([posterLoadImg(centerLogo(center)),api(`/api/center/poster-qr?service=${slots.length===1?slots[0].service_id:''}&slot=${slots.length===1?slots[0].id:''}`).catch(()=>null),loadPosterFonts()]);
    const photos={};
    const loadPhoto=async k2=>{ if(k2 in photos) return photos[k2]; const src=(photoChoices.find(x=>x[0]===k2)||[])[2]; photos[k2]=await posterLoadImg(src); return photos[k2]; };
    const place=[center.city,center.country?t(center.country):''].filter(Boolean).join(', ');
    const slotRows=()=>slots.map(s=>{ const end=plEndTime(s.slot_time,s.duration_minutes); return {time:s.slot_time+(end?'–'+end:''),title:s.service_title,sub:[sameDay?'':wdDay(s.slot_date),(s.points||[]).map(p=>p.name).slice(0,2).join(' · ')].filter(Boolean).join(' · '),free:plFree(s),price:s.service_price,currency:s.currency,color:s.service_color}; });
    const dt=wdParseDate(day);
    const dp=sameDay?{wd:dt.toLocaleDateString(wdLocale(),{weekday:'long'}),wdShort:dt.toLocaleDateString(wdLocale(),{weekday:'short'}).replace('.','').toUpperCase(),day:String(dt.getDate()),month:dt.toLocaleDateString(wdLocale(),{month:'long'}),mon:dt.toLocaleDateString(wdLocale(),{month:'short'}).replace('.','').toUpperCase(),year:String(dt.getFullYear())}:null;
    const dateText=sameDay?dLong(day):`Del ${wdDay(slots[0].slot_date)} al ${wdDay(slots[slots.length-1].slot_date)}`;
    const prices=slots.map(s=>Number(s.service_price||0)).filter(Boolean); const minPrice=prices.length?Math.min(...prices):0;
    const caption=()=>{ const lines=[`${o.headline} 🤿`,'',`📅 ${dateText}`,...slotRows().map(s=>`⏰ ${s.time} · ${s.title}${o.showSpots?` — ${t(`${s.free} ${s.free===1?'plaza':'plazas'}`)}`:''}${o.showPrice&&s.price?` · ${wdMoney(s.price,s.currency)}`:''}`),'',o.message,'',`${t('Reserva')}: ${qrData?.url||location.origin}`,center.phone?`📞 ${center.phone}`:'','',`${es?'#buceo ':''}#scubadiving #${String(center.city||'diving').toLowerCase().normalize('NFD').replace(/[^a-z0-9]/g,'')} #worldives`]; return lines.filter((l,i,a)=>!(l===''&&a[i-1]==='')).join('\n').trim(); };
    const data=photo=>({...o,photo,logo,qr:o.showQr?qrData?.matrix:null,centerName:center.name||state.me?.user?.fullname||'',place,phone:center.phone||'',dateText,dp,slots:slotRows(),totalFree,minPrice,currency:slots[0].currency||'EUR'});
    const drawAccents=()=>{ const t=POSTER_TEMPLATES[o.template]; el.querySelector('#ps-accents').innerHTML=t.accents.map(c=>`<button type="button" class="ps-acc" data-accent="${c}" aria-pressed="${c===o.accent}" aria-label="Color ${c}" style="--a:${c}"></button>`).join(''); };
    // Thumbnails of every template, drawn with the real data
    const thumbs=async()=>{ const photo=o.photoKey==='none'?null:await loadPhoto(o.photoKey); const off=document.createElement('canvas');
      for(const b of $$('.ps-tpl',el)){ const key=b.dataset.template; await drawPoster(off,{...data(photo),template:key,format:'post',accent:key===o.template?o.accent:POSTER_TEMPLATES[key].accents[0]}); const c=b.querySelector('canvas'); const cx=c.getContext('2d'); cx.clearRect(0,0,c.width,c.height); cx.drawImage(off,0,0,c.width,c.height); } };
    let seq=0;
    const redraw=async()=>{ const my=++seq; const photo=o.photoKey==='none'?null:await loadPhoto(o.photoKey); if(my!==seq) return;
      await drawPoster(canvas,data(photo));
      const cap=el.querySelector('#ps-caption'); if(!cap.dataset.edited) cap.value=caption(); };
    el.querySelector('#ps-templates').onclick=e=>{ const b=e.target.closest('.ps-tpl'); if(!b) return; o.template=b.dataset.template; o.accent=POSTER_TEMPLATES[o.template].accents[0]; $$('.ps-tpl',el).forEach(x=>x.setAttribute('aria-pressed',String(x===b))); drawAccents(); redraw(); };
    el.querySelector('#ps-accents').onclick=e=>{ const b=e.target.closest('.ps-acc'); if(!b) return; o.accent=b.dataset.accent; drawAccents(); redraw(); };
    $$('[data-format]',el).forEach(b=>b.onclick=()=>{ o.format=b.dataset.format; $$('[data-format]',el).forEach(x=>x.setAttribute('aria-pressed',String(x===b))); redraw(); });
    el.querySelector('#ps-photo').onchange=e=>{ if(e.target.value==='upload'){ el.querySelector('#ps-file').click(); e.target.value=o.photoKey; return; } o.photoKey=e.target.value; redraw(); thumbs(); };
    el.querySelector('#ps-file').onchange=e=>{ const f=e.target.files[0]; if(!f) return; if(f.size>15*1024*1024){toast('La foto pesa demasiado.');return;} const url=URL.createObjectURL(f); posterLoadImg(url).then(im=>{ if(!im){toast('No se ha podido leer esa foto.');return;} photos.mine=im; if(!photoChoices.some(x=>x[0]==='mine')){ photoChoices.splice(photoChoices.length-1,0,['mine','Mi foto','']); const opt=document.createElement('option'); opt.value='mine'; opt.textContent='Mi foto'; el.querySelector('#ps-photo option[value="upload"]').before(opt);} o.photoKey='mine'; el.querySelector('#ps-photo').value='mine'; redraw(); thumbs(); }); };
    let tt; [['#ps-headline','headline'],['#ps-message','message'],['#ps-badge','badge'],['#ps-cta','cta']].forEach(([s,k2])=>{ let t; el.querySelector(s).oninput=e=>{ o[k2]=e.target.value; clearTimeout(t); t=setTimeout(redraw,120); clearTimeout(tt); tt=setTimeout(thumbs,900); }; });
    [['#ps-price','showPrice'],['#ps-spots','showSpots'],['#ps-qr','showQr']].forEach(([s,k2])=>el.querySelector(s).onchange=e=>{ o[k2]=e.target.checked; redraw(); });
    if(!qrData?.matrix){ const q=el.querySelector('#ps-qr'); q.checked=false; q.disabled=true; o.showQr=false; }
    el.querySelector('#ps-caption').oninput=e=>{ e.target.dataset.edited='1'; };
    el.querySelector('#ps-copy').onclick=async()=>{ try{ await navigator.clipboard.writeText(el.querySelector('#ps-caption').value); toast('Texto copiado.'); }catch{ el.querySelector('#ps-caption').select(); toast('Selecciona y copia el texto.'); } };
    const fileName=()=>`cartel-${(center.name||'worldives').toLowerCase().normalize('NFD').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')}-${day}-${o.template}-${o.format}.png`;
    const blob=()=>new Promise((res,rej)=>{ try{ canvas.toBlob(b=>b?res(b):rej(new Error('No se ha podido crear la imagen.')),'image/png'); }catch(err){ rej(new Error('La foto elegida no se puede usar en el cartel. Prueba con otra.')); } });
    el.querySelector('#ps-download').onclick=async()=>{ try{ const b=await blob(); const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download=fileName(); document.body.appendChild(a); a.click(); setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},2000); toast('Cartel descargado. Súbelo a Instagram desde tu móvil o el ordenador.'); }catch(err){ toast(err.message); } };
    const share=el.querySelector('#ps-share');
    if(navigator.canShare&&navigator.share){ try{ if(navigator.canShare({files:[new File([new Blob(['x'])],'x.png',{type:'image/png'})]})) share.hidden=false; }catch{} }
    share.onclick=async()=>{ try{ const b=await blob(); const file=new File([b],fileName(),{type:'image/png'}); await navigator.share({files:[file],text:el.querySelector('#ps-caption').value}); }catch(err){ if(err?.name!=='AbortError') toast(err.message||'No se ha podido compartir.'); } };
    drawAccents(); await redraw(); thumbs();
  }
  function centerTariffsView(tariffs,extras,equipment){
    return `<div class="cb-module"><div class="cb-module-head"><div><p class="eyebrow">PRECIOS MAESTROS</p><h2>Tarifas y extras</h2><p>Aquí se cambian los precios de forma centralizada. Al cambiar una tarifa de servicio, se aplica a las <strong>salidas futuras y nuevas reservas</strong>; las reservas ya realizadas conservan el precio que pagó el cliente.</p></div></div>
      <section class="cb-panel"><div class="cb-panel-head"><div><p class="eyebrow">SERVICIOS</p><h3>Tarifas de servicios y salidas</h3><p>Una tarifa maestra por servicio. Los cambios con fecha futura se programan sin alterar las reservas ya realizadas.</p></div></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Servicio</th><th>Tarifa vigente</th><th>Próxima tarifa</th><th>Color</th><th></th></tr></thead><tbody>${tariffs.map(t=>{const today=new Date().toISOString().slice(0,10);const current=(t.history||[]).filter(h=>String(h.effective_from)<=today)[0];const next=(t.history||[]).filter(h=>String(h.effective_from)>today).sort((a,b)=>String(a.effective_from).localeCompare(String(b.effective_from)))[0];return `<tr><td><strong>${escapeHtml(t.service.title)}</strong><br><small>${escapeHtml(t.service.service_type||'')}</small></td><td><strong>${Number((current?.price ?? t.service.price)||0).toFixed(2)} €</strong><br><small>${current?`Desde ${escapeHtml(current.effective_from)}`:'Precio actual'}</small></td><td>${next?`<strong>${Number(next.price||0).toFixed(2)} €</strong><br><small>Desde ${escapeHtml(next.effective_from)}</small>`:'<span style="color:var(--muted)">Sin cambio programado</span>'}</td><td><span class="service-color-dot" style="display:inline-block;background:${escapeHtml(t.service.color||'#2563eb')}"></span></td><td><button type="button" class="btn tariff-edit" data-service="${t.service.id}">Cambiar precio</button></td></tr>`}).join('')||'<tr><td colspan="5">Todavía no has creado servicios.</td></tr>'}</tbody></table></div></section>
      <section class="cb-panel" style="margin-top:18px"><div class="cb-panel-head"><div><p class="eyebrow">EXTRAS</p><h3>Complementos</h3><p>Instructor extra, reportaje fotográfico, nitrox, traslado, etc.</p></div><button class="btn btn-primary" id="new-center-extra">+ Nuevo extra</button></div><div class="cb-extra-grid">${extras.map(x=>`<article class="cb-panel cb-extra-card"><div><span class="status ${x.active?'good':'warn'}">${x.active?'Activo':'Pausado'}</span><h3>${escapeHtml(x.name)}</h3><p>${escapeHtml(x.description||'')}</p></div><strong>${Number(x.price||0).toFixed(2)} €</strong><div><button class="btn edit-extra" data-id="${x.id}">Editar</button><button class="btn delete-extra" data-id="${x.id}">Eliminar</button></div></article>`).join('')||'<div class="empty">Todavía no hay extras.</div>'}</div></section>
      <section class="cb-panel" style="margin-top:18px"><div class="cb-panel-head"><div><p class="eyebrow">ALQUILER</p><h3>Equipo de alquiler</h3><p>Precio individual de cada artículo disponible.</p></div></div><div id="cb-equipment"></div></section></div>`;
  }
  async function loadCenterTariffs(d){const [t,e,eq]=await Promise.all([api('/api/center/tariffs'),api('/api/center/extras'),api('/api/center-equipment?center_id='+d.user.center_id)]);window.__centerTariffs=t.items;window.__centerExtras=e.items;$('#cb-content').innerHTML=centerTariffsView(t.items,e.items,eq.items);$('#cb-equipment').innerHTML=eq.items.map(x=>`<div class="equipment-admin-row"><div><strong>${escapeHtml(x.label)}</strong></div><input class="center-equipment-price" data-code="${escapeHtml(x.code)}" type="number" min="0" step="0.01" value="${x.price==null?'':x.price}" placeholder="Precio"><span>€</span><button class="btn save-equipment-price" data-code="${escapeHtml(x.code)}">Guardar</button></div>`).join('');
    $$('.save-equipment-price').forEach(btn=>btn.onclick=async()=>{const input=document.querySelector('.center-equipment-price[data-code="'+btn.dataset.code+'"]');await postJSON('/api/center-equipment',{code:btn.dataset.code,price:input.value});toast('Precio de equipo actualizado.');});
    $$('.tariff-edit').forEach(btn=>btn.onclick=()=>centerTariffForm(t.items.find(x=>Number(x.service.id)===Number(btn.dataset.service)),d));
    $('#new-center-extra').onclick=()=>centerExtraForm();$$('.edit-extra').forEach(b=>b.onclick=()=>centerExtraForm(Number(b.dataset.id)));$$('.delete-extra').forEach(b=>b.onclick=async()=>{if(!confirm('¿Eliminar este extra?'))return;await postJSON('/api/center/extras/delete',{id:+b.dataset.id});loadCenterTariffs(d);});
  }
  function centerTariffForm(serviceEntry,d){const svc=serviceEntry.service;const html=`<div class="modal-backdrop" id="tariff-modal"><div class="modal-card"><button class="modal-close" id="tariff-close">×</button><p class="eyebrow">TARIFA MAESTRA</p><h2>${escapeHtml(svc.title)}</h2><p>El cambio afectará automáticamente a las salidas futuras y nuevas reservas desde la fecha indicada.</p><form id="tariff-form" class="form-grid"><div class="field"><label>Nuevo precio (€)</label><input id="tariff-price" type="number" min="0" step="0.01" required value="${Number(svc.price||0)}"></div><div class="field"><label>Aplicar desde</label><input id="tariff-date" type="date" required value="${new Date().toISOString().slice(0,10)}"></div><div class="full form-actions"><button class="btn btn-primary">Actualizar tarifa</button></div></form></div></div>`;document.body.insertAdjacentHTML('beforeend',html);$('#tariff-close').onclick=()=>$('#tariff-modal').remove();$('#tariff-form').onsubmit=async e=>{e.preventDefault();try{await postJSON('/api/center/tariffs/save',{service_id:svc.id,price:+$('#tariff-price').value,effective_from:$('#tariff-date').value});$('#tariff-modal').remove();toast('Tarifa actualizada para futuras operaciones.');loadCenterTariffs(d);}catch(e){toast(e.message)}};}
  function centerExtraForm(id){const existing=window.__centerExtras?.find(x=>x.id===id);const html=`<div class="modal-backdrop" id="extra-modal"><div class="modal-card"><button class="modal-close" id="extra-close">×</button><p class="eyebrow">EXTRA</p><h2>${id?'Editar':'Nuevo'} extra</h2><form id="extra-form" class="form-grid"><div class="field full"><label>Nombre</label><input id="extra-name" required value="${escapeHtml(existing?.name||'')}" placeholder="Instructor extra"></div><div class="field"><label>Precio (€)</label><input id="extra-price" type="number" min="0" step="0.01" required value="${existing?.price??''}"></div><div class="field full"><label>Descripción</label><textarea id="extra-desc">${escapeHtml(existing?.description||'')}</textarea></div><div class="full form-actions"><button class="btn btn-primary">Guardar extra</button></div></form></div></div>`;document.body.insertAdjacentHTML('beforeend',html);$('#extra-close').onclick=()=>$('#extra-modal').remove();$('#extra-form').onsubmit=async e=>{e.preventDefault();await postJSON('/api/center/extras/save',{id:id||0,name:$('#extra-name').value,description:$('#extra-desc').value,price:+$('#extra-price').value,active:1});$('#extra-modal').remove();toast('Extra guardado.');const d=await api('/api/me');loadCenterTariffs(d);};}
  function centerQRManager(center,bookings,services){const slots=[];(services||[]).forEach(s=>(s.slots||[]).forEach(x=>slots.push({...x,service_title:s.title})));return `<div class="cb-module"><div class="cb-module-head"><div><p class="eyebrow">IDENTIFICACIÓN DIGITAL</p><h2>Check-in / QR</h2><p>El centro ya está seleccionado automáticamente: <strong>${escapeHtml(center.name)}</strong>. No puedes crear QR para otro centro.</p></div></div><div class="cb-qr-purpose-grid"><button class="cb-qr-purpose active" data-purpose="center"><strong>🏪 Centro</strong><span>Identificar el centro y hacer check-in</span></button><button class="cb-qr-purpose" data-purpose="diver"><strong>🤿 Buceador</strong><span>Identificar al cliente al llegar</span></button><button class="cb-qr-purpose" data-purpose="dive"><strong>🌊 Inmersión</strong><span>Compartir los datos de una salida con el Log Book</span></button><button class="cb-qr-purpose" data-purpose="booking"><strong>🎫 Reserva</strong><span>Identificar una reserva concreta</span></button></div><form id="center-qr-form" class="cb-panel form-grid" style="margin-top:18px"><input type="hidden" id="center-qr-purpose" value="center"><div class="field full"><label>Nombre del QR</label><input id="center-qr-label" value="Identificación del centro" required></div><div class="field full" id="center-qr-target-wrap" style="display:none"><label id="center-qr-target-label">Elemento</label><select id="center-qr-target"></select></div><div class="full form-actions"><button class="btn btn-primary">Generar QR</button></div></form><div id="center-qr-output" style="margin-top:18px"></div></div>`;}
  function bindCenterQR(center,bookings,services){const slots=[];(services||[]).forEach(s=>(s.slots||[]).forEach(x=>slots.push({...x,service_title:s.title})));const purposeNames={center:'Identificación del centro',diver:'Check-in del buceador',dive:'Inmersión',booking:'Reserva'}; $$('.cb-qr-purpose').forEach(b=>b.onclick=()=>{ $$('.cb-qr-purpose').forEach(x=>x.classList.remove('active'));b.classList.add('active');const p=b.dataset.purpose;$('#center-qr-purpose').value=p;$('#center-qr-label').value=purposeNames[p];const wrap=$('#center-qr-target-wrap'); if(p==='dive'||p==='booking'){wrap.style.display='block';$('#center-qr-target-label').textContent=p==='dive'?'Salida / inmersión':'Reserva';$('#center-qr-target').innerHTML=(p==='dive'?slots.map(x=>`<option value="${x.id}">${escapeHtml(x.slot_date)} · ${escapeHtml(x.slot_time)} · ${escapeHtml(x.service_title)}</option>`):bookings.map(x=>`<option value="${x.id}">#${x.id} · ${escapeHtml(x.booking_date)} · ${escapeHtml(x.service_title||'Reserva')}</option>`)).join('');}else wrap.style.display='none';}); $('#center-qr-form').onsubmit=async e=>{e.preventDefault();const p=$('#center-qr-purpose').value;const r=await postJSON('/api/qr/create',{center_id:center.id,purpose:p,reference_id:(p==='dive'||p==='booking')?Number($('#center-qr-target').value):null,label:$('#center-qr-label').value});const base=location.origin;$('#center-qr-output').innerHTML=`<div class="qr-box"><p><strong>${escapeHtml($('#center-qr-label').value)}</strong></p><img src="/api/qr/${r.code}" alt="Código QR"><p>${escapeHtml(center.name)} · ${escapeHtml(purposeNames[p])}</p><code>${base}/#/checkin/${r.code}</code><br><button class="btn" type="button" id="center-qr-copy">Copiar enlace</button></div>`;$('#center-qr-copy').onclick=()=>navigator.clipboard?.writeText(`${base}/#/checkin/${r.code}`);toast('QR generado.');};}
  async function renderCenterWorkspace(d){
    const [centerRes,bookingsRes,servicesRes,clientsRes,analyticsRes,expRes]=await Promise.all([api('/api/centers/'+d.user.center_id),api('/api/bookings'),api('/api/provider-services?provider_id='+d.user.id),api('/api/center/clients'),api('/api/center/analytics'),api('/api/provider/experiences').catch(()=>({requests:[]}))]);
    const center=centerRes.item; let bookings=bookingsRes.items; let services=servicesRes.items; let clients=clientsRes.items; let analytics=analyticsRes; analytics.client_count=clients.length; let currentTab='dashboard';
    analytics.metrics=Object.assign({},analytics.metrics,{experience_requests:(expRes.requests||[]).filter(r=>r.status==='requested').length});
    setApp(centerWorkspaceShell(center,analytics.metrics)); proTermsBanner(d.user); const content=$('#cb-content'); const nav=$$('.cb-nav');
    const go=tab=>{nav.forEach(n=>n.classList.toggle('active',n.dataset.cbtab===tab)); location.hash='#/admin?tab='+tab;};
    // Bookings and analytics are reloaded after any change made from the panel, so every tab shows fresh data.
    const reloadData=async()=>{try{const [b,an]=await Promise.all([api('/api/bookings'),api('/api/center/analytics')]); bookings=b.items; analytics=an; analytics.client_count=clients.length; const badge=document.querySelector('.cb-nav[data-cbtab="bookings"] b'); if(badge)badge.textContent=analytics.metrics?.pending||0;}catch(e){}};
    const loadTab=async (tab,opts={})=>{ nav.forEach(n=>n.classList.toggle('active',n.dataset.cbtab===tab)); currentTab=tab;
      if(opts.view) bkUi.view=opts.view;
      if(tab==='dashboard') await reloadData();
      if(['dashboard','qr'].includes(tab)){try{services=(await api('/api/provider-services?provider_id='+d.user.id)).items;}catch(e){}}
      if(tab==='dashboard'){content.innerHTML=centerDashboardPro(center,analytics,bookings,services);}
      else if(tab==='planning'){content.innerHTML='<div id="cb-planning"></div>'; await renderCenterPlanning('cb-planning',{center,onManage:()=>loadTab('services')});}
      else if(tab==='services'){content.innerHTML='<div id="center-services-manager"></div>'; await renderProviderServicesManager(d.user.id,'center','center-services-manager');}
      else if(tab==='bookings'){content.innerHTML='<div id="cb-bookings"></div>'; await renderCenterBookings('cb-bookings',{onChange:reloadData});}
      else if(tab==='clients'){try{clients=(await api('/api/center/clients')).items;}catch(e){} content.innerHTML=centerClientsView(clients); const q=$('#cl-q'); if(q)q.oninput=()=>{const v=q.value.trim().toLowerCase(); $$('.cl-row[data-search]').forEach(r=>{r.hidden=!!v&&!r.dataset.search.includes(v);});};}
      else if(tab==='experiences'){content.innerHTML='<div id="cb-experiences"></div>'; await renderProviderExperiences('cb-experiences','center',{goServices:()=>loadTab('services')});}
      else if(tab==='payments'){content.innerHTML='<div id="cb-payments"></div>'; await renderCenterPayments(d.user.center_id,'cb-payments');}
      else if(tab==='analytics'){content.innerHTML=await centerAnalyticsView(); $('#cb-export-report').onclick=()=>{const rows=[['Fecha','Participantes'],...(analytics.by_day||[]).map(x=>[x.date,x.participants])]; const csv=rows.map(r=>r.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\\n'); const a=document.createElement('a');a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);a.download='worldives-informe-centro.csv';a.click();};}
      else if(tab==='integration'){content.innerHTML=await centerIntegrationView(); $('#cb-new-api-key').onclick=async()=>{try{const r=await postJSON('/api/center/integration/regenerate',{});$('#cb-api-result').innerHTML='<div class="notice warning" style="margin-top:14px"><strong>Guarda esta clave ahora.</strong><br><code>'+escapeHtml(r.api_key)+'</code><br><small>Por seguridad WORLDIVES no vuelve a mostrarla completa.</small></div>';}catch(e){toast(e.message)}};}
      else if(tab==='points'){content.innerHTML='<div id="cb-points"></div>'; renderCenterPointManager(d.user.center_id,'cb-points');}
      else if(tab==='qr'){content.innerHTML=`<div class="pr-tabs" role="tablist"><button type="button" class="pr-tab is-on" data-pt="promos">${wdIcon('gift',16)} Promociones</button><button type="button" class="pr-tab" data-pt="check">${wdIcon('qr',16)} Validar un código</button><button type="button" class="pr-tab" data-pt="checkin">${wdIcon('pin',16)} QR de check-in</button></div><div id="pr-pane"></div>`;
        const pane=$('#pr-pane'); const showPt=pt=>{ $$('.pr-tab').forEach(b=>b.classList.toggle('is-on',b.dataset.pt===pt)); if(pt==='promos') renderCenterPromos('pr-pane',center); else if(pt==='check') renderPromoChecker('pr-pane'); else { pane.innerHTML=centerQRManager(center,bookings,services); bindCenterQR(center,bookings,services); } };
        $$('.pr-tab').forEach(b=>b.onclick=()=>showPt(b.dataset.pt)); showPt(new URLSearchParams(location.hash.split('?')[1]||'').get('pt')||'promos');}
      else if(tab==='center'){content.innerHTML='<div id="cb-showcase"></div>'; await renderCenterShowcaseEditor('cb-showcase',d.user.center_id);}
      else if(tab==='rewards'){content.innerHTML='<div id="cb-rewards"></div>'; await renderRewardsManager('cb-rewards',{centerId:d.user.center_id});}
      else if(tab==='requests'){content.innerHTML='<div id="cb-requests"></div>'; await renderInfoRequests('cb-requests');}
      else if(tab==='stats'){content.innerHTML='<div id="cb-stats"></div>'; await renderProviderStats('cb-stats');}
      else if(tab==='tools'){content.innerHTML='<div id="cb-tools"></div>'; await renderProviderTools('cb-tools',true);}
      else if(tab==='team'){content.innerHTML='<div id="cb-team"></div>'; await renderTeam('cb-team');}
      else if(tab==='activity'){content.innerHTML='<div id="cb-activity"></div>'; await renderActivity('cb-activity');}
      else if(tab==='fiscal'){content.innerHTML='<div id="cb-fiscal"></div>'; await renderFiscalCard('cb-fiscal');}
      else if(tab==='plan'){content.innerHTML='<div id="cb-plan"></div>'; await renderMyPlan('cb-plan');}
    };
    if((state.me?.member_role||'owner')!=='owner') $$('.cb-nav[data-owner]').forEach(n=>n.remove());
    if(state.me?.member_role==='instructor') $$('.cb-nav[data-cbtab="payments"],.cb-nav[data-cbtab="integration"],.cb-nav[data-cbtab="center"]').forEach(n=>n.remove());
    { const pl=state.me?.plan; if(pl&&pl.status!=='active'){ const host=$('#cb-content'); host?.insertAdjacentHTML('beforebegin',`<div class="pl-bar ${pl.status==='expired'||pl.code==='free'?'is-free':''}">${wdIcon('info',16)} ${pl.status==='trial'?`Prueba gratuita del plan ${escapeHtml(pl.name)} hasta el ${escapeHtml(wdLegalDate(pl.expires_at))}.`:pl.status==='expired'?'Tu plan ha terminado: tu ficha sigue como ficha gratuita y no recibe reservas online nuevas.':'Ficha gratuita: recibes solicitudes de información.'} <a href="#/admin?tab=plan">Mi plan</a></div>`); } }
    nav.forEach(n=>n.onclick=()=>loadTab(n.dataset.cbtab));
    content.addEventListener('click',async e=>{const g=e.target.closest('.cb-go'); if(g){e.preventDefault();loadTab(g.dataset.tab,{view:g.dataset.view});return;} if(e.target.closest('.db-new-booking')){openManualBooking({onSaved:async()=>{await reloadData(); if(currentTab==='dashboard')loadTab('dashboard');}});return;} const b=e.target.closest('.cb-booking-open'); if(b){location.hash='#/reserva?id='+b.dataset.id;}});
    $('#cb-refresh').onclick=()=>loadTab(currentTab);
    const requested=new URLSearchParams(location.hash.split('?')[1]||'').get('tab'); loadTab(requested && nav.some(n=>n.dataset.cbtab===requested)?requested:'dashboard');
  }

  async function renderAdmin(){
    if(!state.me){goLogin();return;}
    const d=await api('/api/me');
    if(d.user.role==='center') return renderCenterWorkspace(d);
    if(!['admin','freelance'].includes(d.user.role)){setApp('<section class="page"><div class="empty">Tu cuenta no tiene acceso a gestión.</div></section>');return;}
    if(d.user.role==='freelance') return renderFreelancePanel(d);
    const isAdmin=d.user.role==='admin';
    if(isAdmin&&d.security?.totp_setup_required){ setApp(`<section class="page"><div class="empty"><h2>Activa la verificación en dos pasos</h2><p>Para usar la administración necesitas un código de tu aplicación de verificación además de tu contraseña.</p><a class="btn btn-primary" href="#/cuenta?seguridad=1">Activarla ahora</a></div></section>`); return; }
    let points=(await api('/api/dive-points')).items;
    if(!isAdmin) points=(await api('/api/center-points?center_id='+d.user.center_id)).items;
    const centers=(await api('/api/centers')).items; state.centers=centers;
    const bookings=(await api('/api/bookings')).items;
    const suggestions=isAdmin?(await api('/api/admin/suggestions')).items:(await api('/api/my/position-suggestions')).items;
    const claims=isAdmin?(await api('/api/admin/center-claims')).items:[];
    const clients=!isAdmin?(await api('/api/center/clients')).items:[];
    const users=isAdmin?(await api('/api/admin/users')).items:[];
    const travelExperiences=isAdmin?(await api('/api/admin/travel-experiences')).items:[];
    const virtuals=isAdmin?(await api('/api/admin/virtual-experiences')).items:[];
    const audit=isAdmin?(await api('/api/admin/audit')).items:[];
    const rewardOffers=(await api('/api/provider/reward-offers')).items;
    const meta=await loadMeta();
    const myCenter=!isAdmin?centers.find(c=>String(c.id)===String(d.user.center_id)):null;
    const centerPaid=bookings.filter(b=>b.payment_status==='paid');
    const centerPending=bookings.filter(b=>(b.status==='requested'||b.status==='pending'));
    const centerConfirmed=bookings.filter(b=>b.status==='confirmed');
    setApp(`<section class="page provider-page"><div class="provider-topbar"><div><p class="eyebrow">${isAdmin?'CUENTA ADMINISTRADOR':'PANEL PROFESIONAL · CENTRO DE BUCEO'}</p><h1>${isAdmin?'Centro de control de WORLDIVES':escapeHtml(myCenter?.name||'Panel del centro')}</h1><p class="lead">${isAdmin?'Control administrativo de WORLDIVES DISCOVERY.':'Tu centro de operaciones: reservas, salidas, clientes, pagos y catálogo.'}</p></div>${!isAdmin&&myCenter?`<div class="provider-status"><span class="status good">● Centro activo</span><a href="#/admin?tab=center">Gestionar ficha</a></div>`:''}</div>
      ${isAdmin?'<div class="notice" style="margin-top:18px"><strong>Control total activado</strong><p style="margin:6px 0 0">Las acciones importantes quedan registradas en el historial de actividad.</p></div>':''}
      ${!isAdmin?`<div class="provider-mini-summary"><span><strong>${points.length}</strong> puntos activos</span><span><strong>${bookings.length}</strong> reservas</span><span><strong>${centerPending.length}</strong> por confirmar</span><span><strong>${centerConfirmed.length}</strong> confirmadas</span><span><strong>${centerPaid.length}</strong> pagadas</span></div>`:''}
      <div class="tabs provider-tabs">${isAdmin?'<button class="tab active" data-tab="overview">Inicio</button>':'<button class="tab active" data-tab="overview">Resumen</button><button class="tab" data-tab="bookings">Reservas</button><button class="tab" data-tab="services">Servicios y salidas</button><button class="tab" data-tab="clients">Clientes</button><button class="tab" data-tab="points">Puntos de buceo</button><button class="tab" data-tab="rewards">Recompensas</button><button class="tab" data-tab="suggestions">Correcciones</button><button class="tab" data-tab="qr">QR / Check-in</button><button class="tab" data-tab="center">Mi centro</button><button class="tab" data-tab="payments">Cobros y pagos</button>'}${isAdmin?'<button class="tab" data-tab="points">Puntos</button><button class="tab" data-tab="bookings">Reservas</button><button class="tab" data-tab="adminpay">Pagos</button><button class="tab" data-tab="emails">Correos</button><button class="tab" data-tab="legal">Legal</button><button class="tab" data-tab="pointtexts">Descripciones de puntos</button><button class="tab" data-tab="maps">Mapas</button><button class="tab" data-tab="plans">Planes</button><button class="tab" data-tab="features">Funciones</button><button class="tab" data-tab="virtual">Recorridos virtuales</button><button class="tab" data-tab="experiences">Experiencias</button><button class="tab" data-tab="destinations">Destinos</button><button class="tab" data-tab="media">Imágenes de la web</button><button class="tab" data-tab="promos">Patrocinio</button><button class="tab" data-tab="users">Usuarios</button><button class="tab" data-tab="centers">Centros</button><button class="tab" data-tab="claims">Verificaciones</button><button class="tab" data-tab="suggestions">Correcciones</button><button class="tab" data-tab="qr">QR</button><button class="tab" data-tab="audit">Actividad</button><button class="tab" data-tab="rewards">Recompensas</button>':''}</div><div id="admin-content"></div></section>`);
    const tabs=$$('.tab');
    async function show(t){
      tabs.forEach(x=>x.classList.toggle('active',x.dataset.tab===t));
      const c=$('#admin-content');
      const visibleBookings=(statusFilter&&t==='bookings')?bookings.filter(b=>b.status===statusFilter):bookings;
      if(t==='overview') c.innerHTML=isAdmin?adminOverview(points,virtuals,travelExperiences,users,centers,bookings):centerDashboard(bookings,points,clients,rewardOffers);
      if(t==='center'&&!isAdmin&&myCenter){c.innerHTML=centerProfileEditor(myCenter); bindCenterProfile(myCenter);}
      if(t==='payments'&&!isAdmin&&myCenter){c.innerHTML='<div id="center-payments-manager"></div>';renderCenterPayments(myCenter.id,'center-payments-manager');}
      if(t==='services'&&!isAdmin){c.innerHTML='<div id="center-services-manager"></div>';renderProviderServicesManager(d.user.id,'center','center-services-manager');}
      if(t==='points') c.innerHTML=isAdmin?adminPoints(points,true):`<div id="center-points-tab"></div>`; if(t==='points'&&!isAdmin) renderCenterPointManager(d.user.center_id,'center-points-tab');
      if(t==='bookings') c.innerHTML=adminBookings(visibleBookings);
      if(t==='users') c.innerHTML=adminUsers(users);
      if(t==='experiences') c.innerHTML=adminTravelExperiences(travelExperiences);
      if(t==='destinations') c.innerHTML=adminDestinations(meta.travel);
      if(t==='media'&&isAdmin){ c.innerHTML='<div id="site-theme-manager"></div><div id="site-media-manager"></div><div id="image-origins"></div>'; renderThemeManager('site-theme-manager'); renderSiteMediaManager('site-media-manager'); renderImageOrigins('image-origins'); }
      if(t==='adminpay'&&isAdmin){ c.innerHTML='<div id="admin-payments"></div>'; renderAdminPayments('admin-payments'); }
      if(t==='emails'&&isAdmin){ c.innerHTML='<div id="admin-emails"></div>'; renderAdminEmails('admin-emails'); }
      if(t==='legal'&&isAdmin){ c.innerHTML='<div id="admin-legal"></div>'; renderAdminLegal('admin-legal'); }
      if(t==='plans'&&isAdmin){ c.innerHTML='<div id="admin-plans"></div>'; renderAdminPlans('admin-plans'); }
      if(t==='features'&&isAdmin){ c.innerHTML='<div id="admin-features"></div>'; renderAdminFeatures('admin-features'); }
      if(t==='maps'&&isAdmin){ c.innerHTML='<div id="admin-maps"></div>'; renderAdminMaps('admin-maps'); }
      if(t==='pointtexts'&&isAdmin){ c.innerHTML='<div id="admin-pointtexts"></div>'; renderAdminPointTexts('admin-pointtexts'); }
      if(t==='promos'&&isAdmin){ c.innerHTML='<div id="site-promos-manager"></div>'; renderPromosManager('site-promos-manager'); }
      if(t==='virtual') c.innerHTML=adminVirtuals(virtuals);
      if(t==='suggestions') c.innerHTML=isAdmin?adminSuggestions(suggestions):providerSuggestions(suggestions);
      if(t==='centers') c.innerHTML=adminCenters(centers);
      if(t==='claims') c.innerHTML=adminCenterClaims(claims);
      if(t==='qr') c.innerHTML=adminQR();
      if(t==='audit') c.innerHTML=adminAudit(audit);
      if(t==='clients') c.innerHTML=adminClients(clients);
      if(t==='rewards'){ c.innerHTML='<div id="admin-rewards"></div>'; renderRewardsManager('admin-rewards',{isAdmin,centers,centerId:d.user.center_id}); }
      bindAdmin(t);
    }
    tabs.forEach(t=>t.onclick=()=>show(t.dataset.tab));
    const qsAdmin=new URLSearchParams(location.hash.split('?')[1]||'');
    const requested=qsAdmin.get('tab'); const statusFilter=qsAdmin.get('status'); const editId=Number(qsAdmin.get('edit')||0);
    const centerTabs=['overview','bookings','services','clients','points','rewards','suggestions','qr','center','payments'];
    show(isAdmin&&['adminpay','emails','legal','pointtexts','maps','plans','features','media','promos','virtual','audit','destinations','experiences','users','centers','claims','suggestions','qr','rewards','bookings','points'].includes(requested)?requested:(isAdmin?'overview':(centerTabs.includes(requested)?requested:'overview')));
    if(isAdmin&&editId) editPointForm(editId);
  }
  // Shared by the center workspace and the legacy admin view.
  async function bindCenterProfile(c){
    const form=$('#my-center-form'); if(!form)return;
    const eqWrap=$('#center-equipment-editor');
    if(eqWrap){try{const eq=(await api('/api/center-equipment?center_id='+c.id)).items;eqWrap.innerHTML=eq.map(x=>`<div class="equipment-admin-row"><div><strong>${escapeHtml(x.label)}</strong></div><input class="center-equipment-price" data-code="${escapeHtml(x.code)}" type="number" min="0" step="0.01" value="${x.price==null?'':x.price}" placeholder="Consultar"><span>€</span><button class="btn save-equipment-price" data-code="${escapeHtml(x.code)}">Guardar</button></div>`).join('');$$('.save-equipment-price').forEach(btn=>btn.onclick=async()=>{const input=document.querySelector('.center-equipment-price[data-code="'+btn.dataset.code+'"]');try{await postJSON('/api/center-equipment',{code:btn.dataset.code,price:input.value});toast('Precio de equipo actualizado.');}catch(err){toast(err.message)}});}catch(e){eqWrap.innerHTML='<div class="empty">No se pudo cargar el catálogo de equipo.</div>';}}
    form.onsubmit=async e=>{e.preventDefault();try{await postJSON('/api/provider/center-update',{name:$('#mc-name').value,country:$('#mc-country').value,region:$('#mc-region').value,phone:$('#mc-phone').value,city:$('#mc-city').value,website:$('#mc-web').value,email:$('#mc-email').value,logo_url:$('#mc-logo').value,address:$('#mc-address').value,specialties:$('#mc-spec').value,description:$('#mc-desc').value,instagram_url:$('#mc-instagram').value,facebook_url:$('#mc-facebook').value,twitter_url:$('#mc-twitter').value,youtube_url:$('#mc-youtube').value,tiktok_url:$('#mc-tiktok').value});if($('#mc-photo').files[0]){const fd=new FormData();fd.append('file',$('#mc-photo').files[0]);await api('/api/provider/avatar',{method:'POST',body:fd});}toast('Ficha del centro actualizada.');renderAdmin();}catch(err){toast(err.message)}};
  }
  function adminOverview(points,virtuals,experiences,users,centers,bookings){return `<div class="cards" style="margin-top:18px"><a class="card" href="#/admin?tab=points"><span class="label">CATÁLOGO</span><h3>Gestionar puntos de buceo</h3><p>${points.length} puntos activos. Crear, editar, archivar y corregir ubicaciones.</p></a><a class="card" href="#/admin?tab=virtual"><span class="label">CONTENIDO 360°</span><h3>Gestionar recorridos virtuales</h3><p>${virtuals.length} recorridos. Añade panorámicas, vídeo 360°, Street View o experiencias externas.</p></a><a class="card" href="#/admin?tab=experiences"><span class="label">MARKETPLACE</span><h3>Gestionar experiencias</h3><p>${experiences.length} propuestas y viajes publicados o pendientes de revisión.</p></a><a class="card" href="#/admin?tab=destinations"><span class="label">DESTINOS</span><h3>Gestionar destinos</h3><p>Crea y organiza los destinos que alimentan la sección Experiencias.</p></a><a class="card" href="#/admin?tab=users"><span class="label">CUENTAS</span><h3>Usuarios y permisos</h3><p>${users.length} cuentas. Cambia roles entre administrador, centro, freelance y buceador.</p></a><a class="card" href="#/admin?tab=centers"><span class="label">PROVEEDORES</span><h3>Centros de buceo</h3><p>${centers.length} centros y sus puntos asociados.</p></a><a class="card" href="#/admin?tab=bookings"><span class="label">OPERACIÓN</span><h3>Reservas</h3><p>${bookings.length} reservas y solicitudes.</p></a><a class="card" href="#/admin?tab=audit"><span class="label">CONTROL</span><h3>Actividad administrativa</h3><p>Consulta quién creó, modificó, publicó o eliminó contenido.</p></a></div>`}

  function adminVirtuals(items){return `<div class="notice"><strong>Recorridos virtuales del catálogo</strong><p>Localiza cualquier recorrido. Al pulsar editar vuelves a la ficha del punto para añadir, sustituir o eliminar contenido.</p></div><div class="table-wrap" style="margin-top:18px"><table><thead><tr><th>Recorrido</th><th>Punto</th><th>Tipo</th><th>Proveedor / autor</th><th>Actualizado</th><th></th></tr></thead><tbody>${items.map(v=>`<tr><td><strong>${escapeHtml(v.title)}</strong></td><td>${escapeHtml(v.point_name)} · ${escapeHtml(v.country)}</td><td>${escapeHtml(({panorama:'360° interactivo',video360:'Vídeo 360°',streetview:'Street View',external360:'360° externa'})[v.experience_type]||v.experience_type)}</td><td>${escapeHtml(v.provider||v.created_by_name||'WORLDIVES')}</td><td>${fmtDate(v.updated_at)}</td><td><a class="btn" href="#/admin?tab=points&edit=${v.dive_point_id}">Editar</a></td></tr>`).join('')||'<tr><td colspan="6">No hay recorridos virtuales todavía.</td></tr>'}</tbody></table></div>`}
  function adminDestinations(items){return `<div class="notice"><strong>Destinos de Experiencias</strong><p>Estos destinos alimentan la sección Experiencias. Puedes crear nuevos destinos desde aquí.</p></div><div class="page-actions" style="margin-top:14px"><button class="btn btn-primary" id="new-destination">Nuevo destino</button></div><div class="table-wrap"><table><thead><tr><th>Destino</th><th>Región</th><th>Tipo</th><th></th></tr></thead><tbody>${items.map(t=>`<tr><td><span class="dst-thumb">${t.image_path?`<img src="${escapeHtml(t.image_path)}" alt="">`:''}</span>${escapeHtml(t.title)}</td><td>${escapeHtml(t.region)}</td><td>${escapeHtml(t.kind)}</td><td><button class="btn edit-destination" data-id="${t.id}">Editar</button></td></tr>`).join('')}</tbody></table></div>`}
  function adminAudit(items){return `<div class="notice">Historial de las acciones administrativas y de gestión registradas por WORLDIVES.</div><div class="table-wrap" style="margin-top:18px"><table><thead><tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Elemento</th><th>Detalles</th></tr></thead><tbody>${items.map(a=>`<tr><td>${fmtDate(a.created_at)}</td><td>${escapeHtml(a.fullname||'Sistema')}</td><td>${escapeHtml(a.action)}</td><td>${escapeHtml(a.entity_type||'')} ${a.entity_id?('#'+a.entity_id):''}</td><td>${escapeHtml(a.details||'')}</td></tr>`).join('')||'<tr><td colspan="5">Todavía no hay actividad.</td></tr>'}</tbody></table></div>`}
  function adminPoints(points,isAdmin){return `<div class="page-actions"><button class="btn btn-primary" id="new-point">Nuevo punto</button></div><div class="table-wrap"><table><thead><tr><th>Punto</th><th>Ubicación</th><th>Tipo</th><th>Estado</th><th></th></tr></thead><tbody>${points.map(p=>`<tr><td>${escapeHtml(p.name)}</td><td>${escapeHtml(p.country)} · ${escapeHtml(p.region||'')}<br><small>${Number(p.latitude).toFixed(5)}, ${Number(p.longitude).toFixed(5)}</small></td><td>${escapeHtml(p.dive_type)}</td><td>${escapeHtml(p.verification_status)}</td><td>${isAdmin?`<button class="btn edit-point" data-id="${p.id}">Editar</button>${p.verification_status==='pending_center'?`<button class="btn review-point" data-id="${p.id}" data-decision="approve">Aprobar</button><button class="btn review-point" data-id="${p.id}" data-decision="reject">Rechazar</button>`:''}`:`<button class="btn propose-point" data-id="${p.id}">Proponer corrección</button>`}</td></tr>`).join('')}</tbody></table></div>`}
  function adminBookings(items){
    const today=new Date().toISOString().slice(0,10);
    const ST={pending:['Pendiente','warn'],confirmed:['Confirmada','good'],completed:['Completada','good'],rejected:['Rechazada','bad'],cancelled:['Cancelada','bad']};
    const NEXT={pending:[['confirmed','Confirmar'],['rejected','Rechazar'],['cancelled','Cancelar']],confirmed:[['completed','Completar'],['cancelled','Cancelar']]};
    const shown=items.slice(0,500);
    return `<div class="table-wrap"><table><thead><tr><th>Fecha</th><th>Cliente</th><th>Centro</th><th>Servicio / punto</th><th>Estado</th><th></th></tr></thead><tbody>${shown.map(b=>{ const st=ST[b.status]||[b.status,'warn']; const acts=(NEXT[b.status]||[]).filter(([s])=>s!=='completed'||String(b.booking_date)<=today);
      return `<tr><td><strong>${escapeHtml(wdDay(b.booking_date))}</strong><br><small>${escapeHtml(b.booking_time||'')}</small></td><td>${escapeHtml(b.fullname||'')}<br><small>${escapeHtml(b.email||'')}</small></td><td>${escapeHtml(b.center_name||'')}</td><td>${escapeHtml(b.service_title||'Reserva')}<br><small>${escapeHtml(b.point_name||'Punto a concretar')} · ${Number(b.participants||1)} ${Number(b.participants||1)===1?'persona':'personas'}</small></td><td><span class="status ${st[1]}">${escapeHtml(st[0])}</span></td><td class="ab-actions"><button class="btn booking-detail" data-id="${b.id}">Ver ficha</button>${acts.map(([s,l])=>`<button class="btn booking-status" data-id="${b.id}" data-status="${s}">${l}</button>`).join('')}</td></tr>`; }).join('')||'<tr><td colspan="6">No hay reservas.</td></tr>'}</tbody></table></div>${items.length>shown.length?`<p class="muted" style="margin-top:10px">Se muestran las ${shown.length} reservas más recientes de ${items.length}.</p>`:''}`;
  }
  function adminUsers(items){ const centers=state.centers||[]; return `<div class="table-wrap"><table><thead><tr><th>Nombre</th><th>Email</th><th>Rol</th><th>Centro</th><th>Alta</th><th></th></tr></thead><tbody>${items.map(u=>`<tr><td>${escapeHtml(u.fullname)}</td><td>${escapeHtml(u.email)}</td><td><select class="user-role" data-id="${u.id}"><option value="recreational" ${u.role==='recreational'?'selected':''}>Recreativo</option><option value="center" ${u.role==='center'?'selected':''}>Centro</option><option value="freelance" ${u.role==='freelance'?'selected':''}>Freelance</option><option value="admin" ${u.role==='admin'?'selected':''}>Administrador</option></select></td><td><select class="user-center" data-id="${u.id}"><option value="">—</option>${centers.map(c=>`<option value="${c.id}" ${String(c.id)===String(u.center_id||'')?'selected':''}>${escapeHtml(c.name)}</option>`).join('')}</select></td><td>${fmtDate(u.created_at)}</td><td><button class="btn save-role" data-id="${u.id}">Guardar</button></td></tr>`).join('')}</tbody></table></div>`}

  async function proposePointPosition(id){ const p=(await api('/api/dive-points/'+id)).item; setApp(`<section class="page"><div class="breadcrumb"><a href="#/admin">Gestión</a> / Proponer corrección</div><p class="eyebrow">CORRECCIÓN</p><h1>${escapeHtml(p.name)}</h1><p class="lead">Propón la posición que consideres correcta. No se publicará hasta que el administrador la revise.</p><form id="position-proposal" class="detail" style="margin-top:28px"><article class="detail-main"><div class="form-grid"><div class="field"><label>Latitud</label><input id="s-lat" type="number" step="0.000001" value="${p.latitude}" required></div><div class="field"><label>Longitud</label><input id="s-lon" type="number" step="0.000001" value="${p.longitude}" required></div><div class="field full"><label>Motivo / referencia</label><textarea id="s-note" placeholder="Coordenadas tomadas por el centro, GPS de la embarcación, carta náutica, etc." required></textarea></div></div><div class="form-actions"><button class="btn btn-primary">Enviar corrección</button><a class="btn" href="#/admin">Cancelar</a></div></article></form></section>`); $('#position-proposal').onsubmit=async e=>{e.preventDefault();try{await postJSON('/api/dive-points/'+id+'/suggest',{latitude:+$('#s-lat').value,longitude:+$('#s-lon').value,note:$('#s-note').value});toast('Corrección enviada al administrador.');location.hash='#/admin?tab=suggestions';}catch(err){toast(err.message)}}; }
  function providerSuggestions(items){return `<div class="notice"><strong>Correcciones de puntos</strong><p>Como centro o profesional puedes proponer una nueva posición para cualquier punto. La ubicación oficial solo cambia cuando el administrador la aprueba.</p></div><div class="table-wrap" style="margin-top:12px"><table><thead><tr><th>Punto</th><th>Propuesta</th><th>Estado</th><th>Motivo</th></tr></thead><tbody>${items.map(s=>`<tr><td>${escapeHtml(s.point_name)}</td><td>${Number(s.latitude).toFixed(6)}, ${Number(s.longitude).toFixed(6)}</td><td>${escapeHtml(s.status)}</td><td>${escapeHtml(s.note||'')}</td></tr>`).join('')||'<tr><td colspan="4">Todavía no has enviado correcciones.</td></tr>'}</tbody></table></div>`}
  function adminSuggestions(items){return `<div class="notice">Una corrección aprobada sustituye las coordenadas oficiales del punto y queda registrada.</div><div class="table-wrap" style="margin-top:12px"><table><thead><tr><th>Punto</th><th>Propuesta</th><th>Usuario</th><th>Motivo</th><th></th></tr></thead><tbody>${items.map(s=>`<tr><td>${escapeHtml(s.point_name)}</td><td>${Number(s.latitude).toFixed(6)}, ${Number(s.longitude).toFixed(6)}</td><td>${escapeHtml(s.fullname)}</td><td>${escapeHtml(s.note||'')}</td><td><button class="btn review-s" data-id="${s.id}" data-decision="approve">Aprobar</button><button class="btn" data-id="${s.id}" data-decision="reject">Rechazar</button></td></tr>`).join('')||'<tr><td colspan="5">No hay correcciones pendientes.</td></tr>'}</tbody></table></div>`}
  function adminTravelExperiences(items){return `<div class="notice"><strong>Experiencias de viaje</strong><p>Los centros y profesionales pueden proponer viajes. Desde aquí el administrador puede publicar o rechazar cada propuesta.</p></div><div class="table-wrap" style="margin-top:18px"><table><thead><tr><th>Experiencia</th><th>Destino</th><th>Proveedor</th><th>Fechas</th><th>Estado</th><th></th></tr></thead><tbody>${items.map(e=>`<tr><td>${escapeHtml(e.title)}</td><td>${escapeHtml(e.destination_title)}</td><td>${escapeHtml(e.center_name||e.provider_name||'')}</td><td>${escapeHtml(e.start_date||'')}</td><td>${escapeHtml(e.status)}</td><td>${e.status==='published'?'<span class="status good">Publicada</span>':`<button class="btn experience-status" data-id="${e.id}" data-status="published">Publicar</button> <button class="btn experience-status" data-id="${e.id}" data-status="rejected">Rechazar</button>`}</td></tr>`).join('')||'<tr><td colspan="6">No hay propuestas.</td></tr>'}</tbody></table></div>`}

  function adminCenterClaims(items){ const M={email_domain:'Email del dominio del centro',phone_call:'Llamada al teléfono público del centro',document:'Documento (licencia, alta fiscal o registro)'}; return `<div class="notice"><strong>Verificación de cuentas profesionales</strong><p>Nadie obtiene el rol de centro o profesional al registrarse. Antes de aprobar, comprueba la identidad por uno de estos medios y deja una nota: <b>email del dominio del centro</b>, <b>llamada al teléfono público</b> (no al que escribió en el registro) o <b>documento</b>. Si el teléfono coincide con un centro existente, solo aparece como sugerencia.</p></div><div class="claims-list" style="margin-top:12px">${items.map(x=>`<article class="acc-card claim-card" data-claim="${x.id}"><div class="acc-card-head"><h3>${escapeHtml(x.requested_center_name||x.fullname)} <small>· ${x.requested_role==='freelance'?'Profesional freelance':'Centro de buceo'}</small></h3><span class="status warn">Pendiente</span></div><dl class="claim-data"><dt>Cuenta</dt><dd>${escapeHtml(x.fullname)} · ${escapeHtml(x.email)} ${x.email_matches_domain?'<span class="status good">email del dominio de la web</span>':''}</dd><dt>Teléfono indicado</dt><dd>${escapeHtml(x.phone||'—')}</dd><dt>Ciudad</dt><dd>${escapeHtml(x.city||'—')}</dd><dt>Web</dt><dd>${x.website?`<a href="${escapeHtml(x.website)}" target="_blank" rel="noopener noreferrer">${escapeHtml(x.website)}</a>`:'—'}</dd>${x.suggested_center_name?`<dt>Coincidencia sugerida</dt><dd>${escapeHtml(x.suggested_center_name)} (${escapeHtml(x.suggested_center_city||'')}) · teléfono público ${escapeHtml(x.suggested_center_phone||'—')} <small>Solo es una sugerencia: llama al teléfono público para confirmar.</small></dd>`:''}${x.note?`<dt>Nota</dt><dd>${escapeHtml(x.note)}</dd>`:''}<dt>Solicitud</dt><dd>${fmtDate(x.created_at)}</dd></dl><div class="form-grid"><div class="field"><label for="cm-${x.id}">Cómo lo has verificado</label><select id="cm-${x.id}" class="claim-method"><option value="">Elige…</option>${Object.entries(M).map(([k,v])=>`<option value="${k}">${escapeHtml(v)}</option>`).join('')}</select></div><div class="field"><label for="cn-${x.id}">Nota de la verificación</label><input id="cn-${x.id}" class="claim-note" placeholder="Ej. llamada al 965 000 000 el 12/10, atendió el gerente"></div>${x.suggested_center_id&&x.requested_role!=='freelance'?`<label class="lg-check full" for="cl-${x.id}"><input type="checkbox" id="cl-${x.id}" class="claim-link" value="${x.suggested_center_id}"><span>Vincular a la ficha existente «${escapeHtml(x.suggested_center_name)}» en lugar de crear una nueva</span></label>`:''}</div><div class="form-actions"><button class="btn btn-primary review-claim" data-id="${x.id}" data-decision="approve">Aprobar</button><button class="btn review-claim" data-id="${x.id}" data-decision="reject">Rechazar</button></div></article>`).join('')||'<p class="acc-empty">No hay solicitudes pendientes.</p>'}</div>`}
  function adminCenters(items){return `<div class="page-actions"><button class="btn btn-primary" id="new-center">Nuevo centro</button></div><div class="table-wrap"><table><thead><tr><th>Centro</th><th>Ubicación</th><th>Especialidades</th><th>Puntos</th><th></th></tr></thead><tbody>${items.map(c=>`<tr><td>${escapeHtml(c.name)}</td><td>${escapeHtml(c.city||'')} · ${escapeHtml(c.country)}</td><td>${escapeHtml(c.specialties||'')}</td><td>${c.point_count||0}</td><td><button class="btn edit-center" data-id="${c.id}">Editar</button></td></tr>`).join('')||'<tr><td colspan="5">No hay centros.</td></tr>'}</tbody></table></div>`}
  function adminClients(items){ return `<div class="notice">Clientes que han escaneado el QR del centro o han quedado vinculados por una reserva.</div><div class="table-wrap" style="margin-top:12px"><table><thead><tr><th>Cliente</th><th>Email</th><th>Primer check-in</th><th>Último</th></tr></thead><tbody>${items.map(u=>`<tr><td>${escapeHtml(u.fullname)}</td><td>${escapeHtml(u.email)}</td><td>${fmtDate(u.first_checkin)}</td><td>${fmtDate(u.last_checkin)}</td></tr>`).join('')||'<tr><td colspan="4">Todavía no hay clientes asociados.</td></tr>'}</tbody></table></div>` }
  function adminQR(){return `<div class="notice">Genera un QR para la recepción de un centro. El cliente lo escanea con el móvil; si ya ha iniciado sesión, el centro queda asociado a su cuenta.</div><form id="qr-form" style="margin-top:14px" class="form-grid"><div class="field"><label>Centro</label><select id="qr-center" required></select></div><div class="field"><label>Etiqueta</label><input id="qr-label" value="Recepción"></div><div class="full form-actions"><button class="btn btn-primary">Crear QR</button></div></form><div id="qr-output" style="margin-top:18px"></div>`}
  function bindAdmin(tab){ if(tab==='destinations'){ $('#new-destination')?.addEventListener('click',()=>editDestinationForm()); $$('.edit-destination').forEach(b=>b.onclick=()=>editDestinationForm(+b.dataset.id)); } if(tab==='points'){ $('#new-point')?.addEventListener('click',()=>editPointForm()); $$('.edit-point').forEach(b=>b.onclick=()=>editPointForm(+b.dataset.id)); $$('.propose-point').forEach(b=>b.onclick=()=>proposePointPosition(+b.dataset.id)); } if(tab==='bookings'){ $$('.booking-detail').forEach(b=>b.onclick=()=>renderBookingDetail(+b.dataset.id)); } if(tab==='bookings') $$('.booking-status').forEach(b=>b.onclick=async()=>{try{await postJSON('/api/bookings/'+b.dataset.id+'/status',{status:b.dataset.status});toast('Estado actualizado.');renderAdmin();}catch(e){toast(e.message)}}); if(tab==='experiences') $$('.experience-status').forEach(b=>b.onclick=async()=>{try{await postJSON('/api/admin/travel-experiences/status',{id:+b.dataset.id,status:b.dataset.status});toast('Estado actualizado.');renderAdmin();}catch(e){toast(e.message)}}); if(tab==='users') $$('.save-role').forEach(b=>b.onclick=async()=>{try{const id=b.dataset.id;const role=document.querySelector('.user-role[data-id="'+id+'"]').value;const centerEl=document.querySelector('.user-center[data-id="'+id+'"]');const center_id=+(centerEl?.value||0)||null;await postJSON('/api/admin/users/role',{user_id:+id,role,center_id});toast('Rol actualizado.');}catch(e){toast(e.message)}}); if(tab==='suggestions') $$('.review-s').forEach(b=>b.onclick=async()=>{try{await postJSON('/api/admin/suggestions/review',{id:+b.dataset.id,decision:b.dataset.decision});toast('Revisión guardada.');renderAdmin();}catch(e){toast(e.message)}}); $$('.review-claim').forEach(b=>b.onclick=async()=>{ const card=b.closest('[data-claim]'); const link=card?.querySelector('.claim-link'); try{await postJSON('/api/admin/center-claims/review',{id:+b.dataset.id,decision:b.dataset.decision,verification_method:card?.querySelector('.claim-method')?.value||'',verification_note:card?.querySelector('.claim-note')?.value||'',center_id:link?.checked?+link.value:null});toast('Verificación guardada.');renderAdmin();}catch(e){toast(e.message)}}); $$('.review-point').forEach(b=>b.onclick=async()=>{try{await postJSON('/api/admin/dive-points/review',{id:+b.dataset.id,decision:b.dataset.decision});toast('Revisión del punto guardada.');renderAdmin();}catch(e){toast(e.message)}}); if(tab==='suggestions') $$('.review-s[data-decision="reject"]').forEach(b=>b.onclick=async()=>{try{await postJSON('/api/admin/suggestions/review',{id:+b.dataset.id,decision:'reject'});toast('Rechazada.');renderAdmin();}catch(e){toast(e.message)}}); if(tab==='centers'){ $('#new-center')?.addEventListener('click',()=>editCenterForm()); $$('.edit-center').forEach(b=>b.onclick=()=>editCenterForm(+b.dataset.id)); } if(tab==='qr') loadQRCenters(); }
  async function loadQRCenters(){const cs=(await api('/api/centers')).items; $('#qr-center').innerHTML=cs.map(c=>`<option value="${c.id}">${escapeHtml(c.name)}</option>`).join(''); $('#qr-form').onsubmit=async e=>{e.preventDefault();try{const r=await postJSON('/api/qr/create',{center_id:+$('#qr-center').value,label:$('#qr-label').value}); const base=location.origin; $('#qr-output').innerHTML=`<div class="qr-box"><p><strong>${escapeHtml($('#qr-label').value)}</strong></p><img src="/api/qr/${r.code}" alt="Código QR"><p style="font-size:12px;color:var(--muted)">${base}/#/checkin/${r.code}</p><button class="btn" type="button" id="qr-copy">Copiar enlace</button></div>`; $('#qr-copy').onclick=()=>navigator.clipboard?.writeText(`${base}/#/checkin/${r.code}`);toast('QR creado.');}catch(e){toast(e.message)}}; }
  async function editPointForm(id){
    let p={name:'',country:'España',region:'',dive_type:'Arrecifes',latitude:38.5,longitude:-0.13,difficulty:'Intermedio',min_depth:'',max_depth:'',description:'',access_info:'',center_id:''};
    if(id){p=(await api('/api/dive-points/'+id)).item;} else if(state.me?.user?.role==='center'){p.center_id=state.me.user.center_id;}
    const meta=await loadMeta(); const cs=(await api('/api/centers')).items;
    let virtualItems=[]; if(id){try{virtualItems=(await api('/api/dive-points/'+id+'/virtual')).items||[];}catch{}}
    const virtualTypes={panorama:'360° interactivo',video360:'Vídeo 360°',streetview:'Street View',external360:'Experiencia 360° externa'};
    const virtualList=virtualItems.length ? virtualItems.map(v=>`<div class="doc-card virtual-admin-card"><div><strong>${escapeHtml(v.title)}</strong><div style="font-size:12px;color:var(--muted)">${escapeHtml(virtualTypes[v.experience_type]||v.experience_type)} · ${escapeHtml(v.provider||'WORLDIVES DISCOVERY')}</div>${v.url?`<small>${escapeHtml(v.url)}</small>`:''}${v.media_path?`<small>Archivo: ${escapeHtml(v.media_path)}</small>`:''}</div><div class="doc-actions"><button class="btn virtual-delete" type="button" data-id="${v.id}">Eliminar</button></div></div>`).join('') : '<div class="empty">Este punto todavía no tiene recorridos virtuales.</div>';
    setApp(`<section class="page"><div class="breadcrumb"><a href="#/admin">Gestión</a> / ${id?'Editar punto':'Nuevo punto'}</div><p class="eyebrow">CATÁLOGO</p><h1>${id?'Editar punto':'Nuevo punto'}</h1><p class="lead">La posición se puede introducir manualmente o seleccionando una localización en el mapa detallado.</p><form id="point-form" style="margin-top:28px"><div class="form-grid"><div class="field full"><label>Nombre</label><input id="p-name" value="${escapeHtml(p.name)}" required></div><div class="field"><label>País</label><select id="p-country">${meta.countries.map(x=>`<option ${x.name===p.country?'selected':''}>${escapeHtml(x.name)}</option>`).join('')}</select></div><div class="field"><label>Región / referencia</label><input id="p-region" value="${escapeHtml(p.region||'')}"></div><div class="field"><label>Tipo</label><select id="p-type">${meta.types.map(x=>`<option ${x.name===p.dive_type?'selected':''}>${escapeHtml(x.name)}</option>`).join('')}</select></div><div class="field"><label>Dificultad</label><select id="p-diff"><option ${p.difficulty==='Iniciación'?'selected':''}>Iniciación</option><option ${p.difficulty==='Intermedio'?'selected':''}>Intermedio</option><option ${p.difficulty==='Avanzado'?'selected':''}>Avanzado</option></select></div><div class="field"><label>Latitud</label><input id="p-lat" type="number" step="0.000001" value="${p.latitude}"></div><div class="field"><label>Longitud</label><input id="p-lon" type="number" step="0.000001" value="${p.longitude}"></div><div class="field"><label>Profundidad mínima</label><input id="p-min" type="number" step="0.1" value="${p.min_depth??''}"></div><div class="field"><label>Profundidad máxima</label><input id="p-max" type="number" step="0.1" value="${p.max_depth??''}"></div><div class="field"><label>Centro asociado</label>${state.me?.user?.role==='center'?`<input value="${escapeHtml(cs.find(c=>String(c.id)===String(state.me.user.center_id))?.name||'Mi centro')}" disabled><input id="p-center" type="hidden" value="${state.me.user.center_id}">`:`<select id="p-center"><option value="">Sin asignar</option>${cs.map(c=>`<option value="${c.id}" ${String(c.id)===String(p.center_id||'')?'selected':''}>${escapeHtml(c.name)}</option>`).join('')}</select>`}</div><div class="field"><label>Orientación de titulación</label><select id="p-cert"><option value="">Automática según dificultad/tipo</option>${meta.certifications.map(c=>`<option value="${c.id}" ${String(c.id)===String(p.recommended_certification_id||'')?'selected':''}>${escapeHtml(c.name)}</option>`).join('')}</select></div><div class="field full"><label>Descripción</label><textarea id="p-desc">${escapeHtml(p.description||'')}</textarea></div><div class="field full"><label>Acceso / notas operativas</label><textarea id="p-access">${escapeHtml(p.access_info||'')}</textarea></div></div><div class="notice" style="margin-top:18px"><strong>Ajustar ubicación en el mapa</strong><br><small>Arrastra el marcador o haz clic en otra posición. Las coordenadas se actualizan automáticamente.</small><div id="point-editor-map" class="map-card" style="height:320px;margin-top:12px"></div></div><div class="form-actions"><a class="btn" href="#/admin">Cancelar</a><button class="btn btn-primary">Guardar punto</button></div></form>${id?`<div class="notice" style="margin-top:18px"><strong>Recorrido virtual</strong><p style="margin:8px 0;color:var(--muted)">Añade un 360° interactivo, vídeo 360°, Street View o una experiencia externa. Puedes subir el archivo directamente o guardar una URL.</p><div id="virtual-admin-list" class="checklist">${virtualList}</div><form id="virtual-form" style="margin-top:16px"><div class="form-grid"><div class="field full"><label>Título</label><input id="v-title" placeholder="USAT Liberty · Recorrido 360°" required></div><div class="field"><label>Tipo de experiencia</label><select id="v-type"><option value="panorama">360° interactivo</option><option value="video360">Vídeo 360°</option><option value="streetview">Street View</option><option value="external360">Experiencia 360° externa</option></select></div><div class="field"><label>Proveedor / autor</label><input id="v-provider" placeholder="WORLDIVES, centro, fotógrafo…"></div><div class="field full"><label>URL</label><input id="v-url" type="url" placeholder="https://…"></div><div class="field full"><label>Archivo 360° (opcional)</label><input id="v-file" type="file" accept=".jpg,.jpeg,.png,.webp,.mp4,.webm,.mov"><small>Para un recorrido propio puedes subir una panorámica o un vídeo 360°. Para Street View o una experiencia externa, usa la URL.</small></div><div class="field full"><label>Descripción</label><textarea id="v-description" placeholder="Qué verá el usuario y qué recorrido puede hacer…"></textarea></div></div><div class="form-actions"><button class="btn btn-primary" type="submit">Añadir recorrido virtual</button></div></form></div><div class="notice" style="margin-top:18px"><strong>Material de apoyo del punto</strong><form id="point-photo-form" data-point-id="${id}" enctype="multipart/form-data" style="margin-top:10px"><div class="field"><label>Imagen</label><input name="file" type="file" accept=".jpg,.jpeg,.png,.webp" required></div><div class="field"><label>Descripción</label><input name="caption"></div><button class="btn" type="submit">Subir fotografía</button></form></div>`:''}</section>`);
    $('#point-form').onsubmit=async e=>{e.preventDefault();const data={id,name:$('#p-name').value,country:$('#p-country').value,region:$('#p-region').value,dive_type:$('#p-type').value,latitude:+$('#p-lat').value,longitude:+$('#p-lon').value,difficulty:$('#p-diff').value,min_depth:$('#p-min').value,max_depth:$('#p-max').value,center_id:+($('#p-center').value||0)||null,description:$('#p-desc').value,access_info:$('#p-access').value}; try{if(id) await postJSON('/api/dive-points/update',data,'POST'); else await postJSON('/api/dive-points',data);toast('Punto guardado.');location.hash=state.me?.user?.role==='center'?'#/admin?tab=points':'#/admin';}catch(err){toast(err.message)}};
    if(id){
      $('#virtual-form').onsubmit=async e=>{e.preventDefault(); try{const fd=new FormData(); fd.append('title',$('#v-title').value); fd.append('experience_type',$('#v-type').value); fd.append('provider',$('#v-provider').value); fd.append('url',$('#v-url').value); fd.append('description',$('#v-description').value); const file=$('#v-file').files[0]; if(file) fd.append('file',file); await api('/api/dive-points/'+id+'/virtual/upload',{method:'POST',body:fd}); toast('Recorrido virtual añadido.'); editPointForm(id);}catch(err){toast(err.message)}};
      $$('.virtual-delete').forEach(b=>b.onclick=async()=>{if(!confirm('¿Eliminar este recorrido virtual?'))return; try{const r=await fetch('/api/dive-points/'+id+'/virtual/'+b.dataset.id,{method:'DELETE'}); if(!r.ok){const x=await r.json().catch(()=>({}));throw new Error(x.error||'No se pudo eliminar.');} toast('Recorrido eliminado.');editPointForm(id);}catch(err){toast(err.message)}});
      $('#point-photo-form').onsubmit=async e=>{e.preventDefault(); const pid=e.target.dataset.pointId; try{await api('/api/dive-points/'+pid+'/photos',{method:'POST',body:new FormData(e.target)}); toast('Fotografía subida.'); editPointForm(+pid);}catch(err){toast(err.message)}};
    }
    if(window.L && $('#point-editor-map')){ const emap=(wdTileDefaults(),wdLimitMap(L.map('point-editor-map',{zoomControl:true}))).setView([+p.latitude,+p.longitude],15); wdBaseLayer().addTo(emap); const mk=L.marker([+p.latitude,+p.longitude],{draggable:true,icon:pointIcon(p,{active:true}),title:p.name||'Nuevo punto',alt:p.name||'Nuevo punto'}).addTo(emap); const sync=ll=>{ $('#p-lat').value=ll.lat.toFixed(6); $('#p-lon').value=ll.lng.toFixed(6); mk.setLatLng(ll); }; mk.on('dragend',e=>sync(e.target.getLatLng())); emap.on('click',e=>sync(e.latlng)); }
  }
  async function editDestinationForm(id){ const meta=await loadMeta(); let t={title:'',region:'',kind:'Viaje',image_path:'',summary:'',description:''}; if(id) t=meta.travel.find(x=>x.id===id)||t; setApp(`<section class="page"><div class="breadcrumb"><a href="#/admin?tab=destinations">Gestión</a> / ${id?'Editar destino':'Nuevo destino'}</div><p class="eyebrow">EXPERIENCIAS</p><h1>${id?'Editar destino':'Nuevo destino'}</h1><form id="destination-form" style="margin-top:28px"><div class="form-grid"><div class="field full"><label>Nombre del destino</label><input id="td-title" value="${escapeHtml(t.title)}" required></div><div class="field"><label>Región / país</label><input id="td-region" value="${escapeHtml(t.region||'')}" required></div><div class="field"><label>Tipo</label><input id="td-kind" value="${escapeHtml(t.kind||'Viaje')}" required></div><div class="field full"><label>Foto del destino</label><div class="td-photo"><div class="td-photo-preview" id="td-photo-preview">${t.image_path?`<img src="${escapeHtml(t.image_path)}" alt="">`:'<span>Sin foto</span>'}</div><div><input id="td-file" type="file" accept="image/jpeg,image/png,image/webp"><small>${IMG_HINT}</small>${t.image_path?'<label class="td-remove"><input type="checkbox" id="td-remove"> Quitar la foto actual</label>':''}</div></div></div><div class="field full"><label>Resumen</label><textarea id="td-summary">${escapeHtml(t.summary||'')}</textarea></div><div class="field full"><label>Descripción</label><textarea id="td-description">${escapeHtml(t.description||'')}</textarea></div></div><div class="form-actions"><a class="btn" href="#/admin?tab=destinations">Cancelar</a><button class="btn btn-primary">Guardar destino</button></div></form></section>`); $('#td-file').onchange=e=>{ const f=e.target.files[0]; if(f) $('#td-photo-preview').innerHTML=`<img src="${URL.createObjectURL(f)}" alt="">`; }; $('#destination-form').onsubmit=async e=>{e.preventDefault();try{const r=await postJSON('/api/admin/travel-offers',{id:id||null,title:$('#td-title').value,region:$('#td-region').value,kind:$('#td-kind').value,summary:$('#td-summary').value,description:$('#td-description').value}); const tid=r.id||id; const f=$('#td-file').files[0]; if(f) await uploadForm('/api/admin/travel-offer-image',{id:tid},f); else if($('#td-remove')?.checked) await uploadForm('/api/admin/travel-offer-image',{id:tid,remove:'1'}); __travel=null; try{ state.meta=null; }catch{} toast('Destino guardado.');location.hash='#/admin?tab=destinations';}catch(err){toast(err.message)}}; }
  async function editCenterForm(id){ const meta=await loadMeta(); let c={name:'',country:'España',region:'',city:'',address:'',phone:'',email:'',website:'',specialties:'',latitude:38.54,longitude:-0.12,description:'',logo_url:''}; if(id){c=(await api('/api/centers/'+id)).item;} setApp(`<section class="page"><div class="breadcrumb"><a href="#/admin?tab=centers">Gestión</a> / ${id?'Editar centro':'Nuevo centro'}</div><p class="eyebrow">CENTROS</p><h1>${id?'Editar centro':'Nuevo centro'}</h1><form id="center-form" style="margin-top:28px"><div class="form-grid"><div class="field full"><label>Nombre</label><input id="c-name" value="${escapeHtml(c.name||'')}" required></div><div class="field"><label>País</label><select id="c-country">${meta.countries.map(x=>`<option ${x.name===c.country?'selected':''}>${escapeHtml(x.name)}</option>`).join('')}</select></div><div class="field"><label>Región</label><input id="c-region" value="${escapeHtml(c.region||'')}"></div><div class="field"><label>Ciudad</label><input id="c-city" value="${escapeHtml(c.city||'')}"></div><div class="field"><label>Dirección</label><input id="c-address" value="${escapeHtml(c.address||'')}"></div><div class="field"><label>Teléfono</label><input id="c-phone" value="${escapeHtml(c.phone||'')}"></div><div class="field"><label>Email</label><input id="c-email" type="email" value="${escapeHtml(c.email||'')}"></div><div class="field"><label>Web</label><input id="c-web" value="${escapeHtml(c.website||'')}"></div><div class="field full"><label>Logo URL</label><input id="c-logo" value="${escapeHtml(c.logo_url||'')}" placeholder="URL del logotipo oficial"></div><div class="field full"><label>Especialidades</label><input id="c-spec" value="${escapeHtml(c.specialties||'')}" placeholder="Cuevas, técnico, sidemount…"></div><div class="field"><label>Latitud</label><input id="c-lat" type="number" step="0.000001" value="${c.latitude||0}"></div><div class="field"><label>Longitud</label><input id="c-lon" type="number" step="0.000001" value="${c.longitude||0}"></div><div class="field full"><label>Descripción</label><textarea id="c-desc">${escapeHtml(c.description||'')}</textarea></div></div><div class="notice" style="margin-top:18px"><strong>Ubicación del centro</strong><br><small>Arrastra el marcador o haz clic en el mapa.</small><div id="center-editor-map" class="map-card" style="height:300px;margin-top:12px"></div></div><div class="form-actions"><a class="btn" href="#/admin?tab=centers">Cancelar</a><button class="btn btn-primary">Guardar centro</button></div></form></section>`); $('#center-form').onsubmit=async e=>{e.preventDefault();try{const data={id:id||null,name:$('#c-name').value,country:$('#c-country').value,region:$('#c-region').value,city:$('#c-city').value,address:$('#c-address').value,phone:$('#c-phone').value,email:$('#c-email').value,website:$('#c-web').value,specialties:$('#c-spec').value,latitude:+$('#c-lat').value,longitude:+$('#c-lon').value,description:$('#c-desc').value,logo_url:$('#c-logo').value};await postJSON(id?'/api/centers/update':'/api/centers',data);toast(id?'Centro actualizado.':'Centro creado.');location.hash='#/admin?tab=centers';}catch(err){toast(err.message)}}; if(window.L && $('#center-editor-map')){ const cm=(wdTileDefaults(),wdLimitMap(L.map('center-editor-map'))).setView([+$('#c-lat').value||38.54,+$('#c-lon').value||-0.12],13); L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(cm); const mk=L.marker([+$('#c-lat').value||38.54,+$('#c-lon').value||-0.12],{draggable:true}).addTo(cm); const sync=ll=>{ $('#c-lat').value=ll.lat.toFixed(6); $('#c-lon').value=ll.lng.toFixed(6); mk.setLatLng(ll); }; mk.on('dragend',e=>sync(e.target.getLatLng())); cm.on('click',e=>sync(e.latlng)); } }

  async function renderCheckin(code){ const d=await api('/api/me'); setApp(`<section class="page auth"><div class="auth-card"><p class="eyebrow">WORLDIVES DISCOVERY · CHECK-IN</p><h1 style="font-size:42px">Check-in en el centro</h1><p class="lead" style="font-size:15px">Con el check-in, el centro podrá ver tu ficha de buceador (titulación, tallas, contacto de emergencia y documentos) para prepararte la actividad. Puedes dejar de compartirla cuando quieras desde «Mi cuenta».</p>${d.authenticated?`<label class="lg-check" for="checkin-consent"><input type="checkbox" id="checkin-consent"><span id="checkin-consent-text">Compartir mis datos con este centro</span></label><div class="form-actions"><button id="checkin-btn" class="btn btn-primary" type="button" disabled>Compartir mis datos y hacer check-in</button></div>`:`<p class="notice">Primero <a href="#/login?next=/checkin/${code}" style="font-weight:800">inicia sesión</a> o <a href="#/registro?next=/checkin/${code}" style="font-weight:800">crea tu cuenta</a>.</p>`}<div id="checkin-msg" style="margin-top:16px"></div></div></section>`);
    if(!d.authenticated) return;
    // Ask the server who the centre is (it answers 409 + the centre's name until the diver consents).
    try{ await postJSON('/api/checkin/'+code,{}); }catch(e){ if(e.status===409&&e.data?.center_name){ $('#checkin-consent-text').textContent=`Compartir mis datos con ${e.data.center_name}`; } else if(e.status!==409){ toast(e.message); } }
    $('#checkin-consent').onchange=e=>{ $('#checkin-btn').disabled=!e.target.checked; };
    $('#checkin-btn').onclick=async()=>{try{const r=await postJSON('/api/checkin/'+code,{share_consent:$('#checkin-consent').checked});$('#checkin-msg').innerHTML=`<div class="notice"><strong>${escapeHtml(r.center_name)}</strong><br>Check-in hecho. El centro ya puede ver tu ficha de buceador.</div>`;}catch(e){toast(e.message)}}; }
  async function renderPaymentSuccess(params){
    const sid=params.get('session_id')||''; if(!sid){location.hash='#/area';return;}
    if(!state.me){ goLogin(); return; }
    setApp(`<section class="page pay-ok-page"><div class="pay-ok-card is-wait"><div class="pay-ok-spin" aria-hidden="true"></div><h1>Confirmando tu pago…</h1><p>Estamos comprobándolo con el banco. No cierres esta ventana.</p></div></section>`);
    let d=null, tries=0;
    while(tries<6){ try{ d=await api('/api/payments/session/'+encodeURIComponent(sid)); }catch(err){ d={error:err.message}; break; } if(d.payment?.status!=='pending') break; tries++; await new Promise(r=>setTimeout(r,1500)); if(!location.hash.startsWith('#/pago-ok')) return; }
    if(!d||d.error){ setApp(`<section class="page pay-ok-page"><div class="pay-ok-card is-warn"><div class="pay-ok-icon">${wdIcon('alert',30)}</div><h1>No podemos mostrar este pago</h1><p>${escapeHtml(d?.error||'')}</p><p>Si se ha hecho el cargo, lo verás en tu reserva en unos minutos.</p><div class="page-actions"><a class="btn btn-primary" href="#/area">Ir a Mi área</a></div></div></section>`); return; }
    const p=d.payment, esc=escapeHtml, paid=p.status==='paid';
    const when=p.paid_at?new Date(p.paid_at).toLocaleString(wdLocale(),{dateStyle:'long',timeStyle:'short'}):'';
    const card=p.card_last4?`${CARD_BRANDS[p.card_brand]||esc(p.card_brand||'Tarjeta')} ···· ${esc(p.card_last4)}`:'Tarjeta';
    const head=paid?`<div class="pay-ok-icon">${wdIcon('check',34)}</div><p class="eyebrow">PAGO COMPLETADO</p><h1>¡Reserva confirmada!</h1><p class="lead">Hemos recibido tu pago y tu plaza está asegurada. Te hemos dejado el justificante en tu reserva.</p>`
      :p.status==='review'?`<div class="pay-ok-icon is-warn">${wdIcon('alert',30)}</div><p class="eyebrow">PAGO EN REVISIÓN</p><h1>Estamos revisando tu pago</h1><p class="lead">El importe recibido no coincide con la reserva. No pagues otra vez: te escribiremos en breve.</p>`
      :`<div class="pay-ok-icon is-warn">${wdIcon('clock',30)}</div><p class="eyebrow">PAGO PENDIENTE</p><h1>Todavía no tenemos la confirmación</h1><p class="lead">Algunos bancos tardan unos minutos. Te avisaremos en cuanto llegue; no hace falta que pagues de nuevo.</p>`;
    setApp(`<section class="page pay-ok-page"><div class="pay-ok-card ${paid?'is-ok':'is-warn'}">${head}
      <div class="pay-ok-ticket"><div class="pay-ok-row"><span>Actividad</span><strong>${esc(p.service_title||'Reserva')}</strong></div><div class="pay-ok-row"><span>Centro</span><strong>${esc(p.center_name||'—')}</strong></div>
        ${p.booking_date?`<div class="pay-ok-row"><span>Fecha</span><strong>${esc(wdLongDay?wdLongDay(p.booking_date):p.booking_date)}${p.booking_time?' · '+esc(p.booking_time):''}</strong></div>`:''}${p.participants?`<div class="pay-ok-row"><span>Buceadores</span><strong>${esc(p.participants)}</strong></div>`:''}
        <div class="pay-ok-row is-total"><span>Importe</span><strong>${wdMoney(p.amount_received||p.amount,p.currency)}</strong></div>
        ${paid?`<div class="pay-ok-row"><span>Pagado con</span><strong>${card}</strong></div>${when?`<div class="pay-ok-row"><span>Fecha del pago</span><strong>${esc(when)}</strong></div>`:''}`:''}${p.booking_ref?`<div class="pay-ok-row"><span>Nº de reserva</span><strong>${esc(p.booking_ref)}</strong></div>`:''}<div class="pay-ok-row"><span>Ref. del pago</span><strong>${esc(p.reference||'')}</strong></div></div>
      <div class="page-actions">${p.booking_id?`<a class="btn btn-primary" href="#/reserva?id=${p.booking_id}">Ver mi reserva y el QR</a><a class="btn" href="/api/bookings/${p.booking_id}/receipt.pdf" target="_blank" rel="noopener">${wdIcon('download',15)} Justificante PDF</a>`:''}${p.receipt_url?`<a class="btn" href="${esc(p.receipt_url)}" target="_blank" rel="noopener">Recibo de Stripe</a>`:''}<a class="btn" href="#/area">Mi área</a></div>
      <p class="pay-ok-foot">${wdIcon('lock',14)} Pago procesado por Stripe. WORLDIVES no guarda los datos de tu tarjeta.</p></div></section>`);
  }

  // ---------------------------------------------------------------- v50.30 · Legal, cookies, password recovery
  let LEGAL_INFO=null;
  async function legalInfo(){ if(!LEGAL_INFO){ try{ LEGAL_INFO=await api('/api/legal/info'); }catch{ LEGAL_INFO={version:'',docs:{},owner:{},reasons:{}}; } } return LEGAL_INFO; }
  // Small, safe Markdown renderer for the legal documents (headings, lists, tables, quotes, bold, links).
  function wdMd(md){
    const esc=escapeHtml; const slug=s=>wdFold?wdFold(s).replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,''):s;
    const inline=s=>esc(s).replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
      .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g,(m,txt,url)=>{ const safe=/^(#\/|https?:\/\/|mailto:)/.test(url)?url:'#'; return `<a href="${safe}"${/^https?:/.test(safe)?' target="_blank" rel="noopener"':''}>${txt}</a>`; })
      .replace(/(^|[\s(])(www\.[a-z0-9.-]+\.[a-z]{2,})/gi,'$1<a href="https://$2" target="_blank" rel="noopener">$2</a>')
      .replace(/\[(pendiente de completar|to be completed)\]/g,'<mark class="lg-pending">$1</mark>');
    const out=[]; let list=null, para=[], table=null, first=true;
    const flushP=()=>{ if(para.length){ out.push('<p>'+inline(para.join(' '))+'</p>'); para=[]; } };
    const flushL=()=>{ if(list){ out.push(`<${list.t}>`+list.items.map(i=>'<li>'+inline(i)+'</li>').join('')+`</${list.t}>`); list=null; } };
    const cells=r=>r.trim().replace(/^\||\|$/g,'').split('|').map(c=>c.trim());
    const flushT=()=>{ if(table){ const rows=table.filter(r=>!/^\|?\s*:?-{2,}/.test(r.trim())); const [h,...body]=rows;
      out.push('<div class="lg-table"><table><thead><tr>'+cells(h).map(c=>'<th>'+inline(c)+'</th>').join('')+'</tr></thead><tbody>'+body.map(r=>'<tr>'+cells(r).map(c=>'<td>'+inline(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>'); table=null; } };
    const flush=()=>{ flushP(); flushL(); flushT(); };
    for(const raw of String(md||'').replace(/\r/g,'').split('\n')){ const l=raw.trimEnd(); let m;
      if(!l.trim()){ flush(); continue; }
      if(l.trim().startsWith('|')){ flushP(); flushL(); (table??=[]).push(l); continue; } flushT();
      if((m=l.match(/^(#{1,3})\s+(.*)$/))){ flush(); if(m[1].length===1&&first){ first=false; continue; } const n=Math.min(3,m[1].length); out.push(`<h${n} id="${slug(m[2])}">${inline(m[2])}</h${n}>`); continue; }
      if((m=l.match(/^\s*[-*]\s+(.*)$/))){ flushP(); if(list?.t!=='ul'){ flushL(); list={t:'ul',items:[]}; } list.items.push(m[1]); continue; }
      if((m=l.match(/^\s*\d+\.\s+(.*)$/))){ flushP(); if(list?.t!=='ol'){ flushL(); list={t:'ol',items:[]}; } list.items.push(m[1]); continue; }
      if((m=l.match(/^>\s?(.*)$/))){ flush(); out.push('<blockquote>'+inline(m[1])+'</blockquote>'); continue; }
      flushL(); para.push(l.trim());
    }
    flush(); return out.join('\n');
  }
  async function renderLegal(slug){
    slug=slug||'aviso-legal'; const esc=escapeHtml; const qs=new URLSearchParams(location.hash.split('?')[1]||'');
    let doc, info;
    try{ [doc,info]=await Promise.all([api('/api/legal/doc?slug='+encodeURIComponent(slug)+'&lang='+currentLanguage()),legalInfo()]); }
    catch(e){ setApp(`<section class="page"><div class="empty"><h2>Documento no encontrado</h2><p>Consulta el resto de la información legal.</p><a class="btn btn-primary" href="#/legal/aviso-legal">Aviso legal</a></div></section>`); return; }
    const route=doc.route||slug, toc=[...String(doc.markdown).matchAll(/^##\s+(.*)$/gm)].map(m=>m[1]);
    const slugOf=s=>wdFold(s).replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
    const up=doc.upcoming;
    setApp(`<section class="lg-page">
      <header class="lg-hero"><div class="lg-hero-in"><p class="eyebrow">${wdIcon('file',14)} Información legal</p><h1 translate="no">${esc(doc.title)}</h1>
        <p class="lg-meta">Versión vigente: <span translate="no">${esc(doc.version)}</span> · En vigor desde el <span translate="no">${esc(wdLegalDate(doc.effective_at))}</span></p></div></header>
      <div class="lg-wrap">
        <nav class="lg-nav" aria-label="Documentos legales"><p class="lg-nav-t">Documentos</p>${Object.entries(info.docs||{}).map(([k,v])=>`<a href="#/legal/${k}" ${k===route?'aria-current="page"':''}>${esc(v)}</a>`).join('')}</nav>
        <div class="lg-main">
          ${doc.prevails_note?`<div class="notice lg-prevails" translate="no" lang="${esc(doc.lang)}">${wdIcon('info',16)} ${esc(doc.prevails_note)}</div>`:''}
          ${doc.lang!==currentLanguage()&&!doc.prevails_note?`<div class="notice lg-prevails">${wdIcon('info',16)} Este documento todavía no está traducido a tu idioma. Se muestra la versión oficial.</div>`:''}
          ${up?`<div class="notice warning lg-upcoming" id="lg-upcoming"><strong>Nueva versión anunciada.</strong> Entra en vigor el <span translate="no">${esc(wdLegalDate(up.effective_at))}</span>.${up.summary?` <span translate="no">${esc(up.summary)}</span>`:''} <button type="button" class="btn-link" id="lg-up-read">Leer la nueva versión</button></div>`:''}
          <article class="lg-doc" translate="no" lang="${esc(doc.lang)}">${wdMd(doc.markdown)}${slug==='denuncias'?'<div id="lg-report"></div>':''}</article>
          <section class="lg-history" aria-labelledby="lg-hist-t"><h2 id="lg-hist-t">Versiones de este documento</h2><div id="lg-hist"><p class="muted">Cargando…</p></div></section>
        </div>
        <aside class="lg-side">${toc.length>2?`<div class="lg-toc"><p class="lg-nav-t">En esta página</p>${toc.map(h=>`<a href="#${slugOf(h)}" data-to="${slugOf(h)}" translate="no">${esc(h)}</a>`).join('')}</div>`:''}
          <div class="lg-actions"><button type="button" class="btn" id="lg-print">${wdIcon('download',15)} Imprimir o guardar en PDF</button><a class="btn" href="#/legal/denuncias">${wdIcon('alert',15)} Denunciar contenido</a></div></aside>
      </div></section>`);
    $('#lg-print').onclick=()=>window.print();
    $$('.lg-toc a').forEach(a=>a.onclick=e=>{ e.preventDefault(); const t=document.getElementById(a.dataset.to); if(t){ t.setAttribute('tabindex','-1'); t.scrollIntoView({behavior:'smooth',block:'start'}); t.focus({preventScroll:true}); } });
    if(slug==='denuncias') renderReportForm($('#lg-report'),info,qs.get('url')||'');
    let hist=[]; try{ hist=(await api('/api/legal/history?slug='+encodeURIComponent(doc.slug))).items||[]; }catch{}
    const hm=$('#lg-hist'); if(!hm) return;
    hm.innerHTML=hist.length?`<ul class="lg-hist-list">${hist.map(h=>`<li><div><b translate="no">${esc(h.version)}</b> · <span>${h.effective_at>new Date().toISOString().slice(0,10)?'Entra en vigor el':'En vigor desde el'}</span> <span translate="no">${esc(wdLegalDate(h.effective_at))}</span>${h.version===doc.version?' <span class="status good">Vigente</span>':''}${h.summary?`<p translate="no">${esc(h.summary)}</p>`:''}</div><button type="button" class="btn" data-ver="${h.id}">Leer</button></li>`).join('')}</ul>`:'<p class="muted">Esta es la primera versión.</p>';
    translateTree(hm);
    $$('[data-ver]',hm).forEach(b=>b.onclick=()=>openLegalVersion(+b.dataset.ver));
    const upRow=up&&hist.find(h=>h.version===up.version); if(upRow&&$('#lg-up-read')) $('#lg-up-read').onclick=()=>openLegalVersion(upRow.id);
    else $('#lg-up-read')?.remove();
  }
  function wdLegalDate(d){ if(!d) return ''; try{ return new Date(String(d).slice(0,10)+'T12:00:00').toLocaleDateString(currentLanguage(),{day:'numeric',month:'long',year:'numeric'}); }catch{ return String(d).slice(0,10); } }
  async function openLegalVersion(id){
    let v; try{ v=await api('/api/legal/version?id='+id); }catch(err){ toast(err.message); return; }
    const text=String(v.markdown);
    wdOpenModal({id:'legal-version',size:'lg',title:escapeHtml(v.title),subtitle:`Versión ${escapeHtml(v.version)} · ${escapeHtml(wdLegalDate(v.effective_at))}`,
      body:`<article class="lg-doc" translate="no" lang="${escapeHtml(v.lang)}">${wdMd(text)}</article>`,footer:'<button type="button" class="btn" data-modal-close>Cerrar</button>'});
  }
  // A new version in force of a document the user must accept: one window asks for it (once per visit if postponed).
  function legalAcceptGate(){
    const pend=state.me?.legal?.pending||[]; if(!pend.length||$('#legal-accept')) return;
    if((location.hash||'').startsWith('#/legal/')) return;
    try{ if(sessionStorage.getItem('wd_legal_later')===pend.map(p=>p.slug+p.version).join(',')) return; }catch{}
    const esc=escapeHtml;
    const {el,close}=wdOpenModal({id:'legal-accept',title:'Hemos actualizado nuestras condiciones',subtitle:'Para seguir usando tu cuenta, revisa y acepta las nuevas versiones.',
      body:`<ul class="lg-accept-list">${pend.map(p=>`<li>${wdIcon('file',16)} <a href="#/legal/${esc(p.route)}" target="_blank" rel="noopener">${esc(p.title)}</a> <small>· versión <span translate="no">${esc(p.version)}</span></small></li>`).join('')}</ul>
        <label class="lg-check"><input type="checkbox" id="la-ok"> <span>He leído y acepto estas versiones.</span></label>`,
      footer:'<button type="button" class="btn" id="la-later">Más tarde</button><button type="button" class="btn btn-primary" id="la-accept" disabled>Aceptar</button>'});
    translateTree(el);
    $('#la-ok',el).onchange=e=>{ $('#la-accept',el).disabled=!e.target.checked; };
    $('#la-later',el).onclick=()=>{ try{ sessionStorage.setItem('wd_legal_later',pend.map(p=>p.slug+p.version).join(',')); }catch{} close(); };
    $('#la-accept',el).onclick=async()=>{ try{ const r=await postJSON('/api/legal/accept',{docs:pend.map(p=>p.slug)}); if(state.me) state.me.legal={pending:r.pending,upcoming:r.upcoming}; close(); toast('Gracias. Condiciones aceptadas.'); }catch(err){ toast(err.message); } };
  }
  function renderReportForm(mount,info,url){
    if(!mount) return; const me=state.me?.user; const esc=escapeHtml;
    mount.innerHTML=`<form class="lg-form" id="report-form" translate="yes"><h2>Formulario de denuncia</h2>
      <div class="form-grid">
        <div class="field full"><label for="rp-reason">Motivo</label><select id="rp-reason" required><option value="">Elige un motivo…</option>${Object.entries(info.reasons||{}).map(([k,v])=>`<option value="${k}">${esc(v)}</option>`).join('')}</select></div>
        <div class="field full"><label for="rp-url">Dirección (URL) del contenido</label><input id="rp-url" type="url" placeholder="https://…" value="${esc(url)}"><small>Abre la página del contenido y copia la dirección de la barra del navegador.</small></div>
        <div class="field full"><label for="rp-details">Explica por qué es ilegal o incumple las condiciones</label><textarea id="rp-details" minlength="20" maxlength="3000" required rows="5"></textarea></div>
        <div class="field"><label for="rp-name">Tu nombre</label><input id="rp-name" maxlength="120" value="${esc(me?.fullname||'')}"></div>
        <div class="field"><label for="rp-email">Tu email</label><input id="rp-email" type="email" maxlength="160" value="${esc(me?.email&&!/\.local$/.test(me.email)?me.email:'')}"></div>
        <label class="lg-check full"><input type="checkbox" id="rp-faith" required><span>Declaro que la información de esta denuncia es exacta y completa, y que la envío de buena fe.</span></label>
      </div><div class="form-actions"><button class="btn btn-primary" type="submit">Enviar denuncia</button></div></form>`;
    $('#report-form').onsubmit=async e=>{ e.preventDefault(); const btn=e.submitter||$('#report-form button[type=submit]'); btn.disabled=true;
      try{ const r=await postJSON('/api/reports',{reason:$('#rp-reason').value,target_url:$('#rp-url').value,details:$('#rp-details').value,name:$('#rp-name').value,email:$('#rp-email').value,good_faith:$('#rp-faith').checked});
        mount.innerHTML=`<div class="lg-done">${wdIcon('check',22)}<div><h2>Denuncia recibida</h2><p>Referencia <b>${esc(r.ref)}</b>. La revisaremos con diligencia${$('#rp-email')?.value?' y te escribiremos con la decisión':''}. Gracias por ayudarnos.</p></div></div>`; translateTree(mount);
      }catch(err){ toast(err.message); btn.disabled=false; } };
  }
  // Accessibility (v50.36): every <label> is tied to its field. Labels written without «for» (about a hundred in the
  // panels) are linked at render time to the only control of their field; controls without any label get the
  // placeholder or the nearby text as their accessible name.
  let wdLabelSeq=0;
  function wdLinkLabels(root){
    if(!root?.querySelectorAll) return;
    root.querySelectorAll('label:not([for])').forEach(l=>{ if(l.querySelector('input,select,textarea')) return;
      let c=l.nextElementSibling; if(!(c&&c.matches('input,select,textarea'))){ const box=l.closest('.field,.svc-field,.bk-field,.form-row,.cd-field'); const all=box?box.querySelectorAll('input:not([type=hidden]),select,textarea'):[]; c=all.length===1?all[0]:null; }
      if(!c) return; if(!c.id) c.id='wdf-'+(++wdLabelSeq); l.htmlFor=c.id; });
    root.querySelectorAll('input:not([type=hidden]):not([aria-label]):not([aria-labelledby]),select:not([aria-label]):not([aria-labelledby]),textarea:not([aria-label]):not([aria-labelledby])').forEach(c=>{
      if(c.closest('label')||(c.id&&root.querySelector(`label[for="${CSS.escape(c.id)}"]`))||(c.id&&document.querySelector(`label[for="${CSS.escape(c.id)}"]`))) return;
      const name=c.getAttribute('placeholder')||c.getAttribute('title'); if(name) c.setAttribute('aria-label',name); });
  }
  try{ let t=null; new MutationObserver(()=>{ clearTimeout(t); t=setTimeout(()=>wdLinkLabels(document.body),60); }).observe(document.documentElement,{childList:true,subtree:true}); }catch{}
  // Administración → Funciones: what is switched off disappears from menus and pages (the server refuses it too).
  function applyFeatureSwitches(){ const f=state.meta?.features||{}; Object.keys(f).forEach(k=>document.body.classList.toggle('feat-off-'+k,f[k]===false)); }
  // Demo deployments (WOD_DEMO_MODE=1): a fixed ribbon on every page.
  async function demoRibbon(){ let st; try{ st=await api('/api/setup/status'); }catch{ return; } if(!st.demo||$('#demo-ribbon')) return;
    document.body.classList.add('is-demo');
    document.body.insertAdjacentHTML('afterbegin','<div class="demo-ribbon" id="demo-ribbon" role="note"><strong>Versión de demostración:</strong> los centros y reservas que ves son ejemplos. No se hacen pagos reales.</div>');
    translateTree($('#demo-ribbon')); }
  // Footer: the owner's identification (LSSI-CE art. 10) as soon as it is filled in at Administración → Legal.
  async function footerOwner(){ const el=$('#footer-owner'); if(!el) return; const o=(await legalInfo()).owner||{};
    const parts=[o.owner_name,o.nif&&('NIF '+o.nif),o.address,o.email].filter(Boolean); if(!parts.length) return;
    el.setAttribute('translate','no'); el.textContent=`© ${new Date().getFullYear()} ${o.trade_name||'WORLDIVES DISCOVERY'} · ${parts.join(' · ')}`; }
  function cookieNotice(){
    let seen=null; try{ seen=Number(localStorage.getItem('wd_cookie_notice')||0); }catch{ return; }
    if(seen&&Date.now()-seen<365*864e5) return; if($('#ck-bar')) return;
    document.body.insertAdjacentHTML('beforeend',`<div class="ck-bar" id="ck-bar" role="region" aria-label="Aviso de cookies"><p>${wdIcon('shield',16)}<span>Solo usamos cookies técnicas, necesarias para que la web funcione (por ejemplo, para mantener tu sesión). No usamos cookies de publicidad ni de analítica. <a href="#/legal/cookies">Más información</a></span></p><button type="button" class="btn btn-primary" id="ck-ok">Entendido</button></div>`);
    $('#ck-ok').onclick=()=>{ try{ localStorage.setItem('wd_cookie_notice',String(Date.now())); }catch{} $('#ck-bar')?.remove(); };
    translateTree($('#ck-bar'));
  }
  // Link from the «Confirma la eliminación de tu cuenta» email.
  function renderConfirmDeletion(params){
    const token=params?.get?.('token')||new URLSearchParams(location.hash.split('?')[1]||'').get('token')||'';
    setApp(authCard('Eliminar mi cuenta',token?`<div class="cx-summary is-late">${wdIcon('alert',20)}<p>Al confirmar borraremos tu ficha, tus documentos, tu Log Book y tus puntos. Las reservas y los pagos se conservan sin tu nombre el tiempo que exige la ley. No se puede deshacer.</p></div>
      <p><a href="/api/account/export?format=zip" download>Descarga antes una copia de tus datos</a> (necesitas haber iniciado sesión).</p>
      <div class="form-actions"><a class="btn" href="#/">Cancelar</a><button class="btn danger" type="button" id="cd-ok">Eliminar definitivamente</button></div>`
      :`<div class="notice warning">El enlace no es válido.</div>`));
    $('#cd-ok')?.addEventListener('click',async e=>{ e.target.disabled=true;
      try{ await postJSON('/api/account/delete/confirm',{token}); state.me=null; renderAccount(); setApp(authCard('Cuenta eliminada','<p class="lead" style="font-size:15px">Hemos eliminado tu cuenta y tus datos personales. Gracias por haber buceado con nosotros.</p><div class="form-actions"><a class="btn btn-primary" href="#/">Ir al inicio</a></div>')); }
      catch(err){ toast(err.message); e.target.disabled=false; } });
  }
  async function renderForgot(){
    setApp(authCard('¿Has olvidado tu contraseña?',`<p class="lead" style="font-size:15px">Escribe el email de tu cuenta y te enviaremos un enlace para elegir una contraseña nueva.</p>
      <form id="forgot-form"><div class="field"><label for="fg-email">Email o usuario</label><input id="fg-email" required autocomplete="email"></div><div class="form-actions"><button class="btn btn-primary" type="submit">Enviar enlace</button></div></form>
      <p style="margin-top:18px;font-size:13px;color:var(--muted)"><a href="#/login" style="color:var(--sea);font-weight:800">Volver a iniciar sesión</a></p>`));
    $('#forgot-form').onsubmit=async e=>{ e.preventDefault(); const b=$('#forgot-form button'); b.disabled=true;
      try{ await postJSON('/api/auth/forgot',{email:$('#fg-email').value}); $('#forgot-form').outerHTML=`<div class="notice good" style="margin-top:6px"><strong>Revisa tu correo.</strong><p style="margin:6px 0 0">Si existe una cuenta con esos datos, te hemos enviado un enlace para cambiar la contraseña. Caduca en 1 hora. Mira también en la carpeta de spam.</p></div>`; translateTree($('#app')); }
      catch(err){ toast(err.message); b.disabled=false; } };
  }
  async function renderReset(params){
    const token=params?.get?.('token')||'';
    setApp(authCard('Elige una contraseña nueva',token?`<form id="reset-form"><div class="field"><label for="rs-1">Nueva contraseña</label><input id="rs-1" type="password" minlength="10" required autocomplete="new-password"><small>Mínimo 10 caracteres.</small></div><div class="field"><label for="rs-2">Repite la contraseña</label><input id="rs-2" type="password" minlength="10" required autocomplete="new-password"></div><div class="form-actions"><button class="btn btn-primary" type="submit">Guardar contraseña</button></div></form>`
      :`<div class="notice warning">El enlace no es válido. <a href="#/recuperar">Pide uno nuevo</a>.</div>`));
    $('#reset-form')?.addEventListener('submit',async e=>{ e.preventDefault(); if($('#rs-1').value!==$('#rs-2').value){ toast('Las contraseñas no coinciden.'); return; }
      try{ await postJSON('/api/auth/reset',{token,password:$('#rs-1').value}); toast('Contraseña cambiada. Ya puedes iniciar sesión.'); location.hash='#/login'; }catch(err){ toast(err.message); } });
  }
  // Centres and professionals: the terms for centres change with 15 days of notice. The banner announces the new
  // version (with its summary) and lets them accept it now; a version already in force is asked in legalAcceptGate.
  async function proTermsBanner(user){
    if(!user||!['center','freelance'].includes(user.role)) return; const esc=escapeHtml;
    const lg=state.me?.legal||{}; const up=(lg.upcoming||[]).find(u=>u.slug==='centros'); const pend=(lg.pending||[]).find(p=>p.slug==='centros');
    if(!up&&!pend) return;
    const host=$('#app .cb-main')||$('#app > section'); if(!host||$('#pro-terms-bar')) return;
    const msg=pend?`<strong>Condiciones para centros y profesionales</strong> Hay una nueva versión en vigor (<span translate="no">${esc(pend.version)}</span>). Revísala y acéptala para seguir publicando.`
      :`<strong>Cambios en las condiciones para centros</strong> La nueva versión entra en vigor el <span translate="no">${esc(wdLegalDate(up.effective_at))}</span>.${up.summary?` <span translate="no">${esc(up.summary)}</span>`:''} Si no estás de acuerdo, puedes darte de baja antes de esa fecha.`;
    host.insertAdjacentHTML('afterbegin',`<div class="pro-terms-bar" id="pro-terms-bar" role="status">${wdIcon('file',18)}<p>${msg}</p><a class="btn" href="#/legal/condiciones-centros" target="_blank" rel="noopener">Leer</a><button type="button" class="btn btn-primary" id="pro-terms-ok">Aceptar</button></div>`);
    translateTree($('#pro-terms-bar'));
    $('#pro-terms-ok').onclick=async()=>{ try{ const r=await postJSON('/api/legal/accept',{docs:['centros'],upcoming:!pend}); if(state.me) state.me.legal={pending:r.pending,upcoming:r.upcoming}; $('#pro-terms-bar').remove(); toast('Condiciones aceptadas.'); }catch(err){ toast(err.message); } };
  }

  // ---------------------------------------------------------------- v50.30 · Cancelling a booking
  function bookingCancelCard(b){
    const c=b.cancel; if(!c||!['pending','requested','accepted_pending_payment','confirmed'].includes(b.status)||c.started) return '';
    const amount=wdMoney(c.refund_amount,b.currency), paidAmount=wdMoney(c.paid_amount,b.currency);
    const until=c.deadline?new Date(c.deadline).toLocaleString(wdLocale(),{weekday:'long',day:'numeric',month:'long',hour:'2-digit',minute:'2-digit'}):'';
    const msg=!c.paid_online?'Puedes cancelar sin coste: no has pagado nada online.'
      :c.free?`Cancelación gratuita hasta el ${until}. Si cancelas ahora te corresponde una devolución de ${amount}.`
      :c.refund_amount>0?`El plazo de cancelación gratuita terminó el ${until}. Si cancelas ahora, según la política del centro, te corresponde una devolución de ${amount} (de ${paidAmount} pagados).`
      :`El plazo de cancelación gratuita terminó el ${until}. Si cancelas ahora, según la política del centro, no hay reembolso de los ${paidAmount} pagados.`;
    return `<section class="cx-card ${c.paid_online&&!c.free?'is-late':''}"><div class="cx-icon">${wdIcon('calendar',20)}</div><div class="cx-main"><p class="eyebrow">CANCELACIÓN</p><h3>¿No puedes ir?</h3><p>${escapeHtml(msg)}</p>
      <p class="cx-policy">${escapeHtml(b.cancellation_text||c.policy_text||'')}${b.cancellation_note?' '+escapeHtml(b.cancellation_note):''} <a href="#/legal/condiciones-reserva">Condiciones de reserva</a></p>
      <button type="button" class="btn cx-btn" id="booking-cancel">Cancelar reserva</button></div></section>`;
  }
  function bindBookingCancel(b,id){
    const btn=$('#booking-cancel'); if(!btn) return;
    btn.onclick=async()=>{
      let terms; try{ terms=(await postJSON(`/api/bookings/${id}/cancel`,{preview:true})).terms; }catch(err){ toast(err.message); return; }
      const refund=terms.paid_online?(terms.refund_amount>0?`Según la política del centro te corresponde una devolución de <b>${wdMoney(terms.refund_amount,b.currency)}</b>. La hace el centro a la misma tarjeta y te avisamos por email (después, 5–10 días hábiles según tu banco).`:'<b>No hay reembolso</b> porque estás fuera del plazo de cancelación gratuita.'):'No se te cobrará nada.';
      const {el,close}=wdOpenModal({id:'cancel-modal',title:'Cancelar la reserva',subtitle:`${escapeHtml(b.center_name)} · ${escapeHtml(areaDate(b.booking_date,b.booking_time))}`,
        body:`<div class="cx-summary ${terms.paid_online&&!terms.refund_amount?'is-late':''}">${wdIcon(terms.refund_amount>0||!terms.paid_online?'check':'alert',20)}<p>${refund}</p></div>
          <div class="field"><label for="cx-reason">Motivo (opcional, lo verá el centro)</label><textarea id="cx-reason" rows="3" maxlength="300" placeholder="Por ejemplo: me he resfriado, cambio de planes…"></textarea></div>`,
        footer:'<button type="button" class="btn" data-modal-close>No, mantener la reserva</button><button type="button" class="btn danger" id="cx-ok">Sí, cancelar la reserva</button>'});
      $('#cx-ok',el).onclick=async e=>{ e.currentTarget.disabled=true; try{ const r=await postJSON(`/api/bookings/${id}/cancel`,{reason:$('#cx-reason',el).value}); close();
        toast(r.refund==='proposed'?`Reserva cancelada. Hemos pedido al centro que te devuelva ${wdMoney(r.refund_amount,b.currency)}.`:r.refund==='refunded'?`Reserva cancelada. Te devolvemos ${wdMoney(r.refund_amount,b.currency)}.`:'Reserva cancelada.');
        renderBookingDetail(new URLSearchParams('id='+id)); }catch(err){ toast(err.message); e.currentTarget.disabled=false; } };
    };
  }
  function accountPrivacyCard(u){
    return `<section class="acc-card" id="acc-privacy"><div class="acc-card-head"><h2>${wdIcon('shield',18)} Privacidad y datos</h2></div>
      <p class="acc-help">Descarga una copia de todos tus datos o elimina tu cuenta cuando quieras.</p>
      <div class="acc-privacy-actions"><a class="btn" href="/api/account/export?format=zip" download>${wdIcon('download',15)} Descargar mis datos (ZIP)</a>${u.role==='recreational'?'<button type="button" class="btn danger" id="acc-delete">Eliminar mi cuenta</button>':''}</div>
      <p class="acc-legal-links"><a href="#/legal/privacidad">Privacidad</a> · <a href="#/legal/condiciones-buceadores">Condiciones de uso</a> · <a href="#/legal/condiciones-reserva">Condiciones de reserva</a> · <a href="#/legal/cookies">Cookies</a></p></section>`;
  }
  function bindAccountPrivacy(){
    $('#acc-delete')?.addEventListener('click',()=>{
      const {el,close}=wdOpenModal({id:'delete-account',title:'Eliminar mi cuenta',subtitle:'Esta acción no se puede deshacer',
        body:`<div class="cx-summary is-late">${wdIcon('alert',20)}<p>Borraremos tu ficha, tu documentación, tu Log Book, tus mensajes y tus recompensas. Las reservas pasadas se conservan sin tu nombre, porque la ley obliga a guardar los datos de los pagos. Si tienes reservas próximas, cancélalas antes.</p></div>
          <p style="margin:0 0 10px"><a href="/api/account/export?format=zip" download>Descarga antes una copia de tus datos</a></p>
          <div class="field"><label for="del-pw">Escribe tu contraseña para confirmar</label><input id="del-pw" type="password" autocomplete="current-password" required></div>`,
        footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn danger" id="del-ok">Eliminar definitivamente</button>'});
      $('#del-ok',el).onclick=async()=>{ try{ const r=await postJSON('/api/account/delete',{password:$('#del-pw',el).value}); close();
        if(r&&r.email_sent){ toast('Te hemos enviado un email para confirmar la eliminación. El enlace caduca en 24 horas.'); return; }
        state.me=null; renderAccount(); toast('Tu cuenta se ha eliminado.'); location.hash='#/'; }catch(err){ toast(err.message); } };
    });
  }

  // ---------------------------------------------------------------- v50.31 · Account: email, shared data, professional request, security
  function accountEmailCard(u){
    const verified=!!u.email_verified_at;
    return `<section class="acc-card" id="acc-email"><div class="acc-card-head"><h2>${wdIcon('message',18)} Email</h2>${verified?'<span class="status good">Verificado</span>':'<span class="status warn">Sin verificar</span>'}</div>
      <p class="acc-help"><strong>${escapeHtml(u.email)}</strong></p>${verified?'':'<p class="acc-help">Confirma tu email desde el enlace que te enviamos para recibir los avisos de tus reservas y poder recuperar la cuenta.</p><button type="button" class="btn" id="acc-email-resend">Reenviar el correo de verificación</button>'}
      <details class="acc-upload"><summary>Cambiar mi email</summary><form id="acc-email-form"><div class="field"><label for="acc-new-email">Nuevo email</label><input id="acc-new-email" type="email" required autocomplete="email"></div><div class="field"><label for="acc-email-pw">Tu contraseña</label><input id="acc-email-pw" type="password" required autocomplete="current-password"></div><button class="btn" type="submit">Enviar confirmación al nuevo email</button><small>El cambio se aplica cuando confirmes desde el nuevo email.</small></form></details></section>`;
  }
  function accountSharesCard(){ return `<section class="acc-card" id="acc-shares"><div class="acc-card-head"><h2>${wdIcon('shield',18)} Centros que ven tu ficha</h2></div><p class="acc-help">Un centro ve tu ficha de buceador y tus documentos cuando reservas tú con él o cuando compartes tus datos al hacer check-in con su QR.</p><div id="acc-shares-list"><p class="acc-empty">Cargando…</p></div></section>`; }
  function proRequestCard(u){
    const req=u.requested_role; if(!['center','freelance'].includes(req)||['center','freelance','admin'].includes(u.role)) return '';
    const st=state.me?.pro_request?.status||'pending';
    return `<section class="acc-card"><div class="acc-card-head"><h2>${wdIcon('chart',18)} Cuenta profesional</h2><span class="status ${st==='rejected'?'bad':'warn'}">${st==='rejected'?'No aprobada':'Pendiente de verificación'}</span></div><p class="acc-help">${st==='rejected'?'No hemos podido verificar tu solicitud. Escríbenos si crees que es un error.':`Estamos verificando tu ${req==='center'?'centro':'perfil profesional'}. Te avisaremos por email en cuanto esté aprobado; mientras tanto puedes usar WORLDIVES como buceador.`}</p></section>`;
  }
  function accountSecurityCard(u){ return typeof totpCard==='function'?totpCard(u):''; }
  async function bindAccountExtras(d){
    $('#acc-email-resend')?.addEventListener('click',async()=>{ try{ await postJSON('/api/account/verify-email/resend',{}); toast('Te hemos enviado el correo de verificación.'); }catch(e){ toast(e.message); } });
    $('#acc-email-form')?.addEventListener('submit',async e=>{ e.preventDefault(); try{ await postJSON('/api/account/email',{email:$('#acc-new-email').value,password:$('#acc-email-pw').value}); toast('Revisa el nuevo email y confirma el cambio.'); e.target.reset(); }catch(err){ toast(err.message); } });
    const list=$('#acc-shares-list'); if(list){ try{ const s=await api('/api/account/shares'); list.innerHTML=(s.items||[]).length?s.items.map(x=>`<div class="acc-doc"><span><span><strong>${escapeHtml(x.center_name)}</strong><small>${escapeHtml(x.city||'')} · desde ${fmtDate(x.granted_at)}</small></span></span><button type="button" class="btn" data-unshare="${x.center_id}">Dejar de compartir</button></div>`).join(''):'<p class="acc-empty">No compartes tu ficha con ningún centro (aparte de los centros en los que reservas tú).</p>';
      $$('[data-unshare]',list).forEach(b=>b.onclick=async()=>{ if(!confirm('¿Dejar de compartir tu ficha con este centro? Seguirá viendo los datos de las reservas que hagas tú.')) return; try{ await postJSON('/api/account/shares/revoke',{center_id:+b.dataset.unshare}); toast('Has dejado de compartir tus datos con el centro.'); bindAccountExtras(d); }catch(e){ toast(e.message); } }); }catch{ list.innerHTML=''; } }
    if(typeof bindTotpCard==='function') bindTotpCard(d);
  }
  async function renderVerifyEmail(params){
    const token=params.get('token')||''; setApp(authCard('Verificar email','<p class="lead">Comprobando el enlace…</p>'));
    try{ const r=await postJSON('/api/auth/verify-email',{token}); setApp(authCard(r.changed?'Email cambiado':'Email verificado',`<div class="notice success">${r.changed?'Tu email se ha cambiado. Vuelve a iniciar sesión con la nueva dirección.':'Gracias: tu email está verificado.'}</div><p><a class="btn btn-primary" href="${r.changed?'#/login':'#/cuenta'}">${r.changed?'Iniciar sesión':'Ir a mi cuenta'}</a></p>`)); await loadMe(); }
    catch(e){ setApp(authCard('Enlace no válido',`<div class="notice warn">${escapeHtml(e.message)}</div><p><a class="btn" href="#/cuenta">Ir a mi cuenta</a></p>`)); }
  }

  // ---------------------------------------------------------------- v50.30 · Administration: Legal and Emails
  const EMAIL_STATUS={queued:['En cola','warn'],sending:['Enviando','warn'],sent:['Enviado','good'],failed:['Fallido','bad'],skipped:['Sin email real','muted'],expired:['Caducado','muted']};
  async function renderAdminLegal(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/admin/legal'); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    const missing=['owner_name','nif','address','email'].filter(k=>!d.settings[k]);
    const RS={open:['Abierta','warn'],actioned:['Contenido retirado','good'],dismissed:['Desestimada','muted']};
    mount.innerHTML=`<section class="mm-module adl"><div class="svc-head"><div><p class="eyebrow">Legal</p><h2>Datos del titular y documentos legales</h2><p>Estos datos se insertan en el aviso legal, la privacidad, las condiciones y el pie de todos los correos. Los textos son plantillas completas: haz que los revise un abogado antes de publicar la web.</p></div></div>
      ${missing.length?`<div class="notice warning"><strong>Faltan datos obligatorios.</strong> Mientras no los completes, los documentos muestran «pendiente de completar».</div>`:'<div class="notice good"><strong>Datos del titular completos.</strong></div>'}
      <form id="adl-form" class="form-grid adl-form">${Object.entries(d.fields).map(([k,l])=>`<div class="field ${['address','registry'].includes(k)?'full':''}"><label for="adl-${k}">${esc(l)}</label><input id="adl-${k}" data-k="${k}" maxlength="300" value="${esc(d.settings[k]||'')}" ${k==='fee_percent'?'inputmode="decimal" placeholder="10"':''}></div>`).join('')}
        <div class="form-actions full"><button class="btn btn-primary" type="submit">Guardar datos legales</button></div></form>
      <div id="adl-retention"></div>
      <h3 class="adl-h">Documentos legales</h3>
      <p class="muted">Cada cambio crea una versión nueva con su fecha de entrada en vigor y queda en el historial público. El castellano es la versión de referencia; el inglés también es oficial y el resto de idiomas muestran «prevalece el castellano».</p>
      <div class="table-wrap"><table class="data-table adl-doctable"><thead><tr><th>Documento</th><th>Versión vigente</th><th>Idiomas</th><th>Próxima versión</th><th></th></tr></thead><tbody>${(d.documents||[]).map(x=>`<tr><td><a href="#/legal/${esc(x.route)}" target="_blank" rel="noopener">${esc(x.title)}</a>${x.acceptance?`<div class="adl-det">${x.acceptance==='pro'?'Lo aceptan centros y profesionales':'Lo acepta cada usuario'}${x.notice_days?` · aviso de ${x.notice_days} días`:''}</div>`:''}</td><td>${esc(x.version)}</td><td>${x.langs.map(l=>`<span class="adl-lang">${esc(l)}</span>`).join(' ')}</td><td>${x.upcoming?`${esc(x.upcoming.version)} · ${esc(wdLegalDate(x.upcoming.effective_at))}`:'—'}</td><td><button type="button" class="btn adl-edit" data-slug="${esc(x.slug)}">Editar</button></td></tr>`).join('')}</tbody></table></div>
      <h3 class="adl-h">Denuncias de contenido ${d.open_reports?`<b class="adl-badge">${d.open_reports} abiertas</b>`:''}</h3>
      ${d.reports.length?`<div class="table-wrap"><table class="data-table"><thead><tr><th>Ref.</th><th>Fecha</th><th>Motivo</th><th>Contenido</th><th>Remitente</th><th>Estado</th><th></th></tr></thead><tbody>${d.reports.map(r=>`<tr><td>DEN-${String(r.id).padStart(5,'0')}</td><td>${esc((r.created_at||'').slice(0,10))}</td><td>${esc(d.reasons[r.reason]||r.reason)}</td><td>${r.target_type?`<b>${esc({review:'Reseña',center:'Centro',point:'Punto de buceo',experience:'Experiencia',photo:'Foto',promotion:'Promoción',profile:'Perfil'}[r.target_type]||r.target_type)}</b> `:''}${r.target_url?`<a href="${esc(r.target_url)}" target="_blank" rel="noopener">Abrir</a>`:'—'}<div class="adl-det">${esc(r.details)}</div></td><td>${esc([r.reporter_name,r.reporter_email].filter(Boolean).join(' · ')||'Anónimo')}</td><td><span class="status ${RS[r.status]?.[1]||''}">${esc(RS[r.status]?.[0]||r.status)}</span>${r.resolution?`<div class="adl-det">${esc(r.resolution)}</div>`:''}</td><td>${r.status==='open'?`<button type="button" class="btn adl-resolve" data-id="${r.id}">Resolver</button>`:''}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">No hay denuncias.</div>'}
    </section>`;
    $('#adl-form').onsubmit=async e=>{ e.preventDefault(); const data={}; $$('#adl-form input[data-k]').forEach(i=>data[i.dataset.k]=i.value); try{ await postJSON('/api/admin/legal',data); LEGAL_INFO=null; toast('Datos legales guardados.'); renderAdminLegal(mountId); }catch(err){ toast(err.message); } };
    $$('.adl-edit',mount).forEach(b=>b.onclick=()=>openLegalEditor(b.dataset.slug,'es',()=>renderAdminLegal(mountId)));
    renderRetentionCard($('#adl-retention',mount));
    $$('.adl-resolve',mount).forEach(b=>b.onclick=()=>{
      const {el,close}=wdOpenModal({id:'report-resolve',title:'Resolver denuncia',subtitle:'Se enviará la decisión, con los motivos, a quien la presentó y a quien publicó el contenido',
        body:`<div class="field"><label for="rr-st">Decisión</label><select id="rr-st"><option value="actioned">Retirar o corregir el contenido</option><option value="dismissed">Desestimar: el contenido se mantiene</option></select></div><div class="field"><label for="rr-txt">Explicación de los motivos</label><textarea id="rr-txt" rows="4" maxlength="2000" required placeholder="Explica brevemente qué has comprobado y qué has decidido."></textarea><small>Si retiras contenido de un usuario o centro, infórmale también de los motivos.</small></div>`,
        footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="rr-ok">Guardar decisión</button>'});
      $('#rr-ok',el).onclick=async()=>{ try{ await postJSON('/api/admin/reports/resolve',{id:+b.dataset.id,status:$('#rr-st',el).value,resolution:$('#rr-txt',el).value}); close(); toast('Denuncia resuelta.'); renderAdminLegal(mountId); }catch(err){ toast(err.message); } };
    });
  }
  // Administración → Legal: retention periods of the privacy policy (a daily job applies them).
  async function renderRetentionCard(mount){
    if(!mount) return; const esc=escapeHtml; let d; try{ d=await api('/api/admin/retention'); }catch(err){ mount.innerHTML=''; return; }
    const F=[['inactive_months','Cuentas de buceador sin actividad','meses',`Se avisa por email y se elimina ${d.warn_days} días después si no entra.`],
      ['expired_docs_months','Documentos caducados','meses','Se borran después de su fecha de caducidad.'],
      ['notices_months','Avisos de los centros','meses',''],['audit_months','Registro de actividad','meses',''],['audit_keep','Entradas del registro que se conservan siempre','entradas','']];
    const L=d.last;
    mount.innerHTML=`<h3 class="adl-h">Conservación de datos</h3><p class="muted">Plazos de la política de privacidad. Cada día se aplican automáticamente. Las reservas y los pagos se conservan 6 años y no se borran aquí. Los registros del servidor se conservan ${d.log_days} días (variable WOD_LOG_RETENTION_DAYS).</p>
      <form id="ret-form" class="form-grid">${F.map(([k,l,u,h])=>`<div class="field"><label for="ret-${k}">${esc(l)} (${u})</label><input id="ret-${k}" data-k="${k}" type="number" min="${d.limits[k][0]}" max="${d.limits[k][1]}" value="${d.settings[k]}" required>${h?`<small>${esc(h)}</small>`:`<small>Por defecto: ${d.defaults[k]}</small>`}</div>`).join('')}
        <div class="form-actions full"><button class="btn" type="button" id="ret-run">Guardar y aplicar ahora</button><button class="btn btn-primary" type="submit">Guardar plazos</button></div></form>
      ${L?`<p class="adl-det" id="ret-last">Última ejecución ${esc(L.date)}: ${L.warned} avisos de inactividad, ${L.accounts_deleted} cuentas eliminadas, ${L.documents_deleted} documentos, ${L.notices_deleted} avisos y ${L.audit_deleted} entradas del registro borradas.</p>`:'<p class="adl-det">Todavía no se ha ejecutado.</p>'}`;
    const send=async run=>{ const data={run_now:run}; $$('#ret-form input[data-k]').forEach(i=>data[i.dataset.k]=i.value);
      try{ await postJSON('/api/admin/retention',data); toast(run?'Plazos guardados y aplicados.':'Plazos guardados.'); renderRetentionCard(mount); }catch(err){ toast(err.message); } };
    $('#ret-form').onsubmit=e=>{ e.preventDefault(); send(false); };
    $('#ret-run').onclick=()=>{ if($('#ret-form').reportValidity()&&confirm('Se borrarán ahora los datos que hayan superado los plazos. ¿Continuar?')) send(true); };
  }
  // Administración → Descripciones de puntos: the own texts written from the data of each point, to review one by one.
  // Administración → Medios: credit and origin/licence of every image the platform publishes.
  // ---------------------------------------------------------------- v50.37 · Fase 6: plans, tools and team
  const PLAN_STATUS={trial:['Prueba gratuita','warn'],active:['Activo','good'],expired:['Terminado','bad'],free:['Ficha gratuita','muted']};
  function openInfoRequest({center_id=null,provider_user_id=null,name=''}){
    const me=state.me?.user; const esc=escapeHtml;
    const {el,close}=wdOpenModal({id:'info-request',title:'Solicitar información',subtitle:esc(name),
      body:`<p class="muted" style="margin-top:0">Este centro todavía no tiene reserva online en WORLDIVES. Le enviamos tu mensaje y te contestará directamente.</p>
        <form id="ir-form" class="form-grid"><div class="field"><label for="ir-name">Tu nombre</label><input id="ir-name" required maxlength="120" value="${esc(me?.fullname||'')}" autocomplete="name"></div>
        <div class="field"><label for="ir-email">Tu email</label><input id="ir-email" type="email" required maxlength="160" value="${esc(me?.email&&!/\.local$/.test(me.email)?me.email:'')}" autocomplete="email"></div>
        <div class="field"><label for="ir-phone">Teléfono (opcional)</label><input id="ir-phone" type="tel" maxlength="40" autocomplete="tel"></div>
        <div class="field"><label for="ir-date">Fecha deseada (opcional)</label><input id="ir-date" type="date" min="${new Date().toISOString().slice(0,10)}"></div>
        <div class="field"><label for="ir-pax">Personas</label><input id="ir-pax" type="number" min="1" max="99" value="1"></div>
        <div class="field full"><label for="ir-msg">¿Qué necesitas?</label><textarea id="ir-msg" rows="4" minlength="10" maxlength="2000" required placeholder="Actividad, nivel, dudas…"></textarea></div>
        <label class="lg-check full"><input type="checkbox" id="ir-ok" required> <span>Acepto que WORLDIVES envíe estos datos al centro para que me conteste (<a href="#/legal/privacidad" target="_blank" rel="noopener">privacidad</a>).</span></label></form>`,
      footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="ir-send">Enviar solicitud</button>'});
    translateTree(el);
    $('#ir-send',el).onclick=async()=>{ if(!$('#ir-form',el).reportValidity()) return; const b=$('#ir-send',el); b.disabled=true;
      try{ await postJSON('/api/info-requests',{center_id,provider_user_id,name:$('#ir-name',el).value,email:$('#ir-email',el).value,phone:$('#ir-phone',el).value,wanted_date:$('#ir-date',el).value,
          participants:$('#ir-pax',el).value,message:$('#ir-msg',el).value,accept_privacy:$('#ir-ok',el).checked,lang:currentLanguage()});
        delete el.dataset.dirty; close(); toast('Solicitud enviada. El centro te contestará directamente.'); }
      catch(err){ toast(err.message); b.disabled=false; } };
  }
  function planFeatureList(p,labels,limits){ const esc=escapeHtml;
    return `<ul class="pl-feats">${Object.entries(labels).map(([k,l])=>`<li class="${p.features[k]?'is-on':'is-off'}">${wdIcon(p.features[k]?'check':'extra',14)} ${esc(l)}</li>`).join('')}
      ${Object.entries(limits||{}).map(([k,l])=>`<li class="is-on">${wdIcon('check',14)} ${esc(l)}: ${Number(p.limits?.[k]||0)?Number(p.limits[k]):'sin límite'}</li>`).join('')}</ul>`; }
  async function renderPlans(){
    let d; try{ d=await api('/api/plans'); }catch(err){ setApp(`<section class="page"><div class="empty">${escapeHtml(err.message)}</div></section>`); return; }
    const esc=escapeHtml; const mine=state.me?.plan;
    setApp(`<section class="page pl-page"><p class="eyebrow">Para centros y profesionales</p><h1>Planes de WORLDIVES</h1>
      <p class="lead">Sin comisión por reserva: cobras directamente en tu cuenta de Stripe. Solo pagas, si quieres, la cuota anual de tu plan.${d.trial_days?` Al aprobar tu alta tienes ${d.trial_days} días de prueba gratuita.`:''}</p>
      <div class="pl-grid">${d.items.map(p=>`<article class="pl-card ${mine?.code===p.code?'is-current':''}"><h2>${esc(p.name)}</h2><p class="pl-price">${p.code==='free'?'Gratis':(p.price_year?`${wdMoney(p.price_year,p.currency)} <small>/ año</small>`:'<small>Precio a consultar</small>')}</p>
        <p class="muted">${esc(p.description||'')}</p>${planFeatureList(p,d.features,d.limits)}${mine?.code===p.code?'<span class="status good">Tu plan</span>':''}</article>`).join('')}</div>
      <div class="notice"><strong>Siempre, en cualquier plan:</strong> tus reservas actuales se atienden con normalidad y puedes exportar tus datos. Si un plan termina, tu ficha sigue publicada como ficha gratuita.</div>
      ${state.me?.user&&['center','freelance'].includes(state.me.user.role)?'<p><a class="btn btn-primary" href="#/admin?tab=plan">Gestionar mi plan</a></p>':'<p><a class="btn btn-primary" href="#/registro">Dar de alta mi centro</a></p>'}</section>`);
  }
  async function renderMyPlanRoute(params){
    const sid=params?.get?.('pago'); if(sid){ try{ await postJSON('/api/provider/plan/sync',{session_id:sid}); toast('Pago recibido. Tu plan está activo.'); }catch(err){ toast(err.message); } }
    location.hash='#/admin?tab=plan';
  }
  async function renderMyPlan(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d,pl; try{ [d,pl]=await Promise.all([api('/api/provider/plan'),api('/api/plans')]); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    const p=d.plan; const st=PLAN_STATUS[p.status]||[p.status,''];
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Mi plan</p><h2>${esc(p.name)} <span class="status ${st[1]}">${esc(st[0])}</span></h2>
      <p>${p.expires_at?`${p.status==='trial'?'La prueba gratuita termina':'Activo hasta'} el <b>${esc(wdLegalDate(p.expires_at))}</b>.`:'Ficha gratuita: tu centro aparece en el catálogo y recibe solicitudes de información.'} Las reservas que ya tienes se atienden siempre y puedes exportar tus datos en cualquier plan.</p></div><a class="btn" href="#/planes">Comparar planes</a></div>
      ${planFeatureList(p,pl.features,pl.limits)}
      ${p.exceptions.length?`<p class="adl-det">Excepciones de la administración: ${p.exceptions.map(e=>`${esc(pl.features[e.feature]||e.feature)} ${e.enabled?'activada':'desactivada'} (${esc(e.reason)})`).join(' · ')}</p>`:''}
      <h3 class="adl-h">Renovar o cambiar de plan</h3>
      <div class="pl-grid is-compact">${pl.items.filter(x=>x.code!=='free').map(x=>`<article class="pl-card"><h3>${esc(x.name)}</h3><p class="pl-price">${x.price_year?`${wdMoney(x.price_year,x.currency)} <small>/ año</small>`:'<small>Precio a consultar</small>'}</p>
        ${x.price_year&&d.online_payment&&d.role==='owner'?`<button type="button" class="btn btn-primary pl-pay" data-plan="${esc(x.code)}">${p.code===x.code?'Renovar 12 meses':'Contratar 12 meses'}</button>`:`<p class="adl-det">${d.role!=='owner'?'Solo el propietario puede contratar.':'Escríbenos para activarlo por transferencia.'}</p>`}</article>`).join('')}</div>
      ${d.payments.length?`<h3 class="adl-h">Pagos de la cuota</h3><div class="table-wrap"><table class="data-table"><thead><tr><th>Fecha</th><th>Plan</th><th>Importe</th><th>Forma</th><th>Periodo</th><th>Estado</th></tr></thead><tbody>${d.payments.map(x=>`<tr><td>${esc((x.paid_at||x.created_at||'').slice(0,10))}</td><td>${esc(x.plan_code)}</td><td>${wdMoney(x.amount,x.currency)}</td><td>${x.method==='stripe'?'Tarjeta':'Manual'}</td><td>${esc([x.period_start,x.period_end].filter(Boolean).join(' → '))}</td><td>${esc({paid:'Pagado',pending:'En curso',failed:'No completado'}[x.status]||x.status)}</td></tr>`).join('')}</tbody></table></div>`:''}</section>`;
    $$('.pl-pay',mount).forEach(b=>b.onclick=async()=>{ b.disabled=true; try{ const r=await postJSON('/api/provider/plan/checkout',{plan:b.dataset.plan}); location.href=r.checkout_url; }catch(err){ toast(err.message); b.disabled=false; } });
  }
  async function renderFiscalCard(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let f; try{ f=await api('/api/provider/fiscal'); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    const v=k=>esc(f[k]||''); const miss=new Set(f.missing);
    const exp=f.insurance_expires_at; const days=exp?Math.round((new Date(exp+'T12:00:00')-new Date())/864e5):null;
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Datos fiscales y verificación</p><h2>Datos del prestador (DAC7) y seguro</h2>
      <p>La normativa europea DAC7 obliga a las plataformas a identificar a los prestadores que cobran a través de ellas. Estos datos solo los ve la administración de WORLDIVES y se usan para la declaración anual y para tus justificantes.</p></div></div>
      ${f.missing.length?`<div class="notice warning"><strong>Faltan datos:</strong> completa los campos marcados.</div>`:'<div class="notice good"><strong>Datos completos.</strong></div>'}
      ${days!==null&&days<0?'<div class="notice warning"><strong>Tu seguro de responsabilidad civil ha caducado.</strong> Actualiza la póliza.</div>':days!==null&&days<=30?`<div class="notice warning"><strong>Tu seguro caduca en ${days} días.</strong></div>`:''}
      <form id="fi-form" class="form-grid">
        <div class="field"><label for="fi-type">Tipo de prestador</label><select id="fi-type"><option value="">Elige…</option><option value="company" ${f.entity_type==='company'?'selected':''}>Empresa (persona jurídica)</option><option value="individual" ${f.entity_type==='individual'?'selected':''}>Autónomo (persona física)</option></select></div>
        <div class="field"><label for="fi-legal">Razón social o nombre completo</label><input id="fi-legal" maxlength="160" value="${v('legal_name')}" ${miss.has('legal_name')?'aria-invalid="true"':''}></div>
        <div class="field"><label for="fi-tax">NIF / TIN</label><input id="fi-tax" maxlength="40" value="${v('tax_id')}" ${miss.has('tax_id')?'aria-invalid="true"':''}></div>
        <div class="field"><label for="fi-country">País emisor del NIF</label><input id="fi-country" maxlength="2" placeholder="ES" value="${v('tax_id_country')}" style="text-transform:uppercase" ${miss.has('tax_id_country')?'aria-invalid="true"':''}></div>
        <div class="field" data-for="company"><label for="fi-reg">Número de registro mercantil</label><input id="fi-reg" maxlength="160" value="${v('registration_number')}"></div>
        <div class="field" data-for="individual"><label for="fi-birth">Fecha de nacimiento</label><input id="fi-birth" type="date" value="${v('birth_date')}"></div>
        <div class="field full"><label for="fi-addr">Dirección fiscal</label><input id="fi-addr" maxlength="300" value="${v('fiscal_address')}"></div>
        <div class="field full"><p class="adl-det"><b>Cuenta de cobro:</b> ${f.payout_account?`Stripe · ${esc(f.payout_account)}`:'Sin cuenta de cobro conectada (Cobros y pagos).'}</p></div>
        <label class="lg-check full"><input type="checkbox" id="fi-lic" ${f.declares_licences?'checked':''}> <span>Declaro que el centro tiene las licencias y autorizaciones necesarias para su actividad.</span></label>
        <label class="lg-check full"><input type="checkbox" id="fi-staff" ${f.declares_qualified_staff?'checked':''}> <span>Declaro que el personal que guía y enseña tiene la titulación profesional exigida.</span></label>
        <div class="field full"><label for="fi-licnote">Licencias y titulaciones (opcional)</label><input id="fi-licnote" maxlength="300" value="${v('licences_note')}" placeholder="Ej.: autorización de la Capitanía, centro PADI 5 estrellas…"></div>
        <h3 class="adl-h full">Seguro de responsabilidad civil</h3>
        <div class="field"><label for="fi-ins">Aseguradora</label><input id="fi-ins" maxlength="160" value="${v('insurance_company')}"></div>
        <div class="field"><label for="fi-pol">Número de póliza</label><input id="fi-pol" maxlength="160" value="${v('insurance_policy')}"></div>
        <div class="field"><label for="fi-exp">Caduca el</label><input id="fi-exp" type="date" value="${v('insurance_expires_at')}" ${miss.has('insurance_expires_at')?'aria-invalid="true"':''}></div>
        <div class="field"><label for="fi-doc">Certificado de la póliza (PDF o imagen)</label><input id="fi-doc" type="file" accept="application/pdf,image/jpeg,image/png,image/webp"><small>${f.has_insurance_doc?'Ya hay un certificado subido. Si subes otro, lo sustituye.':'Opcional. Solo lo ve la administración.'}</small></div>
        <div class="form-actions full"><button class="btn btn-primary" type="submit">Guardar</button></div></form></section>`;
    const sync=()=>{ const t=$('#fi-type').value; $$('#fi-form [data-for]').forEach(x=>x.hidden=x.dataset.for!==t); }; $('#fi-type').onchange=sync; sync();
    $('#fi-form').onsubmit=async e=>{ e.preventDefault();
      try{ await postJSON('/api/provider/fiscal',{entity_type:$('#fi-type').value,legal_name:$('#fi-legal').value,tax_id:$('#fi-tax').value,tax_id_country:$('#fi-country').value,
          registration_number:$('#fi-reg').value,birth_date:$('#fi-birth').value,fiscal_address:$('#fi-addr').value,declares_licences:$('#fi-lic').checked,
          declares_qualified_staff:$('#fi-staff').checked,licences_note:$('#fi-licnote').value,insurance_company:$('#fi-ins').value,insurance_policy:$('#fi-pol').value,insurance_expires_at:$('#fi-exp').value});
        const file=$('#fi-doc').files[0]; if(file) await upload('/api/provider/insurance-doc',file);
        toast('Datos guardados.'); renderFiscalCard(mountId); }catch(err){ toast(err.message); } };
  }
  async function renderInfoRequests(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/center/info-requests'); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Solicitudes de información</p><h2>Mensajes de buceadores interesados</h2><p>Contesta directamente por email o teléfono. Te llegan también por email.</p></div></div>
      ${d.items.length?`<div class="ir-list">${d.items.map(r=>`<article class="ir-item ${r.read_at?'':'is-new'}" data-id="${r.id}"><header><b>${esc(r.name)}</b> <small>${esc((r.created_at||'').slice(0,16).replace('T',' '))}</small>${r.read_at?'':'<span class="status warn">Nueva</span>'}${r.status==='answered'?'<span class="status good">Contestada</span>':''}</header>
        <p>${esc(r.message)}</p><p class="adl-det"><a href="mailto:${esc(r.email)}">${esc(r.email)}</a>${r.phone?` · <a href="tel:${esc(r.phone.replace(/\s+/g,''))}">${esc(r.phone)}</a>`:''}${r.wanted_date?` · ${esc(wdLegalDate(r.wanted_date))}`:''}${r.participants?` · ${r.participants} pax`:''}</p>
        <div class="form-actions"><button type="button" class="btn ir-read" data-answered="0">Marcar como leída</button><button type="button" class="btn ir-read" data-answered="1">Marcar como contestada</button></div></article>`).join('')}</div>`:'<div class="empty">Todavía no hay solicitudes.</div>'}</section>`;
    $$('.ir-read',mount).forEach(b=>b.onclick=async()=>{ try{ await postJSON('/api/center/info-requests/read',{id:+b.closest('.ir-item').dataset.id,answered:b.dataset.answered==='1'}); renderInfoRequests(mountId); }catch(err){ toast(err.message); } });
  }
  async function renderProviderStats(mountId,days=30){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/provider/stats?days='+days); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    const t=d.totals, z=d.zone; const max=Math.max(1,...d.series.map(x=>x.views));
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Estadísticas</p><h2>Cómo te encuentran los buceadores</h2><p>Datos agregados, sin datos personales. Disponibles en todos los planes.</p></div>
      <label class="field" style="min-width:160px"><span>Periodo</span><select id="ps-days">${[30,90,365].map(n=>`<option value="${n}" ${n===days?'selected':''}>Últimos ${n} días</option>`).join('')}</select></label></div>
      <div class="acc-kpis">${accKpi('eye',t.views,'visitas a tu ficha')}${accKpi('calendar',t.book_clicks,'clics en «Reservar»')}${accKpi('message',t.info_requests,'solicitudes de información')}</div>
      ${z?`<div class="notice">Media de los ${z.providers} centros de ${esc(z.name)}: <b>${z.views}</b> visitas, <b>${z.book_clicks}</b> clics en «Reservar» y <b>${z.info_requests}</b> solicitudes.</div>`:'<p class="adl-det">La comparación con tu zona aparece cuando hay al menos 3 centros más en ella.</p>'}
      ${d.series.length?`<div class="ps-chart" role="img" aria-label="Visitas por día">${d.series.map(x=>`<span style="height:${Math.round(x.views*100/max)}%" title="${esc(x.day)}: ${x.views}"></span>`).join('')}</div>`:''}</section>`;
    $('#ps-days').onchange=e=>renderProviderStats(mountId,+e.target.value);
  }
  async function renderProviderTools(mountId,isCenter){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    const [ical,widget]=await Promise.all([api('/api/provider/ical').catch(e=>({error:e.message,plan:e.data?.plan_required})),api('/api/provider/widget').catch(()=>null)]);
    const owner=(state.me?.member_role||'owner')==='owner';
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Herramientas</p><h2>Exportar, calendario, widget e importación</h2></div></div>
      <h3 class="adl-h">Exportar mis datos (CSV)</h3><p class="adl-det">Disponible siempre, en cualquier plan. Se abre en Excel, Numbers o Google Sheets.</p>
      <div class="tl-row">${[['clients','Clientes'],['bookings','Reservas'],['services','Servicios'],...(owner?[['payments','Pagos']]:[])].map(([k,l])=>`<a class="btn" href="/api/center/export?kind=${k}" download>${wdIcon('download',15)} ${l}</a>`).join('')}</div>
      <h3 class="adl-h">Calendario (iCal)</h3>
      ${ical.error?`<p class="adl-det">${esc(ical.error)} ${ical.plan?'<a href="#/planes">Ver planes</a>':''}</p>`:`<p class="adl-det">Suscríbete desde Google Calendar, Apple Calendar u Outlook con esta dirección privada. Quien la tenga ve tu agenda: si la compartes por error, genera otra.</p>
        <div class="tl-row"><input id="tl-ical" readonly value="${esc(ical.url||'')}" placeholder="Genera tu dirección privada" aria-label="Dirección del calendario"><button type="button" class="btn" id="tl-ical-copy" ${ical.url?'':'hidden'}>Copiar</button>${owner?`<button type="button" class="btn" id="tl-ical-new">${ical.url?'Generar otra':'Generar dirección'}</button>`:''}</div>`}
      ${widget?`<h3 class="adl-h">Reservas desde tu web y redes</h3>
        <div class="field"><label for="tl-link">Enlace directo (Instagram, Google, tu web)</label><div class="tl-row"><input id="tl-link" readonly value="${esc(widget.link)}"><button type="button" class="btn tl-copy" data-src="tl-link">Copiar</button><a class="btn" href="${esc(widget.whatsapp)}" target="_blank" rel="noopener">Compartir por WhatsApp</a></div></div>
        ${widget.widget?`<div class="field"><label for="tl-iframe">Widget para pegar en tu web</label><div class="tl-row"><textarea id="tl-iframe" rows="3" readonly>${esc(widget.iframe)}</textarea><button type="button" class="btn tl-copy" data-src="tl-iframe">Copiar</button></div></div>`:'<p class="adl-det">El widget para tu web está incluido en los planes con motor de reservas. <a href="#/planes">Ver planes</a></p>'}`:''}
      ${isCenter&&owner?`<h3 class="adl-h">Importar clientes (CSV)</h3><p class="adl-det">Usa la <a href="/api/center/import/template" download>plantilla</a> (nombre, email, teléfono, titulación, notas). Antes de importar verás una vista previa con los duplicados. Los clientes importados son solo tuyos: no reciben correos de WORLDIVES.</p>
        <div class="tl-row"><input type="file" id="tl-csv" accept=".csv,text/csv" aria-label="Archivo CSV de clientes"><button type="button" class="btn" id="tl-preview">Vista previa</button></div><div id="tl-import"></div>`:''}</section>`;
    $$('.tl-copy',mount).forEach(b=>b.onclick=()=>{ const el=$('#'+b.dataset.src); el.select(); navigator.clipboard?.writeText(el.value).catch(()=>{}); toast('Copiado.'); });
    $('#tl-ical-copy')?.addEventListener('click',()=>{ navigator.clipboard?.writeText($('#tl-ical').value).catch(()=>{}); toast('Copiado.'); });
    $('#tl-ical-new')?.addEventListener('click',async()=>{ if($('#tl-ical').value&&!confirm('La dirección actual dejará de funcionar. ¿Generar otra?')) return; try{ await postJSON('/api/provider/ical/regenerate',{}); renderProviderTools(mountId,isCenter); }catch(err){ toast(err.message); } });
    let csvText='';
    $('#tl-preview')?.addEventListener('click',async()=>{ const f=$('#tl-csv').files[0]; if(!f){ toast('Elige el archivo CSV.'); return; } csvText=await f.text();
      try{ const r=await postJSON('/api/center/import',{csv:csvText}); const S={new:['Nuevo','good'],duplicate:['Duplicado','warn'],error:['Error','bad']};
        $('#tl-import').innerHTML=`<p><b>${r.summary.new}</b> nuevos · <b>${r.summary.duplicate}</b> duplicados · <b>${r.summary.error}</b> con errores</p><div class="table-wrap"><table class="data-table"><thead><tr><th>Línea</th><th>Nombre</th><th>Email</th><th>Teléfono</th><th>Estado</th></tr></thead><tbody>${r.rows.slice(0,300).map(x=>`<tr><td>${x.line}</td><td>${esc(x.name)}</td><td>${esc(x.email)}</td><td>${esc(x.phone)}</td><td><span class="status ${S[x.status][1]}">${S[x.status][0]}</span> ${esc(x.note)}</td></tr>`).join('')}</tbody></table></div>
          ${r.summary.new?`<div class="form-actions"><button type="button" class="btn btn-primary" id="tl-confirm">Importar ${r.summary.new} clientes</button></div>`:''}`;
        $('#tl-confirm')?.addEventListener('click',async()=>{ try{ const c=await postJSON('/api/center/import',{csv:csvText,confirm:true}); toast(`${c.created} clientes importados.`); $('#tl-import').innerHTML=''; }catch(err){ toast(err.message); } });
      }catch(err){ toast(err.message); } });
  }
  async function renderTeam(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/center/team'); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    const me=state.me?.user?.id; const R=d.roles;
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Equipo</p><h2>Personas que gestionan el centro</h2>
      <p><b>Propietario</b>: todo, incluidos cobros, plan y equipo. <b>Recepción</b>: reservas, clientes, servicios y salidas. <b>Instructor</b>: ve el planning y las reservas, sin cambiar nada.</p></div></div>
      <div class="table-wrap"><table class="data-table"><thead><tr><th>Persona</th><th>Perfil</th><th></th></tr></thead><tbody>${d.members.map(m=>`<tr><td><b>${esc(m.fullname)}</b><div class="adl-det">${esc(m.email)}</div></td>
        <td><label class="sr-only" for="tm-r-${m.id}">Perfil de ${esc(m.fullname)}</label><select id="tm-r-${m.id}" class="tm-role" data-id="${m.id}" ${m.id===me?'disabled':''}>${Object.entries(R).map(([k,l])=>`<option value="${k}" ${k===m.member_role?'selected':''}>${esc(l)}</option>`).join('')}</select></td>
        <td>${m.id===me?'<small>Tú</small>':`<button type="button" class="btn tm-remove" data-id="${m.id}">Quitar</button>`}</td></tr>`).join('')}</tbody></table></div>
      ${d.invites.length?`<h3 class="adl-h">Invitaciones pendientes</h3><ul class="tm-inv">${d.invites.map(i=>`<li>${esc(i.email)} · ${esc(R[i.member_role])} · caduca ${esc(wdLegalDate(i.expires_at))} <button type="button" class="btn-link tm-revoke" data-id="${i.id}">Anular</button></li>`).join('')}</ul>`:''}
      ${d.team_feature?`<h3 class="adl-h">Invitar a alguien</h3><form id="tm-form" class="form-grid"><div class="field"><label for="tm-email">Email</label><input id="tm-email" type="email" required maxlength="160"></div>
        <div class="field"><label for="tm-role">Perfil</label><select id="tm-role"><option value="reception">Recepción</option><option value="instructor">Instructor</option><option value="owner">Propietario</option></select></div>
        <div class="form-actions full"><button class="btn btn-primary" type="submit">Enviar invitación</button></div></form><p class="adl-det">${d.limit?`Tu plan permite ${d.limit} personas.`:''}</p>`:'<p class="adl-det">El equipo está incluido en el plan Pro. <a href="#/planes">Ver planes</a></p>'}</section>`;
    $('#tm-form')?.addEventListener('submit',async e=>{ e.preventDefault(); try{ await postJSON('/api/center/team/invite',{email:$('#tm-email').value,member_role:$('#tm-role').value}); toast('Invitación enviada.'); renderTeam(mountId); }catch(err){ toast(err.message); } });
    $$('.tm-role',mount).forEach(x=>x.onchange=async()=>{ try{ await postJSON('/api/center/team/role',{user_id:+x.dataset.id,member_role:x.value}); toast('Perfil cambiado.'); }catch(err){ toast(err.message); renderTeam(mountId); } });
    $$('.tm-remove',mount).forEach(b=>b.onclick=async()=>{ if(!confirm('Esta persona dejará de tener acceso al centro. ¿Continuar?')) return; try{ await postJSON('/api/center/team/remove',{user_id:+b.dataset.id}); renderTeam(mountId); }catch(err){ toast(err.message); } });
    $$('.tm-revoke',mount).forEach(b=>b.onclick=async()=>{ try{ await postJSON('/api/center/team/invite/revoke',{id:+b.dataset.id}); renderTeam(mountId); }catch(err){ toast(err.message); } });
  }
  const ACTIVITY_LABELS={booking_created:'Reserva creada',booking_status_changed:'Estado de reserva cambiado',service_created:'Servicio creado',service_updated:'Servicio modificado',slot_created:'Salida creada',
    center_profile_updated:'Datos del centro modificados',provider_fiscal_data_updated:'Datos fiscales modificados',team_invited:'Invitación al equipo',team_role_changed:'Perfil del equipo cambiado',
    team_member_removed:'Persona quitada del equipo',team_joined:'Se une al equipo',clients_imported:'Clientes importados',provider_export:'Exportación de datos',ical_regenerated:'Nueva dirección de calendario',
    review_reply_saved:'Respuesta a una reseña',booking_rescheduled:'Reserva cambiada de salida',refund_issued:'Devolución',points_granted:'Puntos concedidos'};
  async function renderActivity(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/center/activity'); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Registro de actividad</p><h2>Quién ha hecho qué en el centro</h2></div></div>
      ${d.items.length?`<div class="table-wrap"><table class="data-table"><thead><tr><th>Fecha</th><th>Persona</th><th>Acción</th></tr></thead><tbody>${d.items.map(x=>`<tr><td>${esc((x.created_at||'').slice(0,16).replace('T',' '))}</td><td>${esc(x.fullname||'—')}</td><td>${esc(ACTIVITY_LABELS[x.action]||x.action.replace(/_/g,' '))}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">Todavía no hay actividad.</div>'}</section>`;
  }
  async function renderTeamJoin(params){
    const token=params?.get?.('token')||''; const esc=escapeHtml;
    let inv; try{ inv=await api('/api/team/invite?token='+encodeURIComponent(token)); }catch(err){ setApp(authCard('Invitación al equipo',`<div class="notice warning">${esc(err.message)}</div>`)); return; }
    const me=state.me?.user;
    setApp(authCard('Únete al equipo de '+esc(inv.center),`<p class="lead" style="font-size:15px">Te han invitado con el perfil de <b>${esc(inv.role_label)}</b> (${esc(inv.email)}).</p>
      ${me?`<div class="form-actions"><button class="btn btn-primary" id="tj-ok" type="button">Aceptar con mi cuenta</button></div>`:`<form id="tj-form"><div class="field"><label for="tj-name">Nombre y apellidos</label><input id="tj-name" required maxlength="120" autocomplete="name"></div>
        <div class="field"><label for="tj-user">Usuario</label><input id="tj-user" required maxlength="40" autocomplete="username"></div>
        <div class="field"><label for="tj-pass">Contraseña</label><input id="tj-pass" type="password" minlength="10" required autocomplete="new-password"><small>Mínimo 10 caracteres.</small></div>
        <label class="lg-check"><input type="checkbox" id="tj-terms" required> <span>Acepto las <a href="#/legal/condiciones-centros" target="_blank" rel="noopener">condiciones para centros</a> y la <a href="#/legal/privacidad" target="_blank" rel="noopener">política de privacidad</a>.</span></label>
        <div class="form-actions"><button class="btn btn-primary" type="submit">Crear mi cuenta y unirme</button></div></form><p style="font-size:13px">¿Ya tienes cuenta con ese email? <a href="#/login?next=${encodeURIComponent(location.hash)}">Inicia sesión</a>.</p>`}`));
    const done=async()=>{ await loadMe(); toast('Ya formas parte del equipo.'); location.hash='#/admin'; };
    $('#tj-ok')?.addEventListener('click',async()=>{ try{ await postJSON('/api/team/join',{token}); done(); }catch(err){ toast(err.message); } });
    $('#tj-form')?.addEventListener('submit',async e=>{ e.preventDefault(); try{ await postJSON('/api/team/join',{token,fullname:$('#tj-name').value,username:$('#tj-user').value,password:$('#tj-pass').value,accept_terms:$('#tj-terms').checked}); done(); }catch(err){ toast(err.message); } });
  }
  // Administración → Planes
  async function renderAdminPlans(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/admin/plans'); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    const y=new Date().getFullYear();
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Planes</p><h2>Planes, cuotas y excepciones</h2><p>El precio es la cuota anual (pendiente de confirmar con la gestoría si se muestra con IVA incluido). Los cambios valen desde ya para las funciones; los precios, para los pagos nuevos.</p></div></div>
      <div class="ap-plans">${d.plans.map(p=>`<form class="ap-plan pl-card" data-code="${esc(p.code)}"><h3>${esc(p.code)}</h3>
        <div class="field"><label for="ap-n-${p.code}">Nombre</label><input id="ap-n-${p.code}" name="name" value="${esc(p.name)}" maxlength="80" required></div>
        <div class="field"><label for="ap-p-${p.code}">Precio anual</label><input id="ap-p-${p.code}" name="price" inputmode="decimal" value="${p.price_year??''}" ${p.code==='free'?'disabled':''} placeholder="Sin definir"></div>
        <div class="field"><label for="ap-c-${p.code}">Moneda</label><input id="ap-c-${p.code}" name="currency" value="${esc(p.currency)}" maxlength="3"></div>
        <div class="field"><label for="ap-d-${p.code}">Descripción</label><textarea id="ap-d-${p.code}" name="description" rows="2" maxlength="500">${esc(p.description||'')}</textarea></div>
        <fieldset><legend>Funciones</legend>${Object.entries(d.features).map(([k,l])=>`<label class="lg-check"><input type="checkbox" name="f_${k}" ${p.features[k]?'checked':''} ${p.code==='free'&&['online_bookings','online_payments'].includes(k)?'disabled':''}> <span>${esc(l)}</span></label>`).join('')}</fieldset>
        ${Object.entries(d.limits).map(([k,l])=>`<div class="field"><label for="ap-l-${p.code}-${k}">${esc(l)} (0 = sin límite)</label><input id="ap-l-${p.code}-${k}" name="l_${k}" type="number" min="0" value="${Number(p.limits[k]||0)}"></div>`).join('')}
        ${p.code!=='free'?`<label class="lg-check"><input type="checkbox" name="active" ${p.active?'checked':''}> <span>Plan disponible</span></label>`:''}
        <button class="btn btn-primary" type="submit">Guardar</button></form>`).join('')}</div>
      <h3 class="adl-h">Prueba gratuita</h3><form id="ap-trial" class="form-grid"><div class="field"><label for="ap-td">Días de prueba al aprobar un alta</label><input id="ap-td" type="number" min="0" max="365" value="${d.settings.trial_days}"></div>
        <div class="field"><label for="ap-tp">Plan de la prueba</label><select id="ap-tp">${d.plans.filter(p=>p.code!=='free').map(p=>`<option value="${esc(p.code)}" ${p.code===d.settings.trial_plan?'selected':''}>${esc(p.name)}</option>`).join('')}</select></div>
        <div class="form-actions full"><button class="btn btn-primary" type="submit">Guardar</button></div></form>
      <h3 class="adl-h">Informe DAC7</h3><p class="adl-det">Importes cobrados a través de la web por cada prestador y trimestre, número de actividades y comisiones (0). Revísalo con la gestoría antes de presentar el modelo 238.</p>
      <div class="tl-row"><label class="sr-only" for="ap-year">Año</label><select id="ap-year">${[y,y-1,y-2].map(v=>`<option ${v===y-1?'selected':''}>${v}</option>`).join('')}</select><a class="btn" id="ap-dac7" href="/api/admin/dac7?format=csv&year=${y-1}" download>${wdIcon('download',15)} Descargar CSV</a></div>
      <h3 class="adl-h">Centros y profesionales</h3>
      <div class="table-wrap"><table class="data-table"><thead><tr><th>Prestador</th><th>Plan</th><th>Hasta</th><th>Datos fiscales</th><th></th></tr></thead><tbody>${d.providers.map((p,i)=>`<tr><td><b>${esc(p.name)}</b><div class="adl-det">${p.type==='center'?'Centro':'Profesional'}${p.place?' · '+esc(p.place):''}</div></td>
        <td>${esc(p.plan.name)} <span class="status ${(PLAN_STATUS[p.plan.status]||[])[1]||''}">${esc((PLAN_STATUS[p.plan.status]||[p.plan.status])[0])}</span>${p.plan.exceptions.length?`<div class="adl-det">${p.plan.exceptions.length} excepciones</div>`:''}</td>
        <td>${esc(p.plan.expires_at||'—')}</td><td>${p.fiscal_missing.length?`<span class="status warn">Faltan ${p.fiscal_missing.length}</span>`:'<span class="status good">Completos</span>'}</td>
        <td><button type="button" class="btn ap-manage" data-i="${i}">Gestionar</button></td></tr>`).join('')}</tbody></table></div>
      ${d.payments.length?`<h3 class="adl-h">Últimos pagos de cuotas</h3><div class="table-wrap"><table class="data-table"><thead><tr><th>Fecha</th><th>Prestador</th><th>Plan</th><th>Importe</th><th>Forma</th><th>Estado</th></tr></thead><tbody>${d.payments.map(x=>`<tr><td>${esc((x.paid_at||x.created_at||'').slice(0,10))}</td><td>${esc(x.provider_type)} #${x.provider_id}</td><td>${esc(x.plan_code)}</td><td>${wdMoney(x.amount,x.currency)}</td><td>${esc(x.method)}</td><td>${esc(x.status)}</td></tr>`).join('')}</tbody></table></div>`:''}</section>`;
    $$('.ap-plan',mount).forEach(f=>f.onsubmit=async e=>{ e.preventDefault(); const code=f.dataset.code; const g=n=>f.elements[n];
      const data={code,name:g('name').value,price_year:g('price').value,currency:g('currency').value,description:g('description').value,features:{},limits:{},active:g('active')?g('active').checked:true};
      Object.keys(d.features).forEach(k=>data.features[k]=g('f_'+k).checked); Object.keys(d.limits).forEach(k=>data.limits[k]=g('l_'+k).value);
      try{ await postJSON('/api/admin/plans/save',data); toast('Plan guardado.'); }catch(err){ toast(err.message); } });
    $('#ap-trial').onsubmit=async e=>{ e.preventDefault(); try{ await postJSON('/api/admin/plans/settings',{trial_days:$('#ap-td').value,trial_plan:$('#ap-tp').value}); toast('Prueba gratuita guardada.'); }catch(err){ toast(err.message); } };
    $('#ap-year').onchange=e=>{ $('#ap-dac7').href='/api/admin/dac7?format=csv&year='+e.target.value; };
    $$('.ap-manage',mount).forEach(b=>b.onclick=()=>{ const p=d.providers[+b.dataset.i];
      const {el,close}=wdOpenModal({id:'plan-manage',title:esc(p.name),subtitle:`Plan actual: ${esc(p.plan.name)}${p.plan.expires_at?' hasta '+esc(p.plan.expires_at):''}`,
        body:`<h3 class="adl-h">Activar un plan (pago manual)</h3><div class="form-grid"><div class="field"><label for="pm-plan">Plan</label><select id="pm-plan">${d.plans.map(x=>`<option value="${esc(x.code)}">${esc(x.name)}</option>`).join('')}</select></div>
          <div class="field"><label for="pm-months">Meses</label><input id="pm-months" type="number" min="1" max="36" value="12"></div><div class="field"><label for="pm-amount">Importe cobrado</label><input id="pm-amount" inputmode="decimal" placeholder="Precio del plan"></div>
          <div class="field full"><label for="pm-note">Nota (obligatoria)</label><input id="pm-note" maxlength="500" placeholder="Ej.: transferencia del 12/10, factura 2026-031"></div>
          <div class="form-actions full"><button type="button" class="btn btn-primary" id="pm-assign">Guardar</button></div></div>
          <h3 class="adl-h">Excepciones</h3>${p.plan.exceptions.length?`<ul>${p.plan.exceptions.map(x=>`<li>${esc(d.features[x.feature]||x.feature)}: ${x.enabled?'activada':'desactivada'} — ${esc(x.reason)} <button type="button" class="btn-link pm-unexc" data-id="${x.id}">Quitar</button></li>`).join('')}</ul>`:'<p class="adl-det">Ninguna.</p>'}
          <div class="form-grid"><div class="field"><label for="pm-feat">Función</label><select id="pm-feat">${Object.entries(d.features).map(([k,l])=>`<option value="${k}">${esc(l)}</option>`).join('')}</select></div>
          <div class="field"><label for="pm-en">Valor</label><select id="pm-en"><option value="1">Activar</option><option value="0">Desactivar</option></select></div>
          <div class="field full"><label for="pm-why">Motivo (obligatorio)</label><input id="pm-why" maxlength="500"></div>
          <div class="form-actions full"><button type="button" class="btn" id="pm-exc">Añadir excepción</button></div></div>`,
        footer:'<button type="button" class="btn" data-modal-close>Cerrar</button>'});
      const after=()=>{ delete el.dataset.dirty; close(); renderAdminPlans(mountId); };
      $('#pm-assign',el).onclick=async()=>{ try{ await postJSON('/api/admin/plans/assign',{type:p.type,id:p.id,plan:$('#pm-plan',el).value,months:$('#pm-months',el).value,amount:$('#pm-amount',el).value,note:$('#pm-note',el).value}); toast('Plan guardado.'); after(); }catch(err){ toast(err.message); } };
      $('#pm-exc',el).onclick=async()=>{ try{ await postJSON('/api/admin/plans/exception',{type:p.type,id:p.id,feature:$('#pm-feat',el).value,enabled:$('#pm-en',el).value==='1',reason:$('#pm-why',el).value}); toast('Excepción añadida.'); after(); }catch(err){ toast(err.message); } };
      $$('.pm-unexc',el).forEach(x=>x.onclick=async()=>{ try{ await postJSON('/api/admin/plans/exception/remove',{id:+x.dataset.id}); after(); }catch(err){ toast(err.message); } });
    });
  }
  // Administración → Funciones
  async function renderAdminFeatures(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/admin/features'); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Funciones</p><h2>Activar u ocultar funciones de la web</h2><p>Al desactivar una función desaparece de la web y el servidor rechaza su uso. Los datos se conservan y vuelven al activarla.</p></div></div>
      <form id="af-form" class="af-list">${Object.entries(d.labels).map(([k,l])=>`<label class="lg-check"><input type="checkbox" data-k="${k}" ${d.switches[k]?'checked':''}> <span>${esc(l)}</span></label>`).join('')}
        <label class="lg-check"><input type="checkbox" id="af-pilot" ${d.pilot_mode?'checked':''}> <span><b>Modo piloto:</b> solo pueden darse de alta centros y profesionales con invitación</span></label>
        <div class="form-actions"><button class="btn btn-primary" type="submit">Guardar</button></div></form>
      <h3 class="adl-h">Invitaciones para el piloto</h3><form id="af-inv" class="form-grid"><div class="field"><label for="af-note">Para quién (nota)</label><input id="af-note" maxlength="200"></div><div class="field"><label for="af-days">Válida (días)</label><input id="af-days" type="number" min="1" max="365" value="30"></div><div class="form-actions full"><button class="btn" type="submit">Crear invitación</button></div></form>
      ${d.invites.length?`<div class="table-wrap"><table class="data-table"><thead><tr><th>Código</th><th>Nota</th><th>Caduca</th><th>Estado</th><th></th></tr></thead><tbody>${d.invites.map(i=>`<tr><td><code>${esc(i.code)}</code></td><td>${esc(i.note||'')}</td><td>${esc(i.expires_at||'—')}</td><td>${i.used_at?'Usada':'Disponible'}</td><td>${i.used_at?'':`<button type="button" class="btn-link af-revoke" data-id="${i.id}">Anular</button>`}</td></tr>`).join('')}</tbody></table></div>`:''}</section>`;
    $('#af-form').onsubmit=async e=>{ e.preventDefault(); const sw={}; $$('#af-form [data-k]').forEach(x=>sw[x.dataset.k]=x.checked);
      try{ await postJSON('/api/admin/features',{switches:sw,pilot_mode:$('#af-pilot').checked}); state.meta=null; toast('Funciones guardadas.'); }catch(err){ toast(err.message); } };
    $('#af-inv').onsubmit=async e=>{ e.preventDefault(); try{ const r=await postJSON('/api/admin/invites',{note:$('#af-note').value,days:$('#af-days').value}); toast('Invitación '+r.code+' creada.'); renderAdminFeatures(mountId); }catch(err){ toast(err.message); } };
    $$('.af-revoke',mount).forEach(b=>b.onclick=async()=>{ try{ await postJSON('/api/admin/invites',{revoke:+b.dataset.id}); renderAdminFeatures(mountId); }catch(err){ toast(err.message); } });
  }
  async function renderImageOrigins(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/admin/images'); }catch(err){ mount.innerHTML=''; return; }
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Imágenes</p><h2>Origen y licencia de las imágenes</h2><p>Indica de dónde sale cada imagen (foto propia, banco de imágenes con su licencia, cesión del autor…) además del crédito que se muestra. Las imágenes sin origen hay que comprobarlas o sustituirlas antes del lanzamiento.</p></div></div>
      ${d.missing?`<div class="notice warning"><strong>${d.missing} ${d.missing===1?'imagen sin origen':'imágenes sin origen'}.</strong></div>`:'<div class="notice good"><strong>Todas las imágenes tienen origen.</strong></div>'}
      <div class="table-wrap"><table class="data-table"><thead><tr><th>Imagen</th><th>Dónde se usa</th><th>Crédito</th><th>Origen / licencia</th><th></th></tr></thead><tbody>${d.items.map((x,i)=>`<tr${x.missing?' class="is-warn"':''}><td><img src="${esc(x.path)}" alt="" loading="lazy" style="width:72px;height:48px;object-fit:cover;border-radius:6px"><div class="adl-det">${esc(x.path.split('/').pop())}</div></td><td class="adl-det">${x.where.map(esc).join('<br>')}</td>
        <td><label class="sr-only" for="io-c-${i}">Crédito</label><input id="io-c-${i}" maxlength="200" value="${esc(x.credit)}"></td><td><label class="sr-only" for="io-o-${i}">Origen o licencia</label><input id="io-o-${i}" maxlength="300" value="${esc(x.origin)}" placeholder="Ej.: foto propia; Unsplash License; cedida por…"></td>
        <td><button type="button" class="btn io-save" data-i="${i}">Guardar</button></td></tr>`).join('')}</tbody></table></div></section>`;
    $$('.io-save',mount).forEach(b=>b.onclick=async()=>{ const i=+b.dataset.i; try{ await postJSON('/api/admin/images',{path:d.items[i].path,credit:$('#io-c-'+i).value,origin:$('#io-o-'+i).value}); toast('Guardado.'); renderImageOrigins(mountId); }catch(err){ toast(err.message); } });
  }
  async function renderAdminMaps(mountId){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/admin/maps'); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    const n=x=>Number(x||0).toLocaleString(wdLocale()); const pct=d.limit?Math.min(100,Math.round(d.used*100/d.limit)):0;
    const mb=x=>(x/1048576).toLocaleString(wdLocale(),{maximumFractionDigits:0})+' MB';
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Mapas</p><h2>Mapa base, satélite y batimetría</h2><p>El mapa base se sirve desde nuestro servidor. La vista satélite pasa por nuestro servidor con la clave de ArcGIS, que nunca llega al navegador; aquí controlas cuántas teselas se sirven al mes para no salir de la cuota gratuita.</p></div></div>
      <div class="acc-kpis">${accKpi('map',d.pmtiles.exists?mb(d.pmtiles.size):(d.pmtiles.local?'Falta el archivo':'Externo'),'Mapa base (PMTiles) · '+esc(d.pmtiles.url))}
        ${accKpi('globe',d.key_configured?(d.available?'Activa':'Oculta: límite alcanzado'):'Sin clave','Vista satélite (ARCGIS_API_KEY)')}
        ${accKpi('chart',`${n(d.used)} / ${n(d.limit)}`,`Teselas satélite en ${esc(d.month)} (${pct} %)`)}</div>
      ${!d.pmtiles.exists&&d.pmtiles.local?'<div class="notice warning"><strong>Falta el mapa base.</strong> Sigue los pasos de docs/mapas.md para descargar el archivo PMTiles.</div>':''}
      ${!d.key_configured?'<div class="notice"><strong>La vista satélite está oculta.</strong> Añade ARCGIS_API_KEY al archivo .env del servidor (nunca en el código) y reinicia.</div>':''}
      <form id="maps-form" class="form-grid"><div class="field"><label for="maps-limit">Límite mensual de teselas satélite</label><input id="maps-limit" type="number" min="0" max="50000000" step="1000" value="${d.limit}" required><small>Por defecto ${n(d.default_limit)}, por debajo de las 2.000.000 gratuitas. Al 80 % se avisa por email; al llegar al límite la capa se oculta hasta el mes siguiente.</small></div>
        <div class="form-actions full"><button class="btn btn-primary" type="submit">Guardar límite</button></div></form>
      ${d.history.length?`<div class="table-wrap"><table class="data-table"><thead><tr><th>Mes</th><th>Teselas satélite</th></tr></thead><tbody>${d.history.map(h=>`<tr><td>${esc(h.month)}</td><td>${n(h.tiles)}</td></tr>`).join('')}</tbody></table></div>`:''}</section>`;
    $('#maps-form').onsubmit=async e=>{ e.preventDefault(); try{ await postJSON('/api/admin/maps',{limit:$('#maps-limit').value}); toast('Límite guardado.'); renderAdminMaps(mountId); }catch(err){ toast(err.message); } };
  }
  async function renderAdminPointTexts(mountId,pending=true){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    let d; try{ d=await api('/api/admin/point-texts?pending='+(pending?1:0)); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    mount.innerHTML=`<section class="mm-module"><div class="svc-head"><div><p class="eyebrow">Catálogo</p><h2>Descripciones de los puntos de buceo</h2>
      <p>Todas las descripciones se han reescrito con texto propio a partir de los datos de cada punto (lugar, tipo, profundidad, nivel y acceso), en los 10 idiomas. No se inventa ningún dato: lo que falta aparece en «Datos que faltan». El texto anterior se guarda aquí hasta que marques el punto como revisado.</p></div></div>
      <p class="adl-det"><b>${d.reviewed}</b> de <b>${d.total}</b> puntos revisados. <label class="lg-check" style="display:inline-flex"><input type="checkbox" id="apt-all" ${pending?'':'checked'}> <span>Mostrar también los revisados</span></label></p>
      ${d.items.length?`<div class="apt-list">${d.items.map(p=>`<article class="apt-item" data-id="${p.id}"><header><h3>${esc(p.name)}</h3><span class="adl-det">${esc([p.region,p.country].filter(Boolean).join(', '))}</span>${p.description_reviewed?'<span class="status good">Descripción revisada</span>':'<span class="status warn">Pendiente de revisar</span>'}</header>
        <div class="field"><label for="apt-t-${p.id}">Descripción nueva (castellano)</label><textarea id="apt-t-${p.id}" rows="5" maxlength="4000">${esc(p.description||'')}</textarea></div>
        ${p.description_missing.length?`<p class="adl-det"><b>Datos que faltan:</b> ${p.description_missing.map(esc).join(', ')}</p>`:''}
        ${p.description_legacy&&p.description_legacy!==p.description?`<details><summary>Texto anterior</summary><p class="adl-det">${esc(p.description_legacy)}</p></details>`:''}
        <div class="form-actions"><button type="button" class="btn apt-regen">Regenerar desde los datos</button><button type="button" class="btn btn-primary apt-ok">Guardar y marcar como revisada</button></div></article>`).join('')}</div>`:'<div class="empty">No hay descripciones pendientes de revisar.</div>'}</section>`;
    $('#apt-all').onchange=e=>renderAdminPointTexts(mountId,!e.target.checked);
    $$('.apt-item',mount).forEach(el=>{ const id=+el.dataset.id;
      $('.apt-ok',el).onclick=async()=>{ try{ await postJSON('/api/admin/point-texts/review',{id,description:$('textarea',el).value,lang:'es'}); toast('Descripción revisada.'); renderAdminPointTexts(mountId,pending); }catch(err){ toast(err.message); } };
      $('.apt-regen',el).onclick=async()=>{ try{ await postJSON('/api/admin/point-texts/review',{id,regenerate:true}); toast('Descripción regenerada.'); renderAdminPointTexts(mountId,pending); }catch(err){ toast(err.message); } }; });
  }
  async function openLegalEditor(slug,lang,done){
    const esc=escapeHtml; let d; try{ d=await api(`/api/admin/legal/doc?slug=${encodeURIComponent(slug)}&lang=${lang}`); }catch(err){ toast(err.message); return; }
    const today=new Date(), minDays=lang==='es'&&d.version?d.notice_days:0;
    const iso=x=>new Date(x.getTime()-x.getTimezoneOffset()*6e4).toISOString().slice(0,10);
    const minDate=iso(new Date(today.getTime()+minDays*864e5));
    const LANGS=['es','en','fr','de','it','pt','nl','pl','ru','zh'];
    const {el,close}=wdOpenModal({id:'legal-editor',size:'lg',title:'Editar «'+esc(d.title)+'»',subtitle:'Se publica como una versión nueva. Las anteriores se conservan en el historial.',
      body:`<div class="form-grid">
        <div class="field"><label for="le-lang">Idioma</label><select id="le-lang">${LANGS.map(l=>`<option value="${l}" ${l===lang?'selected':''}>${l.toUpperCase()}${l==='es'?' · referencia':l==='en'?' · oficial':''}</option>`).join('')}</select></div>
        <div class="field"><label for="le-eff">Entra en vigor el</label><input id="le-eff" type="date" min="${minDate}" value="${minDate}" required>${minDays?`<small>Los cambios de este documento se anuncian con ${minDays} días de antelación.</small>`:''}</div>
        <div class="field full"><label for="le-title">Título</label><input id="le-title" maxlength="200" value="${esc(d.title)}"></div>
        <div class="field full"><label for="le-md">Texto (Markdown)</label><textarea id="le-md" rows="18" class="le-md" spellcheck="true">${esc(d.markdown||d.base_markdown||'')}</textarea>
          <small>${!d.markdown&&lang!=='es'?'<b>No hay versión en este idioma:</b> se muestra el texto en castellano para que lo traduzcas. ':''}Campos que se rellenan solos: ${d.placeholders.map(p=>`<code>{{${esc(p)}}}</code>`).join(' ')||'—'}</small></div>
        <div class="field full"><label for="le-sum">Resumen de los cambios</label><textarea id="le-sum" rows="2" maxlength="1000" placeholder="Por ejemplo: añadimos el plazo de devolución de la señal."></textarea><small>Aparece en el historial y en el email a los usuarios.</small></div>
        ${lang==='es'&&d.acceptance?`<label class="lg-check full"><input type="checkbox" id="le-notify" checked> <span>Avisar por email a ${d.acceptance==='pro'?'los centros y profesionales':'todos los usuarios'} y pedirles que la acepten cuando entre en vigor</span></label>`:''}
      </div>
      <details class="le-hist"><summary>Historial (${d.history.length})</summary><ul>${d.history.map(h=>`<li><b>${esc(h.version)}</b> · ${esc(h.lang)} · ${esc(wdLegalDate(h.effective_at))}${h.summary?' — '+esc(h.summary):''} <small>(${h.source==='file'?'texto inicial':'publicado '+esc((h.published_at||'').slice(0,10))})</small></li>`).join('')}</ul></details>`,
      footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn" id="le-preview">Vista previa</button><button type="button" class="btn btn-primary" id="le-pub">Publicar versión</button>'});
    $('#le-lang',el).onchange=e=>{ close(); openLegalEditor(slug,e.target.value,done); };
    $('#le-preview',el).onclick=()=>wdOpenModal({id:'legal-preview',size:'lg',title:'Vista previa',body:`<article class="lg-doc" translate="no">${wdMd($('#le-md',el).value)}</article>`,footer:'<button type="button" class="btn" data-modal-close>Cerrar</button>'});
    $('#le-pub',el).onclick=async()=>{ const b=$('#le-pub',el); b.disabled=true;
      try{ const r=await postJSON('/api/admin/legal/publish',{slug,lang,title:$('#le-title',el).value,markdown:$('#le-md',el).value,summary:$('#le-sum',el).value,effective_at:$('#le-eff',el).value,notify:$('#le-notify',el)?$('#le-notify',el).checked:false});
        delete el.dataset.dirty; close(); LEGAL_INFO=null; toast(`Versión ${r.version} publicada. Entra en vigor el ${wdLegalDate(r.effective_at)}.`); done&&done(); }
      catch(err){ toast(err.message); b.disabled=false; } };
  }
  async function renderAdminEmails(mountId,opts={}){
    const mount=document.getElementById(mountId); if(!mount) return; const esc=escapeHtml;
    const q=new URLSearchParams({status:opts.status||'',q:opts.q||'',page:opts.page||0});
    let d; try{ d=await api('/api/admin/emails?'+q); }catch(err){ mount.innerHTML=`<div class="empty">${esc(err.message)}</div>`; return; }
    const s=d.smtp, total=Object.values(d.counts).reduce((a,b)=>a+b,0);
    mount.innerHTML=`<section class="mm-module em">
      <div class="svc-head"><div><p class="eyebrow">Correos automáticos</p><h2>Correos de la plataforma</h2><p>Cada reserva, pago, cancelación o aviso genera su correo en el idioma del destinatario. Aquí ves todos los envíos y una vista previa de cada plantilla.</p></div></div>
      <div class="em-smtp ${s.enabled?'is-on':'is-off'}">${wdIcon('mail',22)}<div><strong>${s.enabled?'Envío activado':'Envío pendiente de configurar'}</strong>
        <p>${s.enabled?`Servidor ${esc(s.host)}:${esc(String(s.port))} (${esc(s.security)}) · remitente «${esc(s.from_name)}» &lt;${esc(s.from)}&gt;${s.reply_to?' · respuestas a '+esc(s.reply_to):''}`:'Los correos se guardan en la cola y se enviarán en cuanto configures el correo corporativo. En el servidor, define <code>WOD_SMTP_HOST</code>, <code>WOD_SMTP_PORT</code>, <code>WOD_SMTP_USER</code>, <code>WOD_SMTP_PASSWORD</code> y <code>WOD_MAIL_FROM</code>, y reinicia.'}</p></div>
        <form id="em-test" class="em-test"><input id="em-test-to" type="email" placeholder="tu@email.com" value="${esc(state.me?.user?.email&&!/\.(local|test)$/.test(state.me.user.email)?state.me.user.email:'')}" required><button class="btn" type="submit">Enviar prueba</button></form></div>
      <div class="em-kpis">${Object.entries(EMAIL_STATUS).map(([k,[l,c]])=>`<button type="button" class="em-kpi ${opts.status===k?'is-on':''}" data-st="${k}"><b>${(d.counts[k]||0).toLocaleString(wdLocale())}</b><span class="status ${c}">${l}</span></button>`).join('')}<button type="button" class="em-kpi ${!opts.status?'is-on':''}" data-st=""><b>${total.toLocaleString(wdLocale())}</b><span class="status">Todos</span></button></div>
      <div class="em-grid"><div>
        <div class="em-tools"><label class="cd-field">${wdIcon('search',16)}<input id="em-q" type="search" placeholder="Buscar por email o asunto" value="${esc(opts.q||'')}"></label></div>
        <div class="table-wrap"><table class="data-table em-table"><thead><tr><th>Fecha</th><th>Para</th><th>Asunto</th><th>Plantilla</th><th>Estado</th></tr></thead><tbody>
        ${d.items.length?d.items.map(r=>`<tr class="em-row" data-id="${r.id}" tabindex="0"><td>${esc(new Date(r.created_at).toLocaleString(wdLocale(),{dateStyle:'short',timeStyle:'short'}))}</td><td>${esc(r.to_email)}<small>${esc(r.lang.toUpperCase())}</small></td><td translate="no">${esc(r.subject)}</td><td>${esc(d.templates.find(t=>t.key===r.template)?.label||r.template)}</td><td><span class="status ${EMAIL_STATUS[r.status]?.[1]||''}">${esc(EMAIL_STATUS[r.status]?.[0]||r.status)}</span>${r.last_error?`<small class="em-err">${esc(r.last_error)}</small>`:''}</td></tr>`).join(''):'<tr><td colspan="5">No hay correos con este filtro.</td></tr>'}
        </tbody></table></div>
        <div class="em-pager">${d.page>0?'<button type="button" class="btn" id="em-prev">Anteriores</button>':''}<span>${d.total?`${d.page*50+1}–${Math.min(d.total,(d.page+1)*50)} de ${d.total.toLocaleString(wdLocale())}`:''}</span>${(d.page+1)*50<d.total?'<button type="button" class="btn" id="em-next">Siguientes</button>':''}</div>
      </div>
      <aside class="em-preview"><h3>Plantillas</h3><p>Vista previa con datos de ejemplo.</p>
        <div class="form-grid"><div class="field full"><label for="em-tpl">Plantilla</label><select id="em-tpl">${['diver','pro','center','admin','any'].map(a=>{ const list=d.templates.filter(t=>EMAIL_AUD[a]===t.audience); return list.length?`<optgroup label="${esc(list[0].audience)}">${list.map(t=>`<option value="${t.key}">${esc(t.label)}</option>`).join('')}</optgroup>`:''; }).join('')}</select></div>
        <div class="field full"><label for="em-lang">Idioma</label><select id="em-lang">${d.langs.map(l=>`<option value="${l}">${esc(LANGS[l]||l)}</option>`).join('')}</select></div></div>
        <p class="em-subject" id="em-subject" translate="no"></p><iframe id="em-frame" class="em-frame" sandbox="" title="Vista previa del correo"></iframe></aside></div>
    </section>`;
    const reload=o=>renderAdminEmails(mountId,{...opts,...o});
    $$('.em-kpi',mount).forEach(b=>b.onclick=()=>reload({status:b.dataset.st,page:0}));
    let t=null; $('#em-q',mount).oninput=e=>{ clearTimeout(t); t=setTimeout(()=>reload({q:e.target.value,page:0}),400); };
    $('#em-prev',mount)?.addEventListener('click',()=>reload({page:d.page-1})); $('#em-next',mount)?.addEventListener('click',()=>reload({page:d.page+1}));
    $('#em-test',mount).onsubmit=async e=>{ e.preventDefault(); try{ const r=await postJSON('/api/admin/emails/test',{to:$('#em-test-to',mount).value}); toast(r.message||'Correo de prueba enviado.'); reload({}); }catch(err){ toast(err.message); } };
    const preview=async()=>{ try{ const p=await api(`/api/admin/email-preview?template=${encodeURIComponent($('#em-tpl',mount).value)}&lang=${$('#em-lang',mount).value}`); $('#em-subject',mount).textContent=p.subject; $('#em-frame',mount).srcdoc=p.html; }catch(err){ toast(err.message); } };
    $('#em-tpl',mount).onchange=preview; $('#em-lang',mount).onchange=preview; preview();
    $$('.em-row',mount).forEach(r=>{ const open=async()=>{ try{ const it=(await api('/api/admin/emails/'+r.dataset.id)).item;
      const {el,close}=wdOpenModal({id:'email-view',size:'lg',title:esc(it.subject),subtitle:`Para ${esc(it.to_name?it.to_name+' · ':'')}${esc(it.to_email)} · ${esc(EMAIL_STATUS[it.status]?.[0]||it.status)}${it.sent_at?' · enviado '+esc(new Date(it.sent_at).toLocaleString(wdLocale())):''}`,
        body:`<iframe class="em-frame em-frame-lg" sandbox="" title="Correo"></iframe>${it.last_error?`<p class="em-err">Último error: ${esc(it.last_error)}</p>`:''}`,
        footer:`<button type="button" class="btn" data-modal-close>Cerrar</button>${it.status!=='skipped'?'<button type="button" class="btn btn-primary" id="em-resend">Reenviar</button>':''}`});
      $('.em-frame',el).srcdoc=it.html||'';
      $('#em-resend',el)?.addEventListener('click',async()=>{ try{ await postJSON('/api/admin/emails/resend',{id:it.id}); close(); toast('Correo puesto de nuevo en la cola.'); reload({}); }catch(err){ toast(err.message); } });
    }catch(err){ toast(err.message); } }; r.onclick=open; r.onkeydown=e=>{ if(e.key==='Enter') open(); }; });
    marketingComposer(mount.querySelector('.em'));
  }
  const EMAIL_AUD={diver:'Buceador',pro:'Profesional',center:'Centro',admin:'Administración',any:'Cualquier usuario',marketing:'Con consentimiento comercial'};
  // ---------------------------------------------------------------- v50.35 · Fase 4: two-step verification, marketing consent
  function totpCard(u){
    const sec=state.me?.security||{}; const on=!!sec.totp_enabled;
    return `<section class="acc-card" id="acc-totp"><div class="acc-card-head"><h2>${wdIcon('lock',18)} Verificación en dos pasos</h2>${on?'<span class="status good">Activada</span>':sec.totp_setup_required?'<span class="status bad">Obligatoria</span>':'<span class="status warn">Desactivada</span>'}</div>
      <p class="acc-help">${on?`Al iniciar sesión te pedimos además un código de tu aplicación de verificación. Te quedan ${Number(sec.recovery_left||0)} códigos de recuperación.`:'Protege tu cuenta con un código de 6 cifras de una aplicación como Google Authenticator, Microsoft Authenticator o Aegis.'}${sec.totp_setup_required?' <b>Los administradores deben activarla para usar la administración.</b>':''}</p>
      <div id="totp-box">${on?`<div class="acc-privacy-actions"><button type="button" class="btn" id="totp-recovery">Nuevos códigos de recuperación</button>${u.role==='admin'?'':'<button type="button" class="btn danger" id="totp-off">Desactivar</button>'}</div>`
        :`<form id="totp-start" class="acc-pw"><div class="field"><label for="totp-pw">Tu contraseña</label><input id="totp-pw" type="password" autocomplete="current-password" required></div><button class="btn btn-primary">Activar</button></form>`}</div></section>`;
  }
  function bindTotpCard(d){
    const box=$('#totp-box'); if(!box) return;
    if(new URLSearchParams(location.hash.split('?')[1]||'').get('seguridad')) setTimeout(()=>$('#acc-totp')?.scrollIntoView({behavior:'smooth'}),200);
    const showCodes=codes=>{ box.innerHTML=`<div class="notice warn"><strong>Guarda estos códigos de recuperación</strong><p>Cada uno sirve una sola vez para entrar si pierdes el móvil. No los volveremos a mostrar.</p><pre class="totp-codes">${codes.map(escapeHtml).join('\n')}</pre><button type="button" class="btn" id="totp-copy">Copiar</button> <button type="button" class="btn btn-primary" id="totp-done">Ya los he guardado</button></div>`;
      $('#totp-copy').onclick=()=>navigator.clipboard?.writeText(codes.join('\n')).then(()=>toast('Códigos copiados.')).catch(()=>{}); $('#totp-done').onclick=async()=>{ await loadMe(); renderAccountPage(); }; };
    $('#totp-start')?.addEventListener('submit',async e=>{ e.preventDefault(); try{ const r=await postJSON('/api/account/totp/setup',{password:$('#totp-pw').value});
      box.innerHTML=`<ol class="totp-steps"><li>Abre tu aplicación de verificación y escanea este código:<div class="totp-qr">${r.qr_svg}</div><small>¿No puedes escanear? Escribe esta clave: <code>${escapeHtml(r.secret.replace(/(.{4})/g,'$1 ').trim())}</code></small></li>
        <li><form id="totp-confirm" class="acc-pw"><div class="field"><label for="totp-code">Escribe el código de 6 cifras que muestra</label><input id="totp-code" inputmode="numeric" autocomplete="one-time-code" maxlength="6" required></div><button class="btn btn-primary">Confirmar y activar</button></form></li></ol>`;
      $('#totp-confirm').onsubmit=async ev=>{ ev.preventDefault(); try{ const x=await postJSON('/api/account/totp/enable',{code:$('#totp-code').value}); toast('Verificación en dos pasos activada.'); showCodes(x.recovery_codes); }catch(err){ toast(err.message); } };
    }catch(err){ toast(err.message); } });
    const ask=(title,action,done)=>{ const {el,close}=wdOpenModal({id:'totp-ask',size:'sm',title,body:`<div class="field"><label for="ta-pw">Contraseña</label><input id="ta-pw" type="password" autocomplete="current-password"></div><div class="field"><label for="ta-code">Código de verificación o de recuperación</label><input id="ta-code" inputmode="numeric" autocomplete="one-time-code" maxlength="20"></div>`,
      footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="ta-ok">Continuar</button>'});
      $('#ta-ok',el).onclick=async()=>{ try{ const r=await postJSON('/api/account/totp/'+action,{password:$('#ta-pw',el).value,code:$('#ta-code',el).value}); close(); done(r); }catch(err){ toast(err.message); } }; };
    $('#totp-recovery')?.addEventListener('click',()=>ask('Nuevos códigos de recuperación','recovery',r=>showCodes(r.recovery_codes)));
    $('#totp-off')?.addEventListener('click',()=>ask('Desactivar la verificación en dos pasos','disable',async()=>{ toast('Verificación en dos pasos desactivada.'); await loadMe(); renderAccountPage(); }));
  }
  function marketingCard(u){
    return `<section class="acc-card" id="acc-marketing"><div class="acc-card-head"><h2>${wdIcon('message',18)} Novedades y ofertas</h2></div>
      <label class="svc-check"><input type="checkbox" id="acc-mkt" ${u.marketing_consent?'checked':''}><span><strong>Quiero recibir novedades y ofertas de WORLDIVES por email</strong><small>Opcional. Puedes darte de baja cuando quieras, también desde el enlace de cada correo. Los avisos de tus reservas te llegan siempre.</small></span></label></section>`;
  }
  function bindMarketingCard(){ $('#acc-mkt')?.addEventListener('change',async e=>{ try{ await postJSON('/api/account/marketing',{consent:e.target.checked}); toast(e.target.checked?'Te enviaremos novedades y ofertas.':'Ya no recibirás comunicaciones comerciales.'); }catch(err){ toast(err.message); e.target.checked=!e.target.checked; } }); }
  async function renderUnsubscribe(params){
    const t=params.get('t')||'';
    setApp(`<section class="page auth"><div class="auth-card" style="max-width:560px"><p class="eyebrow">WORLDIVES DISCOVERY</p><h1>Darse de baja</h1><div id="unsub-box"><p class="lead">Un momento…</p></div></div></section>`);
    try{ await postJSON('/api/marketing/unsubscribe',{t}); $('#unsub-box').innerHTML='<p class="lead">Listo: ya no recibirás comunicaciones comerciales de WORLDIVES DISCOVERY.</p><p>Los avisos de tus reservas y de tu cuenta te seguirán llegando. Puedes volver a apuntarte en «Mi cuenta».</p><a class="btn btn-primary" href="#/">Ir a la portada</a>'; }
    catch(err){ $('#unsub-box').innerHTML=`<p class="lead">${escapeHtml(err.message)}</p><p>Si el enlace no funciona, entra en «Mi cuenta» y desmarca «Novedades y ofertas».</p>`; }
    translateTree($('#unsub-box'));
  }
  // Provider: move a booking to another departure of the same service (the diver gets an email).
  async function openRescheduleModal(b,after){
    let svc; try{ svc=(await api('/api/provider-services/'+b.service_id)); }catch(e){ toast(e.message); return; }
    const today=wdToday(); const slots=(svc.slots||[]).filter(s=>s.id!==b.slot_id&&s.slot_date>=today&&['open','full'].includes(s.status));
    if(!slots.length){ toast('No hay otras salidas de este servicio. Programa una nueva salida antes de cambiar la reserva.'); return; }
    const {el,close}=wdOpenModal({id:'reschedule',title:'Cambiar fecha u hora',subtitle:'Se mueve a otra salida del mismo servicio. El cliente recibe un email con el cambio.',
      body:`<div class="field"><label for="rs-slot">Nueva salida</label><select id="rs-slot">${slots.map(s=>`<option value="${s.id}" ${Number(s.spots_available)<Number(b.participants||1)?'disabled':''}>${escapeHtml(wdLongDay(s.slot_date))} · ${escapeHtml(s.slot_time)} · ${s.spots_available} plazas libres</option>`).join('')}</select></div>
        <div class="field"><label for="rs-reason">Motivo (lo verá el cliente)</label><input id="rs-reason" maxlength="300" placeholder="Ej.: el estado del mar obliga a cambiar la salida"></div>`,
      footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="rs-ok">Cambiar</button>'});
    $('#rs-ok',el).onclick=async()=>{ try{ await postJSON(`/api/bookings/${b.id}/reschedule`,{slot_id:+$('#rs-slot',el).value,reason:$('#rs-reason',el).value}); close(); toast('Reserva cambiada. El cliente recibe un email.'); after&&after(); }catch(err){ toast(err.message); } };
  }
  // Administration: commercial email, only to users who agreed (Fase 4.3).
  function marketingComposer(mount){
    if(!mount) return;
    mount.insertAdjacentHTML('beforeend',`<section class="cb-panel" id="mkt-panel"><div class="cb-panel-head"><div><h3>Comunicación comercial</h3><p>Solo llega a quien dio su consentimiento y tiene el email verificado. Cada correo lleva baja en un clic. Envía antes una prueba a tu email.</p></div></div>
      <form id="mkt-form" class="form-grid"><div class="field full"><label for="mkt-subject">Asunto</label><input id="mkt-subject" maxlength="150" required></div><div class="field full"><label for="mkt-title">Título</label><input id="mkt-title" maxlength="150"></div>
        <div class="field full"><label for="mkt-body">Texto</label><textarea id="mkt-body" rows="5" maxlength="5000" required></textarea></div><div class="field"><label for="mkt-button">Texto del botón</label><input id="mkt-button" maxlength="60" placeholder="Ver en WORLDIVES"></div><div class="field"><label for="mkt-url">Enlace del botón</label><input id="mkt-url" maxlength="500" placeholder="#/experiencias o https://…"></div>
        <div class="form-actions full"><button type="button" class="btn" id="mkt-test">Enviarme una prueba</button><button class="btn btn-primary">Enviar a los suscritos</button></div></form></section>`);
    const f=$('#mkt-form'); const body=test=>({subject:$('#mkt-subject').value,title:$('#mkt-title').value,body:$('#mkt-body').value,button:$('#mkt-button').value,url:$('#mkt-url').value,test});
    $('#mkt-test').onclick=async()=>{ try{ const r=await postJSON('/api/admin/marketing/send',body(true)); toast(`Prueba enviada (${r.recipients}).`); }catch(e){ toast(e.message); } };
    f.onsubmit=async e=>{ e.preventDefault(); if(!confirm('¿Enviar este correo a todas las personas suscritas?')) return; try{ const r=await postJSON('/api/admin/marketing/send',body(false)); toast(`En cola para ${r.recipients} personas.`); }catch(err){ toast(err.message); } };
  }


  // ---------------------------------------------------------------- v50.30 · Top 10: precise location
  function wdNearestPlace(items,lat,lon){
    let best=null; for(const p of items||[]){ const la=+p.latitude, lo=+p.longitude; if(!Number.isFinite(la)||!Number.isFinite(lo)) continue;
      const dx=(lo-lon)*Math.cos(lat*Math.PI/180), dy=la-lat, d=dx*dx+dy*dy; if(!best||d<best.d) best={d,p}; }
    if(!best) return null; const km=Math.sqrt(best.d)*111; const name=String(best.p.subregion||best.p.region||best.p.country||'').split('·').pop().trim();
    return {name,km};
  }
  function wdPickOnMap({start,onPick}){
    const {el,close}=wdOpenModal({id:'tt-map',size:'lg',title:'Elige tu ubicación',subtitle:'Toca el mapa donde estás (o donde quieres bucear) y pulsa «Ver el Top 10 aquí».',
      body:'<div id="tt-pick-map" class="tt-pick-map"></div><p class="tt-pick-coords" id="tt-pick-coords">Todavía no has elegido ningún punto.</p>',
      footer:'<button type="button" class="btn" data-modal-close>Cancelar</button><button type="button" class="btn btn-primary" id="tt-pick-ok" disabled>Ver el Top 10 aquí</button>'});
    if(!window.L){ $('#tt-pick-map',el).innerHTML='<div class="map-fallback"><strong>El mapa no está disponible ahora mismo</strong><span>Busca tu localidad en el buscador.</span></div>'; return; }
    wdTileDefaults(); const m=L.map($('#tt-pick-map',el),{zoomControl:true,attributionControl:true}).setView(start?[start.lat,start.lon]:[39.4,-0.4],start?9:6);
    wdBaseLayer().addTo(m);
    const icon=L.divIcon({className:'tt-me-wrap',html:'<span class="tt-me"></span>',iconSize:[22,22],iconAnchor:[11,11]});
    // Dive sites as context (same round markers and clusters as every other map; tapping one picks its position).
    loadMapLayer().then(layer=>{ const grp=wdMarkerLayer(); const ms=(layer.items||[]).filter(p=>p.latitude!=null).map(p=>{ const x=L.marker([p.latitude,p.longitude],{icon:pointIcon(p),title:p.name,alt:p.name}); x.on('click',()=>m.fire('click',{latlng:x.getLatLng()})); return x; }); grp.addLayers?grp.addLayers(ms):ms.forEach(x=>x.addTo(grp)); grp.addTo(m); }).catch(()=>{});
    let mk=null, sel=null;
    m.on('click',e=>{ sel=e.latlng; if(mk) mk.setLatLng(sel); else mk=L.marker(sel,{icon}).addTo(m); $('#tt-pick-ok',el).disabled=false; $('#tt-pick-coords',el).textContent=`${sel.lat.toFixed(4)}, ${sel.lng.toFixed(4)}`; });
    setTimeout(()=>m.invalidateSize(),160);
    $('#tt-pick-ok',el).onclick=()=>{ close(); onPick(sel.lat,sel.lng); };
  }
  async function wdGeocode(q){
    // Through our own server (/api/geocode): the visitor's IP is not sent to a third party and the provider's usage policy is respected.
    const d=await api('/api/geocode?'+new URLSearchParams({q,lang:currentLanguage()})); const it=(d.items||[])[0]; if(!it) return null;
    return {lat:+it.lat,lon:+it.lon,label:String(it.name||q).split(',')[0]};
  }


  document.addEventListener('submit', async e=>{
    if(e.target?.id==='point-photo-form'){ e.preventDefault(); const pid=e.target.dataset.pointId; try{ await api('/api/dive-points/'+pid+'/photos',{method:'POST',body:new FormData(e.target)}); toast('Fotografía subida.'); editPointForm(+pid); }catch(err){ toast(err.message); } }
  });

  navMobile();
  initLanguage();
  window.addEventListener('DOMContentLoaded',async()=>{ await Promise.all([loadMe(),loadMeta().catch(()=>{}),loadSiteMedia(),loadLanguagePack(),loadMapConfig()]); applyLanguage(); applyFeatureSwitches(); route(); cookieNotice(); footerOwner(); demoRibbon(); });
})();
