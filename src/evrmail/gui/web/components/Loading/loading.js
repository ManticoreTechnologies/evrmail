import { loadTemplate } from '../../utils.js';

export async function initLoadingView() {
  await loadTemplate('components/Loading/loading.html', 'loading-view');
} 