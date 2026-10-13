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
      // PENDIENTE: número de WhatsApp confirmado por el cliente.
      // Formato internacional, sólo dígitos, sin "+" ni espacios. Ej. Argentina celular: "549" + característica + número.
      // Mientras esté vacío, los botones abren WhatsApp con el mensaje listo y la persona elige a quién enviarlo.
      whatsapp: "",

      // PENDIENTE: teléfono confirmado, tal como se va a mostrar (ej. "+54 9 11 1234-5678").
      // Vacío = no se muestra en ningún lado.
      phone: "",

      email: "info@pickmeals.com.ar",
      instagram: "https://www.instagram.com/pickmeals.ar/",
      linktree: "https://linktr.ee/pickmeals",

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
