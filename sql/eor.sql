-- create user foo password 'foo';
-- alter user foo with connection limit 8;
-- create database foo owner foo;


create or replace function updated() returns trigger as $$
begin
   NEW.updated = now();
   return NEW;
end;
$$ language 'plpgsql';


------------------------------------------------------------------------------------
-- users and auth
------------------------------------------------------------------------------------

create table users (
    login                  text                     not null    primary key, -- unique on lower()
    email                  text                     not null,                -- also unique on lower()

    password_hash          text                     not null    default '',
    -- these are used for both email confirmation and password reset
    confirm_code           text                     not null    default '',
    confirm_time           timestamp                NULL,

    status                 text                     not null
      check (status in ('UNCONFIRMED', 'DISABLED', 'ACTIVE', 'PASSWORD_RESET')),

    name                   text                     not null,

    avatar_date            timestamp                not null    default current_timestamp,

    twitter_user_id        text NULL                unique,
    twitter_access_token   text not null            default '',
    twitter_access_secret  text not null            default '',

    facebook_user_id       text NULL                unique,
    facebook_access_token  text not null            default '',

    vkontakte_user_id      text NULL                unique,
    vkontakte_access_token text not null            default '',

    registered             timestamp                not null    default current_timestamp,
    last_login             timestamp                NULL,
    last_activity          timestamp                NULL,

    comment                text                     not null    default ''
);

create unique index lower_login_idx ON users((lower(login)));
create unique index lower_email_idx ON users((lower(email)));
create index confirm_code_idx ON users(confirm_code);


create table roles (
    id                     text                     not null     primary key,
    name                   text                     not null,
    description            text                     not null     default ''
);

create table user_role_link (
    user_login            text                      not null    references users(login)
      on update cascade on delete cascade,
    role_id               text                      not null    references roles(id)
      on update cascade on delete cascade,

    primary key (user_login, role_id)
);

create table permissions (
    object_type            text                     not null    default '',
    permission             text                     not null,
    description            text                     not null    default '',

    primary key (object_type, permission)
);

create table role_permissions (
    role_id               text                      not null    references roles(id)
      on update cascade on delete cascade,
    object_type           text                      not null    default '',
    object_id             text                      not null    default '',  -- '' means no ID
    permission            text                      not null,

    primary key (role_id, permission),

    foreign key (object_type, permission) references permissions(object_type, permission)
      on update cascade on delete cascade
);

------------------------------------------------------------------------------------

insert into roles (id, name) values
  ('administrator', 'Administrator');

insert into permissions (object_type, permission) values
  ('admin-panel', 'access'),
  ('admin-panel', 'admin-only');

insert into role_permissions (role_id, object_type, permission) values
  ('administrator', 'admin-panel', 'access'),
  ('administrator', 'admin-panel', 'admin-only');

INSERT INTO users (login, email, password_hash, status, name) VALUES (
  'admin', 'admin@example.com',
  '$pbkdf2-sha256$7377$RohxTsmZsxailNK6l5IyBg$lFds1glS9Yp18CfqC1CnRUpTV6FFG0ARSiRazTq94g4',
  'ACTIVE', 'Admin'
);

insert into user_role_link values
  ('admin', 'administrator');


------------------------------------------------------------------------------------
-- cms
------------------------------------------------------------------------------------

-- страницы, не имеющие url, выдающиеся движком по событию
create table cms_messages (
    id                  text                not null    primary key,
    purpose             text                not null    default '',

    title               text                not null,
    content             text                not null,
    head                text                not null    default '',

    comment             text                not null    default '',
    updated             timestamp           not null    default current_timestamp   -- trigger
);

create trigger updated
  before update on cms_messages
  for each row
  execute procedure updated();

insert into cms_messages(id, purpose, title, content, head, comment) values
  ('404',       'страница не найдена',  'Страница не найдена', 'Страница не найдена', '', '${detail}'),
  ('forbidden', 'доступ запрещен',      'Доступ запрещен',     'Доступ запрещен', '', '');


create table auto_email_templates (
    id                  text                not null    primary key,
    purpose             text                not null,

    body_type           text                not null    check (body_type in ('text', 'html')),

    subject             text                not null,
    body                text                not null,

    comment             text                not null    default '',
    added               timestamp           not null    default current_timestamp,
    updated             timestamp           not null    default current_timestamp   -- trigger
);

create trigger updated
  before update on auto_email_templates
  for each row
  execute procedure updated();


create table log_messages (
    id                  serial              not null    primary key,
    added               timestamp           not null    default current_timestamp,

    level               text                not null    check (level in ('DEBUG', 'INFO', 'NOTE', 'WARNING', 'ERROR', 'CRITICAL')),

    object              text                not null,
    action              text                not null,
    success             boolean             not null,
    subsystem           text                not null, -- check ?
    message             text                not null,

    user_login          text                NULL       references users(login),

    ip_addr             text                not null,
    user_agent          text                not null
);


create table pages (
    id                  text                not null    primary key,
    title               text                not null,
    content             text                not null,
    head                text                not null    default '',

    meta_kw             text                not null    default '',
    meta_desc           text                not null    default '',

    status              text                not null    default 'DISABLED' check(status in ('DISABLED', 'ACTIVE')),

    comment             text                not null    default '',
    added               timestamp           not null    default current_timestamp,
    updated             timestamp           not null    default current_timestamp   -- trigger
);

create trigger updated
  before update on pages
  for each row
  execute procedure updated();

