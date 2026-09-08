import styles from './LegalScreen.module.css';

interface Props {
  doc: 'privacy' | 'terms';
}

export function LegalScreen({ doc }: Props) {
  return (
    <div className={styles.page}>
      <button className={styles.back} onClick={() => history.back()}>← Volver</button>
      {doc === 'privacy' ? <PrivacyContent /> : <TermsContent />}
    </div>
  );
}

function PrivacyContent() {
  return (
    <article className={styles.article}>
      <h1>Política de Privacidad</h1>
      <p className={styles.updated}>Última actualización: septiembre 2026</p>

      <h2>1. Información que recopilamos</h2>
      <ul>
        <li>Dirección de correo, nombre y avatar (datos de cuenta)</li>
        <li>Respuestas a preguntas, puntuaciones y tiempos de sesión</li>
        <li>Nivel de dominio por habilidad y datos de FSRS/Elo/BKT</li>
        <li>Rachas, XP e historial de ligas</li>
        <li>Idioma y preferencias de dispositivo</li>
      </ul>

      <h2>2. Cómo usamos tus datos</h2>
      <ul>
        <li>Personalizar la dificultad de preguntas y el orden de repaso</li>
        <li>Calcular rachas, XP y posiciones en ligas</li>
        <li>Mejorar la calidad del contenido y detectar errores</li>
        <li>Cumplir obligaciones legales</li>
      </ul>

      <h2>3. Base legal (RGPD)</h2>
      <p>Tratamos tus datos sobre la base de <strong>ejecución de contrato</strong> (prestación del servicio) y <strong>interés legítimo</strong> (mejora del producto y seguridad).</p>

      <h2>4. Retención de datos</h2>
      <p>Conservamos tus datos mientras tu cuenta esté activa. Si la eliminas, los datos se borran en <strong>30 días</strong> salvo obligación legal de retención.</p>

      <h2>5. Tus derechos</h2>
      <ul>
        <li>Acceso, rectificación y portabilidad (exporta tus datos desde Perfil)</li>
        <li>Eliminación (solicita el borrado desde Perfil → Eliminar cuenta)</li>
        <li>Oposición y limitación del tratamiento</li>
      </ul>
      <p>Para ejercer tus derechos: <a href="mailto:privacy@whetzy.com">privacy@whetzy.com</a></p>

      <h2>6. Contacto</h2>
      <p>Whetzy · <a href="mailto:privacy@whetzy.com">privacy@whetzy.com</a></p>
    </article>
  );
}

function TermsContent() {
  return (
    <article className={styles.article}>
      <h1>Términos de Servicio</h1>
      <p className={styles.updated}>Última actualización: septiembre 2026</p>

      <h2>1. Aceptación</h2>
      <p>Al usar Whetzy aceptas estos Términos. Si no los aceptas, no uses el servicio.</p>

      <h2>2. Uso aceptable</h2>
      <ul>
        <li>No automatices ni extraigas el contenido sin autorización</li>
        <li>No compartas credenciales de acceso</li>
        <li>No intentes vulnerar la seguridad del servicio</li>
      </ul>

      <h2>3. Propiedad intelectual</h2>
      <p>El contenido educativo, algoritmos y diseño son propiedad de Whetzy. El código fuente de la plataforma está publicado bajo licencia MIT.</p>

      <h2>4. Limitación de responsabilidad</h2>
      <p>El servicio se proporciona "tal cual". No garantizamos resultados de aprendizaje específicos ni disponibilidad ininterrumpida.</p>

      <h2>5. Modificaciones</h2>
      <p>Podemos modificar estos Términos notificándote con 15 días de antelación. El uso continuado implica aceptación.</p>

      <h2>6. Ley aplicable</h2>
      <p>Estos Términos se rigen por la ley española y los tribunales competentes de Madrid.</p>

      <h2>7. Contacto</h2>
      <p>Whetzy · <a href="mailto:legal@whetzy.com">legal@whetzy.com</a></p>
    </article>
  );
}
