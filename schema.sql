drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  title text not null,
  'text' text not null
);

drop table if exists shakespearetext;
create table shakespearetext (
  line_id integer primary key,
  play_name text not null,
  speech_number text not null,
  line_number text not null,
  speaker text not null,
  text_entry text not null
);

