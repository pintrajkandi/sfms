import { push } from "@/api/resources";

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const b64 = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(b64);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

export function pushSupported(): boolean {
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

/** Request permission + subscribe this browser; returns true on success. */
export async function enablePush(): Promise<{ ok: boolean; reason?: string }> {
  if (!pushSupported()) return { ok: false, reason: "This browser doesn't support push notifications." };
  const { public_key, enabled } = await push.vapidKey();
  if (!enabled || !public_key) return { ok: false, reason: "Push is not configured on the server." };

  const permission = await Notification.requestPermission();
  if (permission !== "granted") return { ok: false, reason: "Notification permission was denied." };

  const reg = await navigator.serviceWorker.ready;
  const existing = await reg.pushManager.getSubscription();
  const sub =
    existing ??
    (await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(public_key) as BufferSource,
    }));
  await push.subscribe(sub.toJSON());
  return { ok: true };
}

export async function disablePush(): Promise<void> {
  if (!pushSupported()) return;
  const reg = await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.getSubscription();
  if (sub) {
    await push.unsubscribe(sub.endpoint);
    await sub.unsubscribe();
  }
}

export async function sendTestPush(): Promise<void> {
  await push.test();
}
