(function () {
  var genBtn = document.getElementById('gen-btn');
  var codeInput = document.getElementById('new-code');
  if (genBtn && codeInput) {
    genBtn.addEventListener('click', function () {
      var chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
      var out = '';
      for (var i = 0; i < 16; i++) {
        out += chars[Math.floor(Math.random() * chars.length)];
      }
      codeInput.value = out;
    });
  }
})();
