window.FigureCollect = (() => {
  const drafts = new WeakMap();
  const icon = name => window.figureIcon(name);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[ch]);
  let nextEntry = 0;
  const newEntry = (key,kind) => ({key, kind, filename:'', title:'', tool:'', model:'', aiUse:'', prompt:'', why:'', image:''});
  const blank = () => ({title:'', author:'', final:newEntry('final','final'), earlier:[]});
  const basename = name => name.replace(/\.(jpe?g|png)$/i, '').replace(/[_-]+/g, ' ').trim() || 'Untitled image';
  function prettyDate(value) {
    const date = new Date(value);
    if (!value || isNaN(date.getTime())) return '';
    return date.toLocaleDateString(undefined, {year:'numeric', month:'short', day:'numeric'});
  }

  async function readImage(file, kind) {
    const bytes = new Uint8Array(await file.slice(0, 8).arrayBuffer());
    const isPNG = [137,80,78,71,13,10,26,10].every((b,i) => bytes[i] === b);
    const isJPEG = bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255;
    if (!isPNG && !isJPEG) throw new Error('choose a PNG or JPG image');
    const image = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = () => reject(new Error('try selecting the file again'));
      reader.onload = () => resolve(reader.result);
      reader.readAsDataURL(new Blob([file], {type:isPNG ? 'image/png' : 'image/jpeg'}));
    });
    await new Promise((resolve, reject) => {
      const preview = new Image();
      preview.onload = resolve;
      preview.onerror = () => reject(new Error('the image could not be decoded'));
      preview.src = image;
    });
    return {...newEntry(String(++nextEntry),kind), filename:file.name, title:basename(file.name), image};
  }

  function mount({host, onCreate, saved = [], onOpen}) {
    let session = drafts.get(host);
    if (!session) {
      session = {draft:blank(), busy:false, importing:false, error:'', readError:{final:'',earlier:''}};
      drafts.set(host, session);
    }
    session.events?.abort();
    const {signal} = session.events = new AbortController();
    const on = (type, fn) => host.addEventListener(type, fn, {signal});
    const draft = session.draft;
    const all = () => [...draft.earlier, draft.final];
    const entryFor = el => all().find(entry => entry.key === el.closest('[data-cc-entry]')?.dataset.ccEntry);
    const q = selector => host.querySelector(selector);

    function field(entry, key, label, options={}) {
      const id = 'cc-field-' + entry.key + '-' + key;
      const attributes = 'id="' + id + '" data-cc-field="' + key + '" placeholder="' + escape(options.hint) + '"' +
        (options.tools ? ' list="cc-tool-suggestions" autocomplete="off"' : '');
      const value = escape(entry[key]);
      return '<label class="cc-field" for="' + id + '"><span>' + label + '</span>' +
        (options.multiline ? '<textarea ' + attributes + ' rows="2">\n' + value + '</textarea>' : '<input type="text" ' + attributes + ' value="' + value + '">') + '</label>';
    }
    function attribution(entry) {
      if (entry.kind === 'sketch') {
        return field(entry,'tool','Sketch medium',{hint:'e.g. Pencil on paper'}) +
          field(entry,'prompt','Sketch notes',{multiline:true,hint:'Describe the source sketch.'}) +
          field(entry,'why','Changes or edits',{multiline:true,hint:'What changed from the original sketch?'});
      }
      const uses = ['Generate an image','Edit a reference image','Enhance or retouch'];
      const useField = '<label class="cc-field cc-wide"><span>How was AI used?</span><select data-cc-field="aiUse"><option value="">Choose if known</option>' +
        uses.map(use => '<option' + (use===entry.aiUse?' selected':'') + '>' + use + '</option>').join('') + '</select></label>';
      return field(entry,'tool','Generative AI tool',{hint:'e.g. ChatGPT or Midjourney',tools:true}) +
        field(entry,'model','Model / version',{hint:'Leave blank if unknown'}) + useField +
        field(entry,'prompt','Exact generation prompt',{multiline:true,hint:'Paste the prompt exactly as entered.'}) +
        field(entry,'why','Human edits / what changed',{multiline:true,hint:'Describe any cropping, retouching or other changes.'});
    }
    function action(name,label,symbol,disabled=false) {
      return '<button class="cc-mini" type="button" data-cc-action="' + name + '" title="' + label + '" aria-label="' + label + '"' + (disabled?' disabled':'') + '>' + icon(symbol) + '</button>';
    }
    function entryCard(entry,index) {
      return '<article class="cc-entry" data-cc-entry="' + entry.key + '"><div class="cc-entry-bar">' +
        '<img class="cc-thumb" alt="" loading="lazy"><div class="cc-entry-name"><strong>' + escape(entry.filename) + '</strong><small>Source ' +
        (index+1) + ' · ' + (entry.kind === 'sketch' ? 'Reference sketch' : 'AI iteration') + '</small></div>' +
        '<div class="cc-entry-actions">' + action('earlier','Move earlier','arrow-left',index===0) +
          action('later','Move later','arrow-right',index===draft.earlier.length-1) + action('remove','Remove image','x') + '</div></div>' +
        '<div class="cc-meta-body"><label class="cc-field"><span>Source type</span><select data-cc-field="kind"><option value="iteration"' + (entry.kind==='iteration'?' selected':'') +
          '>AI iteration</option><option value="sketch"' + (entry.kind==='sketch'?' selected':'') + '>Reference sketch</option></select></label>' +
          field(entry,'title','Version title') + '<div class="cc-attribution-fields">' + attribution(entry) + '</div></div></article>';
    }
    function dropzone(final) {
      if (final) return '<button type="button" data-cc-drop="final" class="cc-drop-final">' +
        '<span class="cc-upload-icon">' + icon('image-up') + '</span><b>Drop your final figure here</b>' +
        '<span>PNG or JPG <span aria-hidden="true">·</span> <u>Choose a file</u></span></button>';
      return '<div class="cc-earlier-drop" data-cc-drop="earlier"><span class="cc-source-icon">' + icon('git-branch') + '</span>' +
        '<div><strong>Add earlier images</strong><small>Drop files here or choose a source type.</small></div><div class="cc-add-actions">' +
        '<button class="cc-secondary" type="button" data-cc-kind="sketch">' + icon('pencil') + ' Add sketch</button>' +
        '<button class="cc-secondary" type="button" data-cc-kind="iteration">' + icon('layers') + ' Add iteration</button></div></div>';
    }
    function showFiles() {
      const final = draft.final;
      q('#cc-final').innerHTML = final.image ? '<div class="cc-final-preview"><img alt="Your final figure preview"></div>' +
        '<div class="cc-entry-bar cc-final-bar"><div class="cc-entry-name"><strong>' + escape(final.filename) + '</strong></div>' +
        '<button type="button" class="cc-link" data-cc-action="replace">Replace</button>' + action('remove','Remove final image','x') + '</div>' +
        field(final,'title','Version title') : dropzone(true);
      if (final.image) q('.cc-final-preview img').src = final.image;
      q('#cc-entries').innerHTML = draft.earlier.map(entryCard).join('');
      host.querySelectorAll('#cc-entries .cc-entry').forEach(node => node.querySelector('.cc-thumb').src = entryFor(node).image);
      q('#cc-count').textContent = draft.earlier.length ? String(draft.earlier.length) : '';
      refreshFeedback();
    }
    function refreshFeedback() {
      if (signal.aborted) return;
      for (const kind of ['final','earlier']) q('#cc-' + kind + '-error').textContent = session.readError[kind];
      q('#cc-error').textContent = session.error;
      q('#cc-status').textContent = session.importing ? 'Reading your images…' : '';
      q('#cc-submit').disabled = session.busy || session.importing;
      q('#cc-submit').innerHTML = (session.busy ? 'Creating package…' : 'Create package') + icon('arrow-right');
      host.querySelectorAll('fieldset').forEach(node=>node.disabled = session.busy);
    }
    const savedMarkup = saved.length ? saved.map(pkg => '<button type="button" class="cc-saved" data-cc-open="' + escape(pkg.id) + '">' + icon('layers') +
      '<span><strong>' + escape(pkg.title || 'Untitled package') + '</strong><small>' + escape([pkg.count ? pkg.count + (pkg.count===1?' image':' images') : '', pkg.author, prettyDate(pkg.updatedAt)].filter(Boolean).join(' · ')) + '</small></span>' + icon('chevron-right') + '</button>').join('') :
      '<p class="cc-library-empty">Packages you create on this device will appear here.</p>';

    host.innerHTML = '<div class="cc-shell"><div class="cc-breadcrumb">' + icon('layers') + '<span>Workspace</span>' + icon('chevron-right') + '<span>New package</span>' +
      (saved.length ? '<button class="cc-library-jump" type="button" data-cc-action="library">' + icon('file-clock') + ' Your packages</button>' : '') + '</div>' +
      '<header class="cc-intro"><h1>Collect the root<span>.</span></h1><p>Upload your final figure and record how it was made.</p></header>' +
      '<form class="cc-form" novalidate><fieldset class="cc-paper"><legend class="cc-sr">New citation package</legend><div class="cc-compose">' +
      '<section class="cc-block cc-final-block"><div class="cc-heading"><div><span class="cc-heading-icon">' + icon('image-up') + '</span><h2>Final figure</h2></div><small>Required</small></div>' +
      '<div id="cc-final" data-cc-entry="final"></div><p class="cc-error" id="cc-final-error" role="alert"></p></section>' +
      '<section class="cc-block cc-attribution-block" data-cc-entry="final"><div class="cc-heading"><div><span class="cc-heading-icon">' + icon('notebook-pen') + '</span><h2>AI attribution</h2></div><small>Optional</small></div>' +
      '<div class="cc-attribution-fields" id="cc-attribution">' + attribution(draft.final) + '</div></section>' +
      '<section class="cc-block cc-details-block"><div class="cc-heading"><div><span class="cc-heading-icon">' + icon('file-text') + '</span><h2>Package details</h2></div></div>' +
      '<div class="cc-package-fields"><label class="cc-field"><span>Package title <em>*</em></span><input id="cc-title" type="text" required placeholder="Give your figure a title" value="' + escape(draft.title) + '"></label>' +
      '<label class="cc-field"><span>Author <small>Optional</small></span><input id="cc-author" type="text" placeholder="Name or team" value="' + escape(draft.author) + '"></label></div></section>' +
      '<section class="cc-block cc-earlier-block"><div class="cc-heading"><div><span class="cc-heading-icon">' + icon('git-branch') + '</span><h2>Sketches &amp; iterations</h2><span id="cc-count"></span></div><small>Optional</small></div>' +
      '<div class="cc-entry-list" id="cc-entries"></div>' + dropzone(false) + '<p class="cc-error" id="cc-earlier-error" role="alert"></p></section>' +
      '</div><div class="cc-bottom"><span id="cc-status" role="status"></span><p class="cc-error" id="cc-error" role="alert" tabindex="-1"></p><button id="cc-submit" class="button primary" type="submit"></button></div>' +
      '<datalist id="cc-tool-suggestions"><option value="ChatGPT"></option><option value="Midjourney"></option><option value="Adobe Firefly"></option><option value="Stable Diffusion"></option></datalist>' +
      '<input id="cc-file-final" type="file" hidden accept="image/png,image/jpeg,.png,.jpg,.jpeg"><input id="cc-file-earlier" type="file" hidden multiple accept="image/png,image/jpeg,.png,.jpg,.jpeg">' +
      '</fieldset></form><section class="cc-library" tabindex="-1"><h2>' + icon('file-clock') + ' Your packages</h2>' + savedMarkup + '</section></div>';
    showFiles();

    let nextKind = 'iteration';
    let dragDepth = 0;
    on('input', event => {
      const el = event.target;
      if (el.id === 'cc-title') {draft.title = el.value; el.removeAttribute('aria-invalid');}
      else if (el.id === 'cc-author') draft.author = el.value;
      else if (el.dataset.ccField && entryFor(el)) {
        const entry = entryFor(el);
        entry[el.dataset.ccField] = el.value;
        if (el.dataset.ccField === 'kind') {
          const index = draft.earlier.indexOf(entry);
          el.closest('.cc-entry').querySelector('.cc-attribution-fields').innerHTML = attribution(entry);
          el.closest('.cc-entry').querySelector('.cc-entry-name small').textContent = 'Source ' + (index+1) + ' · ' + (el.value==='sketch'?'Reference sketch':'AI iteration');
        }
      }
      if (session.error) {session.error='';refreshFeedback();}
    });
    async function importFiles(files, kind) {
      if (!files.length || session.busy || session.importing) return;
      const bucket = kind === 'final' ? 'final' : 'earlier';
      session.error = '';
      session.readError[bucket] = '';
      if (kind === 'final' && files.length > 1) {
        session.readError.final = 'Choose one final figure. Add other images under Sketches & iterations.';
        refreshFeedback();return;
      }
      session.importing = true;refreshFeedback();
      const errors = [];
      try {
        for (const file of files) {
          try {
            const entry = await readImage(file,kind);
            if (kind==='final') {
              const old = draft.final;
              if (!old.title || old.title === basename(old.filename)) old.title=entry.title;
              Object.assign(old,{image:entry.image,filename:entry.filename});
            } else draft.earlier.push(entry);
          } catch (error) { errors.push(file.name + ' — ' + error.message); }
        }
      } finally {
        session.importing=false;
        session.readError[bucket]=errors.join('. ');
        if (!signal.aborted) showFiles();
        else session.refresh?.();
      }
    }
    session.refresh = () => { if(!signal.aborted) showFiles(); };
    on('change', event => {
      if (event.target.id !== 'cc-file-final' && event.target.id !== 'cc-file-earlier') return;
      const files = Array.from(event.target.files || []);
      const kind = event.target.id === 'cc-file-final' ? 'final' : nextKind;
      event.target.value='';
      importFiles(files,kind);
    });
    on('click', event => {
      const el = event.target.closest('button');
      if (!el) return;
      if (el.dataset.ccAction === 'library') {q('.cc-library').focus();return;}
      if (el.hasAttribute('data-cc-open')) {onOpen(el.dataset.ccOpen);return;}
      if (session.busy || session.importing) return;
      if (el.dataset.ccDrop==='final' || el.dataset.ccAction==='replace') { q('#cc-file-final').click();return; }
      if (el.dataset.ccKind) {nextKind=el.dataset.ccKind;q('#cc-file-earlier').click();return;}
      const entry=entryFor(el), action=el.dataset.ccAction;
      if (!entry || !action) return;
      const index=draft.earlier.indexOf(entry);
      if (action==='remove') {
        if (entry===draft.final) {
          if (entry.title === basename(entry.filename)) entry.title='';
          Object.assign(entry,{image:'',filename:''});
        }
        else draft.earlier.splice(index,1);
      } else if (action==='earlier' || action==='later') {
        const to=index+(action==='earlier'?-1:1);
        if(to<0 || to>=draft.earlier.length) return;
        draft.earlier.splice(index,1);draft.earlier.splice(to,0,entry);
      }
      showFiles();
      const row = q('[data-cc-entry="'+entry.key+'"]');
      const focusTarget = row?.querySelector('[data-cc-action="'+action+'"]:not(:disabled)') || row?.querySelector('button:not(:disabled)') ||
        q('[data-cc-drop="final"]') || q('[data-cc-kind="iteration"]');
      focusTarget?.focus();
    });
    const dropTarget = el => el.closest?.('[data-cc-drop], #cc-final');
    on('dragenter',event=>{
      const zone=dropTarget(event.target);
      if (!zone || !Array.from(event.dataTransfer.types).includes('Files')) return;
      event.preventDefault();dragDepth++;zone.classList.add('cc-over');
    });
    on('dragover',event=>{if(dropTarget(event.target)) {event.preventDefault();event.dataTransfer.dropEffect='copy';}});
    on('dragleave',event=>{
      if(!dropTarget(event.target))return;
      dragDepth=Math.max(0,dragDepth-1);
      if (!dragDepth) host.querySelectorAll('.cc-over').forEach(el=>el.classList.remove('cc-over'));
    });
    on('drop',event=>{
      const zone=dropTarget(event.target);
      if (!zone)return;
      event.preventDefault();dragDepth=0;
      host.querySelectorAll('.cc-over').forEach(el=>el.classList.remove('cc-over'));
      importFiles(Array.from(event.dataTransfer.files),zone.dataset.ccDrop==='earlier'?'iteration':'final');
    });
    on('submit',async event=>{
      event.preventDefault();
      if (session.importing || session.busy) return;
      if (!draft.final.image || !draft.title.trim()) {
        if (!draft.final.image)session.readError.final='Choose your final figure to continue.';
        session.error = draft.title.trim()?'Add your final figure above.':'Enter a package title to continue.';
        refreshFeedback();
        if (!draft.title.trim()) q('#cc-title').setAttribute('aria-invalid','true');
        (!draft.final.image ? q('[data-cc-drop="final"]') : q('#cc-title')).focus();
        return;
      }
      session.busy=true;session.error='';refreshFeedback();
      try {
        const entries=all().map(({kind,title,tool,model,aiUse,prompt,why,image,filename})=>({
          kind,title:title.trim() || basename(filename),tool,model:kind==='sketch'?'':model,aiUse:kind==='sketch'?'':aiUse,prompt,why,image,filename
        }));
        await onCreate({title:draft.title.trim(),author:draft.author.trim(),entries});
        Object.assign(draft,blank());
        session.readError={final:'',earlier:''};
      } catch(error) {session.error = error?.message || 'The package could not be saved. Try creating it again.';}
      finally {
        session.busy=false;
        if (!signal.aborted) {
          if(session.error){refreshFeedback();q('#cc-error').focus();}
          else {q('#cc-title').value='';q('#cc-author').value='';q('#cc-attribution').innerHTML=attribution(draft.final);showFiles();}
        } else session.refresh?.();
      }
    });
  }
  function hasUnsavedInput(host) {
    const session = drafts.get(host);
    if (!session) return false;
    const {draft, busy, importing} = session;
    const final = draft.final;
    if (busy || importing || draft.earlier.length || final.image) return true;
    return [draft.title, draft.author, final.title, final.tool, final.model, final.aiUse, final.prompt, final.why]
      .some(value => value.trim().length > 0);
  }
  return {mount, hasUnsavedInput};
})();
