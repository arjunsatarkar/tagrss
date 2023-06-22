<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Feeds | TagRSS</title>
    <link href="/static/styles/main.css" rel="stylesheet">
</head>
<body>
    <h1>TagRSS</h1>
    <nav>
        <p><a href="/add_feed">Add feed</a></p>
    </nav>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Title</th>
                <th>Date</th>
                <th>Tags</th>
            </tr>
        </thead>
        <tbody>
            % for i, item in enumerate(reversed(items)):
                <tr>
                    <td>{{i + 1}}</td>
                    <td><a href="{{item["link"]}}">{{item["title"]}}</a></td>
                    <%
                        dates = []
                        if item.get("date_published", None):
                            dates.append(item["date_published"])
                        end
                        if item.get("date_updated", None):
                            dates.append(item["date_updated"])
                        end
                    %>
                    <td>
                        {{", updated ".join(dates)}}
                    </td>
                    <td>
                        {{", ".join(item["feed"]["tags"])}}
                    </td>
                </tr>
            % end
        </tbody>
    </table>
</body>
</html>
