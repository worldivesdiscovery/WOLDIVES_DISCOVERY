// v50.57 (revisión general 5.4) · Runs in <head>, before anything is drawn. The header of the home page comes drawn in
// index.html, so its photo appears without waiting for the main script; this says whether this visit is the home page
// of the web (not the app: the app draws its own first screen) and in which language the visitor reads, so that its
// texts are shown only if they came in that language. Same rules as WD_APP and currentLanguage() in world-dives-v8.js.
(function(){
  var d=document.documentElement, route=(location.hash||'').replace(/^#\/?/,'').split('?')[0];
  var langs=['es','en','fr','de','it','pt','pl','nl','zh'], retired={ja:'en',ko:'en',ru:'en',zt:'zh'};
  var pick=function(l){ l=l&&String(l).toLowerCase(); l=retired[l]||l; return langs.indexOf(l)>=0?l:null; };
  try{
    var q=new URLSearchParams(location.search), app=q.get('app');
    var inApp=/WorldivesApp\//.test(navigator.userAgent||'')||app==='1'||app==='pruebas'||(app!=='0'&&!!sessionStorage.getItem('wd-app'));
    if((route&&route!=='home')||inApp) return;
    var lang=pick(q.get('lang'))||pick(localStorage.getItem('wod-language'));
    if(!lang){
      var prefs=navigator.languages||[navigator.language||'es'];
      for(var i=0;i<prefs.length&&!lang;i++){ var l=String(prefs[i]).toLowerCase(); lang=pick(/^zh-(tw|hk|hant)/.test(l)?'zt':l.split('-')[0]); }
    }
    d.className+=(d.className?' ':'')+'wd-portada wd-portada-'+(lang||'es');
  }catch(e){}
})();
