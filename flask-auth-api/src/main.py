from flask import Flask

from db.db import init_db
from commands.superuser import superuser_cli

app = Flask(__name__)
app.cli.add_command(superuser_cli)


@app.route('/hello-word')
def hell_word():
    return 'Hello, word'


if __name__ == '__main__':
    init_db()
    app.run()
