import { useEffect } from "react";

/**
 * Tidio live-chat widget loader.
 *
 * Env-gated like every other integration (Razorpay, Auth0, Sentry): the widget
 * only loads when `VITE_TIDIO_KEY` is set, so dev/CI stay clean and no key is
 * hardcoded. Set the key to your Tidio project's public id (the `xxxx` in the
 * `//code.tidio.co/xxxx.js` embed snippet from your Tidio dashboard).
 *
 * The script is injected once and guarded against double-insertion (React strict
 * mode double-invokes effects). Mounted app-wide via ActivityLogger.
 */
const TIDIO_KEY = import.meta.env.VITE_TIDIO_KEY as string | undefined;
const SCRIPT_ID = "tidio-chat-script";

export function TidioChat() {
  useEffect(() => {
    if (!TIDIO_KEY) return;
    if (document.getElementById(SCRIPT_ID)) return;

    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = `//code.tidio.co/${TIDIO_KEY}.js`;
    script.async = true;
    document.body.appendChild(script);
  }, []);

  return null;
}
