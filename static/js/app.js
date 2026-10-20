// Comportamiento común de la aplicación
(function () {
  // Menú lateral en pantallas pequeñas
  document.querySelectorAll('[data-menu-toggle]').forEach(function (boton) {
    boton.addEventListener('click', function () { document.body.classList.toggle('menu-abierto'); });
  });

  // Botones Atrás / Adelante de la barra superior
  document.querySelectorAll('[data-historial]').forEach(function (boton) {
    boton.addEventListener('click', function () {
      if (boton.dataset.historial === 'atras') window.history.back(); else window.history.forward();
    });
  });

  // "Cancelar" lleva al mismo sitio que el botón "Volver" de la página
  document.querySelectorAll('[data-igual-que]').forEach(function (enlace) {
    var origen = document.getElementById(enlace.dataset.igualQue);
    if (origen) enlace.href = origen.href;
  });

  // Confirmación antes de acciones delicadas: <form data-confirmar="¿Seguro?">
  document.querySelectorAll('form[data-confirmar]').forEach(function (form) {
    form.addEventListener('submit', function (evento) {
      if (!window.confirm(form.dataset.confirmar)) evento.preventDefault();
    });
  });

  // Cerrar mensajes
  document.querySelectorAll('.alerta__cerrar').forEach(function (boton) {
    boton.addEventListener('click', function () { boton.closest('.alerta').remove(); });
  });

  // Cambiar estado al elegir en un <select data-enviar-al-cambiar>
  document.querySelectorAll('select[data-enviar-al-cambiar]').forEach(function (select) {
    select.addEventListener('change', function () { select.form.submit(); });
  });

  // Pasarela de pago: agrupa el número de tarjeta y pone la barra en MM/AA
  var numero = document.getElementById('id_numero_tarjeta');
  var vista = document.querySelector('[data-tarjeta-numero]');
  if (numero) {
    numero.addEventListener('input', function () {
      var digitos = numero.value.replace(/\D/g, '').slice(0, 16);
      numero.value = digitos.replace(/(.{4})/g, '$1 ').trim();
      if (vista) vista.textContent = (digitos + '················').slice(0, 16).replace(/(.{4})/g, '$1 ').trim();
    });
  }
  var titular = document.getElementById('id_nombre_titular');
  var vistaTitular = document.querySelector('[data-tarjeta-titular]');
  if (titular && vistaTitular) {
    titular.addEventListener('input', function () { vistaTitular.textContent = titular.value || 'Nombre del titular'; });
  }
  var expira = document.getElementById('id_fecha_expiracion');
  var vistaExpira = document.querySelector('[data-tarjeta-expira]');
  if (expira) {
    expira.addEventListener('input', function () {
      var d = expira.value.replace(/\D/g, '').slice(0, 4);
      expira.value = d.length > 2 ? d.slice(0, 2) + '/' + d.slice(2) : d;
      if (vistaExpira) vistaExpira.textContent = expira.value || 'MM/AA';
    });
  }
})();
