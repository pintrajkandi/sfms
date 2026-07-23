import { useState } from "react";
import { disablePush, enablePush, pushSupported, sendTestPush } from "@/pwa/push";

export function PushToggle() {
  const [msg, setMsg] = useState("");
  const [tone, setTone] = useState<"ok" | "err" | "">("");
  const [busy, setBusy] = useState(false);
  const supported = pushSupported();

  const wrap = (fn: () => Promise<void>) => async () => {
    setBusy(true);
    setMsg("");
    try {
      await fn();
    } catch {
      setTone("err");
      setMsg("Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="sm:col-span-2 rounded-lg border border-slate-200 px-4 py-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-800">Browser push notifications</p>
          <p className="text-xs text-slate-500">Get alerts on this device even when the app is closed.</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={!supported || busy}
            onClick={wrap(async () => {
              const r = await enablePush();
              setTone(r.ok ? "ok" : "err");
              setMsg(r.ok ? "Push notifications enabled on this device." : r.reason ?? "Could not enable.");
            })}
            className="rounded-lg bg-brand-gradient px-3 py-1.5 text-xs font-semibold text-white hover:opacity-95 disabled:opacity-50"
          >
            Enable
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={wrap(async () => { await sendTestPush(); setTone("ok"); setMsg("Test notification sent."); })}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          >
            Send test
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={wrap(async () => { await disablePush(); setTone("ok"); setMsg("Push disabled on this device."); })}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          >
            Disable
          </button>
        </div>
      </div>
      {!supported && <p className="mt-2 text-xs text-amber-600">This browser doesn't support push notifications.</p>}
      {msg && <p className={`mt-2 text-xs ${tone === "ok" ? "text-emerald-600" : "text-rose-600"}`}>{msg}</p>}
    </div>
  );
}
