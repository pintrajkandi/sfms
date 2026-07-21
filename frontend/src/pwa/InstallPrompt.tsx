import { useEffect, useState } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

/**
 * Small dismissible "Install app" banner. Renders nothing until the browser
 * fires `beforeinstallprompt` (i.e. the app is installable and not yet installed).
 */
export function InstallPrompt() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    const onPrompt = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
    };
    const onInstalled = () => setDeferred(null);
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  if (!deferred || hidden) return null;

  return (
    <div className="fixed inset-x-3 bottom-3 z-50 mx-auto flex max-w-md items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-lg print:hidden">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-gradient font-bold text-white">₹</div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-slate-800">Install Fee Ledger</p>
        <p className="truncate text-xs text-slate-500">Add to your home screen for quick, app-like access.</p>
      </div>
      <button
        onClick={async () => {
          await deferred.prompt();
          await deferred.userChoice;
          setDeferred(null);
        }}
        className="rounded-lg bg-brand-gradient px-3 py-1.5 text-xs font-semibold text-white hover:opacity-95"
      >
        Install
      </button>
      <button onClick={() => setHidden(true)} aria-label="Dismiss" className="text-slate-400 hover:text-slate-600">
        ✕
      </button>
    </div>
  );
}
