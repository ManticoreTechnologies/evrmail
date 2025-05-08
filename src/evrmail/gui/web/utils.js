// Utility for loading HTML templates into containers
export async function loadTemplate(path, containerId) {
  const res = await fetch(path);
  const html = await res.text();
  // Extract only the content inside <body>...</body> if present
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*)<\/body>/i);
  const content = bodyMatch ? bodyMatch[1] : html;
  document.getElementById(containerId).innerHTML = content;
} 