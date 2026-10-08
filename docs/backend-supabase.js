/* Supabase backend for the installable app. Data is private to the signed-in person (row-level security). */
(function () {
  const CFG = window.LEDGER_SUPABASE || {};
  window.LEDGER_BACKENDS = window.LEDGER_BACKENDS || {};
  window.LEDGER_BACKENDS.supabase = async function () {
    if (!window.supabase || !CFG.url || !CFG.key) return null;
    const sb = window.supabase.createClient(CFG.url, CFG.key, { auth: { persistSession: true, autoRefreshToken: true } });
    let { data: { session } } = await sb.auth.getSession();
    if (!session) session = await signIn(sb);
    const uid = session.user.id;
    let h, curMonth = null, channel = null;
    const status = (t) => h && h.status && h.status(t);

    async function loadConfig() {
      const { data, error } = await sb.from('ledger_config').select('data').eq('user_id', uid).maybeSingle();
      if (error) throw error; h.config(data ? data.data : null);
    }
    async function loadMonths() {
      const { data, error } = await sb.from('ledger_months').select('id,data').eq('user_id', uid);
      if (error) throw error; const m = {}; (data || []).forEach(r => m[r.id] = { id: r.id, ...r.data }); h.months(m);
    }
    async function loadTx(id) {
      const { data, error } = await sb.from('ledger_txns').select('id,data').eq('user_id', uid).eq('month', id);
      if (error) throw error; if (id === curMonth) h.txns(id, (data || []).map(r => ({ id: r.id, ...r.data })));
    }
    async function refresh() {
      try { await Promise.all([loadConfig(), loadMonths(), curMonth ? loadTx(curMonth) : null]); status(''); }
      catch (e) { console.error(e); status(navigator.onLine ? 'Sync error' : 'Offline'); }
    }
    const wrap = (p) => p.then(({ error }) => { if (error) throw error; status(''); });

    return {
      name: 'supabase',
      start(handlers) {
        h = handlers; refresh();
        document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
        window.addEventListener('online', refresh);
        window.addEventListener('offline', () => status('Offline'));
        channel = sb.channel('ledger-' + uid)
          .on('postgres_changes', { event: '*', schema: 'public', table: 'ledger_txns', filter: 'user_id=eq.' + uid }, () => curMonth && loadTx(curMonth).catch(() => {}))
          .on('postgres_changes', { event: '*', schema: 'public', table: 'ledger_months', filter: 'user_id=eq.' + uid }, () => loadMonths().catch(() => {}))
          .subscribe();
        window.LEDGER_SIGN_OUT = async () => { await sb.auth.signOut(); location.reload(); };
      },
      watchMonth(id) { curMonth = id; loadTx(id).catch(e => console.error(e)); },
      saveConfig(c) { return wrap(sb.from('ledger_config').upsert({ user_id: uid, data: c, updated_at: new Date().toISOString() })); },
      saveMonth(id, m) { return wrap(sb.from('ledger_months').upsert({ user_id: uid, id, data: m, updated_at: new Date().toISOString() })); },
      setTxn(id, t) { return wrap(sb.from('ledger_txns').upsert({ user_id: uid, id, month: t.month, data: t, updated_at: new Date().toISOString() })); },
      delTxn(id) { return wrap(sb.from('ledger_txns').delete().eq('user_id', uid).eq('id', id)); }
    };
  };

  function signIn(sb) {
    const chrome = [document.querySelector('nav.tabs'), document.querySelector('.top .month')];
    chrome.forEach(el => el && (el.hidden = true));
    return new Promise((done) => {
      const resolve = (v) => { chrome.forEach(el => el && (el.hidden = false)); done(v); };
      const app = document.getElementById('app');
      const draw = (msg, tone) => {
        app.innerHTML = `<section class="card" style="margin-top:8vh">
          <h2 style="font-size:22px">Runway</h2>
          <p class="muted">Sign in to see your budget on this device.</p>
          <form id="auth" style="display:flex;flex-direction:column;gap:10px">
            <label class="f" for="au-e">Email<input id="au-e" name="email" type="email" autocomplete="email" required></label>
            <label class="f" for="au-p">Password<input id="au-p" name="password" type="password" autocomplete="current-password" minlength="8" required></label>
            ${msg ? `<p class="${tone || 'muted'}" style="font-size:14px">${msg}</p>` : ''}
            <button class="btn primary block" type="submit" data-mode="in">Sign in</button>
            <button class="btn block" type="submit" data-mode="up">Create account</button>
          </form></section>`;
        const f = document.getElementById('auth');
        f.addEventListener('submit', async (e) => {
          e.preventDefault();
          const mode = (e.submitter && e.submitter.dataset.mode) || 'in';
          const fd = Object.fromEntries(new FormData(f));
          f.querySelectorAll('button').forEach(b => b.disabled = true);
          const res = mode === 'up' ? await sb.auth.signUp({ email: fd.email, password: fd.password }) : await sb.auth.signInWithPassword({ email: fd.email, password: fd.password });
          if (res.error) {
            const m = /confirm/i.test(res.error.message) ? 'Your account is waiting to be confirmed. Tell Claude you signed up.' : /invalid/i.test(res.error.message) ? 'Email or password is wrong.' : res.error.message;
            return draw(m, 'neg');
          }
          if (res.data.session) return resolve(res.data.session);
          draw('Account created. Tell Claude you signed up, then sign in here.', 'pos');
        });
      };
      draw();
    });
  }
})();
