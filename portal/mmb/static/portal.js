const csrf = document.querySelector('meta[name="csrf-token"]').content;
const calendar = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' });
for (const stamp of document.querySelectorAll('time[datetime]')) {
  stamp.textContent = calendar.format(new Date(stamp.dateTime));
}

function dataFor(form) {
  const data = Object.fromEntries(new FormData(form));
  for (const control of form.elements) {
    if (!control.name) continue;
    if (control.type === 'checkbox') data[control.name] = control.checked;
    if (control.type === 'number') data[control.name] = Number(control.value);
    if (control.hasAttribute('data-json')) data[control.name] = JSON.parse(control.value);
  }
  if (form.dataset.revision) data.revision = Number(form.dataset.revision);
  if (form.dataset.version) data.version = Number(form.dataset.version);
  const criteria = [...form.querySelectorAll('[data-assessment]')];
  if (criteria.length) {
    data.assessment = Object.fromEntries(criteria.map(input => [input.dataset.assessment, input.value]));
  }
  return data;
}
for (const form of document.querySelectorAll('form.command, form.multipart')) {
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const output = form.querySelector('output');
    const submitter = event.submitter;
    const multipart = form.classList.contains('multipart');
    output.replaceChildren('正在保存…');
    output.classList.remove('error');
    try {
      const response = await fetch(submitter?.getAttribute('formaction') || form.action, {
        method: 'POST',
        headers: { 'X-CSRF-Token': csrf, ...(multipart ? {} : { 'Content-Type': 'application/json' }) },
        body: multipart ? new FormData(form) : JSON.stringify(dataFor(form))
      });
      if (!response.headers.get('Content-Type')?.includes('application/json')) {
        throw new Error('提交失败，请检查登录状态和文件大小。');
      }
      const data = await response.json();
      if (!response.ok) throw new Error(data.message_zh || data.error || data.results?.map(item => item.message_zh || item.error).join(' · ') || '提交失败。');
      if (data.results) {
        const failures = data.results.filter(item => item.error);
        if (!failures.length) location.assign('/');
        else output.textContent = data.results.map(item => item.task || item.filename + ' · ' + (item.message_zh || item.error)).join(' | ');
      } else {
        location.reload();
      }
    } catch (error) {
      output.textContent = error instanceof SyntaxError ? '请检查输入的 JSON 格式。' : error.message;
      output.classList.add('error');
    }
  });
}
