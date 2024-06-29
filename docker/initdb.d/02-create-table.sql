BEGIN;

CREATE TABLE tb_concepts (
            id serial primary key,
            title text,
            keywords text,
            category text,
            summary text,
            status text,
            filepath text,
            create_time timestamp,
            update_time timestamp,
            token_num integer,
            embedding vector(3072)
);

CREATE TABLE tb_networks (
            id serial primary key,
            source integer,
            target integer
);

END;