create table if not exists {{ params.schema }}.onepiece_characters (
    id                integer primary key,
    name              varchar(255),
    size              varchar(50),
    age               varchar(50),
    bounty            varchar(100),
    job               varchar(255),
    status            varchar(100),
    crew_id           integer,
    crew_name         varchar(255),
    crew_roman_name   varchar(255),
    crew_status       varchar(100),
    crew_is_yonko     boolean,
    fruit_id          integer,
    fruit_name        varchar(255),
    fruit_roman_name  varchar(255),
    fruit_type        varchar(100),
    inserted_at       timestamptz default now()
);
