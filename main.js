(function () {
  "use strict";

  /* ==========================================================================
     PICK MEALS — main.js
     El contenido vive en el HTML. Este archivo sólo enriquece:
     menú, WhatsApp, revelados al hacer scroll y el formulario comercial.
     Configuración (WhatsApp, teléfono, envío del formulario): lib/manifest.js
     ========================================================================== */

  var BRAND = window.__BRAND__ || {};
  var CONTACT = BRAND.contact || {};

  var $ = function (sel, scope) { return (scope || document).querySelector(sel); };
  var $$ = function (sel, scope) { return Array.prototype.slice.call((scope || document).querySelectorAll(sel)); };
  var reduced = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  function safe(fn, name) {
    try { fn(); } catch (e) { console.warn("[" + name + "]", e); }
  }

  /* ---------- WhatsApp ---------- */
  function waNumber() {
    return String(CONTACT.whatsapp || "").replace(/\D/g, "");
  }

  // Sin número configurado, wa.me/?text= abre WhatsApp con el mensaje listo y deja elegir el chat.
  function waUrl(text) {
    var url = "https://wa.me/" + waNumber();
    return text ? url + "?text=" + encodeURIComponent(text) : url;
  }

  function initWhatsAppLinks() {
    $$("[data-wa]").forEach(function (a) {
      if (a.dataset.waBound) return;
      a.dataset.waBound = "1";
      var text = a.getAttribute("data-wa") || BRAND.whatsappDefaultText || "";
      a.setAttribute("href", waUrl(text));
      a.setAttribute("target", "_blank");
      a.setAttribute("rel", "noopener");
    });
  }

  /* ---------- Teléfono (se muestra sólo si está configurado) ---------- */
  function initPhone() {
    var phone = String(CONTACT.phone || "").trim();
    if (!phone) return;
    var tel = "tel:" + phone.replace(/[^\d+]/g, "");
    $$("[data-phone]").forEach(function (el) {
      var link = el.matches("a") ? el : $("a", el);
      var value = $("[data-phone-value]", el);
      if (link) link.setAttribute("href", tel);
      if (value) value.textContent = phone;
      el.hidden = false;
    });
  }

  /* ---------- Año del footer ---------- */
  function initYear() {
    var y = String(new Date().getFullYear());
    $$("[data-year]").forEach(function (el) { el.textContent = y; });
  }

  /* ---------- Header: estado al hacer scroll ---------- */
  function initHeader() {
    var header = $(".site-header");
    if (!header) return;
    var ticking = false;
    function update() {
      header.classList.toggle("is-scrolled", window.scrollY > 24);
      ticking = false;
    }
    update();
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
  }

  /* ---------- Menú móvil ---------- */
  function initMobileMenu() {
    var toggle = $(".nav-toggle");
    var menu = $("#menu-movil");
    if (!toggle || !menu) return;
    var root = document.documentElement;

    function focusables() {
      return $$("a[href], button:not([disabled])", menu).filter(function (el) { return el.offsetParent !== null; });
    }
    function open() {
      menu.classList.add("is-open");
      menu.removeAttribute("inert");
      toggle.setAttribute("aria-expanded", "true");
      toggle.setAttribute("aria-label", "Cerrar menú");
      root.classList.add("menu-open");
      var first = focusables()[0];
      if (first) setTimeout(function () { first.focus(); }, 60);
    }
    function close(returnFocus) {
      menu.classList.remove("is-open");
      menu.setAttribute("inert", "");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Abrir menú");
      root.classList.remove("menu-open");
      if (returnFocus) toggle.focus();
    }
    menu.setAttribute("inert", "");

    toggle.addEventListener("click", function () {
      if (toggle.getAttribute("aria-expanded") === "true") close(true); else open();
    });
    menu.addEventListener("click", function (e) {
      if (e.target.closest("a")) close(false);
    });
    document.addEventListener("keydown", function (e) {
      if (toggle.getAttribute("aria-expanded") !== "true") return;
      if (e.key === "Escape") { close(true); return; }
      if (e.key === "Tab") {
        // trampa de foco: el toggle (cerrar) + los links del menú
        var items = [toggle].concat(focusables());
        var i = items.indexOf(document.activeElement);
        if (e.shiftKey && (i <= 0)) { e.preventDefault(); items[items.length - 1].focus(); }
        else if (!e.shiftKey && i === items.length - 1) { e.preventDefault(); items[0].focus(); }
      }
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth >= 960 && toggle.getAttribute("aria-expanded") === "true") close(false);
    });
  }

  /* ---------- Revelado al hacer scroll (threshold bajo + red de seguridad) ---------- */
  function initReveals() {
    var els = $$("[data-reveal]");
    if (!els.length) return;
    if (!("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("is-revealed"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-revealed");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.01, rootMargin: "0px 0px -2% 0px" });
    els.forEach(function (el) { io.observe(el); });

    setTimeout(function () {
      $$("[data-reveal]:not(.is-revealed)").forEach(function (el) {
        if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add("is-revealed");
      });
    }, 6000);
  }

  /* ---------- Formulario "Quiero vender Pick Meals" ---------- */

  // Único punto de envío. endpoint vacío = WhatsApp (modo local). Con endpoint = POST JSON,
  // y si el servidor falla se cae a WhatsApp: nunca una UI muerta.
  function sendLead(data) {
    var endpoint = (BRAND.leads && BRAND.leads.endpoint) || "";
    if (!endpoint || !window.fetch) return Promise.resolve({ via: "whatsapp" });
    return fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (j) { return j && j.ok ? { via: "server" } : Promise.reject("not-ok"); })
      .catch(function (err) {
        console.warn("[lead] envío al servidor falló, se usa WhatsApp:", err);
        return { via: "whatsapp", fallback: true };
      });
  }

  var TIPO_LABEL = {
    almacen: "Almacén", autoservicio: "Autoservicio", mercado: "Mercado",
    dietetica: "Dietética", kiosco: "Kiosco", otro: "Otro"
  };

  function buildMessage(d) {
    var lines = [
      "Hola PICK MEALS, quiero vender Pick Meals en mi comercio.",
      "",
      "*Nombre:* " + d.nombre,
      "*Comercio:* " + d.comercio,
      "*Tipo de comercio:* " + (TIPO_LABEL[d.tipo] || d.tipo),
      "*Localidad:* " + d.localidad,
      "*Teléfono / WhatsApp:* " + d.telefono,
      "*Email:* " + d.email
    ];
    if (d.mensaje) lines.push("*Consulta:* " + d.mensaje);
    return lines.join("\n");
  }

  function mailtoUrl(d) {
    var to = CONTACT.email || "info@pickmeals.com.ar";
    var subject = "Quiero vender Pick Meals — " + d.comercio;
    return "mailto:" + to + "?subject=" + encodeURIComponent(subject) +
      "&body=" + encodeURIComponent(buildMessage(d).replace(/\*/g, ""));
  }

  var RULES = {
    nombre: function (v) { return v.trim().length >= 3 || "Ingresá tu nombre y apellido."; },
    comercio: function (v) { return v.trim().length >= 2 || "Ingresá el nombre de tu comercio."; },
    tipo: function (v) { return v !== "" || "Elegí el tipo de comercio."; },
    localidad: function (v) { return v.trim().length >= 3 || "Indicá tu localidad y provincia."; },
    telefono: function (v) {
      var t = v.trim();
      return (/^[\d\s()+\-.]+$/.test(t) && t.replace(/\D/g, "").length >= 8) ||
        "Ingresá un teléfono o WhatsApp válido, con código de área.";
    },
    email: function (v) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()) || "Ingresá un email válido (ej.: nombre@tucomercio.com).";
    },
    consentimiento: function (v, el) { return el.checked || "Necesitamos tu conformidad para poder contactarte."; }
  };

  function initLeadForm() {
    var form = $("[data-lead-form]");
    if (!form) return;
    var status = $("[data-form-status]");
    var submit = $("[type=submit]", form);
    var success = $("[data-form-success]");
    var hint = $("[data-submit-hint]");
    if (hint && BRAND.leads && BRAND.leads.endpoint) hint.textContent = "Tus datos llegan directo al equipo de Pick Meals.";

    function fieldWrap(el) { return el.closest(".field"); }

    function validate(el) {
      var rule = RULES[el.name];
      if (!rule) return true;
      var result = rule(el.value || "", el);
      var wrap = fieldWrap(el);
      var err = wrap && $(".field-error", wrap);
      if (result === true) {
        el.removeAttribute("aria-invalid");
        if (wrap) wrap.classList.remove("is-invalid");
        if (err) err.textContent = "";
        return true;
      }
      el.setAttribute("aria-invalid", "true");
      if (wrap) wrap.classList.add("is-invalid");
      if (err) err.textContent = result;
      return false;
    }

    var fields = $$("input, select, textarea", form).filter(function (el) { return RULES[el.name]; });
    fields.forEach(function (el) {
      el.addEventListener("blur", function () {
        if (el.value || el.dataset.touched) { el.dataset.touched = "1"; validate(el); }
      });
      el.addEventListener(el.type === "checkbox" || el.tagName === "SELECT" ? "change" : "input", function () {
        if (el.getAttribute("aria-invalid") === "true" || el.type === "checkbox") validate(el);
      });
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var invalid = fields.filter(function (el) { el.dataset.touched = "1"; return !validate(el); });
      if (invalid.length) {
        status.textContent = invalid.length === 1
          ? "Revisá el campo marcado para poder enviar tu consulta."
          : "Revisá los " + invalid.length + " campos marcados para poder enviar tu consulta.";
        invalid[0].focus();
        return;
      }
      status.textContent = "";

      var hp = form.elements.website;
      var data = {
        nombre: form.elements.nombre.value.trim(),
        comercio: form.elements.comercio.value.trim(),
        tipo: form.elements.tipo.value,
        localidad: form.elements.localidad.value.trim(),
        telefono: form.elements.telefono.value.trim(),
        email: form.elements.email.value.trim(),
        mensaje: form.elements.mensaje.value.trim(),
        consentimiento: form.elements.consentimiento.checked,
        origen: "contacto"
      };
      if (hp && hp.value) { showSuccess(data, "server"); return; } // bot: se descarta en silencio

      var message = buildMessage(data);
      var endpoint = (BRAND.leads && BRAND.leads.endpoint) || "";

      if (!endpoint) {
        // Modo local: abrir WhatsApp dentro del mismo gesto del usuario (evita bloqueos de pop-up).
        window.open(waUrl(message), "_blank", "noopener");
        showSuccess(data, "whatsapp");
        return;
      }

      submit.classList.add("is-sending");
      submit.setAttribute("aria-disabled", "true");
      sendLead(data).then(function (res) {
        submit.classList.remove("is-sending");
        submit.removeAttribute("aria-disabled");
        showSuccess(data, res.via, res.fallback);
      });
    });

    function showSuccess(data, via, fallback) {
      var title = $("[data-success-title]", success);
      var text = $("[data-success-text]", success);
      var wa = $("[data-success-wa]", success);
      var mail = $("[data-success-mail]", success);
      var first = data.nombre.split(" ")[0];
      title.textContent = "¡Gracias, " + first + "!";
      if (via === "server") {
        text.textContent = "Recibimos los datos de " + data.comercio + ". El equipo de Pick Meals se va a comunicar con vos para contarte sobre productos y condiciones comerciales.";
        wa.hidden = true;
      } else {
        text.textContent = fallback
          ? "No pudimos enviar tus datos automáticamente. Tocá el botón y mandalos por WhatsApp con el mensaje ya armado, o envialos por email."
          : "Abrimos WhatsApp con tu mensaje listo para enviar. Si no se abrió, tocá el botón. También podés mandarlo por email.";
        wa.hidden = false;
        wa.setAttribute("href", waUrl(buildMessage(data)));
      }
      mail.setAttribute("href", mailtoUrl(data));
      form.hidden = true;
      success.hidden = false;
      title.focus();
    }

    var reset = $("[data-success-reset]", success);
    if (reset) {
      reset.addEventListener("click", function () {
        form.reset();
        fields.forEach(function (el) { delete el.dataset.touched; });
        success.hidden = true;
        form.hidden = false;
        form.elements.nombre.focus();
      });
    }
  }

  /* ---------- Precarga "Me interesa: <producto>" desde el catálogo ---------- */
  function initPrefill() {
    var form = $("[data-lead-form]");
    if (!form || !window.URLSearchParams) return;
    var producto = new URLSearchParams(location.search).get("producto");
    if (!producto) return;
    producto = producto.replace(/[^\wÁÉÍÓÚÜÑáéíóúüñ .,\-()]/g, "").slice(0, 80).trim();
    if (producto && !form.elements.mensaje.value) form.elements.mensaje.value = "Me interesa: " + producto + ".";
  }

  /* ---------- Boot ---------- */
  function boot() {
    safe(initYear, "initYear");
    safe(initWhatsAppLinks, "initWhatsAppLinks");
    safe(initPhone, "initPhone");
    safe(initHeader, "initHeader");
    safe(initMobileMenu, "initMobileMenu");
    safe(initReveals, "initReveals");
    safe(initPrefill, "initPrefill");
    safe(initLeadForm, "initLeadForm");
    document.documentElement.classList.add("is-ready");
    if (reduced) document.documentElement.classList.add("reduced-motion");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
