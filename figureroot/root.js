(() => {
  'use strict';
  const storagePrefix = 'FigureRoot.';
  const home = document.getElementById('collect');
  const studio = document.getElementById('studio');
  const plans = document.getElementById('plans');
  let underPlans=null,trial=new URLSearchParams(location.search).get('plan')==='lab';
  const config = document.documentElement.dataset;
  const web = /^https?:$/.test(location.protocol);
  const reviewApi = web && config.reviewApi && config.reviewApi !== 'false' ? config.reviewApi : '';
  const routed = web && Boolean(config.siteBase || reviewApi || config.publicPackage);
  const base = new URL(routed ? config.siteBase || document.querySelector('base[href]')?.href || '/' : document.baseURI, document.baseURI);
  if (routed && !base.pathname.endsWith('/')) base.pathname += '/';
  base.search='';base.hash='';
  const routePath = routed && location.pathname.startsWith(base.pathname) ? location.pathname.slice(base.pathname.length).replace(/\/$/,'') : '';
  const demoKey = 'studio-v1';
  const query = new URLSearchParams(location.search);
  const shared = location.hash.startsWith('#review=');
  let db, pending = Promise.resolve(), leaving = false;
  let studioPage = null;

  function openDatabase() {
    return new Promise(resolve => {
      if (!window.indexedDB) return resolve(null);
      const req = indexedDB.open('FigureRootStudio',1);
      req.onupgradeneeded = () => req.result.createObjectStore('packages');
      req.onsuccess = () => resolve(req.result);
      req.onerror = req.onblocked = () => resolve(null);
    });
  }

  async function read(key) {
    let value;
    if (db) value = await new Promise((resolve,reject) => {
      const req = db.transaction('packages').objectStore('packages').get(key);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    if (value != null) return value;
    try { return JSON.parse(localStorage.getItem(storagePrefix + key)) } catch { return null }
  }

  async function listPackages() {
    let local = [];
    try {
      local = Object.keys(localStorage).filter(k=>k.startsWith(storagePrefix+'index:')).map(k=>JSON.parse(localStorage[k]));
    } catch {}
    if (db) {
      const values = await new Promise((resolve,reject)=>{
        const req=db.transaction('packages').objectStore('packages').getAll(IDBKeyRange.bound('index:','index:\uffff'));
        req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
      });
      local.push(...values);
    }
    return [...new Map(local.filter(Boolean).map(row=>[row.id,row])).values()].sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt));
  }

  async function write(key, state) {
    const entries=[[key,state]];
    if(key.startsWith('draft:')) {
      entries.push(['index:'+state.meta.id,{id:state.meta.id,title:state.meta.title,author:state.meta.author,count:state.order.length,updatedAt:new Date().toISOString()}]);
    }
    if(!db) {
      for(const [k,value] of entries)localStorage.setItem(storagePrefix+k,JSON.stringify(value));
      return;
    }
    await new Promise((resolve,reject)=>{
      const txn = db.transaction('packages','readwrite');
      txn.oncomplete=resolve;
      txn.onerror=txn.onabort=()=>reject(txn.error || Error('Could not save this package in browser storage.'));
      const store=txn.objectStore('packages');
      for(const [k,value] of entries)store.put(value,k);
    });
  }

  function save(key, record) {
    const data=structuredClone(record);
    const task=pending.catch(()=>{}).then(()=>write(key,data));
    pending=task;
    return task;
  }

  function locationFor(id) {
    const url = new URL(base);
    if(id)url.searchParams.set('studio',id);
    return url.href;
  }

  function pageURL(page) {
    const url = new URL(locationFor());
    switch(page) {
      case 'vibromat':
        if(routed)return new URL('vibromat/',base).href;
        else url.searchParams.set('studio','demo');
        break;
      case 'reviewer':
        if(routed)return new URL(config.citationPath || 'CSIRO-VM96/',base).href;
        else url.searchParams.set('view','reviewer-demo');
        break;
      case 'plans': url.searchParams.set('view','plans');break;
    }
    return url.href;
  }

  const pageLinks = document.querySelectorAll('a[data-page]');
  for(const link of pageLinks)link.href=pageURL(link.dataset.page);

  async function navigateTo(url) {
    if(leaving)return;
    await pending;
    leaving=true;
    location.assign(url);
  }
  const go = id => navigateTo(locationFor(id));

  function newRecord(draft) {
    const id='FR-'+crypto.randomUUID().replaceAll('-','').slice(0,12).toUpperCase();
    const order=[],images={},versions={};
    for(const [index,entry] of draft.entries.entries()) {
      const vid='v'+(index+1);
      order.push(vid);images[vid]=entry.image;
      const title=entry.title?.trim()||entry.filename||vid;
      versions[vid]={
        id:vid,kind:entry.kind,title,name:title,filename:entry.filename,alt:title,
        tool:entry.tool || '', model:entry.model || '', aiUse:entry.aiUse || '',
        prompt:entry.prompt || '',
        why:entry.why || '', summary:entry.why || entry.filename
      };
    }
    const finalId=order[draft.entries.findIndex(v=>v.kind==='final')];
    const meta={id,title:draft.title.trim(),author:draft.author.trim(),finalId,versions};
    return {meta,order,images,notes:[],reviews:[],privacy:'public'};
  }

  function changeView(name) {
    home.hidden=name!=='collect';studio.hidden=name!=='studio';plans.hidden=name!=='plans';
    document.body.dataset.view=name;
    const active=name==='collect'?'upload':name==='studio'?studioPage:'plans';
    for(const link of pageLinks) {
      if(link.dataset.page===active)link.setAttribute('aria-current','page');
      else link.removeAttribute('aria-current');
    }
    document.querySelector('.skip').href=name==='studio'?'#workspace':name==='plans'?'#plans':'#collect';
  }

  function studioView(state, key, isReview) {
    studioPage = (state.meta || shared) ? null : isReview ? 'reviewer' : 'vibromat';
    changeView('studio');
    if(!state.meta) document.title=(isReview?'VibroMat reviewer':'VibroMat creator studio')+' · FigureRoot';
    window.FigureStudio.mount({initialState:state,share:isReview,storageKey:key,persist:record=>save(key,record),onHome:()=>go()});
  }

  function showTrial() {
    const old=home.querySelector('.plan-trial-notice');
    if(old||!trial)return;
    const hint=document.createElement('p');
    hint.className='plan-trial-notice';hint.textContent='Pro / Lab preview · Your package will open with confidential export selected.';
    home.prepend(hint);
  }

  function leavePlans(tryLab) {
    if(underPlans?.view==='collect') {
      trial=tryLab;
      if(!tryLab)home.querySelector('.plan-trial-notice')?.remove();
      showTrial();history.back();return;
    }
    const url=new URL(locationFor());if(tryLab)url.searchParams.set('plan','lab');
    location.assign(url.href);
  }

  function plansView(push) {
    if(push && document.body.dataset.view!=='plans') {
      underPlans={view:document.body.dataset.view,title:document.title,scroll:window.scrollY};
      history.pushState({figurePlans:true},'',pageURL('plans'));
    }
    changeView('plans');document.title='Plans · FigureRoot';
    FigurePlans.mount({host:plans,onCreate:()=>leavePlans(false),onPro:()=>leavePlans(true),onBack:()=>{if(underPlans||history.state?.figurePlans)history.back();else leavePlans(false)}});
    window.scrollTo(0,0);
  }

  window.addEventListener('popstate',()=>{
    if(new URLSearchParams(location.search).get('view')==='plans'){plansView(false);return}
    if(!underPlans){if(document.body.dataset.view==='plans')location.reload();return}
    changeView(underPlans.view);document.title=underPlans.title;window.scrollTo(0,underPlans.scroll);
  });

  function failure(message) {
    changeView('collect');
    const section=document.createElement('section');
    section.className='route-error';
    const title=document.createElement('h1');title.textContent='Package unavailable';
    const body=document.createElement('p');body.textContent=message;
    const homeButton=document.createElement('button');homeButton.className='button primary';homeButton.textContent='Open FigureRoot';homeButton.onclick=()=>location.assign(locationFor());
    section.append(title,body,homeButton);home.replaceChildren(section);
  }

  document.addEventListener('click',e=>{
    const skip=e.target.closest('a.skip');
    if(skip){
      e.preventDefault();
      const content=document.getElementById(skip.hash.slice(1));
      content?.focus();content?.scrollIntoView({block:'start'});
      return;
    }
    const link = e.target.closest('a[data-page]');
    if(link) {
      if(e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
      const page=link.dataset.page,view=document.body.dataset.view;
      if((page==='vibromat'||page==='reviewer') &&
         (view==='collect'||(view==='plans'&&underPlans?.view==='collect')) &&
         FigureCollect.hasUnsavedInput(home)) {
        link.target='_blank';link.rel='noopener';return;
      }
      link.removeAttribute('target');
      e.preventDefault();
      if(page==='plans'){if(view!=='plans')plansView(true);return}
      if(page==='upload' && view==='plans' && underPlans?.view==='collect'){history.back();return}
      const previewing=page==='vibromat' && document.querySelector('[data-mode="reviewer"][aria-pressed="true"]');
      if(!previewing && link.getAttribute('aria-current')==='page' && !home.querySelector('.route-error')){
        window.scrollTo({top:0,behavior:'smooth'});return;
      }
      navigateTo(link.href).catch(()=>failure('The last change could not be saved on this device.'));
      return;
    }
    if(e.target.closest('[data-home]')) {
      if(document.body.dataset.view==='plans'&&underPlans?.view==='collect'){history.back();return}
      if(document.body.dataset.view==='collect' && !home.querySelector('.route-error')) {window.scrollTo({top:0,behavior:'smooth'});return}
      go().catch(()=>failure('The last change could not be saved on this device.'));
    }
  });

  async function start() {
    try {db=await openDatabase()} catch {}
    if(query.get('view')==='plans'){plansView(false);return}
    const path=reviewApi && routePath.match(/^r\/(FR-[A-F0-9]{24})$/i);
    let snapshot=window.FigureExport.readShare();
    if(shared && !snapshot){failure('This reviewer link is incomplete. Open the full link or request a new copy.');return}
    if(!snapshot && (query.get('view')==='reviewer-demo' || routePath==='CSIRO-VM96')){
      snapshot=FigureExport.validateSnapshot({order:['v1','v2','v3'],notes:FigureData.notes,images:{}});
    }
    if(path && !shared) {
      const apiURL = new URL(reviewApi,base);
      apiURL.pathname = apiURL.pathname.replace(/\/$/,'') + '/' + encodeURIComponent(path[1]);
      const response=await fetch(apiURL, {cache:'no-store'});
      if(!response.ok){failure('This reviewer link is unavailable. Check the address or ask the package author for a fresh link.');return}
      const envelope=await response.json();
      snapshot=window.FigureExport.validateSnapshot(envelope.data);
    }
    if(snapshot) {
      const key=path&&!shared?'review:'+path[1]:'review:'+location.hash;
      const saved=await read(key);
      if(saved?.reviews) snapshot.reviews=saved.reviews;
      studioView(snapshot,key,true);return;
    }
    const id=query.get('studio');
    if(id==='demo'||config.pageEntry==='vibromat'||routePath==='vibromat'||location.hash==='#review') {
      const demo={order:['v1','v2','v3'],images:{},reviews:[],notes:structuredClone(FigureData.notes),privacy:'public',...await read(demoKey)};
      studioView(demo,demoKey,false);return;
    }
    if(id) {
      const key='draft:'+id;
      const state=await read(key);
      if(!state?.meta){failure('This draft was saved on another browser or device. Ask the author for its reviewer link.');return}
      studioView(state,key,false);return;
    }
    changeView('collect');
    FigureCollect.mount({host:home,saved:await listPackages(),onOpen:id=>go(id),onCreate:async draft=>{
      const record=newRecord(draft);
      if(trial)record.privacy='confidential';
      FigureExport.validateSnapshot(record);
      try {await save('draft:'+record.meta.id,record)} catch {throw Error('There is not enough browser storage to save these images. Try smaller files or free up space and try again.')}
      await go(record.meta.id);
    }});
    showTrial();
  }
  window.addEventListener('pageshow',event=>{if(event.persisted)location.reload()});
  start().catch(()=>failure('FigureRoot could not open this package. Reload the page or return to your saved packages.'));
})();
