##
##
##

<%def name="render_message(msg)">
    % if hasattr(messages, msg.message_id):
        ${getattr(messages, msg.message_id)(msg.params)}
    % else:
        <div class="alert alert-info">
            <p>${msg.message_id}</p>
        </div>
    % endif
</%def>


<%def name="flash_messages(queue=u'')">
    <% flash_msgs = request.session.pop_flash(queue) %>
    % if flash_msgs:
        <div id="flash-messages">
            % for msg in flash_msgs:
                ${self.render_message(msg)}
            % endfor
        </div>
    % endif
</%def>
