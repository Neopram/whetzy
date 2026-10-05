/** Pantallas de una sola tarea: ocultan la barra inferior y el swipe global de
 *  App.tsx no navega en ellas, así que la única salida es la que la propia
 *  pantalla decide ofrecer (p. ej. el diálogo de confirmación de QuizScreen).
 *  Un conjunto en vez de una cadena de `!==` porque añadir una pantalla es una
 *  entrada, no una cláusula más que nadie recuerda extender — 'trackexam' fue
 *  la quinta y la cadena ya iba por cuatro. 'duels' faltaba (0.9): un duelo
 *  en vivo es tan "una tarea, una salida" como un examen, pero ni la barra
 *  inferior ni el swipe lo trataban así — un toque o un gesto de sobra salía
 *  del duelo sin avisar. */
export const IMMERSIVE_SCREENS = new Set([
  'quiz',
  'placement',
  'mockexam',
  'trackexam',
  'lesson',
  'readiness',
  'playground',
  'projects',
  'duels',
]);

export function isImmersiveScreen(screen: string): boolean {
  return IMMERSIVE_SCREENS.has(screen);
}

/** A dónde lleva un swipe global (App.tsx), o null si no debe navegar —
 * porque ya está ahí, o porque la pantalla es inmersiva y solo su propia UI
 * decide cómo se sale de ella (0.9: antes el swipe no miraba esto y saltaba
 * a casa por detrás del diálogo de confirmación de QuizScreen). */
export function navigationTargetForSwipe(
  direction: 'left' | 'right',
  currentScreen: string
): 'home' | 'marketplace' | null {
  if (isImmersiveScreen(currentScreen)) return null;
  if (direction === 'right') return currentScreen === 'home' ? null : 'home';
  return currentScreen === 'marketplace' ? null : 'marketplace';
}
