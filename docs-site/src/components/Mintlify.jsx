import React from "react";
import Link from "@docusaurus/Link";
import Admonition from "@theme/Admonition";

/**
 * Drop-in replacements for the Mintlify MDX components used in the docs, so the
 * original .mdx pages render in Docusaurus without per-file rewrites. Registered
 * globally in src/theme/MDXComponents.js.
 */

export function CardGroup({ cols = 2, children }) {
  return (
    <div
      className="mint-card-group"
      style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
    >
      {children}
    </div>
  );
}

export function Card({ title, href, children }) {
  const inner = (
    <div className="mint-card">
      {title && <div className="mint-card-title">{title}</div>}
      {children && <div className="mint-card-body">{children}</div>}
    </div>
  );
  return href ? (
    <Link to={href} className="mint-card-link">
      {inner}
    </Link>
  ) : (
    inner
  );
}

export function Steps({ children }) {
  return <div className="mint-steps">{children}</div>;
}

export function Step({ title, children }) {
  return (
    <div className="mint-step">
      {title && <div className="mint-step-title">{title}</div>}
      <div className="mint-step-body">{children}</div>
    </div>
  );
}

export function AccordionGroup({ children }) {
  return <div className="mint-accordions">{children}</div>;
}

export function Accordion({ title, children }) {
  return (
    <details className="mint-accordion">
      <summary>{title}</summary>
      <div className="mint-accordion-body">{children}</div>
    </details>
  );
}

// Callouts map onto Docusaurus admonitions.
export const Note = ({ children }) => <Admonition type="note">{children}</Admonition>;
export const Tip = ({ children }) => <Admonition type="tip">{children}</Admonition>;
export const Info = ({ children }) => <Admonition type="info">{children}</Admonition>;
export const Warning = ({ children }) => <Admonition type="warning">{children}</Admonition>;
export const Check = ({ children }) => <Admonition type="tip">{children}</Admonition>;
