
create table captcha (
    remote_addr         text                not null,
    form_id             text                not null,
    value               text                not null,
    created             timestamp           not null    default current_timestamp,
    primary key (remote_addr, form_id)
);


create table captcha_words (
    word                text                not null    primary key
);
