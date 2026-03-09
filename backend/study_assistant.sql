-- ================================================
-- AI Study Assistant - Database Setup Script
-- Run this in XAMPP phpMyAdmin or MySQL terminal
-- ================================================

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS study_assistant
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Step 2: Use the database
USE study_assistant;

-- Step 3: Create users table
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    email       VARCHAR(100) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,          -- hashed password (bcrypt)
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Step 4: Verify
SELECT 'Database and table created successfully!' AS status;
