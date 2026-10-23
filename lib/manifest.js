(function () {
  "use strict";

  /* ==========================================================================
     PICK MEALS — datos de marca y CONFIGURACIÓN ÚNICA del sitio.
     Todo lo que haya que cambiar de contacto o de envío del formulario
     se cambia acá, en un solo lugar. Las tres páginas leen este archivo.
     ========================================================================== */

  window.__BRAND__ = {
    name: "Pick Meals",
    url: "https://pickmeals.com.ar",

    contact: {
      // Número de WhatsApp confirmado por el cliente.
      whatsapp: "5491136065066",

      // Teléfono confirmado, tal como se muestra en el sitio.
      phone: "+54 9 11 3606-5066",

      email: "info@pickmeals.com.ar",
      instagram: "https://www.instagram.com/pickmeals.ar/",
      linktree: "https://linktr.ee/pickmeals",

      // Planta de elaboración (no es local de atención al público).
      address: "Padre M. Ashkar 566, Villa Lynch, Buenos Aires",

      // PENDIENTE: URL real de LinkedIn.
      linkedin: ""
    },

    // Mensaje prearmado del botón flotante de WhatsApp (todas las páginas).
    whatsappDefaultText: "Hola PICK MEALS, vi su sitio web y quería hacer una consulta...",

    // Envío del formulario "Quiero vender Pick Meals" — ÚNICO punto de configuración.
    //   endpoint vacío  → modo local: se arma el mensaje con los datos y se abre WhatsApp.
    //   endpoint "lead.php" → al publicar: se guardan los datos en el servidor (plantilla lead.php
    //   de la skill, adaptada a estos campos: nombre, comercio, tipo, localidad, telefono,
    //   email, mensaje, consentimiento). Si el servidor falla, vuelve solo a WhatsApp.
    leads: {
      endpoint: ""
    }
  };
})();
