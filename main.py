from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from jinja2 import Template
import paramiko
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# Параметры подключения к SSH и базе данных
SSH_HOST = 'your_ssh_host'
SSH_PORT = 22
SSH_USER = 'your_ssh_user'
SSH_KEY_PATH = '/path/to/your/private/key'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'your_db_name'
DB_USER = 'your_db_user'
DB_PASSWORD = 'your_db_password'

# Основной шаблон HTML
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Data Table</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/clipboard@2.0.6/dist/clipboard.min.js"></script>
</head>
<body>
<div class="container">
    <h2>{{ title }}</h2>
    <form method="post" action="{{ url }}" class="mb-3">
        <div class="input-group mb-2">
            <input type="text" name="filter" placeholder="Filter" class="form-control" value="{{ filter }}">
            <button type="submit" class="btn btn-primary">Apply Filter</button>
        </div>
        <div>
            <button type="submit" name="filter" value="" class="btn btn-secondary">Clear Filter</button>
        </div>
    </form>
    <table class="table table-bordered">
        <thead>
            <tr>
                {% for col in columns %}
                <th>{{ col }}</th>
                {% endfor %}
                <th>Copy</th>
            </tr>
        </thead>
        <tbody>
            {% for row in data %}
            <tr>
                {% for col in row %}
                <td>{{ col }}</td>
                {% endfor %}
                <td><button class="btn btn-secondary btn-sm" data-clipboard-text="{{ row|join('|') }}">Copy</button></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
<script>
    new ClipboardJS('.btn');
</script>
</body>
</html>
"""

# Функция для подключения к базе данных через SSH


def get_db_connection():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER,
                   key_filename=SSH_KEY_PATH)

    transport = client.get_transport()
    channel = transport.open_channel(
        "direct-tcpip", (DB_HOST, int(DB_PORT)), ("localhost", 0))

    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}',
                           connect_args={'host': 'localhost', 'port': channel})
    Session = sessionmaker(bind=engine)
    return Session()

# Функция для выполнения запроса к базе данных и получения результатов


def fetch_data_from_db(query: str, filter: str):
    session = get_db_connection()
    if filter:
        query = query.replace(";", f" WHERE your_column LIKE '%{filter}%';")
    result = session.execute(query)
    columns = result.keys()
    data = result.fetchall()
    session.close()
    return columns, data

# Основной маршрут для отображения данных


@app.get("/", response_class=HTMLResponse)
@app.post("/", response_class=HTMLResponse)
async def read_data(request: Request, filter: str = Form(None)):
    query = "SELECT * FROM your_table;"
    columns, data = fetch_data_from_db(query, filter)
    template = Template(html_template)
    return template.render(title="Main Data Table", url="/", columns=columns, data=data, filter=filter or "")

# Новый маршрут для другой страницы с другим запросом


@app.get("/another_page", response_class=HTMLResponse)
@app.post("/another_page", response_class=HTMLResponse)
async def another_page(request: Request, filter: str = Form(None)):
    query = "SELECT * FROM another_table;"
    columns, data = fetch_data_from_db(query, filter)
    template = Template(html_template)
    return template.render(title="Another Data Table", url="/another_page", columns=columns, data=data, filter=filter or "")

# Запуск FastAPI сервера
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
