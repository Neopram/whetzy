import { useEffect, useRef } from 'react';

interface GestureCallbacks {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
}

const SWIPE_THRESHOLD = 50;
const SWIPE_TIME_THRESHOLD = 300;

export function useGestures(callbacks: GestureCallbacks) {
  // App.tsx pasa un objeto `{ onSwipeLeft: () => ..., ... }` literal, nuevo en
  // cada render. Si el efecto dependiera de esa referencia (como antes),
  // cualquier re-render de App entre el touchstart y el touchend quita los
  // listeners viejos y pone unos nuevos con touchStartX/Y/Time reiniciados a
  // 0 -- el touchend siguiente calcula el swipe contra ese cero, no contra el
  // dedo real. El ref evita que la identidad de `callbacks` dispare un
  // re-registro: los listeners se montan una vez y leen siempre la última
  // versión de `callbacks` cuando disparan.
  const callbacksRef = useRef(callbacks);
  callbacksRef.current = callbacks;

  useEffect(() => {
    let touchStartX = 0;
    let touchStartY = 0;
    let touchStartTime = 0;

    const handleTouchStart = (e: TouchEvent) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
      touchStartTime = Date.now();
    };

    const handleTouchEnd = (e: TouchEvent) => {
      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;
      const touchDuration = Date.now() - touchStartTime;

      if (touchDuration > SWIPE_TIME_THRESHOLD) return;

      const diffX = touchStartX - touchEndX;
      const diffY = touchStartY - touchEndY;
      const callbacks = callbacksRef.current;

      if (Math.abs(diffX) > Math.abs(diffY)) {
        if (diffX > SWIPE_THRESHOLD) {
          callbacks.onSwipeLeft?.();
        } else if (diffX < -SWIPE_THRESHOLD) {
          callbacks.onSwipeRight?.();
        }
      } else {
        if (diffY > SWIPE_THRESHOLD) {
          callbacks.onSwipeUp?.();
        } else if (diffY < -SWIPE_THRESHOLD) {
          callbacks.onSwipeDown?.();
        }
      }
    };

    document.addEventListener('touchstart', handleTouchStart);
    document.addEventListener('touchend', handleTouchEnd);

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, []);
}
