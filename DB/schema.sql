-- Users table to store admin, teacher, and student information
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP, -- Added for tracking last login
    reset_token VARCHAR(255), -- Added for password reset functionality
    deleted_at TIMESTAMP -- Added for soft deletes
);

-- User profiles table for extended user details (e.g., bio, profile picture)
CREATE TABLE user_profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    bio TEXT, -- Optional bio for user profiles
    profile_picture_url TEXT, -- URL for profile picture (stored in MinIO)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Courses table to store course details
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    teacher_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_published BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP -- Added for soft deletes
);

-- Course metadata table for categories, tags, or other attributes
CREATE TABLE course_metadata (
    metadata_id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    category VARCHAR(100), -- E.g., 'Programming', 'Mathematics'
    tags TEXT[], -- Array of tags for search/filtering
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chapters table to organize course content
CREATE TABLE chapters (
    chapter_id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    chapter_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, chapter_order) -- Added to ensure unique chapter order per course
);

-- Lessons table to store lesson content (videos, documents, etc.)
CREATE TABLE lessons (
    lesson_id SERIAL PRIMARY KEY,
    chapter_id INTEGER NOT NULL REFERENCES chapters(chapter_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    lesson_type VARCHAR(50) NOT NULL CHECK (lesson_type IN ('video', 'document', 'quiz', 'other')),
    minio_url TEXT NOT NULL, -- Changed to TEXT for longer URLs/metadata
    lesson_order INTEGER NOT NULL,
    duration INTEGER CHECK (duration > 0), -- Added CHECK for positive duration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chapter_id, lesson_order) -- Added to ensure unique lesson order per chapter
);

-- Enrollments table to track student course enrollment
CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id)
);

-- Progress table to track student progress in lessons
CREATE TABLE progress (
    progress_id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    UNIQUE(student_id, lesson_id)
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role); -- Added for role-based queries
CREATE INDEX idx_courses_teacher_id ON courses(teacher_id);
CREATE INDEX idx_courses_is_published ON courses(is_published); -- Added for published course queries
CREATE INDEX idx_chapters_course_id ON chapters(course_id);
CREATE INDEX idx_lessons_chapter_id ON lessons(chapter_id);
CREATE INDEX idx_enrollments_student_course ON enrollments(student_id, course_id);
CREATE INDEX idx_progress_student_lesson ON progress(student_id, lesson_id);
CREATE INDEX idx_progress_completed ON progress(completed); -- Added for progress tracking queries




ALTER TABLE progress
ADD COLUMN IF NOT EXISTS course_id INTEGER,
ADD COLUMN IF NOT EXISTS completed_percentage DOUBLE PRECISION DEFAULT 0.0,
ADD CONSTRAINT progress_course_id_fkey FOREIGN KEY (course_id) REFERENCES courses(course_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_student_lesson_unique
ON progress (student_id, lesson_id)
WHERE lesson_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_student_course_unique
ON progress (student_id, course_id)
WHERE course_id IS NOT NULL;