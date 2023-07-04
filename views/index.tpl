<%
    import time
%>
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
                <th>Feed</th>
            </tr>
        </thead>
        <tbody>
            % for i, entry in enumerate(entries):
                <tr>
                    <td>{{i + 1}}</td>
                    <td><a href="{{entry["link"]}}">{{entry["title"]}}</a></td>
                    <%
                        dates = []
                        if entry.get("epoch_published", None):
                            dates.append(time.strftime("%x %X", time.localtime(entry["epoch_published"])))
                        end
                        if entry.get("epoch_updated", None):
                            date_updated = time.strftime("%x %X", time.localtime(entry["epoch_updated"]))
                            if not date_updated in dates:
                                dates.append(date_updated)
                            end
                        end
                    %>
                    <td>
                        {{", updated ".join(dates)}}
                    </td>
                    <td>
                        % tags = core.get_feed_tags(entry["feed_id"])
                        % for i, tag in enumerate(tags):
                            % if i > 0:
                                {{", "}}
                            % end
                            <span class="tag">{{tag}}</span>
                        % end
                    </td>
                    <td>
                        <a href="/manage_feed?feed={{entry["feed_id"]}}">⚙</a>
                    </td>
                </tr>
            % end
        </tbody>
    </table>
</body>
</html>
