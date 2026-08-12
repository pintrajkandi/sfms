import { useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { log } from "@/lib/logger";
import { TidioChat } from "@/components/TidioChat";

/**
 * Prints a full activity trail to the console:
 *   - every route the user lands on ("where I am")
 *   - every button / link click, with its label ("where I clicked")
 * API calls are logged separately in api/client.ts ("which API is calling").
 * Wraps the whole route tree so it covers auth screens and the app alike.
 */
export function ActivityLogger() {
  const location = useLocation();

  // Route changes.
  useEffect(() => {
    log.info(`PAGE ${location.pathname}${location.search}`, { action: "navigate" });
  }, [location.pathname, location.search]);

  // Global click trail — logs the nearest actionable element + its label.
  useEffect(() => {
    function onClick(e: MouseEvent) {
      const el = (e.target as HTMLElement)?.closest(
        "button, a, [role='button'], input[type='checkbox'], input[type='radio']",
      ) as HTMLElement | null;
      if (!el) return;

      const label =
        el.getAttribute("aria-label") ||
        el.textContent?.trim().slice(0, 40) ||
        (el as HTMLAnchorElement).getAttribute?.("href") ||
        el.tagName.toLowerCase();
      const tag = el.tagName.toLowerCase();
      log.info(`CLICK ${tag} "${label}"`, { action: "click" });
    }
    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, []);

  return (
    <>
      <Outlet />
      <TidioChat />
    </>
  );
}
