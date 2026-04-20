with open("app.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    'string_key = "aggregate_" + str(hash("".join(selected_island_keys)))',
    'string_key = f"aggregate_{len(selected_island_keys)}_{selected_island_keys[0] if selected_island_keys else \'none\'}"'
)
text = text.replace(
    'key=f"map_{abs(hash(string_key))}_{selected_year}_{active_layer}",',
    'key=f"map_{string_key}_{selected_year}_{active_layer}",'
)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(text)
