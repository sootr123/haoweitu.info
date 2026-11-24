/* Browser-side figure export and portable reviewer packages. */
(() => {
  'use strict';

  const VERSION_IDS = ['v1', 'v2', 'v3'];
  const PACKAGE_ID = 'figureroot.io/CSIRO-VM96';
  const SHARE_LIMIT = 48000;
  const enc = new TextEncoder();
  const dec = new TextDecoder();

  function to64(bytes) {
    let binary = '';
    for (let i = 0; i < bytes.length; i += 16000) {
      binary += String.fromCharCode(...bytes.subarray(i, i + 16000));
    }
    return btoa(binary);
  }

  function from64(text) {
    return Uint8Array.from(atob(text.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0));
  }

  const safeState = globalThis.FigureSchema.validateSnapshot;

  function readShare() {
    const hash = window.location.hash;
    if (!hash.startsWith('#review=')) {
      if (document.documentElement.dataset.publicPackage === 'CSIRO-VM96') {
        return safeState({order:VERSION_IDS, notes:window.FigureData.notes, images:{}});
      }
      return null;
    }
    try {
      if (hash.length > SHARE_LIMIT) throw Error('Package is too large');
      const payload = JSON.parse(dec.decode(from64(hash.slice(8))));
      if (payload.schema !== 'FigureRoot/1') throw Error('Unknown package');
      return safeState(payload.data);
    } catch {
      return null;
    }
  }

  function staticSiteBase() {
    const {siteBase,reviewApi} = document.documentElement.dataset;
    if (!siteBase || reviewApi || !/^https?:$/.test(location.protocol)) return null;
    return new URL(siteBase,location.origin);
  }

  function makeShare(state, baseURL, staticBase) {
    // Static snapshots open the package root independently of the creator's draft query.
    const url = staticBase ? new URL(staticBase.href) : new URL(baseURL || location.href,location.href);
    if (!/^https?:$/.test(url.protocol)) return '';
    const route = document.documentElement.dataset.citationPath;
    if (route && !state.meta) {
      const baseline = safeState({order:VERSION_IDS, notes:window.FigureData.notes, images:{}});
      const target = new URL(route, staticBase || document.baseURI);
      if (!Object.keys(state.images).length && JSON.stringify(baseline) === JSON.stringify(state)) return target.href;
      url.pathname = target.pathname;
      url.search = '';
    }
    if (state.meta && /^\/r\/[A-Za-z0-9_-]+\/?$/.test(url.pathname) && !url.hash) {
      return url.href;
    }
    // Avoid generating a large base64 string for photos that need the portable file or server.
    if (Object.values(state.images).some(image => image.length > SHARE_LIMIT)) return '';
    const json = JSON.stringify({schema:'FigureRoot/1',data:state});
    if (json.length > SHARE_LIMIT) return '';
    const hash = to64(enc.encode(json)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    url.hash = 'review=' + hash;
    return url.href.length <= SHARE_LIMIT ? url.href : '';
  }

  const icons = {
    x:'<path d="m18 6-12 12M6 6l12 12"/>',
    copy:'<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
    download:'<path d="M12 3v12m-5-5 5 5 5-5M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/>',
    lock:'<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 1 1 8 0v3"/>',
    link:'<path d="m10 13 4-4m-6 7-1 1a4 4 0 0 1-6-6l4-4a4 4 0 0 1 6 0m2 1 1-1a4 4 0 0 1 6 6l-4 4a4 4 0 0 1-6 0" transform="translate(1 1)"/>'
  };
  const icon = name => '<svg class="fe-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + icons[name] + '</svg>';
  const plural = (n,s) => n + ' ' + s + (n === 1 ? '' : 's');

  function packageInfo(state,staticBase) {
    const meta=state.meta;
    if (meta) return {
      id:meta.id,title:meta.title,subtitle:'Figure package',author:meta.author,finalId:meta.finalId,
      label:meta.id,credit:meta.author ? 'Package author · '+meta.author : '',custom:true
    };
    const route = document.documentElement.dataset.citationPath || 'CSIRO-VM96/';
    const label = staticBase ? new URL(route,staticBase).href : 'https://'+PACKAGE_ID;
    return {
      id:'CSIRO-VM96', title:'CSIRO VibroMat', subtitle:'Figure 1 · Wearable Tactile Sensory Substitution System (TRL 5–7)',
      author:'Howard Tu', finalId:'v3', label, stampLabel:staticBase ? label : PACKAGE_ID, custom:false,
      credit:'Package author · Howard Tu. Team · Vision Processing Team (CSIRO Data61 / Swinburne). The product concepts, author notes and review history belong to this FigureRoot demonstration.',
      sourceLabel:'CSIRO Commercialisation Marketplace — VibroMat',
      sourceURL:'https://www.csiro.au/en/work-with-us/ip-commercialisation/marketplace/vibromat'
    };
  }

  function textFor(state,info) {
    const finalNotes = state.notes.filter(n => n.version === info.finalId);
    const count = kind => finalNotes.filter(n => n.type === kind).length;
    if (info.custom) {
      const final = state.meta.versions[info.finalId];
      const toolCredit = final.tool ? ' AI tool: '+final.tool+'.' : '';
      const modelCredit = final.model ? ' Model/version: '+final.model+'.' : '';
      const author = info.author ? ' Prepared by '+info.author+'.' : '';
      const counts = plural(count('confirmed'),'confirmed note')+', '+plural(count('uncertain'),'uncertain note')+
        ', and '+plural(count('filler'),'AI filler note');
      return {
        caption:info.title+'. Final figure: '+final.title+'.'+author+toolCredit+modelCredit+' Package history includes '+plural(state.order.length,'version')+
          '. The final figure has '+counts+'. FigureRoot package: '+info.label,
        stamp:'FigureRoot | '+info.id+' | '+plural(count('uncertain'),'Uncertain Note')
      };
    }
    const uncertain = finalNotes.filter(n => n.type === 'uncertain');
    const originalPair = uncertain.length === 2 &&
      uncertain.some(n => n.title === '96 Pager Motors vs. Visualised Grid Count') &&
      uncertain.some(n => n.title === 'Commercial Form Factor & Battery Ergonomics');
    const params = plural(count('uncertain'), 'uncertain/approximate parameter') +
      (originalPair ? ' (96-motor array scale & housing ergonomics)' : '');
    const summary = plural(count('confirmed'), 'confirmed mechanism') + ', ' + params + ', and ' +
      plural(count('filler'), 'ignored AI filler element');
    return {
      caption:'Figure 1 (AI-Assisted Concept Visual): CSIRO VibroMat sensory substitution system. FigureRoot demo provenance: GPT-4o (3 iterations), curated by Howard Tu. Contains ' +
        summary + '. Inspect full prompt & iteration root: ' + info.label,
      stamp:'FigureRoot | ' + info.stampLabel + ' | ' + plural(count('uncertain'), 'Uncertain Note')
    };
  }

  function renderFigure(src, notes, stamp) {
    return new Promise((resolve,reject) => {
      const img = new Image();
      img.onload = () => {
        try {
          const scale = Math.min(2100 / img.naturalWidth, 2100 / img.naturalHeight);
          const canvas = document.createElement('canvas');
          canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
          const artHeight = Math.max(1, Math.round(img.naturalHeight * scale));
          const unit = canvas.width / 1000;
          const stampFont = Math.max(8, Math.round(unit * 11));
          const strip = stamp ? Math.ceil(stampFont * 2.6) : 0;
          canvas.height = artHeight + strip;
          const c = canvas.getContext('2d');
          c.fillStyle = '#fff';
          c.fillRect(0, 0, canvas.width, canvas.height);
          c.drawImage(img, 0, 0, canvas.width, artHeight);
          for (const n of notes) {
            const color = {confirmed:'#237356',uncertain:'#ab6810',filler:'#536577'}[n.type];
            const x = n.x * canvas.width, y = n.y * artHeight, r = n.r * canvas.width;
            c.beginPath();
            c.arc(x,y,r,0,Math.PI*2);
            c.strokeStyle = color;
            c.lineWidth = 2 * unit;
            const dash = {confirmed:[], uncertain:[7*unit,4*unit],filler:[1*unit,4*unit]}[n.type];
            c.setLineDash(dash);
            c.lineCap = 'round';
            c.stroke();
            c.setLineDash([]);
            const badge = Math.max(8*unit, String(n.id).length * 3.8*unit);
            const bx = Math.max(badge,Math.min(canvas.width-badge,x+r*.707));
            const by = Math.max(badge,Math.min(artHeight-badge,y-r*.707));
            c.beginPath();
            c.arc(bx,by,badge,0,Math.PI*2);
            c.fillStyle = color;
            c.fill();
            c.strokeStyle = '#fff';
            c.lineWidth = unit;
            c.stroke();
            c.fillStyle = '#fff';
            c.textAlign = 'center';
            c.textBaseline = 'middle';
            c.font = 'bold ' + Math.round(badge*1.35) + 'px sans-serif';
            c.fillText(String(n.id), bx, by);
          }
          c.fillStyle = '#394e46';
          c.font = stampFont + 'px monospace';
          c.textAlign = 'right';
          c.textBaseline = 'middle';
          if (stamp) c.fillText(stamp, canvas.width - 9*unit, artHeight + strip/2, canvas.width-18*unit);
          resolve(canvas);
        } catch (e) { reject(e); }
      };
      img.onerror = () => reject(Error('The figure could not be loaded.'));
      img.src = src;
    });
  }

  function blobFrom(canvas) {
    return new Promise((resolve,reject) => {
      canvas.toBlob(b => b ? resolve(b) : reject(Error('The PNG could not be created.')), 'image/png');
    });
  }

  function download(blob,filename) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 60000);
  }

  async function clipboard(value, root) {
    try { await navigator.clipboard.writeText(value); return; } catch { /* Local and embedded viewers may need a selection. */ }
    const focused = document.activeElement;
    const field = document.createElement('textarea');
    field.value = value;
    field.setAttribute('readonly','');
    field.style.cssText = 'position:fixed;top:0;left:0;opacity:0;width:1px;height:1px';
    root.append(field);
    field.select();
    const success = document.execCommand('copy');
    field.remove();
    focused?.focus();
    if (!success) throw Error('Select the text and use your system copy command.');
  }

  async function copyCaption(caption, share, label, root) {
    if (!share) return clipboard(caption,root);
    // Link only the identifier at the end, even when an author also used it in the title.
    const prefix = caption.slice(0,-label.length);
    const plain = prefix + share;
    const escape = text => text.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const linked = '<p>' + escape(prefix) + '<a href="'+escape(share)+'">'+escape(label)+'</a></p>';
    try {
      await navigator.clipboard.write([new ClipboardItem({
        'text/plain':new Blob([plain],{type:'text/plain'}),
        'text/html':new Blob([linked],{type:'text/html'})
      })]);
    } catch { await clipboard(plain,root); }
  }

  async function embeddedImage(src) {
    if (src.startsWith('data:')) return src;
    const response = await fetch(src);
    if (!response.ok) throw Error('Could not read the saved figure.');
    const blob = await response.blob();
    return new Promise((resolve,reject) => {
      const reader = new FileReader();
      reader.onerror = () => reject(Error('Could not embed an image.'));
      reader.onload = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });
  }

  // This function is embedded in the portable HTML. Keep its dependencies inside its body.
  function portableReader() {
    'use strict';
    const root = document.querySelector('main');
    const payload = JSON.parse(document.getElementById('snapshot').textContent);
    const el = (tag,text,className) => {
      const n = document.createElement(tag);
      if (text !== undefined) n.textContent = text;
      if (className) n.className = className;
      return n;
    };
    function render(data) {
      const {state, versions, caption, info} = data;
      let selected = info.finalId;
      root.replaceChildren();
      const header = el('header');
      header.append(el('small','FIGUREROOT   /   '+info.id),el('h1',info.title),el('p',info.subtitle));
      if (info.custom && info.author) header.append(el('p',info.credit));
      const nav = el('nav'), stage = el('section'), sig = el('section');
      const count = type => state.notes.filter(n => n.version === info.finalId && n.type === type).length;
      const banner = el('p','The author flagged '+count('uncertain')+' still uncertain / approximate areas and '+count('filler')+' AI filler details on the final figure. Inspect its circle notes before citing the figure.','alert');
      root.append(header,banner,nav,stage,sig);
      const tabs = {};
      state.order.forEach(id => {
        const btn = el('button',info.custom ? versions[id].title : id.toUpperCase());
        btn.onclick = () => { selected=id; display(); };
        tabs[id] = btn;
        nav.append(btn);
      });
      const reviews = [];
      let reviewKey;
      let persist = false;
      if (!payload.sealed) {
        reviewKey = 'figureroot-offline:' + location.pathname + ':' + data.snapshotId;
        try {
          const saved = JSON.parse(localStorage.getItem(reviewKey) || '[]');
          if (Array.isArray(saved)) reviews.push(...saved.filter(r => typeof r.comment === 'string' && typeof r.time === 'string'));
          persist = true;
        } catch {}
      }
      function display() {
        stage.replaceChildren();
        for (const [id,button] of Object.entries(tabs)) button.setAttribute('aria-pressed',String(id===selected));
        const v = versions[selected], notes = state.notes.filter(n=>n.version===selected);
        if (v.kind) stage.append(el('small',v.kind.toUpperCase()));
        stage.append(el('h2',v.title));
        const art = el('div',undefined,'art'), img = el('img');
        img.src=v.image;
        img.alt=v.alt || v.title;
        art.append(img);
        const list = el('div');
        const labels={confirmed:'Confirmed',uncertain:'Still uncertain',filler:'AI filler'};
        for (const note of notes) {
          const card = el('details'), summary = el('summary','#'+note.id+' · '+labels[note.type]+' · '+note.title);
          card.append(summary,el('p',note.body));
          list.append(card);
          const ring = el('button',undefined,'ring '+note.type);
          ring.setAttribute('aria-label','Inspect note '+note.id+' – '+note.title);
          ring.style.left=note.x*100+'%';
          ring.style.top=note.y*100+'%';
          ring.style.width=note.r*200+'%';
          ring.append(el('b',String(note.id)));
          ring.onclick=()=>{ card.open=true; summary.focus(); card.scrollIntoView({block:'nearest'}); };
          art.append(ring);
        }
        stage.append(art,list);
        const history=el('section',undefined,'history');
        if (info.custom) {
          const sketch = v.kind === 'sketch';
          history.append(el('h3',sketch ? 'Sketch history' : 'Generation history'));
          const fields = el('dl',undefined,'provenance');
          const addField = (label,value,exact=false) => {
            const present = typeof value === 'string' && value.trim() !== '';
            const content = el('dd',present ? value : 'Not recorded',present && exact ? 'verbatim' : '');
            fields.append(el('dt',label),content);
          };
          if (sketch) {
            addField('Medium',v.tool);
            addField('Sketch notes',v.prompt,true);
            if (v.why && v.why !== v.prompt) addField('Changes to the sketch',v.why,true);
          } else {
            if (v.aiUse) addField('How AI was used',v.aiUse);
            addField('AI tool',v.tool);
            addField('Model / version',v.model);
            addField('Exact prompt',v.prompt,true);
            addField('Human edits',v.why,true);
          }
          if (v.filename) addField('Source file',v.filename);
          history.append(fields);
        } else {
          history.append(el('h3','Prompt history'));
          if (v.tool) history.append(el('small','Demo tool history · '+v.tool));
          if (v.prompt) history.append(el('p',v.prompt));
          if (v.why) history.append(el('p',v.why));
          if (v.actualPrompt) {
            const actual=el('details');
            actual.append(el('summary','Product photo generation prompt'),el('p',v.actualPrompt));
            history.append(actual);
          }
        }
        stage.append(history);
      }
      display();
      const meta=el('details');
      meta.append(el('summary','Citation & source'),el('p',caption));
      if (info.credit) meta.append(el('p',info.credit));
      if (info.sourceURL) {
        const source=el('a',info.sourceLabel);
        source.href=info.sourceURL;
        meta.append(source);
      }
      const field=el('textarea'), label=el('label','Reviewer sign-off'), button=el('button','Acknowledge & Record Review');
      label.htmlFor=field.id='review-comment';
      field.value=data.reviewExample;
      const status=el('p',''), records=el('div');
      status.setAttribute('role','status');
      const showRecords=()=>records.replaceChildren(...reviews.map(r=>el('p',r.time+' — '+r.comment)));
      button.onclick=()=>{
        if(!field.value.trim()){field.focus();return;}
        const record={time:new Date().toISOString(),comment:field.value.trim()};
        reviews.push(record);
        if(persist) {try{localStorage.setItem(reviewKey,JSON.stringify(reviews));}catch{persist=false;}}
        field.value=''; showRecords(); status.textContent=persist?'Review recorded in this browser.':'Review recorded in this session.';
      };
      sig.append(meta,el('h2','Review record'),label,field,button,status,records);
      showRecords();
    }

    if (!payload.sealed) {render(payload.data);return;}
    const un64=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
    const form=el('form'), label=el('label','Package passphrase'), pwd=el('input'), button=el('button','Open partner package'), status=el('p','');
    pwd.type='password'; pwd.required=true; pwd.id='package-password'; label.htmlFor=pwd.id;
    status.setAttribute('role','status'); form.append(label,pwd,button,status);
    root.append(el('small','FIGUREROOT   /   PARTNER PACKAGE'),el('h1','Confidential inspection'),el('p','Enter the passphrase provided by the package author.'),form);
    form.onsubmit=async e=>{
      e.preventDefault();
      if (!crypto.subtle) {status.textContent='Open the downloaded file directly in a current browser to unlock it.';return;}
      button.disabled=true;
      try {
        const keyData=await crypto.subtle.importKey('raw',new TextEncoder().encode(pwd.value),'PBKDF2',false,['deriveKey']);
        const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:un64(payload.salt),iterations:310000,hash:'SHA-256'},keyData,{name:'AES-GCM',length:256},false,['decrypt']);
        const clear=await crypto.subtle.decrypt({name:'AES-GCM',iv:un64(payload.iv)},key,un64(payload.ciphertext));
        render(JSON.parse(new TextDecoder().decode(clear)));
      } catch {status.textContent='Could not unlock this package. Check the passphrase and try again.';}
      finally{button.disabled=false;}
    };
  }

  const readerCSS = `
  *{box-sizing:border-box}body{margin:0;color:#263530;background:#f2f4ef;font:16px/1.52 system-ui,sans-serif}main{max-width:960px;background:#fff;margin:32px auto;padding:clamp(18px,4vw,46px);border:1px solid #dce1db;border-radius:15px}small{color:#50645a;font:12px/1.5 ui-monospace,monospace}h1{font-size:clamp(30px,5vw,48px);line-height:1.13;margin:12px 0}h2{font-size:22px}h3{font-size:15px}button,input,textarea{font:inherit}button{border:1px solid #acc1b4;background:white;color:#184633;border-radius:7px;padding:8px 14px;cursor:pointer}button[aria-pressed=true],form button{color:white;background:#254e3e}nav{display:flex;gap:8px;flex-wrap:wrap;margin:22px 0}.art{position:relative;border:1px solid #e1e5df;background:white}.art img{display:block;width:100%;height:auto}.ring{position:absolute;aspect-ratio:1;height:auto;padding:0;transform:translate(-50%,-50%);border-radius:50%;background:transparent;border:2px solid #337659}.ring.uncertain{border-style:dashed;border-color:#ac6e19}.ring.filler{border-style:dotted;border-color:#647383}.ring b{position:absolute;top:-7px;right:5%;display:grid;place-items:center;border-radius:100%;background:#344c42;color:white;font:700 12px/22px system-ui;min-width:22px}details{padding:10px 0;border-bottom:1px solid #dfe5df}summary{cursor:pointer;font-weight:600}details p,.history p{white-space:pre-line}label{display:block;font-weight:600;font-size:14px}input,textarea{display:block;width:100%;padding:10px;border:1px solid #b7c7ba;border-radius:5px;margin:6px 0 12px}textarea{min-height:75px}a{color:#216949}p{overflow-wrap:anywhere}.provenance{margin:0 0 24px}.provenance dt{font-size:13px;font-weight:650;color:#465d4e;margin:13px 0 3px}.provenance dd{margin:0;overflow-wrap:anywhere}.provenance .verbatim{white-space:pre-wrap}.alert{background:#fff6df;color:#755018;padding:12px 14px;border:1px solid #edca82;border-radius:6px}button:focus-visible,summary:focus-visible{outline:3px solid #096745;outline-offset:3px}@media(max-width:800px){main{margin:0;border-radius:0}} `;

  async function seal(data, passphrase) {
    if (!window.crypto?.subtle) throw Error('Open this prototype on HTTPS or localhost to encrypt a package.');
    const salt = crypto.getRandomValues(new Uint8Array(16)), iv = crypto.getRandomValues(new Uint8Array(12));
    const keyData = await crypto.subtle.importKey('raw',enc.encode(passphrase),'PBKDF2',false,['deriveKey']);
    const key = await crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:310000,hash:'SHA-256'},keyData,{name:'AES-GCM',length:256},false,['encrypt']);
    const cipher = await crypto.subtle.encrypt({name:'AES-GCM',iv},key,enc.encode(JSON.stringify(data)));
    return {sealed:true,salt:to64(salt),iv:to64(iv),ciphertext:to64(new Uint8Array(cipher))};
  }

  async function portable(state,versions,info,caption,passphrase) {
    const embedded = {};
    await Promise.all(state.order.map(async id => {
      const v=versions[id];
      embedded[id]={
        title:v.title || v.name || id,
        kind:v.kind || '',
        alt:v.alt || '',
        filename:v.filename || '',
        tool:v.tool || '',
        model:v.model || '',
        aiUse:v.aiUse || '',
        prompt:v.prompt || '',
        why:v.why || '',
        actualPrompt:v.actualPrompt || '',
        image:await embeddedImage(state.images[id] || v.image)
      };
    }));
    let reviewExample='';
    if (!info.custom) reviewExample = state.images.v3
      ? 'Commercialisation Manager: I reviewed the annotations on the uploaded concept figure.'
      : 'Commercialisation Manager: The illustrated grid shows 45 nodes. CSIRO specifies 96 motors in the original prototype. This distinction keeps our licensing materials accurate.';
    const data={versions:embedded,state:{order:state.order,notes:state.notes},info,caption,reviewExample,snapshotId:crypto.randomUUID()};
    const payload=passphrase ? await seal(data,passphrase) : {sealed:false,data};
    const json=JSON.stringify(payload).replace(/</g,'\\u003c');
    const html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FigureRoot · Reviewer package</title><style>'+readerCSS+'</style><main></main><script type="application/json" id="snapshot">'+json+'<\/script><script>('+portableReader.toString()+')();<\/script></html>';
    return new Blob([html],{type:'text/html;charset=utf-8'});
  }

  let activeDialog;
  function open({state, versions, baseURL, onPrivacy}) {
    if (activeDialog?.open) return;
    const previous = document.activeElement;
    const snapshot = safeState(state);
    const staticBase = staticSiteBase();
    const info = packageInfo(snapshot,staticBase);
    if (snapshot.meta) versions = snapshot.meta.versions;
    let share = makeShare(snapshot,baseURL,staticBase);
    const {caption,stamp} = textFor(snapshot,info);
    const apiFlag = document.documentElement.dataset.reviewApi;
    const canPublish = info.custom && apiFlag !== undefined && apiFlag !== 'false' && /^https?:$/.test(location.protocol);
    const finalNotes = snapshot.notes.filter(note => note.version === info.finalId);
    const basename = 'FigureRoot-'+info.id;
    const dialog = document.createElement('dialog');
    activeDialog=dialog;
    dialog.className='fe-dialog';
    dialog.setAttribute('aria-labelledby','fe-title');
    dialog.innerHTML=`
      <header class="fe-header"><div><p class="fe-ident"></p><h2 id="fe-title">Export figure &amp; citation</h2></div><button type="button" class="fe-close" aria-label="Close export" autofocus>${icon('x')}</button></header>
      <div class="fe-scroll">
        <figure class="fe-preview"><div class="fe-canvas"><span>Preparing figure…</span></div><figcaption>Export preview <span>PNG · FINAL VERSION</span></figcaption></figure>
        <div class="fe-layers"><label><input type="checkbox" data-layer="stamp" checked> Include citation stamp</label><label><input type="checkbox" data-layer="notes" checked> Include circle notes</label></div>
        <div class="fe-section"><div class="fe-labelrow"><label for="fe-caption">Figure caption</label><button class="fe-text-button" data-act="caption">${icon('copy')} Copy caption</button></div>
          <textarea id="fe-caption" class="fe-caption" rows="4" readonly></textarea></div>
        <fieldset class="fe-section fe-access"><legend>Package access</legend>
          <div class="fe-choices">
            <label><input type="radio" name="fe-mode" value="public"><span>${icon('link')}<span>Public citation link<small>Free</small></span></span></label>
            <label><input type="radio" name="fe-mode" value="confidential"><span>${icon('lock')}<span>Confidential IP/partner package<small>Pro Lab Plan</small></span></span></label>
          </div>
        </fieldset>
        <div class="fe-share" data-panel="public">
          <div class="fe-linkfield"><label for="fe-link">Reviewer snapshot link</label><div class="fe-inputrow"><input id="fe-link" readonly aria-label="Reviewer snapshot link"><button class="fe-standard" data-act="link">${icon('copy')} Copy link</button></div></div>
          <p class="fe-hint" data-hint="public"></p>
          <button class="fe-standard" data-act="publish" hidden>${icon('link')} Create reviewer link</button>
          <button class="fe-text-button" data-act="portable">${icon('download')} Download offline reviewer package</button>
        </div>
        <div class="fe-share" data-panel="confidential" hidden><label for="fe-pass">Partner passphrase</label><input id="fe-pass" type="password" minlength="12" autocomplete="new-password" placeholder="At least 12 characters"><p class="fe-hint">The downloaded HTML encrypts the figures, version history and circle notes. Send the passphrase to your partner separately.</p>
          <button class="fe-standard" data-act="encrypt">${icon('lock')} Download encrypted package</button></div>
      </div>
      <footer class="fe-footer"><span class="fe-status" role="status" aria-live="polite"></span><button class="fe-primary" data-act="png" disabled>${icon('download')} Download figure</button></footer>`;
    document.body.append(dialog);
    const q=s=>dialog.querySelector(s);
    const status=t=>{q('.fe-status').textContent=t;};
    const action=name=>q('[data-act="'+name+'"]');
    let privacy = state.privacy==='confidential'?'confidential':'public';
    let busy=false;
    const setMode = () => {
      q('[name=fe-mode][value="'+privacy+'"]').checked=true;
      q('[data-panel=public]').hidden=privacy!=='public';
      q('[data-panel=confidential]').hidden=privacy!=='confidential';
      q('#fe-pass').value='';
      status('');
    };
    q('.fe-close').onclick=()=>dialog.close();
    dialog.addEventListener('click',e=>{
      if(e.target!==dialog) return;
      const b=dialog.getBoundingClientRect();
      if(e.clientX<b.left || e.clientX>b.right || e.clientY<b.top || e.clientY>b.bottom) dialog.close();
    });
    dialog.addEventListener('close',()=>{
      dialog.remove(); activeDialog=null;
      if(previous?.isConnected)previous.focus();
    },{once:true});
    q('.fe-ident').textContent=info.id + (info.custom ? ' / FINAL FIGURE' : ' / FIGURE 1');
    q('#fe-caption').value=caption;
    q('#fe-link').value=share;
    q('.fe-linkfield').hidden=!share;
    const localShare = share && ['localhost','127.0.0.1','[::1]'].includes(new URL(share).hostname);
    let guidance = 'Use the offline package to share the figures, version history and circle notes together.';
    if (staticBase && !share) guidance = 'This snapshot is too large for a citation link. Download the offline reviewer package to share the images, prompts and notes in one HTML file.';
    if (share) guidance = localShare
      ? 'This address opens on this computer. Use the offline package to share with another device.'
      : 'The link opens this snapshot on the current site. Anyone with site access and the link can inspect it.';
    const alreadyHosted = share && /^\/r\/[A-Za-z0-9_-]+\/?$/.test(new URL(share).pathname) && !new URL(share).hash;
    action('publish').hidden = !canPublish || alreadyHosted;
    if (!action('publish').hidden) guidance = 'Create a hosted reviewer link to upload a fixed copy of the images, version history and notes. Anyone with the link and site access can inspect it.';
    q('[data-hint=public]').textContent = guidance;
    dialog.querySelectorAll('[name=fe-mode]').forEach(r=>r.onchange=()=>{
      privacy=r.value;
      setMode();
      onPrivacy?.(privacy);
    });
    setMode();
    dialog.showModal();
    function run(button,fn) {
      button.onclick=async () => {
        if(busy) return;
        busy=true;button.disabled=true;status('');
        try{await fn();}catch(err){if(dialog.isConnected)status(err.message || 'Could not finish the export.');}
        finally{busy=false;if(dialog.isConnected)button.disabled=false;}
      };
    }
    run(action('caption'),async()=>{
      await copyCaption(caption,privacy === 'public' ? share : '',info.label,dialog);
      status('Caption copied.');
    });
    run(action('publish'),async()=>{
      if (!canPublish || privacy !== 'public') return;
      status('Creating reviewer snapshot…');
      try {
        const response=await fetch('/api/packages',{
          method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({data:snapshot}),
          credentials:'same-origin',redirect:'error'
        });
        if (!response.ok) throw Error('Upload failed');
        const result=await response.json();
        if (typeof result.url !== 'string') throw Error('Invalid reviewer link');
        const url=new URL(result.url,location.origin);
        if (url.origin !== location.origin || !/^\/r\/[A-Za-z0-9_-]+\/?$/.test(url.pathname) || url.search || url.hash || url.username || url.password) {
          throw Error('Invalid reviewer link');
        }
        share=url.href;
        q('#fe-link').value=share;
        q('.fe-linkfield').hidden=false;
        action('publish').hidden=true;
        q('[data-hint=public]').textContent='This link opens the saved snapshot. Later changes to your studio package stay in the studio.';
        status('Reviewer link created.');
      } catch {
        status('Could not create a hosted link. Retry or download the offline reviewer package.');
      }
    });
    run(action('link'),async()=>{await clipboard(share,dialog);status('Reviewer link copied.');});
    run(action('portable'),async()=>{
      status('Preparing reviewer package…');
      const blob=await portable(snapshot,versions,info,caption,'');
      download(blob,basename+'-review.html');
      status('Reviewer package downloaded.');
    });
    run(action('encrypt'),async()=>{
      const input=q('#fe-pass');
      if(input.value.length<12){status('Use a passphrase of at least 12 characters.');input.focus();return;}
      status('Encrypting partner package…');
      const blob=await portable(snapshot,versions,info,caption,input.value);
      download(blob,basename+'-confidential.html');
      input.value='';
      status('Encrypted package downloaded.');
    });
    let renderId=0;
    let currentCanvas=null;
    run(action('png'),async()=>{
      if (!currentCanvas) return;
      download(await blobFrom(currentCanvas),basename+'-'+info.finalId+'.png');
      status('Figure downloaded.');
    });
    async function updatePreview() {
      const epoch=++renderId;
      currentCanvas=null;
      action('png').disabled=true;
      const withStamp=q('[data-layer=stamp]').checked;
      const withNotes=q('[data-layer=notes]').checked;
      try {
        const canvas=await renderFigure(snapshot.images[info.finalId] || versions[info.finalId].image, withNotes ? finalNotes : [], withStamp ? stamp : '');
        if (!dialog.isConnected || epoch !== renderId) return;
        canvas.setAttribute('aria-label','Final figure for '+info.title + (withNotes?' with circle notes':'') + (withStamp?' and citation stamp':''));
        canvas.setAttribute('role','img');
        q('.fe-canvas').replaceChildren(canvas);
        currentCanvas=canvas;
        action('png').disabled=false;
      } catch {
        if(dialog.isConnected && epoch === renderId) q('.fe-canvas').textContent='Could not load the final figure. Reopen the package and try again.';
      }
    }
    dialog.querySelectorAll('[data-layer]').forEach(input=>input.onchange=updatePreview);
    updatePreview();
  }

  // Browsers retain this document when the user pastes a different snapshot fragment
  // in the same tab. Reload the app so the snapshot is mounted in reviewer mode.
  window.addEventListener('hashchange', event => {
    const previous = new URL(event.oldURL).hash;
    const current = new URL(event.newURL).hash;
    if (previous.startsWith('#review=') || current.startsWith('#review=')) window.location.reload();
  });

  window.FigureExport = Object.freeze({open,readShare,validateSnapshot:safeState});
})();
