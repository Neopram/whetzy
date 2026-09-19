import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import '../../styles/b2b.css'

interface Employee {
  id: string
  name: string
  email: string
  mastery_avg: number
  skills_learned: number
  sessions_completed: number
  last_activity: string
  status: 'active' | 'inactive'
}

interface BatchCode {
  code: string
  created_at: string
  max_uses: number
  uses_remaining: number
  assigned_count: number
}

export default function B2BPanel() {
  const { i18n, t } = useTranslation()
  const lang = i18n.language as 'es' | 'en'

  const [employees] = useState<Employee[]>([
    {
      id: 'emp1',
      name: 'Ana García',
      email: 'ana@company.com',
      mastery_avg: 82,
      skills_learned: 15,
      sessions_completed: 42,
      last_activity: '2026-09-19',
      status: 'active',
    },
    {
      id: 'emp2',
      name: 'Luis Martínez',
      email: 'luis@company.com',
      mastery_avg: 65,
      skills_learned: 8,
      sessions_completed: 21,
      last_activity: '2026-09-15',
      status: 'active',
    },
    {
      id: 'emp3',
      name: 'María López',
      email: 'maria@company.com',
      mastery_avg: 45,
      skills_learned: 3,
      sessions_completed: 5,
      last_activity: '2026-09-10',
      status: 'inactive',
    },
  ])

  const [batchCodes] = useState<BatchCode[]>([
    {
      code: 'BATCH-2026-SEP-001',
      created_at: '2026-09-01',
      max_uses: 50,
      uses_remaining: 42,
      assigned_count: 8,
    },
    {
      code: 'BATCH-2026-AUG-001',
      created_at: '2026-08-01',
      max_uses: 100,
      uses_remaining: 0,
      assigned_count: 100,
    },
  ])

  const avgMastery = employees.length
    ? Math.round(employees.reduce((sum, e) => sum + e.mastery_avg, 0) / employees.length)
    : 0

  const totalSessions = employees.reduce((sum, e) => sum + e.sessions_completed, 0)
  const activeDays = employees.filter((e) => e.status === 'active').length

  return (
    <div className="b2b-panel">
      <div className="b2b-header">
        <h1>{t('b2b.title', 'Panel B2B')}</h1>
        <p>{t('b2b.subtitle', 'Progreso y Comparativas del Equipo')}</p>
      </div>

      <div className="b2b-kpis">
        <div className="kpi-card">
          <span className="kpi-label">{t('b2b.avg_mastery', 'Dominio Promedio')}</span>
          <span className="kpi-value">{avgMastery}%</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">{t('b2b.total_sessions', 'Sesiones Totales')}</span>
          <span className="kpi-value">{totalSessions}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">{t('b2b.active_users', 'Usuarios Activos')}</span>
          <span className="kpi-value">{activeDays}</span>
        </div>
      </div>

      <section className="employees-section">
        <h2>{t('b2b.employees', 'Empleados')}</h2>
        <div className="employees-table">
          <div className="table-header">
            <div className="col-name">{t('b2b.name', 'Nombre')}</div>
            <div className="col-mastery">{t('b2b.mastery', 'Dominio')}</div>
            <div className="col-skills">{t('b2b.skills', 'Skills')}</div>
            <div className="col-sessions">{t('b2b.sessions', 'Sesiones')}</div>
            <div className="col-status">{t('b2b.status', 'Estado')}</div>
          </div>
          {employees.map((emp) => (
            <div key={emp.id} className="table-row">
              <div className="col-name">
                <p className="emp-name">{emp.name}</p>
                <p className="emp-email">{emp.email}</p>
              </div>
              <div className="col-mastery">{emp.mastery_avg}%</div>
              <div className="col-skills">{emp.skills_learned}</div>
              <div className="col-sessions">{emp.sessions_completed}</div>
              <div className="col-status">
                <span className={`status-badge ${emp.status}`}>
                  {emp.status === 'active'
                    ? t('b2b.active', 'Activo')
                    : t('b2b.inactive', 'Inactivo')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="batch-codes-section">
        <h2>{t('b2b.batch_codes', 'Códigos Batch')}</h2>
        <button className="btn-primary">{t('b2b.create_batch', 'Crear Nuevo Código')}</button>
        <div className="batch-codes-list">
          {batchCodes.map((batch) => (
            <div key={batch.code} className="batch-card">
              <div className="batch-header">
                <span className="batch-code">{batch.code}</span>
                <span className="batch-date">{new Date(batch.created_at).toLocaleDateString()}</span>
              </div>
              <div className="batch-stats">
                <div className="batch-stat">
                  <span>{t('b2b.assigned', 'Asignados')}: {batch.assigned_count}</span>
                </div>
                <div className="batch-stat">
                  <span>{t('b2b.remaining', 'Disponibles')}: {batch.uses_remaining}</span>
                </div>
                <div className="batch-stat">
                  <span>{t('b2b.capacity', 'Capacidad')}: {batch.max_uses}</span>
                </div>
              </div>
              <button className="btn-secondary">{t('b2b.copy', 'Copiar Código')}</button>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
