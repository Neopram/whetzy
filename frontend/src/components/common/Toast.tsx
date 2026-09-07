import { useState, useEffect, useCallback } from 'react';
import styles from './Toast.module.css';

type ToastType = 'success' | 'error' | 'info';
interface ToastData { message: string; type: ToastType; }

const listeners: Set<(t: ToastData) => void> = new Set();

export function showToast(message: string, type: ToastType = 'success') {
  listeners.forEach((fn) => fn({ message, type }));
}

export function Toast() {
  const [visible, setVisible] = useState(false);
  const [data, setData] = useState<ToastData>({ message: '', type: 'success' });

  const handleToast = useCallback((t: ToastData) => {
    setData(t);
    setVisible(true);
    setTimeout(() => setVisible(false), 2200);
  }, []);

  useEffect(() => {
    listeners.add(handleToast);
    return () => { listeners.delete(handleToast); };
  }, [handleToast]);

  return (
    <div
      className={`${styles.toast} ${visible ? styles.show : ''} ${styles[data.type]}`}
      role="status"
      aria-live="polite"
    >
      {data.type === 'success' && '✅ '}
      {data.type === 'error' && '❌ '}
      {data.message}
    </div>
  );
}
