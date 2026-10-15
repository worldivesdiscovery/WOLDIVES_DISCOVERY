// v50.57 (revisión general 5.4) · Runs first in <head>, before anything is drawn. The header of the home page comes drawn in
// index.html, so its photo appears without waiting for the main script; this says whether this visit is the home page
// of the web (not the app: the app draws its own first screen) and in which language the visitor reads, so that its
// texts are shown only if they came in that language. Same rules as WD_APP and currentLanguage() in world-dives-v8.js.
// It also starts the main script (data-main) and the language pack: on the home page once its first screen is drawn
// (they no longer compete with the photo of the header), on any other page right away (download now, run when the
// page is ready, as before).
(function(){
  var d=document.documentElement, me=document.currentScript, route=(location.hash||'').replace(/^#\/?/,'').split('?')[0];
  var langs=['es','en','fr','de','it','pt','pl','nl','zh'], retired={ja:'en',ko:'en',ru:'en',zt:'zh'};
  var pick=function(l){ l=l&&String(l).toLowerCase(); l=retired[l]||l; return langs.indexOf(l)>=0?l:null; };
  var home=false, lang=null;
  try{
    var q=new URLSearchParams(location.search), app=q.get('app');
    var inApp=/WorldivesApp\//.test(navigator.userAgent||'')||app==='1'||app==='pruebas'||(app!=='0'&&!!sessionStorage.getItem('wd-app'));
    lang=pick(q.get('lang'))||pick(localStorage.getItem('wod-language'));
    if(!lang){
      var prefs=navigator.languages||[navigator.language||'es'];
      for(var i=0;i<prefs.length&&!lang;i++){ var l=String(prefs[i]).toLowerCase(); lang=pick(/^zh-(tw|hk|hant)/.test(l)?'zt':l.split('-')[0]); }
    }
    home=!inApp&&(!route||route==='home');
    if(home) d.className+=(d.className?' ':'')+'wd-portada wd-portada-'+(lang||'es');
  }catch(e){}
  var main=me&&me.getAttribute('data-main'); if(!main) return;
  var v=main.split('?v=')[1]||'', packed=false, ran=false;
  var preload=function(href,as){ var k=document.createElement('link'); k.rel='preload'; k.as=as; k.href=href; if(as==='fetch') k.crossOrigin='anonymous'; document.head.appendChild(k); };
  // the same address as loadLanguagePack() in world-dives-v8.js
  var pack=function(){ if(!packed&&lang&&lang!=='es'){ packed=true; preload('/idiomas/'+lang+'.json?v='+v,'fetch'); } };
  var run=function(){ if(ran) return; ran=true; var s=document.createElement('script'); s.src=main; s.async=false;
    window.__wdMain=new Promise(function(ok){ s.onload=s.onerror=function(){ ok(); }; }); document.body.appendChild(s); };
  var ready=function(fn){ if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',fn); else fn(); };
  if(home){
    var go=function(){ ready(function(){ pack(); run(); }); };
    // once the page has loaded and the browser says the largest thing of the screen (the photo of the header) is painted;
    // without that notice (older browsers), at «load»; at the latest after 3 s, even if a picture is still loading
    addEventListener('load',function(){
      try{ var po=new PerformanceObserver(function(l){ if(l.getEntries().length){ po.disconnect(); setTimeout(go,0); } }); po.observe({type:'largest-contentful-paint',buffered:true}); }
      catch(e){ go(); }
    });
    setTimeout(go,3000);
  }else{
    pack(); preload(main,'script'); ready(run);
  }
})();
