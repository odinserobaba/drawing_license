from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from jinja2 import Template
import re

app = FastAPI()

# Темный шаблон HTML с Bootstrap, фильтрацией, сортировкой и копированием
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-dark-5@1.1.3/dist/css/bootstrap-dark.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/clipboard@2.0.6/dist/clipboard.min.js"></script>
</head>
<body class="bg-dark text-light">
<div class="container">
    <h2>{{ title }}</h2>
    <form method="post" action="{{ url }}" class="mb-3">
        <div class="input-group mb-2">
            <input type="text" name="filter" placeholder="Filter (e.g., age > 30)" class="form-control" value="{{ filter }}">
            <button type="submit" class="btn btn-primary">Apply Filter</button>
        </div>
        <div>
            <button type="submit" name="filter" value="" class="btn btn-secondary">Clear Filter</button>
        </div>
    </form>
    <table class="table table-bordered table-dark">
        <thead>
            <tr>
                {% for col in columns %}
                <th>
                    <form method="post" action="{{ url }}" style="display:inline;">
                        <input type="hidden" name="filter" value="{{ filter }}">
                        <button type="submit" name="sort" value="{{ col }}" class="btn btn-link text-light">{{ col }} 
                            {% if current_sort == col and order == 'asc' %}
                                ▲
                            {% elif current_sort == col and order == 'desc' %}
                                ▼
                            {% endif %}
                        </button>
                        <input type="hidden" name="order" value="{% if current_sort == col %}{{ 'desc' if order == 'asc' else 'asc' }}{% else %}asc{% endif %}">
                    </form>
                </th>
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
    <button class="btn btn-secondary mt-3" id="copy-all" data-clipboard-text="{{ all_data }}">Copy All</button>
</div>
<script>
    new ClipboardJS('.btn');
    new ClipboardJS('#copy-all');
</script>
</body>
</html>
"""

# Фейковые данные для тестирования
fake_data = [
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob", "age": 24},
    {"id": 3, "name": "Charlie", "age": 29},
    {"id": 4, "name": "David", "age": 35},
    {"id": 5, "name": "Eve", "age": 22}
]

# Преобразование фейковых данных в формат, подходящий для шаблона
columns = list(fake_data[0].keys())
data = [list(item.values()) for item in fake_data]

# Функция для фильтрации данных


def filter_data(data, filter_value):
    if not filter_value:
        return data
    pattern = re.compile(r'(\w+)\s*(>|<|=|>=|<=|!=)\s*(\d+)')
    match = pattern.match(filter_value)
    if match:
        field, operator, value = match.groups()
        value = int(value)
        filtered_data = []
        for row in data:
            row_dict = dict(zip(columns, row))
            if field in row_dict:
                if operator == '>' and row_dict[field] > value:
                    filtered_data.append(row)
                elif operator == '<' and row_dict[field] < value:
                    filtered_data.append(row)
                elif operator == '=' and row_dict[field] == value:
                    filtered_data.append(row)
                elif operator == '>=' and row_dict[field] >= value:
                    filtered_data.append(row)
                elif operator == '<=' and row_dict[field] <= value:
                    filtered_data.append(row)
                elif operator == '!=' and row_dict[field] != value:
                    filtered_data.append(row)
        return filtered_data
    else:
        return [row for row in data if filter_value.lower() in str(row).lower()]

# Функция для сортировки данных


def sort_data(data, sort_by, order):
    index = columns.index(sort_by)
    reverse = order == 'desc'
    return sorted(data, key=lambda x: x[index], reverse=reverse)

# Основной маршрут для отображения данных


@app.get("/", response_class=HTMLResponse)
@app.post("/", response_class=HTMLResponse)
async def read_data(request: Request, filter: str = Form(None), sort: str = Form(None), order: str = Form(None)):
    global columns
    filtered_data = filter_data(data, filter)
    if sort:
        filtered_data = sort_data(filtered_data, sort, order)
        # Не меняем порядок сортировки для следующего нажатия
        order = order
    else:
        order = 'asc'  # Если сортировка не указана, считаем, что нужно сортировать по возрастанию
    all_data = '\n'.join(['|'.join(map(str, row)) for row in filtered_data])
    template = Template(html_template)
    return template.render(title="Main Data Table", url="/", columns=columns, data=filtered_data, filter=filter or "", all_data=all_data, current_sort=sort, order=order)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.2", port=8000)
