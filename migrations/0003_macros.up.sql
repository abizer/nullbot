create table if not exists macros (
	id serial primary key,
	slug citext not null,
	link text not null
);

create unique index if not exists slug_idx on macros(slug);
