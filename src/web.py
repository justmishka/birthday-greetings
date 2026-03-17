from __future__ import annotations

import json
import tempfile
from datetime import date, datetime
from pathlib import Path
from string import Template

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote

from src.adapters.file_repository import FileFriendRepository
from src.domain.birthday_service import compose_greeting, compose_reminders, find_birthdays
from src.domain.models import Friend, Message

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

HTML_PAGE = Template("""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Birthday Greetings</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            padding: 2rem;
        }
        .container { max-width: 780px; width: 100%; }
        h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #f472b6, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        h2 { font-size: 1.2rem; color: #cbd5e1; margin-bottom: 1rem; }
        .subtitle { color: #94a3b8; margin-bottom: 2rem; }
        .card {
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid #334155;
        }
        label { display: block; font-weight: 600; margin-bottom: 0.5rem; color: #cbd5e1; font-size: 0.9rem; }
        input[type="text"], input[type="email"], input[type="date"] {
            background: #0f172a;
            border: 1px solid #475569;
            border-radius: 8px;
            color: #e2e8f0;
            padding: 0.5rem 0.75rem;
            font-size: 0.9rem;
            width: 100%;
        }
        input:focus { outline: none; border-color: #c084fc; }
        select {
            background: #0f172a;
            border: 1px solid #475569;
            border-radius: 8px;
            color: #e2e8f0;
            padding: 0.5rem 0.75rem;
            font-size: 0.9rem;
        }
        select:focus { outline: none; border-color: #c084fc; }
        button {
            background: linear-gradient(135deg, #f472b6, #c084fc);
            color: #0f172a;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.5rem;
            font-size: 0.9rem;
            font-weight: 700;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.9; }
        .btn-sm {
            padding: 0.3rem 0.8rem;
            font-size: 0.75rem;
            border-radius: 6px;
        }
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        .btn-secondary {
            background: #475569;
            color: #e2e8f0;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr auto;
            gap: 0.5rem;
            align-items: end;
            margin-bottom: 1rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1rem;
        }
        th {
            text-align: left;
            padding: 0.5rem;
            color: #94a3b8;
            font-size: 0.8rem;
            text-transform: uppercase;
            border-bottom: 1px solid #334155;
        }
        td {
            padding: 0.5rem;
            border-bottom: 1px solid #1e293b;
            font-size: 0.9rem;
        }
        tr:hover td { background: #1e293b88; }
        .check-row {
            display: flex;
            gap: 0.75rem;
            align-items: end;
            flex-wrap: wrap;
        }
        .check-row > div { flex: 0 0 auto; }
        .hint {
            font-size: 0.8rem;
            color: #64748b;
            margin-top: 0.25rem;
        }
        .date-info {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            color: #94a3b8;
            font-size: 0.9rem;
        }
        .date-info strong { color: #f1f5f9; }
        .results { margin-top: 1.5rem; }
        .msg-card {
            background: #1e293b;
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            border-left: 4px solid #c084fc;
        }
        .msg-card.greeting { border-left-color: #f472b6; }
        .msg-card.reminder { border-left-color: #38bdf8; }
        .msg-to { font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.25rem; }
        .msg-subject { font-weight: 700; color: #f1f5f9; margin-bottom: 0.5rem; }
        .msg-body { color: #cbd5e1; white-space: pre-line; }
        .tag {
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            margin-bottom: 0.5rem;
        }
        .tag.greeting { background: #f472b633; color: #f472b6; }
        .tag.reminder { background: #38bdf833; color: #38bdf8; }
        .empty { color: #64748b; font-style: italic; padding: 1rem 0; }
        .count { color: #94a3b8; margin-bottom: 1rem; }
        .friend-count { color: #64748b; font-size: 0.85rem; margin-bottom: 0.5rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Birthday Greetings</h1>
        <p class="subtitle">Manage your friends list and check who has a birthday on any date.</p>

        <!-- Friends Table -->
        <div class="card">
            <h2>Friends</h2>
            $friends_table

            <!-- Add Friend Form -->
            <form method="POST" action="/add">
                <input type="hidden" name="friends_json" value="$friends_json_escaped">
                <div class="form-row">
                    <div>
                        <label>First name</label>
                        <input type="text" name="first_name" required placeholder="John">
                    </div>
                    <div>
                        <label>Last name</label>
                        <input type="text" name="last_name" required placeholder="Doe">
                    </div>
                    <div>
                        <label>Date of birth</label>
                        <input type="date" name="dob" required>
                    </div>
                    <div>
                        <label>Email</label>
                        <input type="email" name="email" required placeholder="john@example.com">
                    </div>
                    <div>
                        <label>&nbsp;</label>
                        <button type="submit">Add</button>
                    </div>
                </div>
            </form>
        </div>

        <!-- Check Birthdays -->
        <div class="card">
            <h2>Check birthdays</h2>
            <p class="hint" style="margin-bottom: 1rem;">Pick any date to see who has a birthday. Only month and day are matched — birth year is ignored.</p>
            <form method="POST" action="/check">
                <input type="hidden" name="friends_json" value="$friends_json_escaped">
                <div class="check-row">
                    <div>
                        <label>Month</label>
                        <select name="month">
                            $month_options
                        </select>
                    </div>
                    <div>
                        <label>Day</label>
                        <select name="day">
                            $day_options
                        </select>
                    </div>
                    <div>
                        <label>&nbsp;</label>
                        <button type="submit">Check birthdays</button>
                    </div>
                </div>
            </form>
        </div>

        $results
    </div>
</body>
</html>
""")


def _render_friends_table(friends: list[Friend]) -> str:
    if not friends:
        return '<p class="empty">No friends added yet.</p>'

    html = f'<p class="friend-count">{len(friends)} friend(s)</p>'
    html += "<table><thead><tr>"
    html += "<th>Name</th><th>Birthday</th><th>Email</th><th></th>"
    html += "</tr></thead><tbody>"

    for i, f in enumerate(friends):
        month_name = MONTHS[f.date_of_birth.month - 1]
        bday = f"{month_name} {f.date_of_birth.day}"
        html += f"""<tr>
            <td>{_esc(f.first_name)} {_esc(f.last_name)}</td>
            <td>{bday}</td>
            <td>{_esc(f.email)}</td>
            <td><form method="POST" action="/delete" style="display:inline">
                <input type="hidden" name="friends_json" value="{_esc(_friends_to_json(friends))}">
                <input type="hidden" name="index" value="{i}">
                <button type="submit" class="btn-sm btn-danger">Remove</button>
            </form></td>
        </tr>"""

    html += "</tbody></table>"
    return html


def _render_results(messages: list[Message], month: int, day: int) -> str:
    month_name = MONTHS[month - 1]

    if not messages:
        return f'<div class="results"><div class="date-info">No birthdays on <strong>{month_name} {day}</strong>.</div></div>'

    greetings = [m for m in messages if m.subject == "Happy birthday!"]
    reminders = [m for m in messages if m.subject == "Birthday Reminder"]

    html = '<div class="results">'
    html += f'<div class="date-info">Birthdays on <strong>{month_name} {day}</strong>: {len(greetings)} greeting(s), {len(reminders)} reminder(s)</div>'

    for m in greetings:
        html += f'''<div class="msg-card greeting">
            <span class="tag greeting">Greeting</span>
            <div class="msg-to">To: {_esc(m.to)}</div>
            <div class="msg-subject">{_esc(m.subject)}</div>
            <div class="msg-body">{_esc(m.body)}</div>
        </div>'''

    for m in reminders:
        html += f'''<div class="msg-card reminder">
            <span class="tag reminder">Reminder</span>
            <div class="msg-to">To: {_esc(m.to)}</div>
            <div class="msg-subject">{_esc(m.subject)}</div>
            <div class="msg-body">{_esc(m.body)}</div>
        </div>'''

    html += '</div>'
    return html


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _friends_to_json(friends: list[Friend]) -> str:
    return json.dumps([
        {
            "last_name": f.last_name,
            "first_name": f.first_name,
            "dob": f.date_of_birth.isoformat(),
            "email": f.email,
        }
        for f in friends
    ])


def _friends_from_json(raw: str) -> list[Friend]:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    friends = []
    for item in data:
        try:
            friends.append(Friend(
                last_name=item["last_name"],
                first_name=item["first_name"],
                date_of_birth=date.fromisoformat(item["dob"]),
                email=item["email"],
            ))
        except (KeyError, ValueError):
            continue
    return friends


DEFAULT_FRIENDS = [
    Friend("Doe", "John", date(1982, 10, 8), "john.doe@foobar.com"),
    Friend("Ann", "Mary", date(1975, 9, 11), "mary.ann@foobar.com"),
    Friend("Leap", "Larry", date(2000, 2, 29), "larry.leap@foobar.com"),
    Friend("Smith", "Bob", date(1988, 10, 8), "bob.smith@foobar.com"),
]


def _month_options(selected: int) -> str:
    html = ""
    for i, name in enumerate(MONTHS, 1):
        sel = ' selected' if i == selected else ''
        html += f'<option value="{i}"{sel}>{name}</option>\n'
    return html


def _day_options(selected: int) -> str:
    html = ""
    for d in range(1, 32):
        sel = ' selected' if d == selected else ''
        html += f'<option value="{d}"{sel}>{d}</option>\n'
    return html


def _render_page(friends: list[Friend], results: str = "", month: int = 0, day: int = 0) -> str:
    if month == 0:
        month = date.today().month
    if day == 0:
        day = date.today().day

    return HTML_PAGE.substitute(
        friends_table=_render_friends_table(friends),
        friends_json_escaped=_esc(_friends_to_json(friends)),
        month_options=_month_options(month),
        day_options=_day_options(day),
        results=results,
    )


class BirthdayHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        html = _render_page(DEFAULT_FRIENDS)
        self._respond(200, html)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        params = parse_qs(body)
        path = self.path

        friends_json = params.get("friends_json", ["[]"])[0]
        friends = _friends_from_json(friends_json)

        if path == "/add":
            first = params.get("first_name", [""])[0].strip()
            last = params.get("last_name", [""])[0].strip()
            dob_str = params.get("dob", [""])[0]
            email = params.get("email", [""])[0].strip()
            if first and last and dob_str and email:
                try:
                    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                    friends.append(Friend(last, first, dob, email))
                except ValueError:
                    pass
            html = _render_page(friends)

        elif path == "/delete":
            idx = int(params.get("index", ["0"])[0])
            if 0 <= idx < len(friends):
                friends = friends[:idx] + friends[idx + 1:]
            html = _render_page(friends)

        elif path == "/check":
            month = int(params.get("month", [str(date.today().month)])[0])
            day = int(params.get("day", [str(date.today().day)])[0])
            # Use a reference year for the check — 2024 is a leap year so Feb 29 works
            try:
                check_date = date(2024, month, day)
            except ValueError:
                check_date = date(2024, month, 28)  # fallback for invalid dates like Feb 30

            celebrants = find_birthdays(friends, check_date)
            messages = []
            for c in celebrants:
                messages.append(compose_greeting(c))
            messages.extend(compose_reminders(celebrants, friends))

            results_html = _render_results(messages, month, day)
            html = _render_page(friends, results_html, month, day)

        else:
            html = _render_page(friends)

        self._respond(200, html)

    def _respond(self, status: int, html: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass


def main():
    port = 8080
    server = HTTPServer(("", port), BirthdayHandler)
    print(f"Birthday Greetings running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
