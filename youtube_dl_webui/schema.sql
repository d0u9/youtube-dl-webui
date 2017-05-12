drop table if exists task_param;
create table task_param (
  tid varchar primary key not null,
  url text not null
);

drop table if exists task_info;
create table task_info (
  id integer primary key autoincrement,
  title text not null
);

drop table if exists task_status;
create table task_status (
  id integer primary key autoincrement,
  title text not null
);

drop table if exists task_ydl_opt;
create table task_ydl_opt (
  id integer primary key autoincrement,
  title text not null
);
