import re

# ============ FIX SERVER.JS ============
with open('server.js', 'r', encoding='utf-8') as f:
    srv = f.read()

# save-profile: gamitin ang existing username key
old_sp = re.search(r"socket\.on\('save-profile'.*?\n  \}\);", srv, re.DOTALL)
if old_sp:
    new_sp = """socket.on('save-profile', (data) => {
    const uname = data.username;
    if (!uname) return socket.emit('profile-saved');
    if (!users[uname]) users[uname] = { username: uname, rank: 'Rookie', uid: 'N/A', screenshot: '', role: 'Member' };
    if (data.uid) users[uname].uid = data.uid;
    if (data.rank) users[uname].rank = data.rank;
    if (data.screenshot) users[uname].screenshot = data.screenshot;
    socket.emit('profile-saved');
    io.emit('users-update', Object.values(users));
  });"""
    srv = srv[:old_sp.start()] + new_sp + srv[old_sp.end():]

with open('server.js', 'w', encoding='utf-8') as f:
    f.write(srv)
print("✅ server.js fixed")

# ============ FIX INDEX.HTML ============
with open('public/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Profile tab - ilagay ang IGN (readonly) at fields
old_profile = re.search(r'<div id="content-profile".*?</div>\s*</div>\s*</div>', html, re.DOTALL)
if old_profile:
    new_profile = '''<div id="content-profile" class="content">
  <div class="card">
    <h3>👤 IYONG PROFILE</h3>
    <div style="text-align:center; margin-bottom:15px">
      <img id="myAvatar" class="avatar" src="https://via.placeholder.com/80" alt="">
      <p id="myIGN" style="color:#ffd700; font-weight:bold; font-size:18px; margin-top:8px"></p>
      <p id="myRank" style="color:#00adb5; font-size:14px"></p>
    </div>
    <label>UID (CODM):</label>
    <input type="text" id="pUid" placeholder="Ilagay ang UID">
    <label>Rank:</label>
    <select id="pRank">
      <option>Rookie</option><option>Veteran</option><option>Elite</option>
      <option>Pro</option><option>Master</option><option>Grandmaster</option>
      <option>Legendary</option><option>ClanXU Elite</option>
    </select>
    <label>Collection Screenshot (link):</label>
    <input type="text" id="pShot" placeholder="Paste Imgur/Discord link">
    <button style="width:100%;margin-top:10px" onclick="saveProfile()">💾 I-SAVE</button>
  </div>
</div>'''
    html = html[:old_profile.start()] + new_profile + html[old_profile.end():]

# 2. saveProfile function
old_sp_html = re.search(r'function saveProfile\(\).*?\n\}', html, re.DOTALL)
if old_sp_html:
    new_sp_html = '''function saveProfile() {
  socket.emit('save-profile', {
    username: myName,
    uid: document.getElementById('pUid').value,
    rank: document.getElementById('pRank').value,
    screenshot: document.getElementById('pShot').value
  });
}'''
    html = html[:old_sp_html.start()] + new_sp_html + html[old_sp_html.end():]

# 3. users-update - clickable leaderboard + popup
old_lb = re.search(r"socket\.on\('users-update'.*?\n\}\);", html, re.DOTALL)
if old_lb:
    new_lb = '''socket.on('users-update', users => {
  window.currentUsers = users;
  const order = ['ClanXU Elite','Legendary','Grandmaster','Master','Pro','Elite','Veteran','Rookie'];
  const sorted = [...users].sort((a,b) => order.indexOf(a.rank) - order.indexOf(b.rank));
  const lb = document.getElementById('leaderboard');
  if (sorted.length === 0) { lb.innerHTML = '<p style="color:#666">Walang members.</p>'; return; }
  lb.innerHTML = sorted.map((u,i) => {
    const cls = u.rank.replace(/\\s+/g,'');
    return `<div class="lb-row" onclick="showMemberInfo('${escapeHtml(u.username)}')" style="cursor:pointer">
      <span>#${i+1} <strong>${escapeHtml(u.username)}</strong></span>
      <span class="tier ${cls}">${u.rank}</span>
    </div>`;
  }).join('');
});

function showMemberInfo(username) {
  const u = (window.currentUsers || []).find(x => x.username === username);
  if (!u) return;
  const old = document.getElementById('memberModal');
  if (old) old.remove();
  const modal = document.createElement('div');
  modal.id = 'memberModal';
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.9);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px';
  modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
  modal.innerHTML = `<div style="background:#111;border:2px solid #ff2a2a;border-radius:10px;padding:20px;max-width:400px;width:100%;max-height:85vh;overflow-y:auto">
    <div style="text-align:center;margin-bottom:15px">
      <h2 style="color:#ffd700;margin:0">${escapeHtml(u.username)}</h2>
      <p style="color:#00adb5;font-size:14px;margin-top:5px">${u.rank}</p>
    </div>
    <div style="background:#1a1a1a;border-radius:6px;padding:12px;margin-bottom:10px">
      <p style="color:#888;font-size:11px">UID</p>
      <p style="color:#fff;font-size:14px;font-weight:bold">${escapeHtml(u.uid||'N/A')}</p>
    </div>
    <div style="background:#1a1a1a;border-radius:6px;padding:12px;margin-bottom:10px">
      <p style="color:#888;font-size:11px">RANK</p>
      <p style="color:#fff;font-size:14px;font-weight:bold">${escapeHtml(u.rank||'N/A')}</p>
    </div>
    <div style="background:#1a1a1a;border-radius:6px;padding:12px;margin-bottom:10px">
      <p style="color:#888;font-size:11px;margin-bottom:8px">SCREENSHOT</p>
      ${u.screenshot ? `<img src="${u.screenshot}" style="width:100%;border-radius:6px;border:2px solid #ff2a2a" onerror="this.outerHTML='<p style=color:#666;font-size:12px>Walang screenshot.</p>'">` : '<p style="color:#666;font-size:12px">Walang screenshot.</p>'}
    </div>
    <button onclick="document.getElementById('memberModal').remove()" style="width:100%;margin-top:10px">CLOSE</button>
  </div>`;
  document.body.appendChild(modal);
}'''
    html = html[:old_lb.start()] + new_lb + html[old_lb.end():]

# 4. Update myIGN pag nag-login
if 'getElementById(\'myIGN\')' not in html:
    html = html.replace(
        "socket.emit('admin-login', { password: pwd, username: myName });",
        "socket.emit('admin-login', { password: pwd, username: myName });\n      if(document.getElementById('myIGN')) document.getElementById('myIGN').textContent = myName;"
    )
    html = html.replace(
        "socket.emit('request-join', { username: myName, uid: 'N/A', rank: 'Rookie', screenshot: '' });",
        "socket.emit('request-join', { username: myName, uid: 'N/A', rank: 'Rookie', screenshot: '' });\n      if(document.getElementById('myIGN')) document.getElementById('myIGN').textContent = myName;"
    )

# 5. Auto-fill profile fields pag bukas ng Profile tab
if 'fillProfileFields' not in html:
    helper = """
function fillProfileFields() {
  const ign = document.getElementById('myIGN');
  const rank = document.getElementById('myRank');
  if (ign) ign.textContent = myName;
  if (rank && window.currentUsers) {
    const me = window.currentUsers.find(u => u.username === myName);
    if (me) {
      if (rank) rank.textContent = me.rank || '';
      if (document.getElementById('pUid')) document.getElementById('pUid').value = me.uid || '';
      if (document.getElementById('pRank')) document.getElementById('pRank').value = me.rank || 'Rookie';
      if (document.getElementById('pShot')) document.getElementById('pShot').value = me.screenshot || '';
    }
  }
}
"""
    html = html.replace('function switchTab(', helper + '\nfunction switchTab(')
    html = html.replace(
        "if (tabName === 'leaderboard') socket.emit('get-leaderboard');",
        ""
    )
    # Call fillProfileFields sa switchTab
    html = html.replace(
        "event.target.classList.add('active');",
        "event.target.classList.add('active');\n  if(name === 'profile') fillProfileFields();"
    )

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("✅ index.html fixed")
print("\n🎉 DONE! Push mo na.")