/**
 * Pregunta `interactive` (40.1): carga el widget por nombre, guarda su estado,
 * lo envía serializado y, cuando llega la respuesta, vuelve a corregir con el
 * mismo checker que el servidor. Si los dos veredictos no coinciden lo dice en
 * consola y en `data-checker-mismatch`: el test de casos compartidos debería
 * haberlo impedido, así que es un fallo nuestro, nunca del alumno.
 */
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { InteractivePublic, QuizAnswerResponse } from '../../services/api';
import { check, type Json } from '../../widgets/checkers';
import { loadWidget, type WidgetDefinition } from '../../widgets/registry';
import { Button } from '../common/Button';
import styles from './InteractiveQuestion.module.css';
import { Loading } from '../common/Loading';

type Load = { status: 'loading' } | { status: 'missing' } | { status: 'ready'; widget: WidgetDefinition };

export function InteractiveQuestion({
  spec,
  lang,
  feedback,
  submitting,
  onSubmit,
  onUnknown,
}: {
  spec: InteractivePublic;
  lang: 'es' | 'en';
  feedback: QuizAnswerResponse | null;
  submitting: boolean;
  onSubmit: (widgetState: Json) => void;
  onUnknown: () => void;
}) {
  const { t } = useTranslation('producto');
  const [load, setLoad] = useState<Load>({ status: 'loading' });
  const [state, setState] = useState<unknown>(null);
  const [mismatch, setMismatch] = useState(false);
  const sent = useRef<Json | undefined>(undefined);
  const answered = feedback !== null;

  useEffect(() => {
    let cancelled = false;
    setLoad({ status: 'loading' });
    loadWidget(spec.widget).then(
      (widget) => { if (!cancelled) setLoad(widget ? { status: 'ready', widget } : { status: 'missing' }); },
      () => { if (!cancelled) setLoad({ status: 'missing' }); },
    );
    return () => { cancelled = true; };
  }, [spec.widget]);

  useEffect(() => {
    // Sin `widget_target` (respuesta guardada sin conexión) no hay con qué comparar.
    if (!feedback || sent.current === undefined || feedback.widget_target === undefined) return;
    const client = check(spec.checker, sent.current, feedback.widget_target);
    if (client !== feedback.correct) {
      setMismatch(true);
      console.error(
        `[interactive] el checker ${spec.checker} del cliente dice ${client} y el servidor ${feedback.correct}`,
      );
    }
  }, [feedback, spec.checker]);

  if (load.status === 'loading') {
    return <Loading label={t('interactive.loading')} shape="line" />;
  }
  if (load.status === 'missing') {
    return <p className={styles.note} role="alert">{t('interactive.unavailable')}</p>;
  }

  const Widget = load.widget.render;
  const submit = () => {
    if (state === null) return;
    sent.current = load.widget.serialize(state);
    onSubmit(sent.current);
  };

  return (
    <div className={styles.area} data-checker-mismatch={mismatch || undefined}>
      <Widget params={spec.params} lang={lang} disabled={answered} onChange={setState} />
      {!answered && (
        <div className={styles.actions}>
          <Button type="button" full onClick={submit} disabled={submitting || state === null}>
            {t('interactive.check')}
          </Button>
          <Button type="button" variant="ghost" full onClick={onUnknown} disabled={submitting}>
            {t('quiz.dontKnow', { ns: 'common' })}
          </Button>
        </div>
      )}
    </div>
  );
}
