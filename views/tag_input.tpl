<div class="side-by-side-help-container">
    <label>{{get("label", "Tags:")}}
        <input type="text" name="{{input_name}}" value="{{get('input_value', '')}}">
    </label>
    % include("hover_help.tpl", text="Space-separated. Backslashes escape spaces.")
</div>
