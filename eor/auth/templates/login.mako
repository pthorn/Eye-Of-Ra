<%page/>
<%inherit file="victoria.site:templates/00layout.mako"/>
<%namespace name="b" file="victoria.site:templates/00blocks.mako" import="*"/>
<%namespace name="form" file="victoria.site:templates/blocks/forms.mako" import="*"/>

<%block name="page_title">Вход</%block>

<%block name="head">
    <h2 class="page-title">${self.page_title()}</h2>
</%block>


<div class="col-left">
    <div class="block-shadow">

        <form method="POST" action="" class="form-horizontal">
            ${form.form_field(c.form.login, label=u'Имя пользователя')}
            ${form.form_field(c.form.password, type='password', label=u'Пароль')}
            <input type="hidden" name="came_from" value="${c.form.came_from.cvalue}">

            <div class="control-group">
                <div class="controls">
                    <button class="btn">Войти</button>
                </div>
            </div>
        </form>

        <p>
            <a class="social twitter" href="${path('twitter-login')}"><span></span>Войти через Twitter</a>
            <a class="social facebook" href="${path('facebook-login')}"><span></span>Войти через Facebook</a>
            <a class="social vkontakte" href="${path('vkontakte-login')}"><span></span>Войти через Вконтакте</a>
        </p>

        <p><a href="${path('reset-password')}">Забыли пароль?</a></p>
        <p><a href="${path('register')}">Зарегистрироваться</a></p>
    </div>
</div>


<div class="col-right">
    <div class="block-shadow">
        ${b.right_col_menu()}
    </div>
</div>
