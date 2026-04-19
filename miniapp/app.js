const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const panel = document.getElementById('panel');
const closeBtn = document.getElementById('closeBtn');

const views = {
  order: {title: 'Buyurtma berish', text: 'Bu yerga keyingi bosqichda rasmli menyu, taom tanlash va to‘lov oqimi ulanadi.\n\nHozircha buyurtmani bot ichidagi 🍽 Buyurtma berish tugmasi orqali davom ettirasiz.'},
  booking: {title: 'Xona band qilish', text: 'Bu bo‘limda yaqin bosqichda kalendar, vaqt va xona band qilish mini app ichida ishlaydi.\n\nHozircha bot ichidagi 🏠 Xona band qilish tugmasidan foydalaning.'},
  foods: {title: 'Taomlar', text: 'Tez orada bu yerga taomlarning rasmlari, tarkibi va narxlari qo‘shiladi.'},
  contact: {title: 'Kontakt', text: 'Telefon: +998 99 766 55 97\nManzil: Andijon shahar, Samarqand ko‘chasi 54-uy\nMo‘ljal: Toshkent mehmonxonasi ro‘parasidan 100 metr kiriladi.'}
};

document.querySelectorAll('.feature-card').forEach((btn) => {
  btn.addEventListener('click', () => {
    const action = btn.dataset.action;
    const view = views[action];
    if (!view) return;
    panel.innerHTML = `<h2>${view.title}</h2><p>${view.text}</p><span class="badge">Mini App demo oynasi</span>`;
    if (tg) {
      tg.HapticFeedback?.impactOccurred('light');
      tg.MainButton.setText(view.title);
      tg.MainButton.show();
    }
  });
});

if (tg) {
  tg.MainButton.onClick(() => {
    tg.sendData(JSON.stringify({ type: 'miniapp_action', text: 'main_button_click' }));
  });
