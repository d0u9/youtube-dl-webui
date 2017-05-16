DROP TABLE IF EXISTS task_param;
CREATE TABLE task_param (
    tid     TEXT    PRIMARY KEY NOT NULL,
    state   INTEGER NOT NULL DEFAULT 2,
    url     TEXT    NOT NULL
);

DROP TABLE IF EXISTS task_info;
CREATE TABLE task_info (
    tid     TEXT    PRIMARY KEY NOT NULL,
    state   INTEGER NOT NULL DEFAULT 2,
    url     TEXT    NOT NULL,
    title   TEXT,
    filename    TEXT,
    create_time REAL    DEFAULT 0.0,
    finish_time REAL    DEFAULT 0.0,
    format  TEXT,
    ext     TEXT    NOT NULL DEFAULT ''
);

DROP TABLE IF EXISTS task_status;
CREATE TABLE task_status (
    tid     TEXT    PRIMARY KEY NOT NULL,
    state   INTEGER NOT NULL DEFAULT 2,
    percent TEXT    NOT NULL DEFAULT '0.0%',
    tmpfilename TEXT,
    downloaded_bytes    INTEGER DEFAULT 0,
    total_bytes         INTEGER DEFAULT 0,
    total_bytes_estmt   INTEGER DEFAULT 0,
    speed   INTEGER DEFAULT 0,
    eta     INTEGER DEFAULT 0,
    elapsed INTEGER DEFAULT 0,
    start_time  REAL DEFAULT 0.0,
    pause_time  REAL DEFAULT 0.0,
    log     TEXT    NOT NULL DEFAULT '[]'
);

DROP TABLE IF EXISTS task_ydl_opt;
CREATE TABLE task_ydl_opt (
    tid     TEXT    PRIMARY KEY NOT NULL,
    state   INTEGER NOT NULL DEFAULT 2,
    opt     TEXT    NOT NULL DEFAULT '{}'
);
