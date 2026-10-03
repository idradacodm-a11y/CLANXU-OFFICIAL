import re

# ========== FIX INDEX.HTML ==========
with open('public/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# --- 1. Palitan ang login block ---
pattern = re.compile(
    r"const key = prompt\('\[ClanXU\] Enter Clan Key:'\);"
    r".*?"
    r"\n\}\);",
    re.DOTALL
)

new_login = """const savedKey = localStorage.getItem('clanx_key');
const savedName = localStorage.getItem('clanx_name');
const savedAdmin = localStorage.getItem('clanx_admin') === 'true';

function logout() {
  if (confirm('Logout ka ba?')) { localStorage.clear(); location.reload(); }
}

if (savedKey && savedName) {
  myName = savedName;
  socket.emit('check-key', savedKey);
  socket.on('key-result', ok => {
    if (!ok) { localStorage.clear(); location.reload(); return; }
    if (savedAdmin) socket.emit('admin-login', { password: 'CLANXU2026', username: savedName });
    else socket.emit('request-join', savedName);
  });
} else {
  const key = prompt('[ClanXU] Enter Clan Key:');
  socket.emit('check-key', key);
  socket.on('key-result', ok => {
    if (!ok) { alert('Invalid Key'); location.reload(); return; }
    const isAdminAttempt = confirm('Are you the ADMIN?');
    if (isAdminAttempt) {
      const pwd = prompt('Admin Password:');
      const name = prompt('Your IGN:');
      myName = name || 'Admin';
      localStorage.setItem('clanx_key', key);
      localStorage.setItem('clanx_name', myName);
      localStorage.setItem('clanx_admin', 'true');
      socket.emit('admin-login', { password: pwd, username: myName });
    } else {
      const name = prompt('Your IGN:');
      myName = name || 'Recruit';
      localStorage.setItem('clanx_key', key);
      localStorage.setItem('clanx_name', myName);
      localStorage.setItem('clanx_admin', 'false');
      socket.emit('request-join', myName);
    }
  });
}"""

match = pattern.search(html)
if match:
    html = html[:match.start()] + new_login + html[match.end():]
    print("✅ Login block updated")
else:
    print("⚠️ Login block not found (baka naayos na)")

# --- 2. Idagdag ang Mailbox tab ---
if 'mailboxTab' not in html:
    html = html.replace(
        '<div class="tab" onclick="switchTab(\'admin\',event)" id="adminTab" style="display:none">🛡️ Admin</div>',
        '<div class="tab" onclick="switchTab(\'mailbox\',event)" id="mailboxTab" style="display:none">📬 Mailbox</div>\n'
        '<div class="tab" onclick="switchTab(\'admin\',event)" id="adminTab" style="display:none">🛡️ Admin</div>'
    )
    print("✅ Mailbox tab added")
else:
    print("⚠️ Mailbox tab already exists")

# --- 3. Idagdag ang Mailbox content ---
mailbox_html = """
<div id="content-mailbox" class="content">
  <div class="card">
    <h3>📬 MAILBOX (Admin Only)</h3>
    <p style="color:#666;font-size:12px;margin-bottom:15px">Lahat ng pending requests ay nandito. Hindi ito nakikita ng members.</p>
    <h4 style="color:#ffd700;margin:15px 0 8px">👥 JOIN REQUESTS (<span id="jCount">0</span>)</h4>
    <div id="mailJoinList"><p style="color:#666">Walang request.</p></div>
    <h4 style="color:#ffd700;margin:15px 0 8px">🛡️ ADMIN REQUESTS (<span id="aCount">0</span>)</h4>
    <div id="mailAdminList"><p style="color:#666">Walang request.</p></div>
    <h4 style="color:#ffd700;margin:15px 0 8px">⚔️ TRY-OUTS (<span id="tCount">0</span>)</h4>
    <div id="mailTryoutList"><p style="color:#666">Walang try-out.</p></div>
  </div>
</div>
"""

if 'content-mailbox' not in html:
    html = html.replace(
        '<div id="content-admin" class="content">',
        mailbox_html + '\n<div id="content-admin" class="content">'
    )
    print("✅ Mailbox content added")
else:
    print("⚠️ Mailbox content already exists")

# --- 4. Idagdag ang mailbox JS handlers ---
mailbox_js = """
socket.on('mailbox-data', data => { if (isAdmin) renderMailbox(data); });
socket.on('mailbox-refresh', data => { if (isAdmin) renderMailbox(data); });

function renderMailbox(data) {
  if (!data) return;
  document.getElementById('jCount').textContent = data.joins.length;
  document.getElementById('aCount').textContent = data.admins.length;
  document.getElementById('tCount').textContent = data.tryouts.length;

  const j = document.getElementById('mailJoinList');
  j.innerHTML = data.joins.length === 0 ? '<p style="color:#666">Walang request.</p>' :
    data.joins.map(r => `<div style="background:#1a1a1a;padding:10px;border-radius:6px;margin-bottom:8px;border-left:3px solid #ff2a2a">
      <strong style="color:#ffd700">${r.username}</strong>
      <p style="color:#666;font-size:11px;margin:4px 0">${r.time}</p>
      <button onclick="socket.emit('approve-user','${r.id}')" style="padding:6px 10px;font-size:10px">✅ ACCEPT</button>
      <button onclick="socket.emit('deny-user','${r.id}')" style="padding:6px 10px;font-size:10px;background:#444">❌ DENY</button>
    </div>`).join('');

  const a = document.getElementById('mailAdminList');
  a.innerHTML = data.admins.length === 0 ? '<p style="color:#666">Walang request.</p>' :
    data.admins.map(r => `<div style="background:#1a1a1a;padding:10px;border-radius:6px;margin-bottom:8px;border-left:3px solid #ffd700">
      <strong style="color:#ffd700">${r.username}</strong>
      <p style="color:#666;font-size:11px;margin:4px 0">${r.time}</p>
      <button onclick="socket.emit('approve-admin','${r.id}')" style="padding:6px 10px;font-size:10px">✅ ACCEPT</button>
      <button onclick="socket.emit('deny-admin','${r.id}')" style="padding:6px 10px;font-size:10px;background:#444">❌ DENY</button>
    </div>`).join('');

  const t = document.getElementById('mailTryoutList');
  t.innerHTML = data.tryouts.length === 0 ? '<p style="color:#666">Walang try-out.</p>' :
    data.tryouts.map(r => `<div style="background:#1a0a0a;padding:10px;border-radius:6px;margin-bottom:8px;border-left:3px solid #ff2a2a">
      <strong style="color:#ffd700">${r.username}</strong>
      <p style="color:#888;font-size:12px;margin:4px 0">UID: ${r.uid} · Rank: ${r.rank}</p>
      <p style="color:#ccc;font-size:12px">${r.message || ''}</p>
      <button onclick="socket.emit('approve-tryout',${r.id})" style="padding:6px 10px;font-size:10px">✅ ACCEPT</button>
      <button onclick="socket.emit('deny-tryout',${r.id})" style="padding:6px 10px;font-size:10px;background:#444">❌ DENY</button>
    </div>`).join('');
}
"""

if 'renderMailbox' not in html:
    html = html.replace('</script>\n</body>', mailbox_js + '\n</script>\n</body>')
    print("✅ Mailbox JS added")
else:
    print("⚠️ Mailbox JS already exists")

# --- 5. Update admin-approved to show mailbox tab ---
html = html.replace(
    "document.getElementById('adminTab').style.display = 'block';",
    "document.getElementById('adminTab').style.display = 'block';\n  document.getElementById('mailboxTab').style.display = 'block';\n  socket.emit('get-mailbox');"
)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("\n✅ INDEX.HTML DONE!")

# ========== FIX SERVER.JS ==========
with open('server.js', 'r', encoding='utf-8') as f:
    srv = f.read()

# Idagdag ang get-mailbox handler
mailbox_handler = """
  socket.on('get-mailbox', () => {
    if (!admins.includes(socket.id)) return;
    socket.emit('mailbox-data', {
      joins: Object.entries(pendingUsers).map(([id, username]) => ({ id, username, time: 'Pending' })),
      admins: Object.entries(pendingAdmins).map(([id, username]) => ({ id, username, time: 'Pending' })),
      tryouts: tryouts || []
    });
  });
"""

if 'get-mailbox' not in srv:
    srv = srv.replace(
        "  socket.on('get-initial', () => {",
        mailbox_handler + "\n  socket.on('get-initial', () => {"
    )
    print("✅ Server mailbox handler added")
else:
    print("⚠️ Server mailbox handler already exists")

with open('server.js', 'w', encoding='utf-8') as f:
    f.write(srv)

print("\n✅ SERVER.JS DONE!")
print("\n🎉 ALL DONE! Ready to push.")