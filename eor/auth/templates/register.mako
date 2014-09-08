<%page/>
<%inherit file="victoria.site:templates/00layout.mako"/>
<%namespace name="b" file="victoria.site:templates/00blocks.mako" import="*"/>
<%namespace name="form" file="victoria.site:templates/blocks/forms.mako" import="*"/>

<%block name="page_title">Регистрация нового пользователя</%block>

<%block name="head">
    <h2 class="page-title">${self.page_title()}</h2>
</%block>

<div class="col-left">
    <div class="block-shadow">
        % if getattr(c, 'non_unique', False):
            <div class="alert alert-error">
                <p>Если вы забыли пароль, не пытайтесь зарегистрироваться еще раз.
                <p>Вы можете <a href="${path('reset-password')}">восстановить доступ</a> самостоятельно или связаться с менеджером.</p>
            </div>
        % endif

        <form method="POST" action="" class="form-horizontal">
            ${form.form_field(c.form.login, label=u'Имя пользователя')}
            ${form.form_field(c.form.email, label=u'Электронная почта')}
            ${form.form_field(c.form.name, label=u'Ваше имя')}
            ${form.form_field(c.form.password1, type='password', label=u'Пароль')}
            ${form.form_field(c.form.password2, type='password', label=u'Пароль еще раз')}

            <div class="control-group">
                <div class="controls">
                    <button class="btn">Зарегистрироваться</button>
                </div>
            </div>
        </form>
    </div>
</div>


<div class="col-right">
    <div class="block-shadow">
        ${b.right_col_menu()}
    </div>
</div>
