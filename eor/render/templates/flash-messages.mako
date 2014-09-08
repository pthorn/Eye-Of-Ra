
<%def name="logged_in(params)">
    <div class="alert alert-success">
        <p>Вы вошли на сайт.</p>
    </div>
</%def>

<%def name="bad_login(params)">
    <div class="alert alert-danger">
        <p>Неверное имя пользователя или пароль, либо пользователь заблокирован.</p>
    </div>
</%def>

<%def name="user_confirmed(params)">
    <div class="alert alert-success">
        <p>Поздравляем, вы успешно подтвердили свой адрес электронной почты!</p>
        <p>Теперь вы можете войти на сайт, используя ваше имя пользователя и пароль.</p>
    </div>
</%def>

<%def name="password_reset(params)">
    <div class="alert alert-success">
        <p>Вы успешно изменили пароль. Теперь вы можете войти на сайт с новым паролем.</p>
    </div>
</%def>

<%def name="added_social_account(params)">
    <div class="alert alert-success">
        <p>Аккаунт подключен.</p>
    </div>
</%def>

<%def name="other_user_has_same_social_id(params)">
    <div class="alert alert-danger">
        <p>Другой пользователь уже зарегистрирован с этим аккаунтом соцсети.</p>
    </div>
</%def>

<%def name="social_error(params)">
    <div class="alert alert-danger">
        <p>Ошибка входа.</p>
    </div>
</%def>
