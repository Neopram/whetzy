import { useTranslation } from 'react-i18next';

interface Course {
  id: string;
  name_es: string;
  name_en: string;
  description_es: string;
  description_en: string;
  category_es: string;
  category_en: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  price_usd: number;
  rating: number;
  reviews_count: number;
  students_count: number;
  instructor_name_es: string;
  instructor_name_en: string;
  first_lesson: {
    title_es: string;
    title_en: string;
    duration_minutes: number;
  };
}

interface CourseCardProps {
  course: Course;
  onPreview?: (course: Course) => void;
  onEnroll?: (course: Course) => void;
}

export function CourseCard({ course, onPreview, onEnroll }: CourseCardProps) {
  const { i18n, t } = useTranslation();
  const lang = i18n.language as 'es' | 'en';

  const levelLabels: Record<string, string> = {
    beginner: lang === 'es' ? 'Principiante' : 'Beginner',
    intermediate: lang === 'es' ? 'Intermedio' : 'Intermediate',
    advanced: lang === 'es' ? 'Avanzado' : 'Advanced',
  };

  const levelColors: Record<string, string> = {
    beginner: '#10b981',
    intermediate: '#f59e0b',
    advanced: '#ef4444',
  };

  const isEnrolled = Math.random() < 0.2;

  return (
    <div className="course-card">
      <div className="course-header">
        <div
          className="course-level"
          style={{ background: levelColors[course.level] }}
        >
          {levelLabels[course.level]}
        </div>
        <div className="course-rating">
          <span className="stars">★</span>
          <span className="rating-value">{course.rating.toFixed(1)}</span>
          <span className="reviews-count">({course.reviews_count})</span>
        </div>
      </div>

      <div className="course-content">
        <h3 className="course-name">{course[`name_${lang}`]}</h3>
        <p className="course-category">{course[`category_${lang}`]}</p>
        <p className="course-description">{course[`description_${lang}`]}</p>

        <div className="course-instructor">
          <span className="instructor-label">{t('marketplace.by', 'Por')}: </span>
          <span className="instructor-name">
            {course[`instructor_name_${lang}`]}
          </span>
        </div>

        <div className="course-stats">
          <div className="stat">
            <span className="stat-icon">👥</span>
            <span className="stat-value">{course.students_count}</span>
          </div>
          <div className="stat">
            <span className="stat-icon">📚</span>
            <span className="stat-value">{course.first_lesson.duration_minutes} min</span>
          </div>
        </div>

        <div className="course-first-lesson">
          <span className="lesson-icon">▶</span>
          <span className="lesson-title">
            {course.first_lesson[`title_${lang}`]}
          </span>
        </div>
      </div>

      <div className="course-footer">
        <div className="course-price">
          {course.price_usd > 0 ? (
            <>
              <span className="price-currency">$</span>
              <span className="price-amount">{course.price_usd}</span>
            </>
          ) : (
            <span className="price-free">{t('marketplace.free', 'Gratis')}</span>
          )}
        </div>

        <div className="course-actions">
          <button
            className="btn-preview"
            onClick={() => onPreview?.(course)}
            title={t('marketplace.preview_lesson', 'Previsualizar lección')}
          >
            {t('marketplace.preview', 'Vista Previa')}
          </button>
          <button
            className={`btn-enroll ${isEnrolled ? 'enrolled' : ''}`}
            onClick={() => onEnroll?.(course)}
            disabled={isEnrolled}
          >
            {isEnrolled
              ? t('marketplace.enrolled', 'Inscrito')
              : t('marketplace.enroll', 'Inscribirse')}
          </button>
        </div>
      </div>
    </div>
  );
}
