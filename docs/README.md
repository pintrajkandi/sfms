# YukiCares Documentation (Mintlify)

User-facing documentation for YukiCares, built with [Mintlify](https://mintlify.com).

## Structure

- `docs.json` — site config: name, colours, and the navigation/sidebar.
- `*.mdx` — one file per documentation page (grouped in folders that mirror the sidebar).
- `favicon.svg` — browser-tab icon.

## Preview locally

Install the Mintlify CLI once, then run the dev server **from this `docs/` folder** (where `docs.json` lives):

```bash
npm i -g mint        # install the CLI (package name: "mint")
cd docs
mint dev             # serves at http://localhost:3000
```

If the CLI is out of date, update it with `mint update`.

## Publish

1. Create a project at [dashboard.mintlify.com](https://dashboard.mintlify.com) and connect this GitHub repository.
2. Set the **docs directory** to `docs` (so Mintlify finds `docs.json`).
3. Every push to your default branch auto-deploys. You'll get a URL like `https://<your-org>.mintlify.app`, and you can add a custom domain (e.g. `docs.yukicares.cloud`) in the dashboard.

## Editing tips

- Each page starts with frontmatter (`title`, `description`).
- Add a new page by creating an `.mdx` file and listing its path (without the `.mdx`) under the right `group` in `docs.json` → `navigation.groups`.
- Components used here (`<Steps>`, `<Card>`, `<CardGroup>`, `<Note>`, `<Tip>`, `<Warning>`, `<Info>`, `<Accordion>`, `<AccordionGroup>`) are built into Mintlify — no imports needed.

## Branding note

These docs use the name **YukiCares** (matching the marketing site). If the product is renamed, update the `name` in `docs.json` and search-replace "YukiCares" across the `.mdx` files.
