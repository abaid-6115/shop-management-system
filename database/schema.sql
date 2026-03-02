create table users (
    id uuid primary key references auth.users(id) on delete cascade,
    role text default 'staff',
    created_at timestamp default now()
);
