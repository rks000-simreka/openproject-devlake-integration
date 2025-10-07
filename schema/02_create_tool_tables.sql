-- Tool layer tables for OpenProject structured data
-- These tables store extracted and structured data from raw JSON

-- Work packages tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_work_packages (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    subject VARCHAR(512),
    description LONGTEXT,
    start_date DATE,
    due_date DATE,
    estimated_hours DECIMAL(10,2),
    spent_hours DECIMAL(10,2),
    percentage_done INT DEFAULT 0,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    project_id INT,
    project_identifier VARCHAR(100),
    project_name VARCHAR(255),
    type_id INT,
    type_name VARCHAR(100),
    status_id INT,
    status_name VARCHAR(100),
    status_is_closed BOOLEAN DEFAULT FALSE,
    priority_id INT,
    priority_name VARCHAR(100),
    assignee_id INT,
    assignee_name VARCHAR(255),
    assignee_login VARCHAR(100),
    responsible_id INT,
    responsible_name VARCHAR(255),
    responsible_login VARCHAR(100),
    author_id INT,
    author_name VARCHAR(255),
    author_login VARCHAR(100),
    parent_id INT,
    version_id INT,
    version_name VARCHAR(255),
    category_id INT,
    category_name VARCHAR(255),
    custom_fields JSON,
    all_fields JSON,
    PRIMARY KEY (connection_id, id),
    INDEX idx_project (connection_id, project_id),
    INDEX idx_assignee (connection_id, assignee_id),
    INDEX idx_status (connection_id, status_id),
    INDEX idx_type (connection_id, type_id),
    INDEX idx_created (created_at),
    INDEX idx_updated (updated_at),
    INDEX idx_due_date (due_date),
    INDEX idx_parent (connection_id, parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Projects tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_projects (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    identifier VARCHAR(100),
    name VARCHAR(255),
    description LONGTEXT,
    homepage VARCHAR(512),
    status VARCHAR(50),
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    parent_id INT,
    PRIMARY KEY (connection_id, id),
    INDEX idx_identifier (identifier),
    INDEX idx_status (status),
    INDEX idx_parent (connection_id, parent_id),
    UNIQUE KEY unique_identifier (connection_id, identifier)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_users (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    login VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    name VARCHAR(255),
    mail VARCHAR(255),
    admin BOOLEAN DEFAULT FALSE,
    status VARCHAR(50),
    language VARCHAR(10),
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    last_login_on TIMESTAMP NULL,
    avatar_url VARCHAR(512),
    PRIMARY KEY (connection_id, id),
    INDEX idx_login (login),
    INDEX idx_status (status),
    INDEX idx_email (mail),
    UNIQUE KEY unique_login (connection_id, login)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Time entries tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_time_entries (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    work_package_id INT,
    user_id INT,
    user_login VARCHAR(100),
    user_name VARCHAR(255),
    activity_id INT,
    activity_name VARCHAR(100),
    hours DECIMAL(10,2),
    comment TEXT,
    spent_on DATE,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    PRIMARY KEY (connection_id, id),
    INDEX idx_work_package (connection_id, work_package_id),
    INDEX idx_user (connection_id, user_id),
    INDEX idx_spent_on (spent_on),
    INDEX idx_activity (activity_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Statuses tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_statuses (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    name VARCHAR(100),
    position INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_closed BOOLEAN DEFAULT FALSE,
    is_readonly BOOLEAN DEFAULT FALSE,
    default_done_ratio INT,
    PRIMARY KEY (connection_id, id),
    INDEX idx_position (position),
    INDEX idx_is_closed (is_closed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Types tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_types (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    name VARCHAR(100),
    position INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_in_roadmap BOOLEAN DEFAULT FALSE,
    is_milestone BOOLEAN DEFAULT FALSE,
    color VARCHAR(20),
    PRIMARY KEY (connection_id, id),
    INDEX idx_position (position),
    INDEX idx_milestone (is_milestone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Priorities tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_priorities (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    name VARCHAR(100),
    position INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (connection_id, id),
    INDEX idx_position (position),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Versions tool data  
CREATE TABLE IF NOT EXISTS _tool_openproject_versions (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    project_id INT,
    name VARCHAR(255),
    description LONGTEXT,
    status VARCHAR(50),
    due_date DATE,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    wiki_page_title VARCHAR(255),
    PRIMARY KEY (connection_id, id),
    INDEX idx_project (connection_id, project_id),
    INDEX idx_status (status),
    INDEX idx_due_date (due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Activities tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_activities (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    name VARCHAR(100),
    position INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (connection_id, id),
    INDEX idx_position (position),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;