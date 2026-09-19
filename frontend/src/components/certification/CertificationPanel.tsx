import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import '../../styles/certification.css'

interface Domain {
  id: string
  name_es: string
  name_en: string
  readiness: number
  cert_name: string
  cost: string
}

interface MockExam {
  id: string
  name_es: string
  name_en: string
  domain_id: string
  questions: number
  time_minutes: number
  score?: number
  completed_at?: Date
}

interface Certificate {
  id: string
  name_es: string
  name_en: string
  earned_at: Date
  expires_at?: Date
  code: string
}

export default function CertificationPanel() {
  const { i18n, t } = useTranslation()
  const lang = i18n.language as 'es' | 'en'

  const [domains] = useState<Domain[]>([
    { id: 'python', name_es: 'Python', name_en: 'Python', readiness: 87, cert_name: 'PCEP', cost: '$59' },
    { id: 'aws', name_es: 'AWS', name_en: 'AWS', readiness: 72, cert_name: 'SAA-C03', cost: '$150' },
    { id: 'azure', name_es: 'Azure', name_en: 'Azure', readiness: 45, cert_name: 'AZ-900', cost: '$99' },
  ])

  const [mockExams] = useState<MockExam[]>([
    {
      id: 'pcep-1',
      name_es: 'Simulacro PCEP #1',
      name_en: 'PCEP Mock #1',
      domain_id: 'python',
      questions: 40,
      time_minutes: 45,
      score: 82,
      completed_at: new Date('2026-09-15'),
    },
    {
      id: 'saa-1',
      name_es: 'Simulacro SAA-C03 #1',
      name_en: 'SAA-C03 Mock #1',
      domain_id: 'aws',
      questions: 65,
      time_minutes: 130,
    },
  ])

  const [certificates] = useState<Certificate[]>([
    {
      id: 'cert-1',
      name_es: 'Certificado PCEP',
      name_en: 'PCEP Certificate',
      earned_at: new Date('2026-09-01'),
      expires_at: new Date('2028-09-01'),
      code: 'PCEP-0000-9A7B2C',
    },
  ])

  const getReadinessColor = (readiness: number) => {
    if (readiness >= 80) return 'var(--color-success)'
    if (readiness >= 60) return 'var(--color-primary)'
    return 'var(--color-warning)'
  }

  return (
    <div className="certification-panel">
      <section className="readiness">
        <h2>{t('cert.readiness', 'Preparación para Certificaciones')}</h2>
        <div className="domains-grid">
          {domains.map((d) => (
            <div key={d.id} className="domain-card">
              <div className="domain-header">
                <h3>{d[`name_${lang}`]}</h3>
                <span className="cert-name">{d.cert_name}</span>
              </div>
              <div className="readiness-bar-container">
                <div className="readiness-bar">
                  <div
                    className="readiness-fill"
                    style={{
                      width: `${d.readiness}%`,
                      backgroundColor: getReadinessColor(d.readiness),
                    }}
                  />
                </div>
                <span className="readiness-percent">{d.readiness}%</span>
              </div>
              <p className="cost">{d.cost}</p>
              <button className="btn-primary">
                {d.readiness >= 80 ? t('cert.schedule', 'Agendar') : t('cert.continue', 'Continuar')}
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="mock-exams">
        <h2>{t('cert.mocks', 'Simulacros')}</h2>
        <div className="mocks-list">
          {mockExams.map((m) => (
            <div key={m.id} className="mock-card">
              <div className="mock-header">
                <h3>{m[`name_${lang}`]}</h3>
                {m.score && <span className="score">✓ {m.score}%</span>}
              </div>
              <div className="mock-details">
                <span>{m.questions} Q</span>
                <span>•</span>
                <span>{m.time_minutes} min</span>
              </div>
              {m.completed_at ? (
                <p className="completed">
                  {t('cert.completed', 'Completado')} {m.completed_at.toLocaleDateString()}
                </p>
              ) : (
                <button className="btn-secondary">{t('cert.start', 'Comenzar')}</button>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="earned-certs">
        <h2>{t('cert.earned', 'Certificados Obtenidos')}</h2>
        <div className="certs-grid">
          {certificates.map((c) => (
            <div key={c.id} className="cert-item">
              <div className="cert-icon">🏆</div>
              <h3>{c[`name_${lang}`]}</h3>
              <p className="cert-code">{c.code}</p>
              <p className="cert-date">
                {t('cert.earned_date', 'Obtenido:')} {c.earned_at.toLocaleDateString()}
              </p>
              {c.expires_at && (
                <p className="cert-expiry">
                  {t('cert.expires', 'Vence:')} {c.expires_at.toLocaleDateString()}
                </p>
              )}
              <button className="btn-secondary">{t('cert.verify', 'Verificar')}</button>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
