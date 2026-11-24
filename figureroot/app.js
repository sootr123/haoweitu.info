'use strict';

window.FigureStudio = (() => {
  let mounted = false;
  return {mount(options) {
    if (mounted) return;
    mounted = true;
    mountWorkspace(options);
  }};
})();

function mountWorkspace({initialState, share, persist:saveRecord}) {
  const state = initialState;
  const meta = state.meta;
  const demo = !meta;
  const {types, source} = window.FigureData;
  const versions = meta?.versions || window.FigureData.versions;
  const finalId = meta?.finalId || 'v3';
  const reviewExample = demo ? window.FigureData.reviewExample : '';
  const studio = document.getElementById('studio');
  const topbar = document.getElementById('mode-tabs').closest('header');
  const versionLabel = id => demo
    ? {v1:'Initial draft',v2:'Revision',v3:'Packaged figure'}[id]
    : {sketch:'Sketch',iteration:'Iteration',final:'Final figure'}[versions[id].kind] || 'Iteration';
  const $ = (selector, root = document) => root.querySelector(selector);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const icon = name => window.figureIcon(name);
  const pad = n => String(n).padStart(2, '0');
  const ui = {mode:share || location.hash === '#review' ? 'reviewer':'creator',version:finalId,filter:'all',selected:null,compare:false,before:state.order.find(id=>id!==finalId)||finalId,after:finalId,adding:false,showNotes:true,reordering:false,large:false};
  const creator = () => ui.mode === 'creator' && !share;
  let toastTimer, uploadVersion, dialogReturn, relocation = null, reviewDraft = state.images[finalId] ? '' : reviewExample;
  const imageOf = id => state.images[id] || versions[id].image;
  const currentNotes = () => state.notes.filter(n => n.version === ui.version);
  const matching = () => currentNotes().filter(n => ui.filter === 'all' || n.type === ui.filter);
  const num = (list, type) => list.filter(n => n.type === type).length;
  const safeIconButton = (action,name,label) => `<button class="icon-btn" data-action="${action}" title="${esc(label)}" aria-label="${esc(label)}">${icon(name)}</button>`;
  const chip = type => `<span class="status ${type}"><b></b>${esc(types[type])}</span>`;
  function toast(message) {
    const node = $('#toast');
    node.textContent = message;
    node.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => node.classList.remove('visible'),3200);
  }
  function persist() {
    const record = share ? {reviews:state.reviews} : state;
    try {
      Promise.resolve(saveRecord(record)).catch(reportSaveError);
    } catch { reportSaveError(); }
  }
  function reportSaveError() {
    toast('Changes could not be saved in this browser. Export to keep a copy.');
  }
  function renderMetadata() {
    $('#versions-count').textContent=state.order.length;
    if (demo) return;
    const el=selector=>$(selector,studio);
    document.title=meta.title+' · FigureRoot';
    el('#package-title').textContent=meta.title;
    el('.crumb .mono').textContent=meta.id;
    el('.trl').remove();
    el('.hero-source strong').textContent=meta.author || 'Unspecified';
    el('.subtitle').textContent=state.order.length+' '+(state.order.length===1?'image':'images')+' in this citation package';
    el('.inspector .source-card')?.remove();
    el('footer .mono').textContent=meta.id+' / Citation package';
    const avatar=$('.avatar',topbar);
    if (avatar) {
      const parts=(meta.author||'').trim().split(/\s+/).filter(Boolean);
      avatar.textContent=parts.length?((parts[0][0]||'')+(parts.length>1?parts.at(-1)[0]:'')).toUpperCase():'FR';
      avatar.title=avatar.ariaLabel='Package details';
    }
  }
  function refresh() {
    $('#mode-tabs').innerHTML = [
      ...(share ? [] : [['creator','scan-line','Creator Studio']]),
      ['reviewer','scan-eye',share?'Reviewer View':'Reviewer preview']
    ].map(([id,ico,label])=>`<button class="mode ${ui.mode===id?'active':''}" data-mode="${esc(id)}" aria-pressed="${ui.mode===id}">${icon(ico)} ${label}</button>`).join('');
    $('#review-alert').innerHTML='';
    if (ui.mode==='reviewer') {
      const list = state.notes.filter(n=>n.version===finalId);
      const uncertain = num(list,'uncertain'), filler = num(list,'filler');
      if (demo) {
        $('#review-alert').innerHTML=`<div class="alert">${icon('triangle-alert')}<span>Author flagged <strong>${uncertain} still uncertain / approximate areas</strong> and <strong>${filler} AI filler details</strong> on Figure 1. Inspect circles before quoting in patent or partner docs.</span></div>`;
      } else if (uncertain || filler) {
        const flagged=[];
        if(uncertain)flagged.push(uncertain+' uncertain '+(uncertain===1?'area':'areas'));
        if(filler)flagged.push(filler+' AI filler '+(filler===1?'detail':'details'));
        $('#review-alert').innerHTML=`<div class="alert">${icon('triangle-alert')}<span>The author flagged <strong>${flagged.join(' and ')}</strong> on the final figure. Inspect its circle notes before citing it.</span></div>`;
      }
    }
    renderViewer(); renderNotes(); renderHistory(); renderReview();
  }
  function circles() {
    if (!ui.showNotes) return '';
    return matching().map(n=>`<button style="left:${n.x*100}%;top:${n.y*100}%;width:${n.r*200}%" class="hotspot ${n.type} ${ui.selected===n.id?'chosen':''}" data-note="${n.id}" aria-label="${esc('Note '+n.id+' · '+types[n.type]+' · '+n.title)}" title="${esc(n.title)}"><b>${pad(n.id)}</b></button>`).join('');
  }
  function compareColumn(id, side) {
    return `<div class="compare-col"><div class="compare-label"><span>${side==='before'?'Before':'After'}</span><select aria-label="${side} version" data-compare="${side}">${state.order.map(v=>`<option value="${esc(v)}" ${v===id?'selected':''}>${esc(v)} · ${esc(versions[v].title)}</option>`).join('')}</select></div><img src="${esc(imageOf(id))}" alt="${esc(versions[id].alt)}"><p>${esc(versions[id].summary)}</p></div>`;
  }
  function renderViewer() {
    const id=ui.version;
    const list=currentNotes();
    $('#viewer').classList.toggle('expanded',ui.large);
    document.body.classList.toggle('expanded-canvas',ui.large);
    $('#viewer').innerHTML=`<div class="panel-heading"><div class="heading-group">${icon('scan')}<h2>Figure workspace</h2></div><div class="flex items-center gap-2">${state.order.length>1?`<button class="small-btn compare ${ui.compare?'on':''}" data-action="compare" aria-pressed="${ui.compare}">${icon('columns-2')} Compare</button>`:''}${safeIconButton('expand',ui.large?'minimize-2':'maximize-2',ui.large?'Close expanded figure':'Expand figure')}</div></div>
      ${ui.compare?`<div class="compare-grid">${compareColumn(ui.before,'before')}${compareColumn(ui.after,'after')}</div>`:
      `<div class="canvas-wrap"><div class="photo ${creator()?'editable':''} ${ui.adding?'placing':''}" id="photo"><img id="figure-photo" src="${esc(imageOf(id))}" alt="${esc(versions[id].alt)}">${circles()}</div></div>`}
      <div class="figure-caption"><div class="caption-title"><span class="version-badge">${esc(id)}</span><span>${ui.compare?'Version comparison':esc(versions[id].title)}</span></div><div class="caption-tools">
      ${!ui.compare?safeIconButton('visibility',ui.showNotes?'eye':'eye-off',ui.showNotes?'Hide circle notes':'Show circle notes'):''}
      ${creator()&&!ui.compare?safeIconButton('upload','image-up','Upload custom image for this version'):''}
      ${!ui.compare?safeIconButton('history','file-clock','View prompt and image source'):''}</div></div>
      <div class="canvas-foot"><span>${icon(ui.compare?'git-compare-arrows':'mouse-pointer-2')} ${ui.compare?'Choose two versions to compare.':ui.adding?(relocation?'Click the new circle location.':'Click the figure to place your circle.'):list.length?'Select a circle to inspect its note.':creator()?'Click the figure to add a circle note.':'This iteration has no circle notes.'}</span>
      ${creator()&&!ui.compare?`<button class="text-btn" data-action="add">${icon(ui.adding?'x':'circle-plus')}${ui.adding?'Cancel':'Add circle'}</button>`:''}</div>`;
  }
  function renderNotes() {
    const list=currentNotes(), notes=matching();
    const selected=notes.find(n=>n.id===ui.selected);
    $('#notes').innerHTML=`<div class="panel-heading"><div class="heading-group">${icon('circle-dot')}<h2>Circle notes</h2></div><span class="counter">${pad(list.length)}</span></div>
      <div class="filter-bar"><label class="filter-control">${icon('list-filter')}<select id="note-filter" aria-label="Filter circle notes by status">${[['all','All statuses'],['uncertain','Still uncertain'],['confirmed','Confirmed'],['filler','AI filler']].map(([val,label])=>`<option value="${val}" ${ui.filter===val?'selected':''}>${label} (${val==='all'?list.length:num(list,val)})</option>`).join('')}</select>${icon('chevron-down')}</label></div>
      <div class="notes-list">${notes.map(n=>`<div class="note-entry ${ui.selected===n.id?'open':''}"><button class="note-summary" aria-expanded="${ui.selected===n.id}" data-note="${n.id}"><span class="note-number ${n.type}">${pad(n.id)}</span><span class="note-info">${chip(n.type)}<strong>${esc(n.short||n.title)}</strong></span>${icon(ui.selected===n.id?'chevron-down':'chevron-right')}</button>
      ${selected===n?`<div class="note-body"><h3>${esc(n.title)}</h3><p>${esc(n.body)}</p>${creator()?`<button class="text-btn" data-edit="${n.id}">${icon('pencil')} Edit note</button>`:''}</div>`:''}</div>`).join('')||`<div class="empty-state">${icon('circle-dashed')}<strong>${list.length?'No matching notes':'No circle notes yet'}</strong><span>${list.length?'Choose another status.':creator()?'Select an area of the figure to annotate.':'Explore another iteration.'}</span></div>`}</div>`;
  }
  function historyCardDescription(v) {
    if (demo) return `<p>${esc(v.summary)}</p>`;
    const metadata = v.kind==='sketch' ? [v.tool] : [v.tool, v.model];
    const provenance = metadata.filter(Boolean).map(esc).join(' · ');
    const summary = v.why || (!provenance && v.summary);
    return [
      provenance && `<p class="version-provenance">${provenance}</p>`,
      summary && `<p class="version-summary">${esc(summary)}</p>`
    ].filter(Boolean).join('');
  }
  function renderHistory() {
    $('#reorder-control').innerHTML=creator()&&state.order.length>1?`<button class="text-btn subtle" data-action="reorder">${icon(ui.reordering?'check':'arrow-up-down')} ${ui.reordering?'Done reordering':'Reorder versions'}</button>`:'';
    $('#history').innerHTML=state.order.map((id,index)=>`<article class="version-card ${ui.version===id?'current':''}" ${ui.reordering?'draggable="true"':''} data-card="${esc(id)}">
      <button class="version-select" data-version="${esc(id)}" aria-pressed="${id===ui.version}">
        <div class="thumb"><img src="${esc(imageOf(id))}" alt=""><span class="thumb-ver">${esc(id)}</span>${id===ui.version?`<span class="selected-badge">${icon('check')} Selected</span>`:''}</div>
        <div class="version-copy"><span class="version-label">${esc(versionLabel(id).toUpperCase())}</span><h3>${esc(versions[id].title)}</h3>${historyCardDescription(versions[id])}</div>
      </button>
      <div class="version-actions"><button class="text-btn" data-prompt="${esc(id)}">${icon('file-text')} Prompt &amp; history ${icon('arrow-up-right')}</button>
      ${ui.reordering?`<span class="move-actions"><button data-move="-1" data-id="${esc(id)}" ${index===0?'disabled':''} aria-label="Move ${esc(id)} earlier">${icon('arrow-left')}</button><button data-move="1" data-id="${esc(id)}" ${index===state.order.length-1?'disabled':''} aria-label="Move ${esc(id)} later">${icon('arrow-right')}</button></span>`:creator()?`<button class="icon-btn" data-upload="${esc(id)}" aria-label="Upload custom image for ${esc(id)}" title="Upload custom image for this version">${icon('image-up')}</button>`:''}</div>
      </article>`).join('');
  }
  function renderReview() {
    const host=$('#review-section');
    if(ui.mode!=='reviewer'){host.innerHTML='';return}
    host.innerHTML=`<div class="review-card panel"><div class="heading-group">${icon('notebook-pen')}<h2>Reviewer sign-off</h2></div><label for="review-text">Review comment</label><textarea id="review-text" maxlength="4000" rows="3" required>${esc(reviewDraft)}</textarea><div class="review-actions"><div class="muted">Review records are saved in this browser.</div><button class="button primary" data-action="sign">${icon('check-check')} Acknowledge &amp; Record Review</button></div>${state.reviews.length?`<div class="record-list">${state.reviews.slice().reverse().map(r=>`<article><small>${icon('circle-check')} Review acknowledged · ${esc(new Date(r.date).toLocaleString())}</small><p>${esc(r.comment)}</p></article>`).join('')}</div>`:''}</div>`;
  }
  const dialog=$('#dialog');
  function openDialog(title,html) {
    dialogReturn=document.activeElement;
    $('#dialog-inner').innerHTML=`<div class="dialog-head"><h2>${esc(title)}</h2>${safeIconButton('close','x','Close dialog')}</div>${html}`;
    if(!dialog.open) dialog.showModal();
  }
  dialog.addEventListener('close',()=>{ if(dialogReturn?.isConnected)dialogReturn.focus(); });
  dialog.addEventListener('click',e=>{if(e.target===dialog){const b=dialog.getBoundingClientRect();if(e.clientX<b.left||e.clientX>b.right||e.clientY<b.top||e.clientY>b.bottom)dialog.close()}});
  function details() {
    if (!demo) {
      openDialog('Package details',`<div class="dialog-content"><span class="version-label">${esc(meta.id)}</span><h3>${esc(meta.title)}</h3><dl class="detail-list"><dt>Author</dt><dd>${esc(meta.author || 'Unspecified')}</dd><dt>Images</dt><dd>${state.order.length}</dd><dt>Final figure</dt><dd>${esc(versions[finalId].title)}</dd></dl></div>`);
      return;
    }
    openDialog('Package details',`<div class="dialog-content"><span class="version-label">FIGURE 01 · CSIRO-VM96</span><h3>CSIRO VibroMat — Wearable Tactile Sensory Substitution System (TRL 5–7)</h3><dl class="detail-list"><dt>Author</dt><dd>Howard Tu</dd><dt>Team</dt><dd>Vision Processing Team (CSIRO Data61 / Swinburne)</dd><dt>Purpose</dt><dd>Commercialisation Marketplace &amp; IP Licensing Pitch Deck</dd><dt>Reference source</dt><dd><a href="${source}" target="_blank" rel="noopener">CSIRO Commercialisation Marketplace — VibroMat (96-motor tactile display) ${icon('external-link')}</a></dd></dl><div class="source-context"><strong>About this demo</strong><p>CSIRO documents the head-mounted camera, image-processing software and a back mat with 96 independently driven motors. The product photos, example author notes and review workflow were created for this FigureRoot demonstration.</p></div></div>`);
  }
  function historyDetail(id) {
    const v=versions[id];
    if (!demo) {
      const sketch = v.kind === 'sketch';
      const missing = '<span class="provenance-unknown">Unspecified</span>';
      const fact = (name,value) => `<div><dt>${name}</dt><dd>${value ? esc(value) : missing}</dd></div>`;
      const facts = [
        fact(sketch ? 'Medium or tool' : 'AI tool',v.tool),
        !sketch || v.model ? fact('Model / version',v.model) : '',
        v.filename ? fact('Source file',v.filename) : ''
      ].join('');
      const fields = `<dl class="provenance-facts">${facts}</dl>
        ${!sketch && v.aiUse ? `<h3>AI contribution</h3><p class="provenance-verbatim">${esc(v.aiUse)}</p>` : ''}
        <h3>${sketch?'Sketch notes':'Generation prompt'}</h3>
        ${v.prompt ? `<blockquote class="provenance-verbatim">${esc(v.prompt)}</blockquote>` : `<p class="provenance-unknown">Unspecified</p>`}
        <h3>Human changes &amp; iteration decisions</h3>
        <p class="${v.why?'provenance-verbatim':'provenance-unknown'}">${v.why?esc(v.why):'Unspecified'}</p>`;
      const image=imageOf(id);
      const ext=image.startsWith('data:image/jpeg')?'jpg':image.startsWith('data:image/webp')?'webp':'png';
      const filename=(v.filename||v.title||id).replace(/\.[a-zA-Z0-9]+$/,'')+'.'+ext;
      openDialog(v.name||v.title,`<div class="dialog-content"><img class="prompt-img" src="${esc(image)}" alt="${esc(v.alt)}"><div class="prompt-meta"><span class="version-badge">${esc(id)}</span><span>${esc(versionLabel(id))}</span></div>${fields}<div class="dialog-actions"><a class="small-btn" download="${esc(filename)}" href="${esc(image)}">${icon('download')} Download image</a>${creator()?`<button class="small-btn" data-upload="${esc(id)}">${icon('image-up')} Replace image</button>`:''}</div></div>`);
      return;
    }
    openDialog(v.name,`<div class="dialog-content"><img class="prompt-img" src="${esc(imageOf(id))}" alt="${esc(v.alt)}"><div class="prompt-meta"><span class="version-badge">${esc(id)}</span><span>Demo tool history · ${esc(v.tool)}</span></div><h3>Prompt used in the case study</h3><blockquote>${esc(v.prompt)}</blockquote><h3>${id==='v3'?'Packaging decision':'Why we iterated'}</h3><p>${esc(v.why)}</p><details class="actual-prompts"><summary>Product photo generation prompt</summary><p>${esc(v.actualPrompt || 'Wordless studio product photography, generated with imagegen for this prototype.')}</p></details><div class="dialog-actions"><a class="small-btn" download="VibroMat-${esc(id)}.png" href="${esc(v.download||'generated/'+id+'.png')}">${icon('download')} Original product photo</a>${creator()?`<button class="small-btn" data-upload="${esc(id)}">${icon('image-up')} Upload custom image</button>`:''}</div></div>`);
  }
  function noteForm(existing,point) {
    if(!creator())return;
    const n=existing || {title:'',body:'',type:'uncertain',r:.045,...point};
    const formTitle=existing?'Edit circle note':'Add circle note';
    openDialog(formTitle,`<form class="dialog-content note-form" id="note-form"><div class="note-form-meta"><span class="version-badge">${esc(ui.version)}</span> ${esc(versions[ui.version].title)}</div><label>Title<input name="title" required maxlength="120" value="${esc(n.title)}" placeholder="What does this area show?"></label><label>Status<select name="type">${Object.keys(types).map(k=>`<option value="${k}" ${n.type===k?'selected':''}>${types[k]}</option>`).join('')}</select></label><label>Author note<textarea name="body" rows="4" required maxlength="2500" placeholder="Explain what a reviewer can rely on.">${esc(n.body)}</textarea></label><label>Circle size<input name="radius" type="range" min="1.5" max="18" step=".1" value="${n.r*100}"></label><div class="dialog-actions">${existing?'<button type="button" class="small-btn" id="relocate">Move circle</button>':''}${existing?'<button type="button" class="text-btn delete-note" id="delete-note">Delete note</button>':''}<button type="button" class="small-btn" data-action="close">Cancel</button><button class="button primary" type="submit">Save note</button></div></form>`);
    const form=$('#note-form');
    form.addEventListener('submit',e=>{
      e.preventDefault();let title=form.elements.title.value.trim(),body=form.elements.body.value.trim();
      if(!title||!body){toast('Enter a title and an author note.');return}
      const item={version:ui.version,x:n.x,y:n.y,id:existing?.id??Math.max(0,...state.notes.map(note=>note.id))+1,title,body,type:form.elements.type.value,r:Number(form.elements.radius.value)/100};
      if(existing)state.notes[state.notes.indexOf(existing)]=item;else state.notes.push(item);
      ui.filter='all';ui.selected=item.id;ui.showNotes=true;ui.adding=false;
      persist();dialog.close();refresh();toast('Circle note saved');
    });
    if(existing) $('#relocate').onclick=()=>{
      if(!form.reportValidity())return;
      relocation={original:existing,fields:{title:form.elements.title.value,body:form.elements.body.value,type:form.elements.type.value,r:Number(form.elements.radius.value)/100}};
      ui.adding=true;ui.showNotes=true;dialog.close();renderViewer();toast('Click the new location for this note.'); 
    };
    if(existing)$('#delete-note').onclick=()=>{let btn=$('#delete-note');if(btn.dataset.confirm){state.notes=state.notes.filter(t=>t.id!==n.id);ui.selected=null;persist();dialog.close();refresh();toast('Circle note deleted')}else{btn.dataset.confirm='yes';btn.textContent='Confirm delete'}};
    form.elements.title.focus();
  }
  function setVersion(id) {
    relocation=null;ui.version=id;ui.filter='all';ui.selected=null;ui.compare=false;ui.adding=false;ui.showNotes=true;
    refresh();
  }
  function selectNote(id) {
    relocation=null;ui.compare=false;ui.showNotes=true;ui.adding=false;ui.selected=ui.selected===id?null:id;
    if(ui.large && ui.selected!==null){
      const n=state.notes.find(n=>n.id===id);
      openDialog(n.title,`<div class="dialog-content">${chip(n.type)}<p>${esc(n.body)}</p>${creator()?`<button class="small-btn" data-edit="${n.id}">${icon('pencil')} Edit note</button>`:''}</div>`);
    }
    renderViewer(); renderNotes();
  }
  function startUpload(id) { if(!creator())return; uploadVersion=id;$('#upload').value='';$('#upload').click(); }
  $('#upload').addEventListener('change',async e=>{
    const file=e.target.files[0],target=uploadVersion;
    if(!file||!target||!creator())return;
    if(!['image/png','image/jpeg'].includes(file.type)){toast('Choose a PNG or JPEG image.');return}
    try {
      const data=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=()=>reject(r.error);r.readAsDataURL(file)});
      const img=new Image();img.src=data;await img.decode();
      if (!demo) {
        state.images[target]=data;
        const version=versions[target];
        if (version.summary===version.filename) version.summary=file.name;
        version.filename=file.name;
        version.alt=version.title;
      } else {
        const factor=Math.min(1,2400/Math.max(img.naturalWidth,img.naturalHeight));
        const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(img.naturalWidth*factor));canvas.height=Math.max(1,Math.round(img.naturalHeight*factor));
        const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(img,0,0,canvas.width,canvas.height);
        state.images[target]=canvas.toDataURL('image/jpeg',.91);
      }
      if(target===finalId && reviewDraft===reviewExample) reviewDraft='';
      persist();
      if(dialog.open) dialog.close();
      setVersion(target);
      toast('Image replaced. Check circle positions on the new image.');
    } catch {toast('This file could not be opened. Choose another PNG or JPEG.');}
  });
  function move(id,to) {
    if(!creator()||!ui.reordering)return;
    if(to<0||to>=state.order.length)return;
    state.order.splice(state.order.indexOf(id),1);state.order.splice(to,0,id);persist();renderHistory();
  }
  $('#history').addEventListener('dragstart',e=>{const el=e.target.closest('[data-card]');if(el&&ui.reordering){e.dataTransfer.setData('text/plain',el.dataset.card);e.dataTransfer.effectAllowed='move'}});
  $('#history').addEventListener('dragover',e=>{if(ui.reordering)e.preventDefault()});
  $('#history').addEventListener('drop',e=>{if(!ui.reordering)return;e.preventDefault();const id=e.dataTransfer.getData('text/plain'),to=e.target.closest('[data-card]')?.dataset.card;if(versions[id]&&to)move(id,state.order.indexOf(to))});
  function exportFigure() {
    window.FigureExport.open({state,versions,baseURL:location.href.split('#')[0],onPrivacy:value=>{if(creator()){state.privacy=value;persist()}},report:toast});
  }
  $('#export').onclick=exportFigure;
  document.addEventListener('click',e=>{
    if (studio.hidden || !(studio.contains(e.target) || topbar.contains(e.target) || dialog.contains(e.target))) return;
    const b=e.target.closest('button,a[data-action]');
    if(b){
      const d=b.dataset;
      if(d.mode){if(share)return;relocation=null;ui.mode=d.mode;ui.adding=false;ui.reordering=false;refresh();$('#mode-tabs [aria-pressed="true"]')?.focus();return}
      if(d.note){selectNote(Number(d.note));return}
      if(d.version){setVersion(d.version);return}
      if(d.prompt){historyDetail(d.prompt);return}
      if(d.edit){noteForm(state.notes.find(n=>n.id===Number(d.edit)));return}
      if(d.upload){startUpload(d.upload);return}
      if(d.move){move(d.id,state.order.indexOf(d.id)+Number(d.move));return}
      switch(d.action) {
        case 'details': details();break;
        case 'close': dialog.close();break;
        case 'compare': relocation=null;ui.compare=!ui.compare;ui.adding=false;ui.selected=null;renderViewer();renderNotes();break;
        case 'expand': ui.large=!ui.large;renderViewer();$('#viewer [data-action="expand"]')?.focus();break;
        case 'visibility': ui.showNotes=!ui.showNotes;renderViewer();break;
        case 'upload': startUpload(ui.version);break;
        case 'history': historyDetail(ui.version);break;
        case 'reorder': ui.reordering=!ui.reordering;renderHistory();break;
        case 'add': if(creator()){relocation=null;ui.adding=!ui.adding;renderViewer();if(ui.adding){const p=$('#photo');p.tabIndex=0;p.focus();p.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();noteForm(null,{x:.5,y:.5})}}}}break;
        case 'sign': {
          const input=$('#review-text'),comment=input.value.trim();
          if(!comment){input.setCustomValidity('Enter a review comment.');input.reportValidity();break}
          state.reviews.push({date:new Date().toISOString(),comment});reviewDraft='';persist();renderReview();toast('Review acknowledged and recorded');break;
        }
      }
      return;
    }
    const p=e.target.closest('#photo');
    if(p&&creator()&&!ui.compare) {
      const area=p.getBoundingClientRect(), point={x:(e.clientX-area.left)/area.width,y:(e.clientY-area.top)/area.height};
      if(relocation && ui.adding){
        Object.assign(relocation.original,relocation.fields,point);
        if(relocation.original.short && relocation.original.short!==relocation.original.title) delete relocation.original.short;
        ui.selected=relocation.original.id;relocation=null;ui.adding=false;ui.filter='all';persist();refresh();toast('Circle moved');
      }else noteForm(null,point);
    }
  });
  studio.addEventListener('change',e=>{
    if(e.target.id==='note-filter'){ui.filter=e.target.value;ui.selected=null;renderNotes();renderViewer();$('#note-filter').focus()}
    if(e.target.dataset.compare){
      const side=e.target.dataset.compare,other=side==='before'?'after':'before',previous=ui[side];
      ui[side]=e.target.value;if(ui[side]===ui[other])ui[other]=previous;renderViewer();
    }
  });
  studio.addEventListener('input',e=>{if(e.target.id==='review-text'){reviewDraft=e.target.value;e.target.setCustomValidity('')}});
  document.addEventListener('keydown',e=>{
    if(!studio.hidden&&e.key==='Escape'&&!dialog.open&&!document.querySelector('dialog[open]')){if(ui.large){ui.large=false;renderViewer()}else if(ui.adding){ui.adding=false;renderViewer()}}
  });
  for (const area of [studio,topbar]) area.querySelectorAll('[data-icon]').forEach(el=>el.outerHTML=icon(el.dataset.icon));
  renderMetadata();
  refresh();
}
