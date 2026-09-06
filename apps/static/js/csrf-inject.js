/**
 * csrf-inject.js — SASPanel
 * Automatically injects the Flask-WTF CSRF token into every POST form
 * on the page. The token is read from <meta name="csrf-token"> which is
 * rendered by the header layout templates.
 *
 * This is the preferred pattern for apps that use non-WTForms HTML forms
 * alongside Flask-WTF's global CSRF protection (CSRFProtect).
 */
(function () {
  'use strict';

  function injectCsrf() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (!meta) return; // CSRF meta tag not present (should not happen)

    var token = meta.getAttribute('content');
    if (!token) return;

    var forms = document.querySelectorAll('form[method="post"], form[method="POST"]');
    forms.forEach(function (form) {
      // Skip if token already present (e.g. WTForms-rendered form)
      if (form.querySelector('input[name="csrf_token"]')) return;

      var input = document.createElement('input');
      input.type  = 'hidden';
      input.name  = 'csrf_token';
      input.value = token;
      form.prepend(input);
    });
  }

  // Run on DOMContentLoaded (covers all static forms)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectCsrf);
  } else {
    injectCsrf(); // already loaded
  }

  // Also observe for dynamically added forms (e.g. modal dialogs)
  if (window.MutationObserver) {
    var observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (m) {
        m.addedNodes.forEach(function (node) {
          if (node.nodeType !== 1) return;
          var forms = node.tagName === 'FORM'
            ? [node]
            : Array.from(node.querySelectorAll('form[method="post"], form[method="POST"]'));
          forms.forEach(function (form) {
            if (!form.querySelector('input[name="csrf_token"]')) {
              var meta  = document.querySelector('meta[name="csrf-token"]');
              var input = document.createElement('input');
              input.type  = 'hidden';
              input.name  = 'csrf_token';
              input.value = meta ? meta.getAttribute('content') : '';
              form.prepend(input);
            }
          });
        });
      });
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }
})();
