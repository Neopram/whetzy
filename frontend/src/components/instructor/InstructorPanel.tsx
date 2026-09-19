import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import '../../styles/instructor.css'

interface Course {
  id: string
  name_es: string
  name_en: string
  students_count: number
  rating: number
  revenue_usd: number
  created_at: Date
}

interface StudentProgress {
  id: string
  name_es: string
  name_en: string
  course_id: string
  progress_percent: number
  last_activity: Date
  skills_completed: number
}

export default function InstructorPanel() {
  const { i18n, t } = useTranslation()
  const lang = i18n.language as 'es' | 'en'

  const [courses] = useState<Course[]>([
    {
      id: 'curso1',
      name_es: 'Python Avanzado',
      name_en: 'Advanced Python',
      students_count: 148,
      rating: 4.8,
      revenue_usd: 3560,
      created_at: new Date('2026-06-15')
    },
    {
      id: 'curso2',
      name_es: 'Algoritmos y Estructuras',
      name_en: 'Algorithms & Data Structures',
      students_count: 92,
      rating: 4.6,
      revenue_usd: 1840,
      created_at: new Date('2026-08-01')
    },
    {
      id: 'curso3',
      name_es: 'Desarrollo Web Full Stack',
      name_en: 'Full Stack Web Development',
      students_count: 56,
      rating: 4.7,
      revenue_usd: 1120,
      created_at: new Date('2026-09-10')
    }
  ])

  const [students] = useState<StudentProgress[]>([
    { id: 's1', name_es: 'Ana García', name_en: 'Ana García', course_id: 'curso1', progress_percent: 78, last_activity: new Date(), skills_completed: 12 },
    { id: 's2', name_es: 'Carlos López', name_en: 'Carlos López', course_id: 'curso1', progress_percent: 45, last_activity: new Date(Date.now() - 86400000), skills_completed: 6 },
    { id: 's3', name_es: 'Sofia Martínez', name_en: 'Sofia Martínez', course_id: 'curso2', progress_percent: 92, last_activity: new Date(), skills_completed: 18 }
  ])

  const totalEarnings = courses.reduce((sum, c) => sum + c.revenue_usd, 0)
  const totalStudents = courses.reduce((sum, c) => sum + c.students_count, 0)
  const avgRating = (courses.reduce((sum, c) => sum + c.rating, 0) / courses.length).toFixed(1)

  return (
    <div className="instructor-panel">
      <section className="instructor-header">
        <h1>{t('instructor.title', 'Panel de Instructor')}</h1>
        <p className="subtitle">{t('instructor.subtitle', 'Gestiona tus cursos y estudiantes')}</p>
        <p className="mock-badge">⚠️ {t('common.mock_data', 'Datos de prueba')}</p>
      </section>

      <section className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">{t('instructor.total_earnings', 'Ingresos Totales')}</div>
          <div className="kpi-value">${totalEarnings.toLocaleString()}</div>
          <div className="kpi-subtext">{t('instructor.usd', 'USD')}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">{t('instructor.total_students', 'Estudiantes Totales')}</div>
          <div className="kpi-value">{totalStudents}</div>
          <div className="kpi-subtext">{t('instructor.enrolled', 'Inscritos')}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">{t('instructor.avg_rating', 'Calificación Promedio')}</div>
          <div className="kpi-value">{avgRating} ⭐</div>
          <div className="kpi-subtext">{t('instructor.from_students', 'De estudiantes')}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">{t('instructor.courses_published', 'Cursos Publicados')}</div>
          <div className="kpi-value">{courses.length}</div>
          <div className="kpi-subtext">{t('common.active', 'Activos')}</div>
        </div>
      </section>

      <section className="courses-section">
        <h2>{t('instructor.your_courses', 'Tus Cursos')}</h2>
        <div className="courses-table">
          <div className="table-header">
            <div className="col-name">{t('common.course', 'Curso')}</div>
            <div className="col-students">{t('instructor.students', 'Estudiantes')}</div>
            <div className="col-rating">{t('common.rating', 'Calificación')}</div>
            <div className="col-revenue">{t('instructor.revenue', 'Ingresos')}</div>
          </div>
          {courses.map((course) => (
            <div key={course.id} className="table-row">
              <div className="col-name">{course[`name_${lang}`]}</div>
              <div className="col-students">{course.students_count}</div>
              <div className="col-rating">{course.rating} ⭐</div>
              <div className="col-revenue">${course.revenue_usd.toLocaleString()}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="students-section">
        <h2>{t('instructor.student_progress', 'Progreso de Estudiantes')}</h2>
        <div className="students-grid">
          {students.map((student) => (
            <div key={student.id} className="student-card">
              <div className="student-name">{student[`name_${lang}`]}</div>
              <div className="student-course">
                {courses.find(c => c.id === student.course_id)?.[`name_${lang}`]}
              </div>
              <div className="progress-bar-container">
                <div className="progress-bar" style={{ width: `${student.progress_percent}%` }}></div>
              </div>
              <div className="progress-text">{student.progress_percent}% {t('common.complete', 'completo')}</div>
              <div className="student-meta">
                {t('instructor.skills_done', 'Skills completadas')}: {student.skills_completed}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
