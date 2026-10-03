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

const TIERS = {
  "ClanXU Elite": 8000,
  "Legendary": 7000,
  "Grandmaster": 6000,
  "Master": 5000,
  "Pro": 4000,
  "Elite": 3000,
  "Veteran": 2000,
  "Rookie": 1000
};

io.on('connection', (socket) => {
  console.log('Connected:', socket.id);

  socket.on('check-key', (key) => {
    socket.emit('key-result', key === CLAN_KEY);
  });

  socket.on('request-join', (username) => {
    pendingUsers[socket.id] = username;
    socket.emit('wait-approval');
    admins.forEach(id => {
      const adminSocket = io.sockets.sockets.get(id);
      if (adminSocket) adminSocket.emit('new-user-request', { id: socket.id, username });
    });
  });

  socket.on('admin-login', (data) => {
    if (data.password !== ADMIN_PASSWORD) {
      socket.emit('admin-login-fail', 'Mali ang password!');
      return;
    }
    if (admins.length >= MAX_ADMINS && !admins.includes(socket.id)) {
      pendingAdmins[socket.id] = data.username || 'Admin Applicant';
      admins.forEach(id => {
        const a = io.sockets.sockets.get(id);
        if (a) a.emit('new-admin-request', { id: socket.id, username: data.username });
      });
      socket.emit('wait-admin-approval');
      return;
    }
    makeAdmin(socket, data.username);
  });

  socket.on('approve-user', (id) => {
    if (!admins.includes(socket.id)) return;
    const target = io.sockets.sockets.get(id);
    if (target) {
      users[id] = { username: pendingUsers[id] || 'Member', rank: 'Rookie', uid: 'N/A', screenshot: '' };
      target.emit('approved');
      delete pendingUsers[id];
      io.emit('users-update', Object.values(users));
    }
  });

  socket.on('deny-user', (id) => {
    if (!admins.includes(socket.id)) return;
    const target = io.sockets.sockets.get(id);
    if (target) {
      target.emit('denied');
      delete pendingUsers[id];
    }
  });

  socket.on('approve-admin', (id) => {
    if (!admins.includes(socket.id)) return;
    const target = io.sockets.sockets.get(id);
    if (target) makeAdmin(target, pendingAdmins[id] || 'Admin');
    delete pendingAdmins[id];
  });

  socket.on('deny-admin', (id) => {
    if (!admins.includes(socket.id)) return;
    const target = io.sockets.sockets.get(id);
    if (target) target.emit('admin-denied');
    delete pendingAdmins[id];
  });

  socket.on('save-profile', (data) => {
    if (!users[socket.id]) users[socket.id] = {};
    users[socket.id] = {
      ...users[socket.id],
      username: data.username || users[socket.id].username,
      uid: data.uid || 'N/A',
      rank: data.rank || 'Rookie',
      screenshot: data.screenshot || users[socket.id].screenshot || ''
    };
    socket.emit('profile-saved');
    io.emit('users-update', Object.values(users));
  });

  socket.on('chat-message', (data) => {
    const msg = {
      id: Date.now() + '-' + Math.random().toString(36).substr(2, 6),
      user: data.user,
      text: data.text,
      type: data.type || 'text',
      time: new Date().toLocaleTimeString()
    };
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
    admins.forEach(id => {
      const a = io.sockets.sockets.get(id);
      if (a) a.emit('new-tryout', t);
    });
    socket.emit('tryout-submitted');
  });

  socket.on('approve-tryout', (id) => {
    if (!admins.includes(socket.id)) return;
    tryouts = tryouts.filter(t => t.id !== id);
    io.emit('tryout-approved', id);
  });

  socket.on('deny-tryout', (id) => {
    if (!admins.includes(socket.id)) return;
    tryouts = tryouts.filter(t => t.id !== id);
    io.emit('tryout-denied', id);
  });

  socket.on('get-initial', () => {
    socket.emit('initial-data', {
      chat: chatHistory,
      users: Object.values(users),
      announcements: announcements,
      isAdmin: admins.includes(socket.id)
    });
  });

  socket.on('disconnect', () => {
    admins = admins.filter(id => id !== socket.id);
    delete pendingUsers[socket.id];
    delete users[socket.id];
    io.emit('users-update', Object.values(users));
  });
});

function makeAdmin(socket, username) {
  if (!admins.includes(socket.id)) admins.push(socket.id);
  if (!users[socket.id]) users[socket.id] = { username: username || 'Admin', rank: 'ClanXU Elite', uid: 'N/A', screenshot: '' };
  users[socket.id].rank = 'ClanXU Elite';
  socket.emit('admin-approved');
  io.emit('users-update', Object.values(users));
}

const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => {
  console.log('');
  console.log('===========================================');
  console.log('  ✅ CLANXU SERVER RUNNING!');
  console.log('===========================================');
  console.log('  Running on port: ' + PORT);
  console.log('===========================================');
});