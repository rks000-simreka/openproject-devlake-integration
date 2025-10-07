-- Raw layer tables for OpenProject data storage
-- These tables store the raw JSON responses from OpenProject API

-- Work packages raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_work_packages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    project_id INT,
    INDEX idx_connection_project (connection_id, project_id),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Projects raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_projects (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Time entries raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_time_entries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    work_package_id INT,
    INDEX idx_connection_wp (connection_id, work_package_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Statuses raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_statuses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Types raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_types (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Priorities raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_priorities (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Versions raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_versions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    project_id INT,
    INDEX idx_connection_project (connection_id, project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Activities raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_activities (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;