import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Hanapin ang login block
pattern = re.compile(
    r"const key = prompt\('\[ClanXU\] Enter Clan Key:'\);.*?\n\}\);",
    re.DOTALL
)

new_login = """// === SAVE LOGIN ===
const savedKey = localStorage.getItem('clanx_key');
const savedName = localStorage.getItem('clanx_name');
const savedAdmin = localStorage.getItem('clanx_admin') === 'true';

function logout() {
  if (confirm('Logout ka ba?')) {
    localStorage.clear();
    location.reload();
  }
}

if (savedKey && savedName) {
  // AUTO-LOGIN - hindi na tatanungin
  myName = savedName;
  socket.emit('check-key', savedKey);
  socket.on('key-result', ok => {
    if (!ok) { localStorage.clear(); location.reload(); return; }
    if (savedAdmin) {
      socket.emit('admin-login', { password: 'CLANXU2026', username: savedName });
    } else {
      socket.emit('request-join', savedName);
    }
  });
} else {
  // FIRST TIME LOGIN
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
    print("✅ SAVE LOGIN ADDED!")
else:
    print("⚠️ Block not found. Current login code:")
    idx = html.find('const key = prompt')
    print(html[idx:idx+500])

# Idagdag ang logout button
if 'onclick="logout()"' not in html:
    html = html.replace(
        '<h1>CLAN <span>XU</span> OFFICIAL</h1>',
        '<h1>CLAN <span>XU</span> OFFICIAL</h1>\n<button onclick="logout()" style="position:absolute;top:10px;right:10px;padding:6px 12px;font-size:10px;background:#333;border:1px solid #ff2a2a;color:#fff;border-radius:4px">LOGOUT</button>'
    )
    print("✅ LOGOUT BUTTON ADDED!")

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("DONE!")