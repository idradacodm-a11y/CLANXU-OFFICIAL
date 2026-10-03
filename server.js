const express = require('express');
const http = require('http');
const { Server } = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.static('public'));

const ADMIN_PASSWORD = "CLANXU2026";
const CLAN_KEY = "ClanXU";
const MAX_ADMINS = 4;

let pendingUsers = {};
let pendingAdmins = {};
let admins = [];
let users = {};
let announcements = [];
let chatHistory = [];
let tryouts = [];
let joinRequests = {};   // <-- IDINAGDAG

const TIERS = {
  "ClanXU Elite": 8000, "Legendary": 7000, "Grandmaster": 6000,
  "Master": 5000, "Pro": 4000, "Elite": 3000, "Veteran": 2000, "Rookie": 1000
};

function getMailboxData() {
  return {
    joins: Object.entries(pendingUsers).map(([id, username]) => ({ id, username, time: new Date().toLocaleString() })),
    admins: Object.entries(pendingAdmins).map(([id, username]) => ({ id, username, time: new Date().toLocaleString() })),
    tryouts: tryouts
  };
}

io.on('connection', (socket) => {
  socket.on('check-key', (key) => socket.emit('key-result', key === CLAN_KEY));

  socket.on('request-join', (data) => {
    // data = { username, uid, rank, screenshot }
    const uname = data.username;
    
    // CHECK KUNG EXISTING MEMBER NA
    const existing = Object.values(users).find(u => u.username === uname);
    if (existing) {
      // Kilala na natin siya! Auto-approve, hindi na kailangan ng admin
      socket.emit('approved');
      // I-update yung uid/rank/screenshot kung may bago
      if (data.uid && data.uid !== 'N/A') existing.uid = data.uid;
      if (data.rank && data.rank !== 'Rookie') existing.rank = data.rank;
      if (data.screenshot) existing.screenshot = data.screenshot;
      io.emit('users-update', Object.values(users));
      return;
    }
    
    // CHECK KUNG NAG-REQUEST NA SIYA (naghihintay pa ng approval)
    const alreadyPending = Object.values(joinRequests).find(r => r.username === uname);
    if (alreadyPending) {
      socket.emit('wait-approval');
      return;
    }
    
    // BAGONG MEMBER - kailangan ng approval
    joinRequests[socket.id] = data;
    pendingUsers[socket.id] = uname;
    socket.emit('wait-approval');
    io.to('admin-room').emit('mailbox-refresh', getMailboxData());
    io.to('admin-room').emit('new-user-request', { id: socket.id, ...data });
  });

  socket.on('admin-login', (data) => {
    if (data.password !== ADMIN_PASSWORD) return socket.emit('admin-login-fail', 'Mali ang password!');
    if (admins.length >= MAX_ADMINS && !admins.includes(socket.id)) {
      pendingAdmins[socket.id] = data.username || 'Admin';
      io.to('admin-room').emit('mailbox-refresh', getMailboxData());
      return socket.emit('wait-admin-approval');
    }
    makeAdmin(socket, data.username);
  });

  socket.on('approve-user', (id) => {
    if (!admins.includes(socket.id)) return;
    const t = io.sockets.sockets.get(id);
    const uname = pendingUsers[id] || 'Member';
    if (t) {
      if (!users[uname]) users[uname] = {};
      users[uname] = { username: uname, rank: 'Rookie', uid: 'N/A', screenshot: '', role: 'Member' };
      t.emit('approved');
      delete pendingUsers[id];
      io.emit('users-update', Object.values(users));
      io.to('admin-room').emit('mailbox-refresh', getMailboxData());
    }
  });

  socket.on('deny-user', (id) => {
    if (!admins.includes(socket.id)) return;
    const t = io.sockets.sockets.get(id);
    if (t) t.emit('denied');
    delete pendingUsers[id];
    io.to('admin-room').emit('mailbox-refresh', getMailboxData());
  });

  socket.on('approve-admin', (id) => {
    if (!admins.includes(socket.id)) return;
    const t = io.sockets.sockets.get(id);
    if (t) makeAdmin(t, pendingAdmins[id] || 'Admin');
    delete pendingAdmins[id];
    io.to('admin-room').emit('mailbox-refresh', getMailboxData());
  });

  socket.on('deny-admin', (id) => {
    if (!admins.includes(socket.id)) return;
    const t = io.sockets.sockets.get(id);
    if (t) t.emit('admin-denied');
    delete pendingAdmins[id];
    io.to('admin-room').emit('mailbox-refresh', getMailboxData());
  });

  socket.on('save-profile', (data) => {
    if (!data.username) return socket.emit('profile-saved');
    if (!users[data.username]) users[data.username] = {};
    users[data.username] = { ...users[data.username], ...data };
    socket.emit('profile-saved');
    io.emit('users-update', Object.values(users));
  });

  socket.on('chat-message', (data) => {
    const msg = { id: Date.now() + '-' + Math.random().toString(36).substr(2, 6), user: data.user, text: data.text, type: data.type || 'text', time: new Date().toLocaleTimeString() };
    chatHistory.push(msg);
    if (chatHistory.length > 200) chatHistory.shift();
    io.emit('chat-message', msg);
  });

  socket.on('delete-message', (id) => {
    if (!admins.includes(socket.id)) return;
    chatHistory = chatHistory.filter(m => m.id !== id);
    io.emit('message-deleted', id);
  });

  socket.on('announce', (text) => {
    if (!admins.includes(socket.id)) return;
    const a = { id: Date.now(), text, time: new Date().toLocaleString() };
    announcements.unshift(a);
    io.emit('announcement', a);
  });

  socket.on('submit-tryout', (data) => {
    const t = { id: Date.now(), ...data, time: new Date().toLocaleString() };
    tryouts.unshift(t);
    io.to('admin-room').emit('mailbox-refresh', getMailboxData());
    socket.emit('tryout-submitted');
  });

  socket.on('approve-tryout', (id) => {
    if (!admins.includes(socket.id)) return;
    tryouts = tryouts.filter(t => t.id !== id);
    io.emit('tryout-approved', id);
    io.to('admin-room').emit('mailbox-refresh', getMailboxData());
  });

  socket.on('deny-tryout', (id) => {
    if (!admins.includes(socket.id)) return;
    tryouts = tryouts.filter(t => t.id !== id);
    io.emit('tryout-denied', id);
    io.to('admin-room').emit('mailbox-refresh', getMailboxData());
  });

  socket.on('get-mailbox', () => {
    if (!admins.includes(socket.id)) return;
    socket.emit('mailbox-data', getMailboxData());
  });

  socket.on('get-initial', () => {
    socket.emit('initial-data', {
      chat: chatHistory,
      users: Object.values(users),
      announcements: announcements,
      isAdmin: admins.includes(socket.id),
      mailbox: admins.includes(socket.id) ? getMailboxData() : { joins: [], admins: [], tryouts: [] }
    });
  });

  socket.on('disconnect', () => {
    admins = admins.filter(id => id !== socket.id);
    delete pendingUsers[socket.id];
    io.emit('users-update', Object.values(users));
  });
});

function makeAdmin(socket, username) {
  if (!admins.includes(socket.id)) admins.push(socket.id);
  socket.join('admin-room');
  const uname = username || 'Admin';
  if (!users[uname]) users[uname] = { username: uname, rank: 'ClanXU Elite', uid: 'N/A', screenshot: '', role: 'Admin' };
  users[uname].rank = 'ClanXU Elite';
  users[uname].role = 'Admin';
  socket.emit('admin-approved');
  socket.emit('mailbox-data', getMailboxData());
  io.emit('users-update', Object.values(users));
}

const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => console.log(`Server running on port ${PORT}`));