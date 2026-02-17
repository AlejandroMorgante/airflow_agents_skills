create table if not exists {{ params.schema }}.onepiece_fruits (
    id            integer primary key,
    name          varchar(255),
    roman_name    varchar(255),
    type          varchar(100),
    description   text,
    image_url     text,
    inserted_at   timestamptz default now()
);
