import { marked } from 'marked';
import DOMPurify from 'dompurify';

// Configure marked options
marked.setOptions({
  gfm: true,
  breaks: true,
});

export function renderMarkdownSafe(markdownText: string): string {
  if (!markdownText) return '';
  try {
    const rawHtml = marked.parse(markdownText) as string;
    // Sanitize with DOMPurify
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
      ALLOWED_TAGS: [
        'p', 'br', 'b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li',
        'code', 'pre', 'blockquote', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'table', 'thead', 'tbody', 'tr', 'th', 'td', 'span'
      ],
      ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'style'],
    });

    // Add target="_blank" rel="noopener noreferrer" to links
    return cleanHtml.replace(/<a\s+(?:[^>]*?\s+)?href="([^"]*)"/g, '<a href="$1" target="_blank" rel="noopener noreferrer"');
  } catch (err) {
    console.error('Markdown parse error:', err);
    return DOMPurify.sanitize(markdownText);
  }
}
