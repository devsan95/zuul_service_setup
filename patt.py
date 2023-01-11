import re

txt = str(b'httpd                            RUNNING   pid 337, uptime 0:00:02\nzuul-launcher                    RUNNING   pid 336, uptime 0:00:02\nzuul-server                      RUNNING   pid 338, uptime 0:00:02\n')
processes = txt.split('\\n')
res = '\n'.join(processes)
print(res)
