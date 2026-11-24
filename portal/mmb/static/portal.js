const csrf = document.querySelector('meta[name="csrf-token"]').content;

function dataFor(form) {
  const data = Object.fromEntries(new FormData(form));
  for (const control of form.elements) {
    if (!control.name) continue;
    if (control.type === 'checkbox') data[control.name] = control.checked;
    if (control.type === 'number') data[control.name] = Number(control.value);
    if (control.hasAttribute('data-json')) data[control.name] = JSON.parse(control.value);
  }
  if (form.dataset.revision) data.revision = Number(form.dataset.revision);
  const criteria = [...form.querySelectorAll('[data-criterion]')];
  if (criteria.length) {
    data.verdicts = Object.fromEntries(criteria.map(row => [
      row.dataset.criterion, Object.fromEntries([...row.querySelectorAll('[data-field]')].map(
        input => [input.dataset.field, input.value]
      ))
    ]));
  }
  return data;
}
const invite = document.querySelector('.invitation');
if (invite) {
  invite.elements.token.value = location.hash.slice(1);
  if (invite.elements.token.value) history.replaceState(null, '', location.pathname);
}
document.querySelector('#reload-invite')?.addEventListener('click', () => location.reload());

for (const form of document.querySelectorAll('form.command, form.multipart')) {
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const output = form.querySelector('output');
    const submitter = event.submitter;
    const multipart = form.classList.contains('multipart');
    output.replaceChildren('Saving…');
    output.classList.remove('error');
    try {
      const response = await fetch(submitter?.getAttribute('formaction') || form.action, {
        method: 'POST',
        headers: { 'X-CSRF-Token': csrf, ...(multipart ? {} : { 'Content-Type': 'application/json' }) },
        body: multipart ? new FormData(form) : JSON.stringify(dataFor(form))
      });
      if (!response.headers.get('Content-Type')?.includes('application/json')) {
        throw new Error('Request could not be completed. Check your session and upload size.');
      }
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || data.results?.map(item => item.error).join(' · ') || 'Request failed');
      if (data.token) {
        const invitation = new URL('/invite/' + location.pathname.split('/').at(-1), location.origin);
        invitation.hash = data.token;
        const link = document.createElement('input');
        link.value = invitation.href;
        link.readOnly = true;
        link.setAttribute('aria-label', 'Invitation link');
        const copy = document.createElement('button');
        copy.type = 'button';
        copy.textContent = 'Copy invitation link';
        copy.addEventListener('click', async () => {
          link.select();
          try { await navigator.clipboard.writeText(link.value); copy.textContent = 'Copied'; }
          catch { copy.textContent = 'Link selected'; }
        });
        output.replaceChildren(link, copy);
        const nextRevision = Number(form.dataset.revision) + 1;
        form.dataset.revision = String(nextRevision);
      } else if (data.results) {
        const failures = data.results.filter(item => item.error);
        if (!failures.length) location.assign('/');
        else output.textContent = data.results.map(item => item.task || item.filename + ' · ' + item.error).join(' | ');
      } else if (form.dataset.accepted) {
        location.assign(data.stage === 'BASELINE_IN_PROGRESS' ? form.dataset.accepted : '/');
      } else {
        location.reload();
      }
    } catch (error) {
      output.textContent = error.message;
      output.classList.add('error');
    }
  });
}
