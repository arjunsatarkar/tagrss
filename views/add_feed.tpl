<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add Feed</title>
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
        <input type="submit" value="Add">
    </form>
</body>
</html>
