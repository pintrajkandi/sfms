/**
 * Money formatting — NEVER do financial math with the JS `number` type.
 * Amounts arrive from the API as decimal strings; format them, don't compute on them.
 * For arithmetic use a decimal lib (e.g. dinero.js) on minor units (CLAUDE.md §1/§6).
 */
export function formatMoney(amount: string | number, currency = "USD", locale = "en-US"): string {
  const value = typeof amount === "string" ? amount : amount.toString();
  const numeric = Number.parseFloat(value); // display-only conversion
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
  }).format(numeric);
}

export function toMinorUnits(amount: string): bigint {
  const [whole, frac = ""] = amount.split(".");
  const cents = (frac + "00").slice(0, 2);
  return BigInt(whole) * 100n + BigInt(cents) * (whole.startsWith("-") ? -1n : 1n);
}
