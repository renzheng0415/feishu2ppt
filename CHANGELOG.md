# Changelog

## 1.0.0

- Enforce a two-command `plan` then `render` approval flow.
- Preserve mixed text, multiple tables and media without silent loss.
- Key media caches by Feishu token or source identity.
- Accept current Lark DocxXML media tokens exposed through the `src` attribute.
- Keep multiple URL-only media assets distinct during document-to-plan mapping.
- Preserve prompt-template examples containing `XX` or “请根据” without disabling the real placeholder gate.
- Reuse the same placeholder policy for plan validation and final PPT publishing.
- Detect downloaded media by magic bytes and repair incorrect image/video suffixes before OfficeCLI rendering.
- Paginate long prose by character budget, bound gallery leads to one line and generate video posters with ffmpeg when available.
- Allocate content pages and text boxes by estimated line count to prevent unequal bullet lengths from colliding.
- Use a conservative eight-line page budget and 18pt body text for dense Chinese source documents.
- Reject non-HTTPS, local, private, link-local and reserved media endpoints.
- Split long tables into 12-row pages with repeated headers.
- Validate all 20 layout schemas before rendering.
- Reject missing media, placeholders, unknown themes/layouts/charts and non-finite chart data.
- Validate candidate PPTX files before atomically replacing final output.
- Add stale-runtime upgrade backups, a 20-layout live gallery and malformed-plan regression coverage.

## 0.2.2

- Move all quality checks before final-file replacement.
- Reject missing media and invalid chart values.

## 0.2.1

- Preserve mixed document content, define theme precedence and validate chart styles.
- Repair stale runtime links and make PPTX creation recoverable.

## 0.2.0

- Add the explicit plan gate, README, examples, showcase, installers and automated tests.
