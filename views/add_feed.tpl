<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add Feed | TagRSS</title>
    <link href="/static/styles/main.css" rel="stylesheet">
</head>
<body>
    <a href="/" class="no-visited-indication">&lt; home</a>
    % if not get("already_present", False):
        % if get("after_add", False):
            <p><em>Added feed {{feed_source}}</em></p>
        % end
    % else:
        <p><em>Feed {{feed_source}} was already added; no changes made.</em></p>
    % end
    <h1>Add a feed</h1>
    <form method="post">
        <label>Source:
            <input type="url" name="feed_source">
        </label>
        <br>
        % include("tag_input.tpl", input_name="tags")
        <input type="submit" value="Add">
    </form>
    % include("footer.tpl")
</body>
</html>
