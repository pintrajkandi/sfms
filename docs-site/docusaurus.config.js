// @ts-check
// Docusaurus config for the YukiCares docs. Served at https://yukicares.cloud/docs/.

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "YukiCares Docs",
  tagline: "User guide for YukiCares — the all-in-one school finance platform.",
  favicon: "img/favicon.svg",

  url: "https://yukicares.cloud",
  baseUrl: "/docs/",

  organizationName: "yukicares",
  projectName: "yukicares-docs",

  // Absolute Mintlify-style links (/settings/overview) get baseUrl applied via
  // <Link>; keep the build resilient rather than failing on a stray link.
  onBrokenLinks: "warn",
  onBrokenMarkdownLinks: "warn",

  i18n: { defaultLocale: "en", locales: ["en"] },

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          // Docs are the whole site (no /docs/docs); baseUrl already adds /docs/.
          routeBasePath: "/",
          sidebarPath: require.resolve("./sidebars.js"),
        },
        blog: false,
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: { respectPrefersColorScheme: true },
      navbar: {
        title: "YukiCares Docs",
        items: [
          {
            href: "https://yukicares.cloud",
            label: "Open App",
            position: "right",
          },
        ],
      },
      footer: {
        style: "dark",
        links: [
          {
            title: "Product",
            items: [
              { label: "Website", href: "https://yukicares.cloud" },
              { label: "Sign in", href: "https://yukicares.cloud/login" },
            ],
          },
          {
            title: "Help",
            items: [{ label: "support@yukicares.cloud", href: "mailto:support@yukicares.cloud" }],
          },
        ],
        copyright: `© ${new Date().getFullYear()} YukiCares. All rights reserved.`,
      },
    }),
};

module.exports = config;
