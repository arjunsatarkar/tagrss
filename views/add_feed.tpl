<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add Feed | TagRSS</title>
    <link href="/static/styles/main.css" rel="stylesheet">
</head>
<body>
    <a href="/">&lt; home</a>
    % if not get("already_present", False):
        % if get("after_add", False):
            <p><em>Added feed {{feed_source}}</em></p>
        % end
    % else:
        <p><em>Feed {{feed_source}} was already added; no changes made.</em></p>
    % end
    <h1>Add a feed</h1>
    <form method="post">
        <input type="url" placeholder="Feed source" name="feed_source">
        <br>
        <div class="side-by-side-help-container">
            <input type="text" placeholder="Tags" name="tags">
            <span class="hover-help" tabindex="0" title="Space separated. Backslashes escape spaces.">🛈</span>
        </div>
        <br>
        <input type="submit" value="Add">
    </form>
</body>
</html>
