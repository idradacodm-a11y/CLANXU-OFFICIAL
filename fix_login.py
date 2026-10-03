import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(
    r"const key = prompt\('\[ClanXU\] Enter Clan Key:'\);"
    r".*?"
    r"socket\.on\('key-result', ok => \{"
    r".*?"
    r"\n\}\);",
    re.DOTALL
)

match = pattern.search(content)
if not match:
    print("ERROR: Hindi mahanap ang login block.")
    exit()

new_code = """const savedKey = localStorage.getItem('clanx_key');
const savedName = localStorage.getItem('clanx_name');
const savedAdmin = localStorage.getItem('clanx_admin') === 'true';

function logout() {
  if (confirm('Logout ka ba?')) {
    localStorage.clear();
    location.reload();
  }
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

content = content[:match.start()] + new_code + content[match.end():]

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE! Naayos na ang login block.")