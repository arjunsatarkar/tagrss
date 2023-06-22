<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Feeds</title>
</head>
<body>
    <table>
        <tr>
            <th>Title</th>
            <th>Date</th>
        </tr>
        % for i, item in enumerate(reversed(items)):
            <tr>
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
            </tr>
        % end
    </table>
</body>
</html>
