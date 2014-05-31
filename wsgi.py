import web
import poker
import os
import logging

LOG_DIR = os.environ.get('OPENSHIFT_PYTHON_LOG_DIR', './').strip()
LOG_FILE = os.path.join(LOG_DIR, 'pokerbot.log')
LOG = logging.getLogger("bot")
poker.logs.set_logging_options(color=False, filename=LOG_FILE)

urls = (
    '/', 'index'
)

app = web.application(urls, globals())


class index:
    def GET(self):
        return self.POST()

    def POST(self):
        form = web.input(name="", pocket="", actions="", state="")
        try:
            bot = poker.get_bot(form.name, form.pocket,
                                form.actions, form.state)
            return bot.decide()
        except Exception, e:
            LOG.exception(e)
            raise

application = app.wsgifunc()


if __name__ == "__main__":
    app.run()
