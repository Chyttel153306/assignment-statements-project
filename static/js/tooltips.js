/* Lightweight help shared by static controls, dynamic results, and SVG nodes. */
(() => {
  'use strict';
  const tooltip = document.createElement('div');
  tooltip.id = 'ui-tooltip';
  tooltip.className = 'ui-tooltip';
  tooltip.setAttribute('role', 'tooltip');
  tooltip.hidden = true;
  document.body.append(tooltip);

  const hints = {
    '#reset-trace': 'Return to the start of the trace without deleting the checked statement.',
    '#highlight-step': 'Scroll to and focus the selected transition in the trace table.',
    '#lab-search': 'Find a test by its statement or the mistake it checks.',
    '#lab-filter': 'Filter by expected validity or by the result of a test run.',
    '[data-example="valid"]': 'Fill the input with a predefined valid statement.',
    '[data-example="invalid"]': 'Fill the input with a predefined invalid statement.',
    '[data-move="-1"]': 'Move to the previous transition in the validation trace.',
    '[data-move="1"]': 'Move to the next transition. The diagram updates with it.',
    '#retry-connection': 'Try connecting to the Flask server on your computer again.'
  };
  Object.entries(hints).forEach(([selector, text]) => {
    document.querySelectorAll(selector).forEach(item => item.dataset.tooltip = text);
  });
  document.querySelectorAll('.nav-item').forEach(row => {
    row.querySelector('a').dataset.tooltip = row.querySelector('.help-tip').dataset.tooltip;
  });

  let active = null;
  let pinned = false;
  let hideTimer;

  function close() {
    clearTimeout(hideTimer);
    if (active) {
      const described = (active.getAttribute('aria-describedby') || '').split(/\s+/).filter(id => id && id !== tooltip.id);
      if (described.length) active.setAttribute('aria-describedby', described.join(' '));
      else active.removeAttribute('aria-describedby');
      if (active.matches('.help-tip, [data-tooltip-tap]')) active.setAttribute('aria-expanded', 'false');
    }
    tooltip.hidden = true;
    active = null;
    pinned = false;
  }

  function position() {
    if (!active || tooltip.hidden) return;
    if (!active.isConnected || !active.getClientRects().length) { close(); return; }
    const margin = 12, gap = 12;
    const viewport = window.visualViewport;
    const width = viewport?.width || window.innerWidth;
    const height = viewport?.height || window.innerHeight;
    const offsetX = viewport?.offsetLeft || 0, offsetY = viewport?.offsetTop || 0;
    tooltip.style.maxWidth = `${Math.max(1, Math.min(320, width - margin * 2))}px`;
    tooltip.style.maxHeight = `${Math.max(1, height - margin * 2)}px`;
    const target = active.getBoundingClientRect();
    const box = tooltip.getBoundingClientRect();
    let left = target.left + (target.width - box.width) / 2;
    let top = target.top - box.height - gap;
    // A sidebar hint is placed beside the rail when there is enough room.
    if (active.closest('.sidebar') && target.right + gap + box.width < offsetX + width - margin) {
      left = target.right + gap;
      top = target.top + (target.height - box.height) / 2;
    } else if (top < offsetY + margin) {
      top = target.bottom + gap;
    }
    left = Math.max(offsetX + margin, Math.min(left, offsetX + width - box.width - margin));
    top = Math.max(offsetY + margin, Math.min(top, offsetY + height - box.height - margin));
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  }

  function show(trigger, pin = false) {
    clearTimeout(hideTimer);
    if (!trigger.dataset.tooltip) return;
    if (active !== trigger) { close(); active = trigger; }
    pinned = pin;
    tooltip.textContent = trigger.dataset.tooltip;
    tooltip.hidden = false;
    const described = new Set((trigger.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean));
    described.add(tooltip.id);
    trigger.setAttribute('aria-describedby', [...described].join(' '));
    if (trigger.matches('.help-tip, [data-tooltip-tap]')) {
      trigger.setAttribute('aria-controls', tooltip.id);
      trigger.setAttribute('aria-expanded', 'true');
    }
    position();
  }

  function scheduleClose() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      if (!pinned && !tooltip.matches(':hover') && active && document.activeElement !== active) close();
    }, 180);
  }
  document.addEventListener('pointerover', event => {
    if (event.pointerType === 'touch') return;
    const trigger = event.target.closest('[data-tooltip]');
    if (trigger && (!pinned || trigger === active)) show(trigger, pinned);
    if (tooltip.contains(event.target)) clearTimeout(hideTimer);
  });
  document.addEventListener('pointerout', event => {
    if (!active || event.pointerType === 'touch') return;
    if (active.contains(event.relatedTarget) || tooltip.contains(event.relatedTarget)) return;
    scheduleClose();
  });
  document.addEventListener('focusin', event => {
    const trigger = event.target.closest('[data-tooltip]');
    if (trigger) show(trigger);
    else if (!tooltip.contains(event.target)) close();
  });
  document.addEventListener('focusout', scheduleClose);
  document.addEventListener('click', event => {
    const trigger = event.target.closest('.help-tip, [data-tooltip-tap]');
    if (trigger) {
      if (active === trigger && pinned) close();
      else show(trigger, true);
    } else if (!tooltip.contains(event.target)) close();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') close();
    const trigger = event.target.closest('[data-tooltip-tap]');
    if (trigger && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      if (active === trigger && pinned) close(); else show(trigger, true);
    }
  });
  window.addEventListener('resize', position);
  document.addEventListener('scroll', event => {
    if (!tooltip.contains(event.target)) close();
  }, true);
  window.addEventListener('hashchange', close);
  window.visualViewport?.addEventListener('resize', position);
  window.DFAHelp = { close };
})();
