// No academic results or authenticated API responses are cached.
self.addEventListener('push', event => {
  let payload = {title:'MUJhe ky',body:'Your academic results changed.',url:'/app'};
  try { payload = {...payload,...event.data.json()}; } catch {}
  event.waitUntil(self.registration.showNotification(payload.title, {body:payload.body,icon:'/icon.svg',badge:'/icon.svg',data:{url:'/app'}}));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(async windows => {
    for (const window of windows) { if (new URL(window.url).origin === self.location.origin) { await window.navigate('/app'); await window.focus(); return; } }
    return clients.openWindow('/app');
  }));
});
