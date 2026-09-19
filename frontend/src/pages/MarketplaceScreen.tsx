import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { CourseCard } from '../components/marketplace/CourseCard';
import '../styles/marketplace.css';

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

export function MarketplaceScreen() {
  const { i18n, t } = useTranslation();
  const lang = i18n.language as 'es' | 'en';

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory] = useState('all');
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [sortBy, setSortBy] = useState('popular');

  const mockCourses: Course[] = [
    {
      id: 'c1',
      name_es: 'Python Avanzado',
      name_en: 'Advanced Python',
      description_es: 'Domina patrones avanzados, metaprogramación y optimización.',
      description_en: 'Master advanced patterns, metaprogramming, and optimization.',
      category_es: 'Programación',
      category_en: 'Programming',
      level: 'advanced',
      price_usd: 49.99,
      rating: 4.8,
      reviews_count: 342,
      students_count: 1240,
      instructor_name_es: 'Dr. Carlos López',
      instructor_name_en: 'Dr. Carlos Lopez',
      first_lesson: {
        title_es: 'Decoradores y Closures',
        title_en: 'Decorators and Closures',
        duration_minutes: 15,
      },
    },
    {
      id: 'c2',
      name_es: 'Algoritmos y Estructuras de Datos',
      name_en: 'Algorithms & Data Structures',
      description_es: 'Aprende los fundamentos de computación eficiente.',
      description_en: 'Learn the fundamentals of efficient computing.',
      category_es: 'Fundamentos',
      category_en: 'Fundamentals',
      level: 'intermediate',
      price_usd: 39.99,
      rating: 4.6,
      reviews_count: 287,
      students_count: 856,
      instructor_name_es: 'Dra. Sofia García',
      instructor_name_en: 'Dr. Sofia Garcia',
      first_lesson: {
        title_es: 'Complejidad Temporal',
        title_en: 'Time Complexity',
        duration_minutes: 12,
      },
    },
  ];

  const levels = ['all', 'beginner', 'intermediate', 'advanced'];


  const filteredCourses = useMemo(() => {
    let filtered = mockCourses;

    if (searchTerm.trim()) {
      const lower = searchTerm.toLowerCase();
      filtered = filtered.filter((c) =>
        c[`name_${lang}`].toLowerCase().includes(lower) ||
        c[`description_${lang}`].toLowerCase().includes(lower)
      );
    }

    if (selectedLevel !== 'all') {
      filtered = filtered.filter((c) => c.level === selectedLevel);
    }

    if (sortBy === 'popular') {
      filtered.sort((a, b) => b.students_count - a.students_count);
    } else if (sortBy === 'rating') {
      filtered.sort((a, b) => b.rating - a.rating);
    }

    return filtered;
  }, [searchTerm, selectedCategory, selectedLevel, sortBy, lang]);

  return (
    <div className="marketplace">
      <div className="marketplace-header">
        <h1>{t('marketplace.title', 'Marketplace de Cursos')}</h1>
        <p>{t('marketplace.subtitle', 'Descubre cursos de calidad')}</p>
      </div>

      <div className="marketplace-controls">
        <div className="search-box">
          <input
            type="text"
            className="search-input"
            placeholder={t('marketplace.search_placeholder', 'Buscar cursos...')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <span className="search-icon">🔍</span>
        </div>

        <div className="filters">
          <div className="filter-group">
            <label>{t('marketplace.level', 'Nivel')}</label>
            <select value={selectedLevel} onChange={(e) => setSelectedLevel(e.target.value)}>
              {levels.map((lvl) => (
                <option key={lvl} value={lvl}>
                  {lvl === 'all'
                    ? t('marketplace.all_levels', 'Todos')
                    : lvl === 'beginner'
                      ? t('marketplace.beginner', 'Principiante')
                      : lvl === 'intermediate'
                        ? t('marketplace.intermediate', 'Intermedio')
                        : t('marketplace.advanced', 'Avanzado')}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>{t('marketplace.sort', 'Ordenar')}</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="popular">{t('marketplace.sort_popular', 'Más Popular')}</option>
              <option value="rating">{t('marketplace.sort_rating', 'Mayor Calificación')}</option>
            </select>
          </div>
        </div>
      </div>

      <div className="courses-grid">
        {filteredCourses.length > 0 ? (
          filteredCourses.map((course) => (
            <CourseCard
              key={course.id}
              course={course}
              onPreview={(c) => console.log('Preview:', c.id)}
              onEnroll={(c) => console.log('Enroll:', c.id)}
            />
          ))
        ) : (
          <div className="no-courses">
            <p>{t('marketplace.no_courses', 'No se encontraron cursos')}</p>
          </div>
        )}
      </div>
    </div>
  );
}
