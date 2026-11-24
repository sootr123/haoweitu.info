/* FigureRoot subscription preview. The prototype's package actions are supplied by the router. */
window.FigurePlans = (() => {
  const icon = name => window.figureIcon(name);
  const features = items => '<ul class="fp-features">' + items.map(item =>
    '<li>' + icon('check') + '<span>' + item + '</span></li>').join('') + '</ul>';

  function mount({host, onCreate, onPro, onBack}) {
    host.innerHTML = `<div class="fp-shell">
      <nav class="fp-crumb" aria-label="Breadcrumb"><button type="button" data-fp="back">${icon('arrow-left')} Workspace</button>${icon('chevron-right')}<span>Plans</span></nav>
      <header class="fp-intro"><h1>Plans &amp; pricing<span>.</span></h1><p>Choose how you share and review figure packages. You can try both sharing workflows for free in this preview.</p></header>
      <div class="fp-grid">
        <article class="fp-card" aria-labelledby="fp-free">
          <header><span class="fp-icon">${icon('book-open-text')}</span><h2 id="fp-free">Free</h2></header>
          <p class="fp-audience">For researchers sharing figures openly.</p>
          <div class="fp-cost"><strong>AU$0</strong><span>Open research</span></div>
          <div class="fp-featblock"><h3>Public packages</h3>${features([
            'Shareable citation links',
            'Sketches, prompts and version history',
            'Circle notes and reviewer acknowledgement',
            'Figure and caption exports'
          ])}</div>
          <button class="fp-action" type="button" data-fp="free">Start a package ${icon('arrow-right')}</button>
        </article>
        <article class="fp-card fp-pro" aria-labelledby="fp-lab">
          <header><span class="fp-icon">${icon('git-branch')}</span><h2 id="fp-lab">Pro / Lab</h2></header>
          <p class="fp-audience">For labs sharing confidential figures with partners.</p>
          <div class="fp-cost"><strong>AU$19–39</strong><span>Per lab, per month · Pilot price range</span></div>
          <div class="fp-featblock"><h3>Confidential packages</h3>${features([
            'All Free features',
            'Passphrase-protected reviewer packages',
            'Encrypted files for offline partner review'
          ])}<p class="fp-planned"><span>Planned</span> Review locks and long-term archiving</p></div>
          <button class="fp-action" type="button" data-fp="pro">Try a confidential package ${icon('arrow-right')}</button>
        </article>
        <article class="fp-card" aria-labelledby="fp-institutional">
          <header><span class="fp-icon">${icon('layers')}</span><h2 id="fp-institutional">Institutional</h2></header>
          <p class="fp-audience">For institutions and research integrity offices.</p>
          <div class="fp-cost fp-cost-quote"><strong>Custom quote</strong><span>Annual institutional pilot</span></div>
          <div class="fp-featblock"><h3>Scope your pilot</h3>${features([
            'Participating labs and departments',
            'Review, access and retention requirements',
            'Annual scope and pricing by agreement'
          ])}</div>
          <button class="fp-action" type="button" data-fp="institutional" aria-haspopup="dialog">View pilot details ${icon('arrow-right')}</button>
        </article>
      </div>
    </div>
    <dialog class="fp-dialog" id="fp-dialog" aria-labelledby="fp-dialog-title">
      <div class="fp-dialog-head"><h2 id="fp-dialog-title">Institutional pilot</h2><button type="button" data-fp="close" aria-label="Close pilot details">${icon('x')}</button></div>
      <form id="fp-brief">
        <p>Prepare a brief for your research integrity or procurement team to scope an annual quote.</p>
        <label>Institution or team <small>Optional</small><input name="institution" maxlength="180" autocomplete="organization" placeholder="Institution name"></label>
        <label>Participating labs <small>Optional</small><input name="labs" type="number" min="1" max="100000" step="1" placeholder="Number of labs"></label>
        <label>Review requirements <small>Optional</small><textarea name="needs" maxlength="1600" rows="3" placeholder="Who needs access, how long figures must be retained, and how reviews are approved"></textarea></label>
        <button class="fp-action" type="submit">${icon('download')} Download pilot brief</button>
      </form>
    </dialog>`;
    const q = selector => host.querySelector(selector);
    const action = name => q('[data-fp="' + name + '"]');
    action('back').onclick = onBack;
    action('free').onclick = onCreate;
    action('pro').onclick = onPro;
    const dialog = q('#fp-dialog');
    action('institutional').onclick = () => dialog.showModal();
    action('close').onclick = () => dialog.close();
    dialog.onclose = () => action('institutional').focus();
    dialog.onclick = event => {
      if (event.target !== dialog) return;
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) {
        dialog.close();
      }
    };
    q('#fp-brief').onsubmit = event => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const field = key => String(form.get(key) || '').trim() || 'To be agreed';
      const brief = [
        'FigureRoot institutional pilot brief',
        '',
        'Institution or team: ' + field('institution'),
        'Participating labs: ' + field('labs'),
        'Review requirements: ' + field('needs'),
        '',
        'Scope for an annual quote',
        '1. Identify the participating labs, pilot owner and expected figure volume.',
        '2. Agree how public research and confidential partner packages will be reviewed.',
        '3. Document retention periods, access requirements and pilot evaluation criteria.',
        '4. Confirm the annual scope and pricing with the institution.'
      ].join('\n');
      const url = URL.createObjectURL(new Blob([brief], {type:'text/plain;charset=utf-8'}));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'FigureRoot-institutional-pilot-brief.txt';
      host.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url),1000);
    };
  }
  return {mount};
})();
