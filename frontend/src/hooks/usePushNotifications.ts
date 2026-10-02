/**
 * Web Push subscription management (3.3).
 *
 * Registers the current user for Web Push via VAPID.  The hook:
 *   1. Fetches the VAPID public key from the backend.
 *   2. Calls Notification.requestPermission() if not yet granted.
 *   3. Subscribes via PushManager and POSTs the subscription to /push/subscribe.
 *   4. On unsubscribe, calls DELETE /push/subscribe and removes the local sub.
 *
 * Usage:
 *   const { supported, permission, subscribe, unsubscribe } = usePushNotifications();
 */

import { useCallback, useEffect, useState } from 'react';
import { API_BASE_URL } from '../services/api';

const API_BASE = `${API_BASE_URL}/push`;

async function fetchVapidKey(): Promise<string | null> {
  try {
    const r = await fetch(`${API_BASE}/vapid-key`);
    if (!r.ok) return null;
    const { vapid_public_key } = await r.json();
    return vapid_public_key as string;
  } catch {
    return null;
  }
}

// `<ArrayBuffer>` explícito: desde TypeScript 7 un `Uint8Array` a secas puede ir sobre
// SharedArrayBuffer y `applicationServerKey` lo rechaza (tsc -b rompía el build, 2026-10-02).
function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
}

async function postSubscription(sub: PushSubscription): Promise<void> {
  const { endpoint, keys } = sub.toJSON() as {
    endpoint: string;
    keys: { p256dh: string; auth: string };
  };
  await fetch(`${API_BASE}/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ endpoint, keys }),
  });
}

async function deleteSubscription(endpoint: string): Promise<void> {
  await fetch(`${API_BASE}/subscribe`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ endpoint }),
  });
}

export interface PushState {
  supported: boolean;
  permission: NotificationPermission | 'unsupported';
  subscribed: boolean;
  subscribe: () => Promise<boolean>;
  unsubscribe: () => Promise<void>;
}

export function usePushNotifications(): PushState {
  const supported =
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window;

  const [permission, setPermission] = useState<NotificationPermission | 'unsupported'>(
    supported ? Notification.permission : 'unsupported',
  );
  const [subscribed, setSubscribed] = useState(false);

  useEffect(() => {
    if (!supported) return;
    navigator.serviceWorker.ready
      .then((reg) => reg.pushManager.getSubscription())
      .then((sub) => setSubscribed(sub !== null))
      .catch(() => undefined);
  }, [supported]);

  const subscribe = useCallback(async (): Promise<boolean> => {
    if (!supported) return false;
    const vapidKey = await fetchVapidKey();
    if (!vapidKey) return false;

    let perm = Notification.permission;
    if (perm === 'default') {
      perm = await Notification.requestPermission();
      setPermission(perm);
    }
    if (perm !== 'granted') return false;

    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey),
      });
      await postSubscription(sub);
      setSubscribed(true);
      return true;
    } catch {
      return false;
    }
  }, [supported]);

  const unsubscribe = useCallback(async (): Promise<void> => {
    if (!supported) return;
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (!sub) return;
      await deleteSubscription(sub.endpoint);
      await sub.unsubscribe();
      setSubscribed(false);
    } catch {
      /* ignore */
    }
  }, [supported]);

  return { supported, permission, subscribed, subscribe, unsubscribe };
}
