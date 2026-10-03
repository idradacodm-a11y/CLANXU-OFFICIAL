import re

# ============ FIX SERVER.JS ============
with open('server.js', 'r', encoding='utf-8') as f:
    srv = f.read()

# 1. Siguraduhing may joinRequests declaration
if 'let joinRequests' not in srv:
    srv = srv.replace(
        'let pendingUsers = {};',
        'let pendingUsers = {};\nlet joinRequests = {};'
    )

# 2. Palitan ang request-join handler
rj_pattern = re.compile(
    r"socket\.on\('request-join'.*?\n  \}\);",
    re.DOTALL
)
new_rj = """socket.on('request-join', (data) => {
    const uname = data.username || data;
    if (!uname) return;
    
    // EXISTING? Auto-approve
    if (users[uname]) {
      socket.emit('approved');
      io.emit('users-update', Object.values(users));
      return;
    }
    
    // PENDING NA? Wag mag-doble
    const alreadyPending = Object.values(joinRequests).find(r => r.username === uname);
    if (alreadyPending) {
      socket.emit('wait-approval');
      return;
    }
    
    // BAGO - idagdag sa queue
    const reqData = typeof data === 'object' ? data : { username: data };
    joinRequests[socket.id] = reqData;
    pendingUsers[socket.id] = uname;
    socket.emit('wait-approval');
    io.to('admin-room').emit('mailbox-refresh', getMailboxData());
    io.to('admin-room').emit('new-user-request', { id: socket.id, ...reqData });
  });"""
if rj_pattern.search(srv):
    srv = rj_pattern.sub(new_rj, srv)

# 3. Siguraduhing may getMailboxData
if 'function getMailboxData' not in srv:
    srv = srv.replace(
        'io.on(\'connection\'',
        '''function getMailboxData() {
  return {
    joins: Object.entries(joinRequests).map(([id, d]) => ({
      id, username: d.username, uid: d.uid, rank: d.rank, screenshot: d.screenshot,
      time: new Date().toLocaleString()
    })),
    admins: Object.entries(pendingAdmins).map(([id, u]) => ({ id, username: u, time: new Date().toLocaleString() })),
    tryouts: tryouts
  };
}

io.on('connection\''''
    )

# 4. Siguraduhing naka-join sa admin-room
if "socket.join('admin-room')" not in srv:
    srv = srv.replace(
        'socket.emit(\'admin-approved\');',
        "socket.join('admin-room');\n  socket.emit('admin-approved');"
    )

with open('server.js', 'w', encoding='utf-8') as f:
    f.write(srv)
print("✅ server.js fixed")

# ============ FIX INDEX.HTML ============
with open('public/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Palitan lahat ng request-join emission
html = html.replace(
    "socket.emit('request-join', savedName);",
    "socket.emit('request-join', { username: savedName, uid: localStorage.getItem('clanx_uid')||'N/A', rank: localStorage.getItem('clanx_rank')||'Rookie', screenshot: localStorage.getItem('clanx_shot')||'' });"
)
html = html.replace(
    "socket.emit('request-join', myName);",
    "socket.emit('request-join', { username: myName, uid: 'N/A', rank: 'Rookie', screenshot: '' });"
)

# 2. Siguraduhing may renderMailbox
if 'function renderMailbox' not in html:
    mailbox_js = """
socket.on('mailbox-data', d => { if (isAdmin) renderMailbox(d); });
socket.on('mailbox-refresh', d => { if (isAdmin) renderMailbox(d); });

function renderMailbox(data) {
  if (!data) return;
  document.getElementById('jCount').textContent = data.joins.length;
  document.getElementById('aCount').textContent = data.admins.length;
  document.getElementById('tCount').textContent = data.tryouts.length;

  const j = document.getElementById('mailJoinList');
  j.innerHTML = data.joins.length === 0 ? '<p style="color:#666">Walang request.</p>' :
    data.joins.map(r => `<div style="background:#1a1a1a;padding:10px;border-radius:6px;margin-bottom:8px;border-left:3px solid #ff2a2a">
      <strong style="color:#ffd700">${r.username}</strong>
      <p style="color:#888;font-size:12px;margin:4px 0">UID: ${r.uid||'N/A'} · Rank: ${r.rank||'Rookie'}</p>
      <p style="color:#666;font-size:11px;margin:4px 0">${r.time}</p>
      ${r.screenshot ? `<img src="${r.screenshot}" style="max-width:100%;border-radius:6px;margin:8px 0;border:2px solid #ff2a2a">` : ''}
      <button onclick="socket.emit('approve-user','${r.id}')" style="padding:6px 10px;font-size:10px">✅ ACCEPT</button>
      <button onclick="socket.emit('deny-user','${r.id}')" style="padding:6px 10px;font-size:10px;background:#444">❌ DENY</button>
    </div>`).join('');

  const a = document.getElementById('mailAdminList');
  a.innerHTML = data.admins.length === 0 ? '<p style="color:#666">Walang request.</p>' :
    data.admins.map(r => `<div style="background:#1a1a1a;padding:10px;border-radius:6px;margin-bottom:8px;border-left:3px solid #ffd700">
      <strong style="color:#ffd700">${r.username}</strong>
      <button onclick="socket.emit('approve-admin','${r.id}')" style="padding:6px 10px;font-size:10px">✅ ACCEPT</button>
      <button onclick="socket.emit('deny-admin','${r.id}')" style="padding:6px 10px;font-size:10px;background:#444">❌ DENY</button>
    </div>`).join('');

  const t = document.getElementById('mailTryoutList');
  t.innerHTML = data.tryouts.length === 0 ? '<p style="color:#666">Walang try-out.</p>' :
    data.tryouts.map(r => `<div style="background:#1a0a0a;padding:10px;border-radius:6px;margin-bottom:8px;border-left:3px solid #ff2a2a">
      <strong style="color:#ffd700">${r.username}</strong>
      <p style="color:#888;font-size:12px">UID: ${r.uid} · Rank: ${r.rank}</p>
      <button onclick="socket.emit('approve-tryout',${r.id})" style="padding:6px 10px;font-size:10px">✅ ACCEPT</button>
      <button onclick="socket.emit('deny-tryout',${r.id})" style="padding:6px 10px;font-size:10px;background:#444">❌ DENY</button>
    </div>`).join('');
}
"""
    html = html.replace('</script>\n</body>', mailbox_js + '\n</script>\n</body>')

# 3. Siguraduhing naka-call ang get-mailbox pag admin-approved
html = html.replace(
    "document.getElementById('mailboxTab').style.display = 'block';",
    "document.getElementById('mailboxTab').style.display = 'block';\n  socket.emit('get-mailbox');"
)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("✅ index.html fixed")
print("\n🎉 DONE! Push mo na.")