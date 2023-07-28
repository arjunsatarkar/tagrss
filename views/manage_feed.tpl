<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manage Feed | TagRSS</title>
    <link href="/static/styles/main.css" rel="stylesheet">
</head>
<body>
    <a href="/" class="no-visited-indication">&lt; home</a>
    % if get("after_update", False):
        <p><em>Updated feed details.</em></p>
    % end
    <h1>Manage feed</h1>
    <table>
        <tr>
            <th>Title</th>
            <td>{{feed["title"]}}</td>
        </tr>
        <tr>
            <th>Source</th>
            <td><a href="{{feed['source']}}" class="no-visited-indication">{{feed["source"]}}</a></td>
        </tr>
        <tr>
            <th>Tags</th>
            <td>
                % tags = feed["tags"]
                % for i, tag in enumerate(tags):
                    % if i > 0:
                        {{", "}}
                    % end
                    <span class="tag">{{tag}}</span>
                % end
            </td>
        </tr>
    </table>
    <form method="post">
        <input type="number" name="id" value="{{feed['id']}}" style="display: none;">
        <label>Title:
            <input type="text" name="title" value="{{feed['title']}}"><br>
        </label>
        <label>Source:
            <input type="text" name="source" value="{{feed['source']}}"><br>
        </label>
        <div class="side-by-side-help-container">
            <label>Tags:
                <input type="text" name="tags" value="{{feed['serialised_tags']}}">
            </label>
            <span class="hover-help" tabindex="0" title="Space separated. Backslashes escape spaces.">🛈</span>
        </div>
        <input type="submit" value="Update" name="update_feed">
    </form>
    <hr>
    <form method="post" action="/delete_feed">
        <input type="number" name="id" value="{{feed['id']}}" style="display: none;">
        <input type="submit" value="Delete" name="delete_feed">
    </form>
    % include("footer.tpl")
</body>
</html>