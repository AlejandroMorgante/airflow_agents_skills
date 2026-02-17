create table if not exists {{ params.schema }}.onepiece_sagas (
    id              integer primary key,
    title           varchar(255),
    saga_number     varchar(10),
    saga_chapitre   varchar(100),
    saga_volume     varchar(100),
    saga_episode    varchar(100),
    inserted_at     timestamptz default now()
);
