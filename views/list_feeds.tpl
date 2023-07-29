<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>List Feeds | TagRSS</title>
    <link href="/static/styles/main.css" rel="stylesheet">
</head>
<body>
    <a href="/" class="no-visited-indication">&lt; home</a>
    <h1>Feeds</h1>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>ID</th>
                <th>Feed</th>
                <th>Source</th>
                <th>Manage</th>
            </tr>
        </thead>
        <tbody>
            % for i, feed in enumerate(feeds):
                <tr>
                    <td>{{i + 1 + offset}}</td>
                    <td>{{feed["id"]}}</td>
                    <td>{{feed["title"]}} (<a href="/?included_feeds={{feed['id']}}" class="no-visited-indication">filter</a>)</td>
                    <td><a href="{{feed['source']}}" class="no-visited-indication">🔗</a></td>
                    <td><a href="/manage_feed?feed={{feed['id']}}" class="no-visited-indication">⚙</a></td>
                </tr>
            % end
        </tbody>
    </table>
    <form>
        <label>Page
            <input type="number" value="{{page_num}}" min="1" max="{{total_pages}}" name="page_num">
        </label> of {{total_pages}}.
        <label>Per page:
            <input type="number" value="{{per_page}}" min="1" max="{{max_per_page}}" name="per_page">
        </label>
        <input type="submit" value="Go">
    </form>
    % include("footer.tpl")
</body>
</html>
